from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import requests
import json
import re
import os
import datetime

# --- Constants ---
OPENFDA_API_URL = "https://api.fda.gov/drug/event.json"
# Use /tmp for Vercel serverless environment (ephemeral storage)
# In production with persistence, this should be a database.
DATA_FILE = "/tmp/adverse_events.json" if os.environ.get("VERCEL") else "adverse_events.json"

app = FastAPI()

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    data: Optional[List[str]] = None
    report_saved: bool = False
    missing_info: Optional[List[str]] = None

# --- Core Functions (Merged from fda_chatbot.py) ---

def fetch_adverse_events(drug_name):
    print(f"DEBUG: Fetching adverse events for '{drug_name}'...")
    try:
        params = {
            'search': f'patient.drug.medicinalproduct:"{drug_name}"',
            'limit': 5
        }
        response = requests.get(OPENFDA_API_URL, params=params, timeout=10) # Added timeout
        response.raise_for_status()
        
        data = response.json()
        
        if 'results' not in data:
            return None
            
        events = []
        for result in data['results']:
            reactions = [r.get('reactionmeddrapt', 'Unknown') for r in result.get('patient', {}).get('reaction', [])]
            report_id = result.get('safetyreportid', 'N/A')
            events.append(f"Report {report_id}: {', '.join(reactions)}")
            
        return events

    except Exception as e:
        print(f"Error fetching data from OpenFDA: {e}")
        return None

def extract_adverse_event(user_input):
    patterns = [
        r"took\s+(?P<drug>.*?)\s+and\s+experienced\s+(?P<reaction>.*)",
        r"took\s+(?P<drug>.*?)\s+and\s+felt\s+(?P<reaction>.*)",
        r"took\s+(?P<drug>.*?)\s+and\s+had\s+(?P<reaction>.*)",
        r"after\s+taking\s+(?P<drug>.*?)\s*,\s*I\s+had\s+(?P<reaction>.*)",
        r"used\s+(?P<drug>.*?)\s+and\s+got\s+(?P<reaction>.*)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            return {
                "drug": match.group("drug").strip(),
                "reaction": match.group("reaction").strip(),
                "timestamp": datetime.datetime.now().isoformat()
            }
    return None

def save_adverse_event(event_data):
    try:
        # Load existing data
        if os.path.exists(DATA_FILE):
             with open(DATA_FILE, 'r') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = [] 
        else:
            existing_data = []
            
        existing_data.append(event_data)
        
        with open(DATA_FILE, 'w') as f:
            json.dump(existing_data, f, indent=4)
            
        print(f"Successfully saved report to {DATA_FILE}")
        
    except Exception as e:
        print(f"Error saving data: {e}")

def parse_message(user_input):
    text = user_input.strip().lower()
    
    # Query Patterns
    query_patterns = [
        r"show\s+(?:me\s+)?(?:adverse\s+events|side\s+effects)\s+(?:for|of)\s+(?P<drug>.*)",
        r"what\s+are\s+the\s+(?:adverse\s+events|side\s+effects)\s+(?:for|of)\s+(?P<drug>.*)",
        r"tell\s+me\s+about\s+(?:side\s+effects\s+of\s+)?(?P<drug>.*)",
        r"is\s+(?P<drug>.*)\s+safe",
        r"does\s+(?P<drug>.*)\s+have\s+side\s+effects",
        r"reactions\s+to\s+(?P<drug>.*)"
    ]
    
    for pattern in query_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return {
                "intent": "query",
                "drug": match.group("drug").strip("? ."),
                "reaction": None
            }

    # Report Patterns
    extracted_data = extract_adverse_event(user_input)
    if extracted_data:
        age_patterns = [
            r"age\s*(?:is|:|of)?\s*(\d{1,3})",
            r"(\d{1,3})\s*(?:years?|yrs?|yo)(?:\s+old)?",
            r"\((\d{1,3})\)"
        ]
        age = None
        for p in age_patterns:
            m = re.search(p, text)
            if m:
                age = m.group(1)
                break
        
        gender = None
        if re.search(r"\b(male|man|boy)\b", text):
            gender = "Male"
        elif re.search(r"\b(female|woman|girl)\b", text):
            gender = "Female"

        return {
            "intent": "report",
            "drug": extracted_data["drug"],
            "reaction": extracted_data["reaction"],
            "age": age,
            "gender": gender
        }
        
    return {"intent": "unknown", "drug": None, "reaction": None}

# --- API Routes ---

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    user_input = request.message.strip()
    
    if not user_input:
        return ChatResponse(response="Please say something!")

    parsed = parse_message(user_input)
    
    if parsed["intent"] == "query":
        drug_name = parsed["drug"]
        events = fetch_adverse_events(drug_name)
        
        if events:
            response_text = f"Found {len(events)} recent reports for {drug_name}."
            return ChatResponse(response=response_text, data=events)
        else:
            return ChatResponse(response=f"I couldn't find any specific adverse event reports for '{drug_name}' right now.")

    elif parsed["intent"] == "report":
        extracted_data = {
            "drug": parsed["drug"],
            "reaction": parsed["reaction"],
            "age": parsed.get("age"),
            "gender": parsed.get("gender"),
            "timestamp": "now"
        }
        
        missing = []
        if not extracted_data["age"]:
            missing.append("age")
        if not extracted_data["gender"]:
            missing.append("gender")
            
        if missing:
            return ChatResponse(
                response=f"I need a few more details to complete the report. Could you tell me the patient's {' and '.join(missing)}?",
                missing_info=missing
            )

        save_adverse_event(extracted_data)
        
        response_text = (
            f"I detected a potential adverse event and saved it.\n"
            f"Drug: {extracted_data['drug']}\n"
            f"Reaction: {extracted_data['reaction']}\n"
            f"Age: {extracted_data['age']}\n"
            f"Gender: {extracted_data['gender']}"
        )
        return ChatResponse(response=response_text, report_saved=True)

    return ChatResponse(
        response="I didn't quite catch that. Try asking 'What are the side effects of [drug]?' or 'I took [drug] and felt [symptom]'."
    )

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

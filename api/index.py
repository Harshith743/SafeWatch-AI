from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import sys

# Ensure we can import from local modules if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.utils import (
    fetch_adverse_events, 
    parse_with_llm, 
    parse_message, 
    save_adverse_event
)

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

# --- API Routes ---

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    user_input = request.message.strip()
    
    if not user_input:
        return ChatResponse(response="Please say something!")

    # 1. Try LLM first
    parsed = parse_with_llm(user_input)
    
    # 2. Fallback to Regex if LLM fails or is not configured
    if not parsed:
        print("Using Regex Fallback")
        parsed = parse_message(user_input)
    
    if parsed["intent"] == "query":
        drug_name = parsed.get("drug")
        if not drug_name:
             return ChatResponse(response="I couldn't identify the drug name. Could you specify which drug you are asking about?")

        events = fetch_adverse_events(drug_name)
        
        if events:
            response_text = f"Found {len(events)} recent reports for {drug_name}."
            return ChatResponse(response=response_text, data=events)
        else:
            return ChatResponse(response=f"I couldn't find any specific adverse event reports for '{drug_name}' right now.")

    elif parsed["intent"] == "report":
        extracted_data = {
            "drug": parsed.get("drug"),
            "reaction": parsed.get("reaction"),
            "age": parsed.get("age"),
            "gender": parsed.get("gender"),
            "timestamp": "now"
        }
        
        missing = []
        if not extracted_data.get("drug"):
             return ChatResponse(response="I couldn't identify the drug name. What drug did you take?")
        if not extracted_data.get("reaction"):
             return ChatResponse(response="I couldn't identify the reaction. What happened?")
             
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

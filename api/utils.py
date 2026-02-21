import requests
import json
import re
import os
import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# --- Configuration ---
# --- Configuration ---
# Load .env from the root directory (parent of backend/)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

print(f"DEBUG: Loading .env from {os.path.abspath(dotenv_path)}")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"DEBUG: GEMINI_API_KEY found: {bool(GEMINI_API_KEY)}")

OPENFDA_API_URL = "https://api.fda.gov/drug/event.json"
# Use /tmp for Vercel serverless environment (ephemeral storage)
# In production with persistence, this should be a database.
# For local dev, we can just use the local file.
DATA_FILE = "adverse_events.json" 

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash-lite') # Exact match from ListModels
        print("DEBUG: Gemini Model initialized successfully.")
    except Exception as e:
        print(f"DEBUG: Failed to initialize Gemini model: {e}")
        model = None
else:
    print("DEBUG: GEMINI_API_KEY is missing. Model not initialized.")
    model = None

# --- Core Functions ---

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
        KV_REST_API_URL = os.getenv("KV_REST_API_URL")
        KV_REST_API_TOKEN = os.getenv("KV_REST_API_TOKEN")

        # 1. Try Vercel KV (Upstash Redis) for production persistence
        if KV_REST_API_URL and KV_REST_API_TOKEN:
            from upstash_redis import Redis
            redis = Redis(url=KV_REST_API_URL, token=KV_REST_API_TOKEN)
            
            # Save the event to a Redis list
            redis.lpush("adverse_events", json.dumps(event_data))
            print("Successfully saved report to Vercel KV Database")
            return

        # 2. Fallback to local JSON file for local development
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

def parse_with_llm(user_input):
    """
    Uses Gemini API to extract structured data from user input.
    """
    print(f"DEBUG: Entering parse_with_llm. Model is: {model}")
    if not model:
        print(f"DEBUG: Model is None, returning None.")
        return None
        
    try:
        prompt = f"""
        Analyze the following user text related to drug safety/adverse events.
        Extract the following fields in JSON format:
        - intent: "query" (asking for info), "report" (reporting a personal experience), or "unknown"
        - drug: The name of the drug mentioned (or null)
        - reaction: The adverse event/reaction experienced (for reports) or asked about (optional for queries) (or null)
        - age: Patient age if mentioned (e.g., "25"), else null
        - gender: Patient gender if mentioned (e.g., "Male", "Female"), else null
    
        User Text: "{user_input}"
        """
        
        print(f"DEBUG: Sending prompt to Gemini...")
        # Use JSON mode for reliability
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        print(f"DEBUG: Raw LLM Response: {response.text}")
        
        data = json.loads(response.text)
        print(f"DEBUG: Parsed Data: {data}")
        return data
    except Exception as e:
        print(f"LLM Parse Error details: {type(e).__name__}: {str(e)}")
        return None

def parse_message(user_input):
    text = user_input.strip().lower()
    
    # Query Patterns - Expanded for robust natural language understanding
    query_patterns = [
        # --- Explicit "Show me" / "List" ---
        r"(?:please\s+)?(?:show|list|give|display|tell)\s+(?:me\s+)?(?:all\s+)?(?:the\s+)?(?:common\s+|potential\s+|possible\s+)?(?:adverse\s+events|side\s+effects|reactions|adverse\s+reactions|negative\s+effects|bad\s+effects|symptoms|issues|problems|complications|hazards|risks|dangers)\s+(?:associated\s+with|related\s+to|caused\s+by|for|of|from)\s+(?P<drug>.*)",
        
        # --- "What are" questions ---
        r"what\s+(?:are|can\s+be)\s+(?:the\s+)?(?:common\s+|potential\s+|possible\s+)?(?:adverse\s+events|side\s+effects|reactions|adverse\s+reactions|negative\s+effects|bad\s+effects|symptoms|issues|problems|complications|hazards|risks|dangers)(?:\s+reported)?\s+(?:associated\s+with|related\s+to|caused\s+by|for|of|from|to|with)\s+(?P<drug>.*)",
        r"what\s+(?:happens|can\s+happen)\s+(?:if|when)\s+(?:i|you|someone|one)\s+(?:take|takes|use|uses)\s+(?P<drug>.*)",
        r"what\s+(?:issues|problems)\s+(?:do|does)\s+(?P<drug>.*)\s+(?:cause|have)",
        
        # --- Safety / Danger questions ---
        r"(?:is|are)\s+(?P<drug>.*)\s+(?:safe|dangerous|harmful|bad|risky)(?:\s+to\s+take|to\s+use)?",
        r"how\s+(?:safe|dangerous|bad|risky)\s+is\s+(?P<drug>.*)",
        r"(?:safety|danger|risk)\s+(?:profile\s+)?of\s+(?P<drug>.*)",
        
        # --- "Does X cause Y?" (Generalized to catch the drug query) ---
        r"does\s+(?P<drug>.*?)\s+(?:cause|lead\s+to|result\s+in|trigger|produce|create|have)\s+(?:any\s+)?(?:side\s+effects|adverse\s+events|reactions|issues|problems)",
        r"can\s+(?P<drug>.*?)\s+(?:make\s+you|cause|lead\s+to|result\s+in)\s+(?:feel|have|experience)",
        
        # --- Specific "Issues with" / "Report on" ---
        r"(?:any\s+)?(?:reports|information|data|details|facts|complaints)\s+(?:on|about|regarding|concerning)\s+(?:the\s+)?(?:safety|side\s+effects|adverse\s+events)\s+(?:of|for|with)\s+(?P<drug>.*)",
        r"(?:problems|issues|concerns|trouble|complications)\s+(?:with|caused\s+by|from|using|taking)\s+(?P<drug>.*)",
        r"bad\s+(?:reactions|experiences?|things?)\s+(?:to|from|with)\s+(?P<drug>.*)",
        
        # --- Short / Conversational ---
        r"tell\s+me\s+about\s+(?P<drug>.*)",
        r"(?:side\s+effects|adverse\s+events|reactions)\s+(?:of|for)\s+(?P<drug>.*)",
        r"(?:side\s+effects|adverse\s+events|reactions)\s+(?P<drug>.*)", # "Side effects Ibuprofen"
        r"(?P<drug>.*?)\s+(?:side\s+effects|adverse\s+events|reactions|safety)", # "Ibuprofen side effects"
        
        # --- Catch-all "Reactions to" ---
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

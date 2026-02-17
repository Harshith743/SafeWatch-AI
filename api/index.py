
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import fda_chatbot

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

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    user_input = request.message.strip()
    
    if not user_input:
        return ChatResponse(response="Please say something!")

    # Logic from chatbot() function in fda_chatbot.py adapted for API
    parsed = fda_chatbot.parse_message(user_input)
    
    # 1. Check for query
    if parsed["intent"] == "query":
        drug_name = parsed["drug"]
        events = fda_chatbot.fetch_adverse_events(drug_name)
        
        if events:
            response_text = f"Found {len(events)} recent reports for {drug_name}."
            return ChatResponse(response=response_text, data=events)
        else:
            return ChatResponse(response=f"I couldn't find any specific adverse event reports for '{drug_name}' right now.")

    # 2. Check for report: "I took [drug] and experienced [reaction]"
    elif parsed["intent"] == "report":
        extracted_data = {
            "drug": parsed["drug"],
            "reaction": parsed["reaction"],
            "age": parsed.get("age"),
            "gender": parsed.get("gender"),
            "timestamp": "now" # In real app, use datetime
        }
        
        # Check for missing info
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

        # Save immediately for web demo
        fda_chatbot.save_adverse_event(extracted_data)
        
        response_text = (
            f"I detected a potential adverse event and saved it.\n"
            f"Drug: {extracted_data['drug']}\n"
            f"Reaction: {extracted_data['reaction']}\n"
            f"Age: {extracted_data['age']}\n"
            f"Gender: {extracted_data['gender']}"
        )
        return ChatResponse(response=response_text, report_saved=True)

    # 3. Fallback
    return ChatResponse(
        response="I didn't quite catch that. Try asking 'What are the side effects of [drug]?' or 'I took [drug] and felt [symptom]'."
    )

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

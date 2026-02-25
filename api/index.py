from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

from sqlalchemy.orm import Session
from api.database import engine, Base, get_db
from api.models import User
from api.auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta

# Initialize SQLite database
# This creates the file 'safewatch.db' and the 'users' table
Base.metadata.create_all(bind=engine)

from api.utils import (
    fetch_adverse_events, 
    parse_with_llm, 
    parse_message, 
    save_adverse_event,
    fetch_drug_statistics
)
from api.pdf_generator import generate_report_pdf

app = FastAPI()

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    email: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    data: Optional[List[str]] = None
    stats: Optional[List[dict]] = None
    report_saved: bool = False
    missing_info: Optional[List[str]] = None

# --- Auth Routes ---

@app.post("/api/signup", response_model=Token)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user_email = db.query(User).filter(User.email == user.email).first()
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    db_username = db.query(User).filter(User.username == user.username).first()
    if db_username:
        raise HTTPException(status_code=400, detail="Username already taken")
        
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "username": new_user.username, "email": new_user.email}

@app.post("/api/login", response_model=Token)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "username": db_user.username, "email": db_user.email}

from api.auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user, get_optional_current_user
from api.models import User, Report, SearchHistory
# ... (keep existing imports, handled below)
from typing import Optional, List

# ...

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_optional_current_user)):
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
        stats = fetch_drug_statistics(drug_name)
        
        # Save to search history if user is logged in
        if current_user and drug_name:
            history_record = SearchHistory(user_id=current_user.id, drug=drug_name)
            db.add(history_record)
            db.commit()
            
        if events:
            response_text = f"Found {len(events)} recent reports for {drug_name}."
            return ChatResponse(response=response_text, data=events, stats=stats)
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

        # Save to database if user is logged in
        if current_user:
            new_report = Report(
                user_id=current_user.id,
                drug=extracted_data["drug"],
                reaction=extracted_data["reaction"],
                age=extracted_data["age"],
                gender=extracted_data["gender"]
            )
            db.add(new_report)
            db.commit()
        else:
            # Fallback to local files if anonymous
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

@app.get("/api/user/reports")
async def get_user_reports(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reports = db.query(Report).filter(Report.user_id == current_user.id).order_by(Report.id.desc()).all()
    return reports

@app.get("/api/user/history")
async def get_user_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    history = db.query(SearchHistory).filter(SearchHistory.user_id == current_user.id).order_by(SearchHistory.id.desc()).all()
    return history

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/export/report/{report_id}")
async def export_report_pdf(report_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Find the report
    report = db.query(Report).filter(Report.id == report_id, Report.user_id == current_user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    # Generate the PDF
    pdf_buffer = generate_report_pdf(report)
    
    # Return File Stream Response
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename=safewatch_report_{report.id}.pdf"}
    )

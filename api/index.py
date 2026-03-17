from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Literal
import os
from sqlalchemy import inspect, text

from sqlalchemy.orm import Session
from api.database import engine, Base, get_db
from api.models import User
from api.auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta

# Initialize database tables
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

class ReportFormField(BaseModel):
    name: Literal["name", "age", "gender", "drug", "adverse_event"]
    label: str
    required: bool = True
    value: Optional[str] = None

class ReportForm(BaseModel):
    fields: List[ReportFormField]

class ChatResponse(BaseModel):
    response: str
    data: Optional[List[str]] = None
    stats: Optional[List[dict]] = None
    report_saved: bool = False
    missing_info: Optional[List[str]] = None
    warning: Optional[str] = None
    report_form: Optional[ReportForm] = None

class ReportSubmitRequest(BaseModel):
    name: str
    age: str
    gender: str
    drug: str
    adverse_event: str


def _ensure_reports_table_columns():
    """
    Lightweight migration for environments without Alembic.
    Ensures `reports.name` exists (nullable) for older databases.
    """
    try:
        inspector = inspect(engine)
        if "reports" not in inspector.get_table_names():
            return
        cols = {c["name"] for c in inspector.get_columns("reports")}
        if "name" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE reports ADD COLUMN name TEXT"))
    except Exception as e:
        # Avoid crashing the app on managed DBs with restricted permissions;
        # the feature will still work for fresh installs.
        print(f"WARNING: Could not ensure reports.name column: {e}")


_ensure_reports_table_columns()

class MedicationCreate(BaseModel):
    drug_name: str
    dosage: Optional[str] = None

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
from api.models import User, Report, SearchHistory, Medication
# ... (keep existing imports, handled below)
from typing import Optional, List

# ...

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_optional_current_user)):
    user_input = request.message.strip()
    
    if not user_input:
        return ChatResponse(response="Please say something!")

    user_medications = None
    if current_user:
        user_medications = db.query(Medication).filter(Medication.user_id == current_user.id).all()

    # 1. Try LLM first
    parsed = parse_with_llm(user_input, user_medications)
    
    warning = parsed.get("response_warning") if parsed else None
    
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
            return ChatResponse(response=response_text, data=events, stats=stats, warning=warning)
        else:
            return ChatResponse(response=f"I couldn't find any specific adverse event reports for '{drug_name}' right now.", warning=warning)

    elif parsed["intent"] == "report":
        extracted_drug = parsed.get("drug")
        extracted_reaction = parsed.get("reaction")

        fields: List[ReportFormField] = [
            ReportFormField(name="name", label="Name", value=None),
            ReportFormField(name="gender", label="Gender", value=parsed.get("gender")),
            ReportFormField(name="age", label="Age", value=parsed.get("age")),
            ReportFormField(name="drug", label="Drug", value=extracted_drug),
            ReportFormField(name="adverse_event", label="Adverse event", value=extracted_reaction),
        ]

        # UX: if we didn't extract anything, treat it as a direct "start a report" request
        if not extracted_drug and not extracted_reaction:
            response_text = "Sure — please fill out the report details below."
        else:
            response_text = "I started a report using what you shared. Please complete the remaining details below."

        return ChatResponse(
            response=response_text,
            warning=warning,
            report_form=ReportForm(fields=fields),
        )

    return ChatResponse(
        response=(
            "I couldn't understand that request. "
            "You can ask things like: 'What are the side effects of [drug]?' or "
            "'I took [drug] and felt [symptom]—is that a side effect?'."
        )
    )


@app.post("/api/report/submit", response_model=ChatResponse)
async def submit_report(
    request: ReportSubmitRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    payload = {
        "name": request.name.strip(),
        "age": request.age.strip(),
        "gender": request.gender.strip(),
        "drug": request.drug.strip(),
        "reaction": request.adverse_event.strip(),
    }

    missing = [k for k, v in payload.items() if not v]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required fields: {', '.join(missing)}")

    if current_user:
        new_report = Report(
            user_id=current_user.id,
            name=payload["name"],
            drug=payload["drug"],
            reaction=payload["reaction"],
            age=payload["age"],
            gender=payload["gender"],
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        return ChatResponse(
            response=f"Thanks - your adverse event report was submitted (Report #{new_report.id}).",
            report_saved=True,
        )

    # Anonymous fallback persistence
    save_adverse_event(
        {
            "name": payload["name"],
            "drug": payload["drug"],
            "reaction": payload["reaction"],
            "age": payload["age"],
            "gender": payload["gender"],
            "timestamp": "now",
        }
    )
    return ChatResponse(
        response="Thanks - your adverse event report was submitted.",
        report_saved=True,
    )

@app.get("/api/user/reports")
async def get_user_reports(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reports = db.query(Report).filter(Report.user_id == current_user.id).order_by(Report.id.desc()).all()
    return reports

@app.get("/api/user/history")
async def get_user_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    history = db.query(SearchHistory).filter(SearchHistory.user_id == current_user.id).order_by(SearchHistory.id.desc()).all()
    return history

@app.get("/api/user/medications")
async def get_user_medications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    medications = db.query(Medication).filter(Medication.user_id == current_user.id).order_by(Medication.id.desc()).all()
    return medications

@app.post("/api/user/medications")
async def add_user_medication(med: MedicationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_med = Medication(
        user_id=current_user.id,
        drug_name=med.drug_name,
        dosage=med.dosage
    )
    db.add(new_med)
    db.commit()
    db.refresh(new_med)
    return new_med

@app.delete("/api/user/medications/{med_id}")
async def delete_user_medication(med_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    med = db.query(Medication).filter(Medication.id == med_id, Medication.user_id == current_user.id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    db.delete(med)
    db.commit()
    return {"status": "deleted"}

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

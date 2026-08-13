"""
Main FastAPI app.

Endpoints:
  POST /api/upload-resume       -> parse an uploaded resume, return structured info
  POST /api/start-session       -> create a session, generate & store the first question
  POST /api/submit-answer       -> save an answer, generate & store the next question (or end)
  GET  /api/session-summary/{id}-> full transcript + status for a session

Run with:  uvicorn app.main:app --reload
Docs at:   http://127.0.0.1:8000/docs
"""

import os
import shutil

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app import models, schemas
from app.services.resume_parser import extract_text_from_resume, extract_resume_info
from app.services.retrieval import build_queries, retrieve_relevant_chunks
from app.services.question_generator import generate_question

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Recruiter RAG")

# Allows your Next.js frontend (running on a different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for local dev; tighten before any real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_QUESTIONS = 5
VALID_ROLES = ["AI Engineer", "ML Engineer", "Data Scientist"]


@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    os.makedirs("data/uploads", exist_ok=True)
    temp_path = f"data/uploads/{file.filename}"
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    text = extract_text_from_resume(temp_path)
    resume_info = extract_resume_info(text)
    return {"resume_info": resume_info}


@app.post("/api/start-session", response_model=schemas.StartSessionResponse)
def start_session(req: schemas.StartSessionRequest, db: Session = Depends(get_db)):
    if req.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"role must be one of {VALID_ROLES}")

    session = models.InterviewSession(role=req.role, resume_info=req.resume_info)
    db.add(session)
    db.commit()
    db.refresh(session)

    queries = build_queries(req.resume_info, req.role)
    chunks = retrieve_relevant_chunks(queries[0], req.role, top_k=3)
    result = generate_question(chunks, req.resume_info, req.role)

    qa = models.QuestionAnswer(
        session_id=session.id,
        question_text=result["question"],
        grounded_in_sources=result["grounded_in_sources"],
    )
    db.add(qa)
    db.commit()
    db.refresh(qa)

    return schemas.StartSessionResponse(session_id=session.id, question=qa.question_text, question_id=qa.id)


@app.post("/api/submit-answer", response_model=schemas.NextQuestionResponse)
def submit_answer(req: schemas.SubmitAnswerRequest, db: Session = Depends(get_db)):
    qa = db.query(models.QuestionAnswer).filter(models.QuestionAnswer.id == req.question_id).first()
    if not qa or qa.session_id != req.session_id:
        raise HTTPException(status_code=404, detail="question not found for this session")

    qa.answer_text = req.answer
    db.commit()

    session = db.query(models.InterviewSession).filter(models.InterviewSession.id == req.session_id).first()

    answered_count = (
        db.query(models.QuestionAnswer)
        .filter(models.QuestionAnswer.session_id == req.session_id, models.QuestionAnswer.answer_text.isnot(None))
        .count()
    )

    if answered_count >= MAX_QUESTIONS:
        session.status = "completed"
        db.commit()
        return schemas.NextQuestionResponse(session_id=session.id, interview_complete=True)

    asked_questions = [q.question_text for q in session.questions]
    queries = build_queries(session.resume_info, session.role)
    query = queries[answered_count % len(queries)]
    chunks = retrieve_relevant_chunks(query, session.role, top_k=3)
    result = generate_question(chunks, session.resume_info, session.role, asked_questions=asked_questions)

    new_qa = models.QuestionAnswer(
        session_id=session.id,
        question_text=result["question"],
        grounded_in_sources=result["grounded_in_sources"],
    )
    db.add(new_qa)
    db.commit()
    db.refresh(new_qa)

    return schemas.NextQuestionResponse(session_id=session.id, question=new_qa.question_text, question_id=new_qa.id)


@app.get("/api/session-summary/{session_id}")
def session_summary(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.InterviewSession).filter(models.InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    qas = [
        {"question": qa.question_text, "answer": qa.answer_text, "sources": qa.grounded_in_sources}
        for qa in session.questions
    ]

    return {
        "session_id": session.id,
        "role": session.role,
        "status": session.status,
        "questions_and_answers": qas,
    }

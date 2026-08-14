from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String, nullable=False)
    resume_info = Column(JSON, nullable=False)
    status = Column(String, default="in_progress")  # in_progress | completed
    insights = Column(Text, nullable=True)  # filled in once the interview completes
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    questions = relationship("QuestionAnswer", back_populates="session", order_by="QuestionAnswer.id")


class QuestionAnswer(Base):
    __tablename__ = "question_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=True)
    grounded_in_sources = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("InterviewSession", back_populates="questions")

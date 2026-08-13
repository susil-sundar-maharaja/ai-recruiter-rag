from typing import Optional
from pydantic import BaseModel


class StartSessionRequest(BaseModel):
    role: str
    resume_info: dict


class StartSessionResponse(BaseModel):
    session_id: int
    question: str
    question_id: int


class SubmitAnswerRequest(BaseModel):
    session_id: int
    question_id: int
    answer: str


class NextQuestionResponse(BaseModel):
    session_id: int
    question: Optional[str] = None
    question_id: Optional[int] = None
    interview_complete: bool = False

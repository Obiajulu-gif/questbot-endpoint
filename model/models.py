from pydantic import BaseModel
from typing import List, Optional

# Pydantic models for request/response validation
class QuizQuestionResponse(BaseModel):
    question: str
    options: List[str]
    hint: str
    complexity: int
    attempts_remaining: int
    error: Optional[str] = None

class AnswerRequestQuiz(BaseModel):
    answer: str

class AnswerCheckResponse(BaseModel):
    correct: bool
    message: str
    attempts_remaining: Optional[int] = None
    hint: Optional[str] = None
    complexity: Optional[int] = None

class BreakOptionsResponse(BaseModel):
    options: List[str]

class ResetResponse(BaseModel):
    message: str
    status: bool

class QueryRequest(BaseModel):
    query: str

class AnswerRequestRiddle(BaseModel):
    user_answer: str

class FunFactResponse(BaseModel):
    success: bool
    facts: str

from pydantic import BaseModel, validator
from typing import List, Optional, Literal

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


class ChallengeCreate(BaseModel):
    duration: int
    time_unit: Literal['minutes', 'hours', 'days', 'weeks'] = 'minutes'
    
    @validator('duration')
    def validate_duration(cls, v, values):
        time_unit = values.get('time_unit', 'minutes')
        
        # Maximum limits for different time units
        max_limits = {
            'minutes': 60 * 24 * 7,  # 1 week in minutes
            'hours': 24 * 7,         # 1 week in hours
            'days': 7,               # 7 days
            'weeks': 1               # 1 week
        }
        
        if v <= 0:
            raise ValueError('Duration must be greater than 0')
        
        if v > max_limits[time_unit]:
            raise ValueError(f'Duration must not exceed {max_limits[time_unit]} {time_unit}')
        
        return v

    def get_minutes(self) -> int:
        """Convert the duration to minutes based on the time unit"""
        conversion = {
            'minutes': 1,
            'hours': 60,
            'days': 60 * 24,
            'weeks': 60 * 24 * 7
        }
        return self.duration * conversion[self.time_unit]

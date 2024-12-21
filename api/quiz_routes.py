import sys
import os
import logging
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine.quiz_handler import BlockchainQuizGame
from model.models import QuizQuestionResponse, AnswerCheckResponse, BreakOptionsResponse, ResetResponse
from model.models import AnswerRequestQuiz as AnswerRequest

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



# Initialize FastAPI app
app = FastAPI(
    title="Blockchain Quiz API",
    description="An interactive API for a blockchain-themed quiz game",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a global game instance
game = BlockchainQuizGame()

@app.post("/quiz/question", response_model=QuizQuestionResponse)
async def get_quiz_question():
    """
    Generate a new quiz question.
    
    Returns:
        QuizQuestionResponse: A quiz question with options, hint, and complexity level
    """
    try:
        response = game.generate_quiz_question()
        
        # Ensure options are properly formatted as a list
        if isinstance(response['options'], str):
            response['options'] = [opt.strip() for opt in response['options'].split('\n')]
        
        return QuizQuestionResponse(**response)
    except Exception as e:
        logger.error(f"Error generating quiz question: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to generate question", "message": str(e)}
        )

@app.post("/quiz/answer", response_model=AnswerCheckResponse)
async def check_answer(answer_request: AnswerRequest):
    """
    Check the user's answer to the current quiz question.
    
    Args:
        answer_request (AnswerRequest): The answer submission

    Returns:
        AnswerCheckResponse: Feedback on the answer (correct/incorrect)
    """
    try:
        if not game.current_answer:
            raise HTTPException(
                status_code=400,
                detail="No active question. Please get a new question first."
            )
        
        response = game.check_answer(answer_request.answer)
        return AnswerCheckResponse(**response)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error checking answer: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to check answer", "message": str(e)}
        )

@app.post("/quiz/break", response_model=BreakOptionsResponse)
async def get_break_options():
    """
    Generate break options when the user wants to pause the quiz.
    
    Returns:
        BreakOptionsResponse: Suggested alternative activities
    """
    try:
        break_options = game.generate_break_options()
        # Convert string response to list if necessary
        if isinstance(break_options, str):
            options_list = [opt.strip() for opt in break_options.split('\n') if opt.strip()]
        else:
            options_list = break_options
            
        return BreakOptionsResponse(options=options_list)
    except Exception as e:
        logger.error(f"Error generating break options: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to generate break options", "message": str(e)}
        )

@app.post("/quiz/reset", response_model=ResetResponse)
async def reset_game():
    """
    Reset the game to its initial state.
    
    Returns:
        ResetResponse: A success message and status
    """
    global game
    try:
        game = BlockchainQuizGame()
        logger.info("Game reset successfully")
        return ResetResponse(message="Game reset successfully", status=True)
    except Exception as e:
        logger.error(f"Error resetting game: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to reset game", "message": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
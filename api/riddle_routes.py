import os
import sys
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# Ensure the parent directory is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the existing RiddleGame logic
from ai_engine.riddle_generation import RiddleGame
from model.models import AnswerRequestRiddle as AnswerRequest

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Blockchain Riddle Game API",
    description="API for an interactive blockchain riddle game",
    version="1.0.0"
)

# Add CORS middleware to allow frontend interactions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global game instance
game = RiddleGame()

@app.get("/riddle")
async def generate_riddle():
    """Generate a new riddle"""
    try:
        response = game.generate_riddle()

        if not response or "error" in response:
            logger.error("Error generating riddle: %s", response.get("error", "Unknown error"))
            raise HTTPException(status_code=500, detail=response.get("error", "Failed to generate riddle"))

        return {
            "riddle": response.get("riddle"),
            "hint": response.get("hint"),
            "complexity": response.get("complexity"),
            "attempts_remaining": response.get("attempts_remaining")
        }
    except Exception as e:
        logger.exception("Unexpected error during riddle generation")
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.post("/check-answer")
async def check_riddle_answer(answer_request: AnswerRequest):
    """Check the user's answer for the current riddle"""
    try:
        result = game.check_answer(answer_request.user_answer)
        return result
    except Exception as e:
        logger.exception("Unexpected error during answer checking")
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.get("/break-options")
async def get_break_options():
    """Get alternative activity options"""
    try:
        options = game.generate_break_options()
        return {"break_options": options}
    except Exception as e:
        logger.exception("Unexpected error during break options generation")
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.post("/quiz/reset")
async def reset_game():
    """
    Reset the game to its initial state.
    
    Returns:
    - A success message
    """
    global game
    try:
        game = RiddleGame()
        logger.info("Game reset successfully.")
        return {"message": "Game reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting game: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

import sys
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the parent directory is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import route modules
from api.quiz_routes import (
    game as quiz_game,
    get_quiz_question,
    check_answer,
    get_break_options as quiz_break_options,
    reset_game as reset_quiz
)
from api.riddle_routes import (
    game as riddle_game,
    generate_riddle,
    check_riddle_answer,
    get_break_options as riddle_break_options,
    reset_game as reset_riddle
)
from api.rag_routes import (
    startup_event,
    process_query,
    health_check
)

from api.fun_facts_routes import (
    get_random_fact
)

from api.creative_writing_routes import (
    create_challenge,
    evaluate_challenge,
    get_challenge_scores,
    get_challenge_status
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize main FastAPI app
app = FastAPI(
    title="Blockchain Learning Platform API",
    description="Combined API for Quiz, Riddle, and RAG-based learning interactions",
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

# Register startup event from RAG routes
app.add_event_handler("startup", startup_event)

# Quiz routes
app.post("/quiz/question")(get_quiz_question)
app.post("/quiz/answer")(check_answer)
app.post("/quiz/break")(quiz_break_options)
app.post("/quiz/reset")(reset_quiz)

# Riddle routes
app.get("/riddle")(generate_riddle)
app.post("/riddle/check-answer")(check_riddle_answer)
app.get("/riddle/break-options")(riddle_break_options)
app.post("/riddle/reset")(reset_riddle)

# RAG routes
app.post("/rag/query")(process_query)
app.get("/rag/health")(health_check)

# Fun facts route
app.get("/fun-fact")(get_random_fact)

# Creative writing routes
app.post("/prompt")(create_challenge)
app.post("/evaluate/{challenge_id}")(evaluate_challenge)
app.get("/scores/{challenge_id}")(get_challenge_scores)
app.get("/challenge/{challenge_id}")(get_challenge_status)

# Add a combined health check endpoint
@app.get("/health")
async def combined_health_check():
    """Health check endpoint for the entire application"""
    try:
        # Check RAG health
        rag_health = await health_check()
        
        return {
            "status": "healthy",
            "components": {
                "rag": rag_health,
                "quiz": "active" if quiz_game is not None else "inactive",
                "riddle": "active" if riddle_game is not None else "inactive",
                'fun_facts': 'active' if get_random_fact is not None else 'inactive',
                'creative_writing': 'active' if create_challenge is not None else 'inactive'
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

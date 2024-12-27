import sys
import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
# from pydantic import BaseModel, validator
from typing import Optional, Dict, Literal
import os
from datetime import datetime, timedelta
import uuid
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from ai_engine.creative_writing import InteractiveCreativeWriting
except ImportError:
    logger.error("Failed to import InteractiveCreativeWriting. Ensure the module is in the correct path.")
    raise

try:
    from model.models import ChallengeCreate
except ImportError:
    logger.error("Failed to import QueryRequest. Ensure the models module is available.")
    raise

# Initialize environment
load_dotenv()

app = FastAPI(title="Creative Writing Challenge API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for challenges with TTL
challenges: Dict[str, 'Challenge'] = {}

# Initialize the InteractiveCreativeWriting system
writing_system = InteractiveCreativeWriting()


class Challenge:
    def __init__(self, id: str, prompt: str, criteria: str, duration_minutes: int):
        self.id = id
        self.prompt = prompt
        self.criteria = criteria
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=duration_minutes)
        self.status = 'active'
        self.submission = None
        self.evaluation = None
        self.scores = None

def cleanup_expired_challenges():
    """Remove expired challenges from memory"""
    current_time = datetime.now()
    expired_ids = [
        challenge_id for challenge_id, challenge in challenges.items()
        if current_time > challenge.end_time + timedelta(minutes==1)  # Keep for 1 minutes after expiry
    ]
    for challenge_id in expired_ids:
        del challenges[challenge_id]

async def cleanup_temp_file(filepath: str):
    """Clean up temporary file"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        logger.error(f"Failed to cleanup temporary file {filepath}: {str(e)}")

@app.post("/prompt")
async def create_challenge(
    challenge_create: ChallengeCreate,
    background_tasks: BackgroundTasks
):
    """Create a new writing challenge with a specified duration."""
    try:
        # Cleanup expired challenges
        background_tasks.add_task(cleanup_expired_challenges)
        
        # Convert duration to minutes
        duration_minutes = challenge_create.get_minutes()
        
        prompt, criteria = writing_system.get_writing_prompt()
        
        challenge_id = str(uuid.uuid4())
        challenge = Challenge(
            id=challenge_id,
            prompt=prompt,
            criteria=criteria,
            duration_minutes=duration_minutes
        )
        
        challenges[challenge_id] = challenge
        
        return {
            "id": challenge_id,
            "prompt": prompt,
            "criteria": criteria,
            "end_time": challenge.end_time,
            "status": challenge.status,
            "duration": {
                "value": challenge_create.duration,
                "unit": challenge_create.time_unit
            }
        }
    
    except Exception as e:
        logger.error(f"Error creating challenge: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create challenge")

@app.post("/evaluate/{challenge_id}")
async def evaluate_challenge(
    background_tasks: BackgroundTasks,
    challenge_id: str,
    pdf_file: UploadFile = File(...)
):
    """Submit and evaluate a challenge submission."""
    if challenge_id not in challenges:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    challenge = challenges[challenge_id]
    
    if challenge.status != 'active':
        raise HTTPException(status_code=400, detail="Challenge is not active")
    
    if datetime.now() > challenge.end_time:
        challenge.status = 'expired'
        raise HTTPException(status_code=400, detail="Challenge has expired")
    
    # Validate file type
    if not pdf_file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    temp_path = f"temp_{challenge_id}_{uuid.uuid4()}.pdf"
    
    try:
        # Save PDF temporarily
        with open(temp_path, "wb") as buffer:
            content = await pdf_file.read()
            buffer.write(content)
        
        # Extract text using existing method
        submission_text = writing_system.extract_text_from_pdf(temp_path)
        
        if not submission_text:
            raise HTTPException(status_code=400, detail="Failed to extract text from PDF")
        
        # Store submission and evaluate
        challenge.submission = submission_text
        challenge.evaluation = writing_system.evaluate_submission(submission_text)
        challenge.scores = json.loads(writing_system.get_json_scores(challenge.evaluation))
        challenge.status = 'completed'
        
        return {
            "message": "Submission evaluated successfully",
            "evaluation": challenge.evaluation
        }
        
    except Exception as e:
        logger.error(f"Error evaluating submission: {str(e)}")
        challenge.status = 'failed'
        raise HTTPException(status_code=500, detail="Failed to evaluate submission")
    
    finally:
        # Clean up temp file in the background
        background_tasks.add_task(cleanup_temp_file, temp_path)

@app.get("/scores/{challenge_id}")
async def get_challenge_scores(challenge_id: str):
    """Get the scores for a completed challenge."""
    if challenge_id not in challenges:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    challenge = challenges[challenge_id]
    
    if challenge.status != 'completed':
        raise HTTPException(status_code=400, detail="Challenge evaluation not completed")
    
    if not challenge.scores:
        raise HTTPException(status_code=404, detail="Scores not found")
    
    return challenge.scores

@app.get("/challenge/{challenge_id}")
async def get_challenge_status(challenge_id: str):
    """Get the current status of a challenge."""
    if challenge_id not in challenges:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    challenge = challenges[challenge_id]
    
    # Update status if expired
    if challenge.status == 'active' and datetime.now() > challenge.end_time:
        challenge.status = 'expired'
    
    return {
        "id": challenge.id,
        "status": challenge.status,
        "end_time": challenge.end_time,
        "prompt": challenge.prompt,
        "criteria": challenge.criteria,
        "evaluation": challenge.evaluation if challenge.status == 'completed' else None,
        "scores": challenge.scores if challenge.status == 'completed' else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
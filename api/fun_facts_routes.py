import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


try:
    from ai_engine.fun_facts import BNBFunFacts
except ImportError:
    logger.error("Failed to import BNBFunFacts. Ensure the module is in the correct path.")
    raise

try:
    from model.models import FunFactResponse
except ImportError:
    logger.error("Failed to import FunFactResponse. Ensure the module is in the correct path.")
    raise


try:
    from markdown_converter.markdown_converter import MarkdownConverter as md
except ImportError:
    logger.error("Failed to import MarkdownConverter. Ensure the module is in the correct path.")
    raise

# Initialize FastAPI app
app = FastAPI(
    title="BNB Fun Facts API",
    description="API for generating fun facts about the BNB blockchain ecosystem",
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

# Load environment variables
load_dotenv()

# Initialize fun facts generator
fun_facts_generator = BNBFunFacts()


@app.get("/random-fact", response_model=FunFactResponse)
async def get_random_fact():
    """Generate a random fun fact about a random topic"""
    result = fun_facts_generator.generate_fun_facts()

    # Remove Markdown fomating
    result['facts'] = md.remove_markdown(result['facts'])

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

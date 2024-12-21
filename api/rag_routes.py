import os
import sys
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv



# Ensure the path includes the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the existing ConversationalModel
try:
    from ai_engine.rag import ConversationalModel
except ImportError:
    logger.error("Failed to import ConversationalModel. Ensure the module is in the correct path.")
    raise

try:
    from model.models import QueryRequest
except ImportError:
    logger.error("Failed to import QueryRequest. Ensure the models module is available.")
    raise

try:
    from markdown_converter.markdown_converter import MarkdownConverter as md
except ImportError:
    logger.error("Failed to import MarkdownConverter. Ensure the module is in the correct path.")
    raise

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Conversational AI API",
    description="RESTful API for Conversational AI with PDF and URL document loading",
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

# Predefined document paths
PDF_PATHS = [
    r"C:\Users\Okeoma\Downloads\whitepaper_Prompt Engineering_v4.pdf",
]

URLS = [
    "https://questbot.gitbook.io/questbot",
    "https://questbot.gitbook.io/questbot/introduction-what-is-questbot",
    "https://questbot.gitbook.io/questbot/why-questbot",
    "https://questbot.gitbook.io/questbot/core-features",
    "https://questbot.gitbook.io/questbot/how-questbot-works",
    "https://questbot.gitbook.io/questbot/integration-details",
    "https://questbot.gitbook.io/questbot/aligning-with-hackathon-tracks",
    "https://questbot.gitbook.io/questbot/impact-potential",
    "https://questbot.gitbook.io/questbot/impact-potential",
    "https://questbot.gitbook.io/questbot/faqs"
        ]

# Global variables
global_model = None
qa_chain = None

@app.on_event("startup")
async def startup_event():
    """Initialize the model on application startup."""
    global global_model, qa_chain

    try:
        logger.info("Initializing Conversational AI Model...")
        
        # Import here to avoid circular imports
        from ai_engine.rag import ConversationalModel

        # Initialize model with predefined documents
        global_model = ConversationalModel(
            pdf_paths=PDF_PATHS, 
            urls=URLS
        )

        # Run model initialization and store QA chain
        qa_chain = global_model.run()

        logger.info(f"Model initialized successfully with {len(PDF_PATHS)} PDF(s) and {len(URLS)} URL(s)")
    except Exception as e:
        logger.error(f"Failed to initialize model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model initialization failed: {str(e)}")

@app.post("/query")
async def process_query(request: QueryRequest):
    """Process a query using the initialized conversational AI model."""
    global global_model, qa_chain

    if global_model is None or qa_chain is None:
        logger.error("Model or QA chain not initialized")
        raise HTTPException(status_code=500, detail="Model not initialized")

    try:
        # Add query to memory
        global_model.memory.chat_memory.add_user_message(request.query)
        
        # Process query using the QA chain
        logger.info(f"Processing query: {request.query}")
        response = qa_chain.invoke(request.query)
        
        # Convert markdown to plain text
        response = md.remove_markdown(response)
        
        # Add response to memory
        global_model.memory.chat_memory.add_ai_message(response)
        
        logger.info("Query processed successfully")
        return {"response": response}

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/health")
async def health_check():
    """Simple health check endpoint to verify API is running."""
    global global_model, qa_chain
    status = "healthy" if (global_model is not None and qa_chain is not None) else "model not initialized"
    return {
        "status": status,
        "pdf_paths": PDF_PATHS,
        "urls": URLS
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
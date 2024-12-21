# QuestBot - Interactive Blockchain Learning Platform

A comprehensive learning platform featuring interactive quizzes, riddles, and AI-powered conversations about blockchain technology, focusing on the BNB ecosystem.

## Project Structure

The project is structured as follows:

* **`ai_engine`**: This directory contains the core logic for the conversational AI.
    * `rag.py`: Implements the RAG model using Langchain, Pinecone, and an embedding model.  Handles document loading, vectorstore creation/update, and question answering.
    * `quiz_handler.py`: Contains the main logic for the quiz game, including question generation, answer verification, and break options.  Uses external AI models for generation and verification.
    * `riddle_generation.py`: Likely responsible for generating riddle-like questions, leveraging similar prompt engineering techniques as `quiz section`.
* **`api`**: This directory (assumed) would contain the FastAPI application for serving the functionality.
    * `quiz_routes.py`:  Contains FastAPI routes related to the quiz model interactions.
    * `rag_routes.py`:  Contains FastAPI routes related to the RAG model interactions.
    *  `riddle_routes.py`: (Assumed) Contains FastAPI routes related to the riddle model interactions.
* **`prompts`**: This directory  containa prompt engineering templates for the various AI models.
* **`model`**:  This defines the Pydantic models used for request/response validation across the application.
* **`markdown_converter`**: This contains a Python class function to preprocess the LLM markdown response.
* **`requirements.txt`**: Lists the project's dependencies.


## Technologies Used

* **Python:** The primary programming language.
* **FastAPI:**  Used for building the API. (Assumed based on `main.py` snippet and `uvicorn` command in documentation).
* **Langchain:**  For building and managing the LLM application. Specifically utilized for RAG functionalities within the `ai_engine` component.
* **Pinecone:** A vector database used by Langchain for efficient document retrieval in the RAG system.
* **Google Generative AI API:** Likely used as the Large Language Model (LLM) for both question generation and answer verification.  (Requires API key).
* **Unstructured:** A library for loading documents from various sources, including PDFs and URLs.  Used in `dummy.py`.
* **Hashlib:** Used for computing document hashes in `rag.py` for efficient vectorstore updates.
* **uvicorn:** An ASGI server used to run the FastAPI application.


## Data Handling

The RAG model (`rag.py`) loads documents from specified PDF files (`PDF_PATHS` in `rag_routes.py`) and URLs (`URLS` in `rag_routes.py`). It creates or updates a Pinecone vectorstore containing embeddings of these documents.  The quiz game component (`quiz_handler.py`) may use additional data sources or files.


## Running the Application

1. **Install Dependencies:**  Run `pip install -r requirements.txt`.
2. **Set up environment variables:** Create a `.env` file with your Google Generative AI API key:  `GOOGLE_API_KEY=your_google_generativeai_api_key`, `PINECONE_API_KEY=your_pinecone_api_key`.
3. **Run the API:** Execute `uvicorn main:app --reload`.
4. **Access the APIs:** Navigate to the endpoints interface at the URL  http://localhost:8000/docs.

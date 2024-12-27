import os
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_community.document_loaders import PyPDFLoader
import json

# Initialize environment
load_dotenv()

def initialize_models():
    """Initialize and return the AI models with proper error handling."""
    try:
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        
        # Model for creative tasks
        creative_config = {
            "temperature": 0.8,
            "top_p": 0.8,
            "top_k": 40,
        }

        # Model for evaluation
        evaluation_config = {
            "temperature": 0.2,
            "top_p": 0.5,
            "top_k": 20,
        }

        creative_model = genai.GenerativeModel(
            'gemini-2.0-flash-exp', 
            generation_config=creative_config,
        )
        
        evaluation_model = genai.GenerativeModel(
            'gemini-1.5-flash', 
            generation_config=evaluation_config
        )
        
        return creative_model.start_chat(), evaluation_model
    
    except Exception as e:
        print(f"Error initializing models: {e}")
        return None, None

class InteractiveCreativeWriting:
    def __init__(self):
        self.creative_chat, self.evaluation_model = initialize_models()
        self.current_prompt = None
        self.current_criteria = None
        
        if not self.creative_chat or not self.evaluation_model:
            raise RuntimeError("Failed to initialize AI models")

    def get_writing_prompt(self) -> Tuple[str, str]:
        """
        Generate a creative writing prompt and evaluation criteria.
        Returns tuple of (prompt, criteria)
        """
        try:
            # Generate the creative writing prompt
            prompt_response = self.creative_chat.send_message(
                "Generate two sections:\n\n"
                "SECTION 1 - CREATIVE PROMPT:\n"
                "Create an engaging Web3/Blockchain/Tech-focused writing prompt that includes:\n"
                "- A warm welcome with emojis\n"
                "- An imaginative scenario or challenge\n"
                "- Clear writing rules (word count, style)\n"
                "- An encouraging closing question\n\n"
                "SECTION 2 - EVALUATION CRITERIA:\n"
                "List specific criteria for evaluating submissions in detail including:\n"
                "- Technical understanding\n"
                "- Creativity and innovation\n"
                "- Writing clarity and structure\n"
                "- Engagement and impact\n"
                "- Adherence to prompt requirements\n\n"
                "Format with clear SECTION 1 and SECTION 2 headers."
                "It should not contain this or anything related:Okay, here are the two sections as requested:, to it just the the sections"
            )
            
            # Split the response into prompt and criteria
            full_text = prompt_response.text
            sections = full_text.split("SECTION 2")[0:2]
            
            if len(sections) == 2:
                self.current_prompt = sections[0].replace("SECTION 1", "").strip()
                self.current_criteria = sections[1].strip()
                return self.current_prompt, self.current_criteria
            else:
                raise ValueError("Failed to generate properly formatted prompt and criteria")
            
        except Exception as e:
            print(f"Error generating prompt: {e}")
            return "Write about blockchain technology's future.", "Evaluate based on creativity and technical accuracy."

    def evaluate_submission(self, submission: str) -> str:
        """
        Evaluate a user's creative writing submission based on the current prompt and criteria.
        Returns detailed feedback.
        """
        try:
            if not self.current_prompt or not self.current_criteria:
                raise ValueError("No prompt or criteria available for evaluation")

            evaluation_prompt = (
                f"You are evaluating a creative writing submission based on the following:\n\n"
                f"ORIGINAL PROMPT:\n{self.current_prompt}\n\n"
                f"EVALUATION CRITERIA:\n{self.current_criteria}\n\n"
                f"SUBMISSION:\n{submission}\n\n"
                f"Provide a detailed evaluation that includes:\n"
                f"1. Numerical scores (1-5) for each criterion\n"
                f"2. Specific feedback for each score\n"
                f"3. Notable highlights from the submission\n"
                f"4. Constructive suggestions for improvement"
            )
            
            response = self.evaluation_model.generate_content(evaluation_prompt)
            return response.text
            
        except Exception as e:
            print(f"Error evaluating submission: {e}")
            return "Unable to generate evaluation. Please try again."

    def get_json_scores(self, feedback: str) -> str:
        """
        Convert evaluation feedback into a structured JSON format.
        """
        try:
            json_prompt = (
                f"Convert this evaluation feedback into a JSON structure with these fields:\n"
                f"- technical_understanding: score and feedback\n"
                f"- creativity: score and feedback\n"
                f"- clarity: score and feedback\n"
                f"- engagement: score and feedback\n"
                f"- adherence: score and feedback\n"
                f"- overall_score: average of all scores\n"
                f"Feedback to convert:\n{feedback}"
            )
            
            response = self.evaluation_model.generate_content(
                json_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Parse and reformat the JSON for consistency
            scores_dict = json.loads(response.text)
            return json.dumps(scores_dict, indent=2)
            
        except Exception as e:
            print(f"Error formatting JSON scores: {e}")
            return "{}"

    def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """Extract text content from a PDF file."""
        try:
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            return "\n".join([doc.page_content for doc in documents])
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return None

def run_interactive_session():
    """Run an interactive creative writing session."""
    try:
        system = InteractiveCreativeWriting()
        
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\n=== 🌟 Web3 Creativity Quest 🌟 ===\n")
            
            # Get and display prompt and criteria
            prompt, criteria = system.get_writing_prompt()
            print("=== Writing Prompt ===")
            print(prompt)
            print("\n=== Evaluation Criteria ===")
            print(criteria)
            
            # Get submission
            print("\nUpload your PDF file")
            pdf_path = input("Enter the path to your PDF file: ").strip()
            
            if not pdf_path.lower().endswith('.pdf'):
                print("\nInvalid file format. Please upload a PDF file.\n")
                continue
            
            if not os.path.isfile(pdf_path):
                print("\nFile not found. Please check the path and try again.\n")
                continue
            
            print("\n📄 Reading submission from PDF...\n")
            submission = system.extract_text_from_pdf(pdf_path)
            
            if not submission:
                print("\nFailed to extract text from PDF. Please try another file.\n")
                continue
            
            # Evaluate submission
            print("\n📝 Evaluating your submission...\n")
            feedback = system.evaluate_submission(submission)
            print("\n=== 💫 Evaluation Feedback 💫 ===")
            print(feedback)
            
            # Generate JSON scores
            print("\n=== 📊 Detailed Scores 📊 ===")
            json_scores = system.get_json_scores(feedback)
            print(json_scores)
            
            # Ask to continue
            try_again = input("\n🎮 Would you like another challenge? (yes/no): ").lower()
            if try_again != 'yes':
                print("\n🌟 Thank you for participating in the Web3 Creativity Quest! Keep imagining and creating! 🌟\n")
                break

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please try restarting the application.")

if __name__ == "__main__":
    run_interactive_session()
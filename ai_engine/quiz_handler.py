import os
import re
from typing import Dict, Optional, List, Set
from dotenv import load_dotenv
import google.generativeai as genai

# Initialize environment
load_dotenv()

def _load_prompt(file_name: str) -> str:
    """Load prompt from a file with error handling."""
    try:
        file_path = os.path.join('prompts', file_name)
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Warning: Prompt file {file_name} not found.")
        return "Help generate an interesting blockchain quiz question."
    except Exception as e:
        print(f"Error loading prompt: {e}")
        return "Help generate an interesting blockchain quiz question."

# Configure API with error handling
try:
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
except Exception as e:
    print(f"Error configuring Google API: {e}")
    genai.configure(api_key='')

# Generation configurations
generation_config = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 40,
}

verification_config = {
    "temperature": 0.2,
    "top_p": 0.5,
    "top_k": 20,
}

# Verification prompt for answer checking
verification_prompt = """
You are an expert at verifying if two answers are equivalent. 
Your task is to:
1. Carefully compare two given answers
2. Determine if they represent the same concept or solution
3. Respond with ONLY 'EQUIVALENT' or 'DIFFERENT'
4. Be strict but fair in your comparison
5. Ignore minor differences like capitalization, spacing, or punctuation
"""

# Create models with fallback configuration
try:
    quiz_model = genai.GenerativeModel(
        'gemini-2.0-flash-exp', 
        generation_config=generation_config, 
        system_instruction=_load_prompt("quizzes_prompt.txt")
    )
    quiz_chat = quiz_model.start_chat()
    
    verification_model = genai.GenerativeModel(
        'gemini-1.5-flash', 
        generation_config=verification_config, 
        system_instruction=verification_prompt
    )
except Exception as e:
    print(f"Error creating models: {e}")
    quiz_model = None
    verification_model = None

class BlockchainQuizGame:
    def __init__(self):
        self.complexity = 1
        self.attempts = 0
        self.max_attempts = 5
        self.current_question_display = None  
        self.current_question = None  
        self.current_answer = None
        self.current_hint = None
        self.current_options = []
        self.asked_questions: Set[str] = set()  

    def generate_break_options(self) -> str:
        """Generate break options using the AI model."""
        try:
            base_prompt = _load_prompt("quizzes_prompt.txt")

            prompt = f"""
            User wants to take a break from the blockchain quiz game. 
            Generate a friendly response suggesting alternative activities using the base prompt: {base_prompt}"""
            
            result = quiz_model.generate_content(prompt)
            return result.text.strip()
        
        except Exception as e:
            print(f"Error generating break options: {e}")
            return """Sure! Here are some fun options:
1. Check your current ranking on the leaderboard.
2. View your achievements and badges.
3. Review the questions you answered correctly and incorrectly.
4. Learn some fun facts or trivia about blockchain and Web3.
5. Play a short mini-game or puzzle related to blockchain."""

    def verify_answer(self, correct_answer: str, user_answer: str) -> bool:
        """Verify if the user's answer is equivalent to the correct answer"""
        if not verification_model:
            # Fallback to simple comparison if verification model fails
            return self.simple_answer_check(correct_answer, user_answer)
        
        try:
            # Construct verification prompt
            verification_text = f"""
Correct Answer: {correct_answer}
User Answer: {user_answer}

Are these answers equivalent?"""
            
            # Generate verification
            result = verification_model.generate_content(verification_text)
            verification = result.text.strip().upper()
            
            print(f"Verification Result: {verification}")  
            
            # Check verification result
            return 'EQUIVALENT' in verification
        
        except Exception as e:
            print(f"Verification error: {e}")
            # Fallback to simple comparison
            return self.simple_answer_check(correct_answer, user_answer)
    
    def simple_answer_check(self, correct_answer: str, user_answer: str) -> bool:
        """Fallback method to check answers if verification fails"""
        def normalize_answer(ans):
            # Remove punctuation, convert to lowercase, and strip
            return re.sub(r'[^\w\s]', '', ans).lower().strip()
        
        return normalize_answer(correct_answer) == normalize_answer(user_answer)

    def generate_quiz_question(self) -> Dict:
        """Generate a quiz question with comprehensive error handling"""
        if not quiz_model:
            return {
                "error": "AI model not initialized",
                "question": "Technical difficulty encountered",
                "hint": "Please check API configuration",
                "complexity": self.complexity,
                "attempts_remaining": self.max_attempts
            }
        
        try:
            prompt_text = f"""Generate a multiple choice question about the BNB Blockchain.
    Complexity Level: {self.complexity}

    Format your response EXACTLY like this:
    Question (Complexity Level {self.complexity}): [Your question]
    Options:
    A) [Option 1]
    B) [Option 2]
    C) [Option 3]
    D) [Option 4]
    Hint: [Your hint]
    ANSWER: [Correct option letter]"""

            result = quiz_chat.send_message(prompt_text)
            response_text = result.text.strip()

            # Extract components using regex
            question_pattern = r"Question.*?: (.+?)(?=\nOptions:)"
            options_pattern = r"Options:\n(A\).+?\nB\).+?\nC\).+?\nD\).+?)(?=\nHint:)"
            hint_pattern = r"Hint: (.+?)(?=\nANSWER:)"
            answer_pattern = r"ANSWER: (.+)$"

            question = re.search(question_pattern, response_text, re.DOTALL).group(1).strip()
            options = re.search(options_pattern, response_text, re.DOTALL).group(1).strip()
            hint = re.search(hint_pattern, response_text, re.DOTALL).group(1).strip()
            answer = re.search(answer_pattern, response_text).group(1).strip()

            self.current_riddle = question
            self.current_answer = answer
            self.current_hint = hint
            self.attempts = 0

            return {
                "question": f"Question (Complexity Level {self.complexity}): {question}",
                "options": options,
                "hint": f"Hint: {hint}",
                "complexity": self.complexity,
                "attempts_remaining": self.max_attempts
            }
        except Exception as e:
            print(f"Error generating question: {e}")
            return {
                "error": f"Error generating question: {e}",
                "question": "Technical difficulty encountered",
                "hint": "Please try again",
                "complexity": self.complexity,
                "attempts_remaining": self.max_attempts
            }

    def check_answer(self, user_answer: str) -> Dict:
        """Check if the provided answer is correct with AI verification"""
        if not self.current_answer:
            return {
                "correct": False,
                "message": "No active question",
                "attempts_remaining": 0
            }
        
        user_answer = user_answer.strip()
        self.attempts += 1
        
        # If options exist, get the selected option's text
        if self.current_options:
            try:
                # Convert numeric input to option text
                if user_answer.isdigit():
                    index = int(user_answer) - 1
                    if 0 <= index < len(self.current_options):
                        user_answer = self.current_options[index]
                    else:
                        return {
                            "correct": False,
                            "message": "Invalid option number",
                            "attempts_remaining": self.max_attempts - self.attempts,
                            "hint": self.current_hint
                        }
            except Exception:
                pass
        
        # Use AI verification
        is_correct = self.verify_answer(self.current_answer, user_answer)
        
        if is_correct:
            # Correct answer
            self.complexity = min(self.complexity + 1, 5)
            self.attempts = 0
            return {
                "correct": True,
                "message": "Correct! Moving to next level.",
                "complexity": self.complexity
            }
        else:
            # Wrong answer
            remaining = self.max_attempts - self.attempts
            if remaining <= 0:
                message = f"No worries! The answer is {self.current_answer}. Want to try another one or need a break?"
                self.attempts = 0
            else:
                message = f"Wrong! {remaining} attempts remaining"
            
            return {
                "correct": False,
                "message": message,
                "attempts_remaining": remaining,
                "hint": self.current_hint
            }

def main():
    game = BlockchainQuizGame()
    print("\nWelcome to the Blockchain and Web3 Quiz Game!")
    print("Let's test your blockchain knowledge!")
    
    def play_game():
        response = game.generate_quiz_question()
        if "error" in response:
            print(f"\nError: {response['error']}")
            return False
        

        print(response['question'])
        print("Options:")
        print(response['options'])
        print(response['hint'])
        print()

        while True:
            user_answer = input("Your answer (enter A, B, C, or D): ").strip().upper()
            

            if user_answer == 'quit':
                return False
            
            answer_result = game.check_answer(user_answer)
            print(answer_result['message'])
            
            if answer_result['correct']:
                # Offer choice after correct answer
                choice = input("\nOptions:\n1. Continue Quiz\n2. Take a Break\nChoose (1/2): ").strip()
                if choice == '2':
                    print(game.generate_break_options())
                    return False
                elif choice == '1':
                    return play_game()
            
            if answer_result['attempts_remaining'] <= 0:
                # Offer choice after failed attempts
                choice = input("\nOptions:\n1. Try Again\n2. Take a Break\nChoose (1/2): ").strip()
                if choice == '2':
                    print(game.generate_break_options())
                    return False
                elif choice == '1':
                    return play_game()
        
        return False

    # Start the game
    try:
        play_game()
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
    finally:
        print("\nThank you for playing the Blockchain and Web3 Quiz Game!")

if __name__ == "__main__":
    main()



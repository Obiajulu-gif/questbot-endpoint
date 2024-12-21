import os
import re
from typing import Dict, Optional
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
        return "Help verify if two answers are equivalent."
    except Exception as e:
        print(f"Error loading prompt: {e}")
        return "Help verify if two answers are equivalent."

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

# Load base prompts with error handling
base_prompt = _load_prompt(file_name="riddle.txt")
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
    riddle_model = genai.GenerativeModel(
        'gemini-2.0-flash-exp', 
        generation_config=generation_config, 
        system_instruction=base_prompt,
    )
    riddle_chat = riddle_model.start_chat()
    
    verification_model = genai.GenerativeModel(
        'gemini-1.5-flash', 
        generation_config=verification_config, 
        system_instruction=verification_prompt
    )
except Exception as e:
    print(f"Error creating models: {e}")
    riddle_model = None
    verification_model = None

class RiddleGame:
    def __init__(self):
        self.complexity = 1
        self.attempts = 0
        self.max_attempts = 5  
        self.current_riddle = None
        self.current_answer = None
        self.current_hint = None
    
    def generate_break_options(self) -> str:
        """Generate break options using the AI model."""
        try:
            base_prompt = _load_prompt("quizzes_prompt.txt")

            prompt = f"""
            User wants to take a break from the blockchain riddle game. 
            Generate a friendly response suggesting alternative activities using the base prompt: {base_prompt}"""
            
            result = riddle_model.generate_content(prompt)
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

    def generate_riddle(self) -> Dict:
        """Generate a riddle with comprehensive error handling and improved parsing"""
        if not riddle_model:
            return {
                "error": "AI model not initialized",
                "riddle": "Technical difficulty encountered",
                "hint": "Please check API configuration",
                "complexity": self.complexity,
                "attempts_remaining": self.max_attempts
            }
        
        try:
            # Create the full prompt text
            prompt_text = f""" Generate a riddle about the BNB Blockchain Ecosystem within the Web3 space. 
The riddle should match the specified complexity level: {self.complexity}. 

Important: Your response MUST include:
1. A riddle about blockchain/Web3
2. A hint to help solve the riddle
3. The correct answer

Please format your response with only this clear sections:
RIDDLE: [Your riddle text]
HINT: [A helpful hint]
ANSWER: [The correct answer]

Complexity Level: {self.complexity}
"""
            
            # Generate riddle
            result = riddle_chat.send_message(prompt_text)
            
            # Improved parsing function
            def extract_section(text, prefix):
                # Remove possible Markdown formatting
                text = re.sub(r'\*\*', '', text)
                
                # More robust regex to extract section
                pattern = fr'{prefix}:\s*(.+?)(?=\n[A-Z]+:|$)'
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                return match.group(1).strip() if match else None
            
            # Extract sections
            riddle = extract_section(result.text, 'RIDDLE')
            hint = extract_section(result.text, 'HINT')
            answer = extract_section(result.text, 'ANSWER')
            
            # Fallback parsing if section extraction fails
            if not riddle:
                riddle_match = re.search(r'I am\s.+?\?', result.text, re.IGNORECASE)
                if riddle_match:
                    riddle = riddle_match.group(0).strip()
            
            # Validate extracted information
            if not riddle or not hint or not answer:
                print("Parsing failed. Full text:", result.text)
                raise ValueError("Could not extract complete riddle information")
                
            self.current_riddle = riddle
            self.current_answer = answer
            self.current_hint = hint
            self.attempts = 0
            
            return {
                "riddle": riddle,
                "hint": hint,
                "complexity": self.complexity,
                "attempts_remaining": self.max_attempts
            }
            
        except Exception as e:
            print(f"Detailed Error generating riddle: {e}")
            return {
                "error": f"Error generating riddle: {e}",
                "riddle": "Technical difficulty encountered",
                "hint": "Please try again",
                "complexity": self.complexity,
                "attempts_remaining": self.max_attempts
            }

    def check_answer(self, user_answer: str) -> Dict:
        """Check if the provided answer is correct with AI verification"""
        if not self.current_answer:
            return {
                "correct": False,
                "message": "No active riddle",
                "attempts_remaining": 0
            }
        
        user_answer = user_answer.strip()
        self.attempts += 1
        
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
    game = RiddleGame()
    print("\nWelcome to the Blockchain Riddle Game!")
    
    def play_game():
        # Ensure models are initialized
        if not riddle_model or not verification_model:
            print("Error: AI models could not be initialized. Cannot start game.")
            return False

        response = game.generate_riddle()
        if "error" in response:
            print(f"\nError: {response['error']}")
            return False
        
        print(f"\nRiddle (Complexity {response['complexity']}):")
        print(response['riddle'])
        print(f"\nAttempts Remaining: {response['attempts_remaining']}")
        print(f"Hint: {response['hint']}")
        
        while True:
            user_answer = input("Your answer: ").strip()
            
            if user_answer.lower() == 'quit':
                return False
            
            answer_result = game.check_answer(user_answer)
            print(answer_result['message'])
            
            if answer_result['correct']:
                # Offer choice after correct answer
                choice = input("\nOptions:\n1. Continue Playing\n2. Take a Break\nChoose (1/2): ").strip()
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
        print("\nThank you for playing the Blockchain Riddle Game!")

if __name__ == "__main__":
    main()
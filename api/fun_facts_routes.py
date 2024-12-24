import os
from typing import Dict, List
from dotenv import load_dotenv
import google.generativeai as genai
import random

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
        return "Generate engaging facts about the BNB blockchain ecosystem."
    except Exception as e:
        print(f"Error loading prompt: {e}")
        return "Generate engaging facts about the BNB blockchain ecosystem."

# Configure API with error handling
try:
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
except Exception as e:
    print(f"Error configuring Google API: {e}")
    genai.configure(api_key='')

# Generation configurations
generation_config = {
    "temperature": 0.8,  
    "top_p": 0.9,
    "top_k": 40,
}

# Load base prompt
base_prompt = _load_prompt(file_name="fun_facts.txt")

# Create model with fallback configuration
try:
    fun_facts_model = genai.GenerativeModel(
        'gemini-2.0-flash-exp', 
        generation_config=generation_config,
        system_instruction=base_prompt,
    )
    fun_facts_chat = fun_facts_model.start_chat()
except Exception as e:
    print(f"Error creating model: {e}")
    fun_facts_model = None

class BNBFunFacts:
    def __init__(self):
        self.main_categories = {
            "Technical": [
                "Consensus Mechanism",
                "Network Architecture",
                "Cross-Chain Technology",
                "Smart Contract Innovation",
                "Scalability Solutions"
            ],
            "Economic": [
                "Tokenomics",
                "Gas Fee Mechanics",
                "Token Burns",
                "Market Dynamics",
                "Staking Economics"
            ],
            "Ecosystem": [
                "DeFi Protocols",
                "GameFi Projects",
                "NFT Marketplaces",
                "DEX Platforms",
                "Yield Farming"
            ],
            "Development": [
                "Developer Tools",
                "Security Features",
                "Testing Frameworks",
                "Documentation",
                "Community Resources"
            ],
            "Governance": [
                "BNB Proposals",
                "Voting Mechanisms",
                "Community Decisions",
                "Protocol Upgrades",
                "Validator Operations"
            ],
            "Innovation": [
                "Layer 2 Solutions",
                "ZK Technology",
                "Oracle Integration",
                "AI Integration",
                "Green Initiatives"
            ],
            "Partnerships": [
                "Enterprise Collaborations",
                "Academic Research",
                "Industry Alliances",
                "Cross-Chain Bridges",
                "Integration Projects"
            ]
        }
        
        # Dynamic topic generation
        self.special_topics = [
            "Historical Milestones",
            "Future Roadmap",
            "Community Success Stories",
            "Educational Initiatives",
            "Hackathon Achievements",
            "Sustainability Efforts",
            "User Adoption Metrics",
            "Regional Developments",
            "Competition Analysis",
            "Research Breakthroughs"
        ]
    
    def get_random_topic(self) -> str:
        """Generate a random topic by combining elements or selecting special topics"""
        if random.random() < 0.3: 
            return random.choice(self.special_topics)
        else:
            category = random.choice(list(self.main_categories.keys()))
            subcategory = random.choice(self.main_categories[category])
            return f"{category}: {subcategory}"

    def generate_fun_facts(self, topic: str = None) -> Dict:
        """Generate fun facts about the BNB blockchain ecosystem"""
        if not fun_facts_model:
            return {
                "error": "AI model not initialized",
                "facts": "Technical difficulty encountered"
            }
        
        try:
            if not topic:
                topic = self.get_random_topic()
            
            prompt_text = f"""Generate 1 fascinating and detailed fun facts about {topic} in the BNB blockchain ecosystem.
            Include specific numbers, dates, statistics, or technical details when relevant.
            Format as a numbered list with each fact being 2-3 sentences.
            Focus on unique, lesser-known, but accurate information.
            If possible, include comparisons with other blockchain ecosystems or real-world analogies."""
            
            response = fun_facts_chat.send_message(prompt_text)
            
            return {
                "success": True,
                "facts": response.text,
            }
            
        except Exception as e:
            return {
                "error": f"Error generating fun facts: {e}",
                "facts": "Unable to generate facts at this time"
            }

def main():
    fun_facts = BNBFunFacts()
    print("\nWelcome to the BNB Blockchain Fun Facts Generator!")
    
    while True:
        print("\nGenerating random fun facts...")
        result = fun_facts.generate_fun_facts()
        
        if "error" in result:
            print(f"\nError: {result['error']}")
        else:
            print(result['facts'])
        
        print("\n" + "-"*50)
        
        cont = input("\nWould you like to generate more fun facts? (y/n): ").strip().lower()
        if cont != 'y':
            break
            
    print("\nThank you for using the BNB Blockchain Fun Facts Generator!")

if __name__ == "__main__":
    main()

import os
import hashlib
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain.docstore.document import Document
from langchain.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables import RunnableParallel
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langchain_unstructured import UnstructuredLoader

from pinecone import Pinecone as pc
from pinecone import ServerlessSpec
from markdownify import markdownify as md

# Load environment variables
load_dotenv()
os.environ['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY')
os.environ['PINECONE_API_KEY'] = os.getenv('PINECONE_API_KEY')

# Initialize Pinecone client
pine_client = pc(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "questbot"  

# Check if the index exists or create a new one
if index_name not in pine_client.list_indexes().names():
    print("Creating index")
    pine_client.create_index(
        name=index_name,
        metric="cosine",
        dimension=768,
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )
    print(pine_client.describe_index(index_name))

def _load_prompt(file_name: str) -> str:
    """Load prompt from a file with error handling."""
    try:
        file_path = os.path.join('prompts', file_name)
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Warning: Prompt file {file_name} not found.")
        return "Help answer questions based on the provided context."
    except Exception as e:
        print(f"Error loading prompt: {e}")
        return "Help answer questions based on the provided context."

# Load base system prompt
system_prompt = _load_prompt(file_name="rag.txt")

class ConversationalModel:
    def __init__(self, pdf_paths=None, urls=None):
        """
        Initializes the conversational model with PDF files and/or URLs.

        Args:
            pdf_paths (list, optional): List of paths to PDF files.
            urls (list, optional): List of website URLs to load.
        """
        self.pdf_paths = pdf_paths or []
        self.urls = urls or []
        self.vectorstore = None
        self.embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self.chat_model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=True,
            human_prefix="Human",
            ai_prefix="AI",
            k=5
        )

    def _compute_document_hash(self, document):
        """
        Compute a unique hash for a document to check if it's already indexed.
        
        Args:
            document (Document): The document to hash.
        
        Returns:
            str: A unique hash for the document.
        """
        # Use page content and metadata to generate a hash
        hash_content = document.page_content + str(document.metadata)
        return hashlib.md5(hash_content.encode()).hexdigest()

    def load_documents(self):
        """
        Loads documents from PDF files and URLs.

        Returns:
            list: A list of Document objects.
        """
        documents = []

        # Load PDFs
        for pdf_path in self.pdf_paths:
            pdf_loader = PyPDFLoader(pdf_path)
            documents.extend(pdf_loader.load_and_split())

        # Load URLs using UnstructuredLoader
        for url in self.urls:
            unstructured_loader = UnstructuredLoader(web_url=url)
            documents.extend(unstructured_loader.load_and_split())

        return documents

    def create_or_update_vectorstore(self, documents):
        """
        Creates or updates Pinecone vectorstore, avoiding reindexing existing documents.

        Args:
            documents (list): A list of Document objects.
        """
        # Initialize the Pinecone index
        index = pine_client.Index(index_name)
        
        # Prepare documents for indexing
        new_documents = []
        document_hashes = set()

        for doc in documents:
            # Compute document hash
            doc_hash = self._compute_document_hash(doc)
            
            # Check if document is already in the index
            if doc_hash not in document_hashes:
                new_documents.append(doc)
                document_hashes.add(doc_hash)

        # If there are new documents, add them to the vectorstore
        if new_documents:
            Pinecone.from_documents(
                new_documents, 
                self.embedding_model, 
                index_name=index_name
            )
            print(f"Added {len(new_documents)} new documents to the index.")

        # Create vectorstore from the existing index
        self.vectorstore = Pinecone.from_existing_index(
            index_name, 
            self.embedding_model
        )

    def get_qa_chain(self):
        """
        Creates a retrieval-based QA chain with conversation memory.

        Returns:
            RetrievalQA: The QA chain.
        """
        # Get the retriever
        retriever = self.vectorstore.as_retriever()

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            ("human", "Context: {context}\n\nChat History: {chat_history}\n\nQuestion: {question}"),
        ])

        # Helper function to format documents
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # Create the QA chain
        qa_chain = (
            RunnableParallel({
                "context": retriever | format_docs,
                "question": RunnablePassthrough(),
                "chat_history": lambda _: "\n".join([
                    f"{msg.type.capitalize()}: {msg.content}" 
                    for msg in self.memory.chat_memory.messages
                ])
            })
            | prompt 
            | self.chat_model
            | StrOutputParser()
        )

        return qa_chain
        
    def run(self):
        """
        Runs the conversational model by processing the documents and enabling interaction.

        Returns:
            Runnable: The initialized QA chain.
        """
        # Load documents and create/update vectorstore
        documents = self.load_documents()
        self.create_or_update_vectorstore(documents)

        # Create the QA chain
        qa_chain = self.get_qa_chain()
        return qa_chain


if __name__ == "__main__":
    # Provide the PDF paths and optionally URLs
    pdf_paths = [
        # r"C:\Users\Okeoma\Downloads\whitepaper_Prompt Engineering_v4.pdf",
        
    ]
    urls = [
        # Optional URLs
        "https://questbot.gitbook.io/questbot",
        "https://questbot.gitbook.io/questbot/core-features",
        "https://questbot.gitbook.io/questbot/how-questbot-works",
        #    "https://python.langchain.com/docs/how_to/document_loader_web/"
    ]

    try:
        print("\nInitializing AI Assistant...")
        model = ConversationalModel(pdf_paths=pdf_paths)
        qa_chain = model.run()
        print("AI Assistant is ready! (Type 'exit' to end the conversation)\n")

        while True:
            # Get user input with formatted prompt
            query = input("\nYou: ").strip()
            
            # Check for exit condition
            if query.lower() in ['exit', 'quit', 'bye']:
                print("\nAI: Goodbye! Have a great day!")
                break
            
            if query:
                try:
                    # Add query to memory
                    model.memory.chat_memory.add_user_message(query)
                    
                    # Invoke QA chain
                    response = qa_chain.invoke(query)
                    
                    


                    # Add response to memory
                    model.memory.chat_memory.add_ai_message(response)
                    
                    print("\nAI:", response)
                except Exception as e:
                    print(f"\nError: {str(e)}")
                    print("AI: I apologize, but I encountered an error. Please try asking your question differently.")
            else:
                print("\nAI: Please ask me a question!")

    except Exception as e:
        print(f"\nSystem Error: {str(e)}")
        print("Failed to initialize the AI Assistant. Please check your configuration.")
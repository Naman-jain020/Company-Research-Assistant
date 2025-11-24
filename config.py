import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask Configuration
    SECRET_REMOVED = os.getenv('SECRET_REMOVED', 'dev-secret-key-change-in-production')
    
    # Groq API Configuration
    GROQ_API_REMOVED = os.getenv('GROQ_API_REMOVED') or 'REMOVED'
    GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
    
    # Tavily API Configuration
    TAVILY_API_REMOVED = os.getenv('TAVILY_API_REMOVED')
    USE_TAVILY = os.getenv('USE_TAVILY', 'true').lower() == 'true'
    
    # Search Configuration
    MAX_SEARCH_RESULTS = int(os.getenv('MAX_SEARCH_RESULTS', 10))
    MAX_URLS_TO_SCRAPE = int(os.getenv('MAX_URLS_TO_SCRAPE', 5))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 10))
    
    # Document Configuration
    DOCUMENTS_FOLDER = os.getenv('DOCUMENTS_FOLDER', './documents')
    
    # Agent Configuration
    MAX_SUB_QUERIES = int(os.getenv('MAX_SUB_QUERIES', 5))
    CONTEXT_WINDOW_SIZE = int(os.getenv('CONTEXT_WINDOW_SIZE', 10))


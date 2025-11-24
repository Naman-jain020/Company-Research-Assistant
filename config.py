import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Groq API Configuration
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    GROQ_MODEL = os.getenv('GROQ_MODEL')
    
    # Tavily API Configuration
    TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
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


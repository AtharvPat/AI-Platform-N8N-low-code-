# backend/config.py
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./outputs"))
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 104857600))  # 10MB
    ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "csv,xlsx").split(",")
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # Ensure directories exist
    UPLOAD_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

config = Config()
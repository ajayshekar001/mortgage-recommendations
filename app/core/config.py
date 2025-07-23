from pydantic_settings import BaseSettings
import json
import os

class Settings(BaseSettings):
    GOOGLE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./loan_decisions.db"
    
    def __init__(self):
        super().__init__()
        # Try to load from secrets.json
        secrets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'secrets.json')
        if os.path.exists(secrets_path):
            with open(secrets_path, 'r') as f:
                secrets = json.load(f)
                self.GOOGLE_API_KEY = secrets.get('google_api_key', '')
                self.OPENAI_API_KEY = secrets.get('open_ai_key', '')
    
    class Config:
        env_file = ".env"

settings = Settings() 
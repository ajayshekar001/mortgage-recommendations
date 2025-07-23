import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Add the project root to Python path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Run the server
if __name__ == "__main__":
    try:
        import uvicorn
        logger.info("Starting FastAPI server...")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Python path: {sys.path}")
        logger.info(f"Environment variables loaded: {'OPENAI_API_KEY' in os.environ}")
        
        uvicorn.run(
            "app.api.main:app",
            host="localhost",
            port=8000,
            reload=True,
            log_level="debug"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        raise 
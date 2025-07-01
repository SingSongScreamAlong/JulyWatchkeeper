import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration from environment variables
HOST = os.getenv("API_HOST", "0.0.0.0")
PORT = int(os.getenv("API_PORT", 8000))
DEBUG = os.getenv("API_DEBUG", "true").lower() == "true"

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=DEBUG)

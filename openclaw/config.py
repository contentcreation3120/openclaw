import os
from dotenv import load_dotenv
load_dotenv()

class _Settings:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

settings = _Settings()

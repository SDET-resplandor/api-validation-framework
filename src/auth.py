import os
import secrets
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv
 
load_dotenv()
 
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
 
def get_expected_api_key() -> str:
    expected_api_key = os.getenv("API_KEY")
    if not expected_api_key:
        raise RuntimeError("CRITICAL: 'API_KEY' environment variable is missing or empty.")
    return expected_api_key
 
def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    expected_api_key = get_expected_api_key()
    if not api_key or not secrets.compare_digest(api_key, expected_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access denied: Invalid or missing API Key."
        )
    return api_key
 
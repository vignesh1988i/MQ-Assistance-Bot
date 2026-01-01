"""Configuration"""
import os
from dotenv import load_dotenv

load_dotenv()

MCP_BRIDGE_URL = os. getenv("MCP_BRIDGE_URL", "http://localhost:8090/api/chat")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))
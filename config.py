from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL")

SELF_HEALING_ENABLED = True
HEADLESS = False
IMPLICIT_WAIT = 5
EXPLICIT_WAIT = 10
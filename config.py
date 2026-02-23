from dotenv import load_dotenv
import os

load_dotenv()

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# GEMINI_MODEL   = os.getenv("GEMINI_MODEL")

GEMINI_API_KEY = "AIzaSyClccU5XbllcA9-2n8nuSdSbuL2bGC1qL4"
GEMINI_MODEL   = "gemini-2.5-flash"

SELF_HEALING_ENABLED = True
HEADLESS = False
IMPLICIT_WAIT = 5
EXPLICIT_WAIT = 10
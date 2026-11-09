import os
import sys
from dotenv import load_dotenv
from google import genai

# Ensure UTF-8 output on Windows consoles to prevent charmap errors with emojis
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ---------------------------------------
# Load environment variables
# ---------------------------------------
load_dotenv()


def get_api_key():
    """
    Retrieve Gemini API key from environment, .env file, or Streamlit Cloud Secrets.
    Never crashes if key is not yet set.
    """
    key = os.getenv("GEMINI_API_KEY")
    if key and key.strip():
        return key.strip()

    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "GEMINI_API_KEY" in st.secrets:
                return str(st.secrets["GEMINI_API_KEY"]).strip()
            # Also check if it was nested
            if "general" in st.secrets and "GEMINI_API_KEY" in st.secrets["general"]:
                return str(st.secrets["general"]["GEMINI_API_KEY"]).strip()
    except Exception:
        pass

    return None


def get_client():
    """Create or return a Google GenAI client instance."""
    key = get_api_key()
    if not key:
        return None
    try:
        return genai.Client(api_key=key)
    except Exception as error:
        print(f"Error creating GenAI client: {error}")
        return None


# Configurable model with recommended defaults
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
FALLBACK_MODELS = ["gemini-flash-latest", "gemini-2.5-flash-lite"]

# Conversation memory
conversation_history = []

SYSTEM_INSTRUCTION = """
You are Riosa, an interactive and friendly voice AI assistant.

Your responses will be spoken aloud and displayed on screen, so keep them:
- Short, clear, natural, and conversational.
- Usually 1 to 3 sentences unless the user explicitly requests more detail.
- Simple and easy to understand.
- Friendly and helpful.
- Avoid markdown headers or excessive bullet points that sound awkward when spoken aloud.
"""


def clear_history():
    """Clear conversation history memory."""
    global conversation_history
    conversation_history = []


def get_history():
    """Return a copy of the current conversation history."""
    return list(conversation_history)


def ask_llm(text):
    """
    Send user prompt to Google Gemini and return assistant response.
    Maintains multi-turn context memory.
    """
    global conversation_history

    client = get_client()
    if not client:
        return (
            "⚠️ GEMINI_API_KEY is not configured yet. "
            "Please add GEMINI_API_KEY to your Streamlit Cloud Secrets or .env file to activate Riosa."
        )

    if not text or not text.strip():
        return "I didn't receive a question."

    user_message = text.strip()

    # Append user message to history
    conversation_history.append({
        "role": "user",
        "text": user_message
    })

    # Build prompt with system instructions and recent conversation
    conversation = SYSTEM_INSTRUCTION.strip() + "\n\nConversation History:\n"

    recent_messages = conversation_history[-12:]
    for message in recent_messages:
        role = "User" if message["role"] == "user" else "Assistant"
        conversation += f"\n{role}: {message['text']}"

    conversation += "\nAssistant:"

    # Try primary model then fallback models
    models_to_try = [DEFAULT_MODEL] + [m for m in FALLBACK_MODELS if m != DEFAULT_MODEL]

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=conversation
            )

            answer = response.text
            if answer and answer.strip():
                answer = answer.strip()
                conversation_history.append({
                    "role": "assistant",
                    "text": answer
                })
                return answer

        except Exception as error:
            print(f"Model {model_name} error: {error}")
            continue

    if conversation_history and conversation_history[-1]["role"] == "user":
        conversation_history.pop()

    return "Sorry, I'm having trouble connecting to the AI service right now. Please try again."


if __name__ == "__main__":
    print("=" * 50)
    print("Riosa Voice AI - Gemini Test")
    print("=" * 50)

    question = "What is Python?"
    print(f"\n👤 You: {question}")
    answer = ask_llm(question)
    print(f"\n🤖 Riosa: {answer}\n")

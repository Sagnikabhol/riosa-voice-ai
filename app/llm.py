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

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY was not found. "
        "Please check your .env file or Streamlit Cloud Secrets."
    )

# ---------------------------------------
# Create Gemini client
# ---------------------------------------
client = genai.Client(api_key=api_key)

# Configurable model with recommended defaults
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
FALLBACK_MODELS = ["gemini-flash-latest", "gemini-2.5-flash-lite"]

# ---------------------------------------
# Conversation memory
# ---------------------------------------
conversation_history = []


# ---------------------------------------
# Voice assistant instructions
# ---------------------------------------
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

    # Keep recent context (last 12 turns) to stay within reasonable limits
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

    # If all models fail, remove user message so memory is not corrupted
    if conversation_history and conversation_history[-1]["role"] == "user":
        conversation_history.pop()

    return "Sorry, I'm having trouble connecting to the AI service right now. Please try again."


# ---------------------------------------
# Quick standalone test
# ---------------------------------------
if __name__ == "__main__":
    print("=" * 50)
    print("Riosa Voice AI - Gemini Test")
    print("=" * 50)

    question = "What is Python?"
    print(f"\n👤 You: {question}")
    answer = ask_llm(question)
    print(f"\n🤖 Riosa: {answer}\n")

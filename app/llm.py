import os

from dotenv import load_dotenv
from google import genai


# ---------------------------------------
# Load environment variables
# ---------------------------------------
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY was not found. "
        "Please check your .env file."
    )


# ---------------------------------------
# Create Gemini client
# ---------------------------------------
client = genai.Client(api_key=api_key)


# ---------------------------------------
# Conversation memory
# ---------------------------------------
conversation_history = []


# ---------------------------------------
# Voice assistant instructions
# ---------------------------------------
SYSTEM_INSTRUCTION = """
You are a helpful voice AI assistant.

Your responses will be spoken aloud, so keep them
short, clear, natural, and conversational.

Rules:
- Usually answer in 1 to 3 sentences.
- Keep simple questions very short.
- Use simple and easy-to-understand language.
- Do not use Markdown.
- Do not use headings.
- Do not use bullet points or numbered lists.
- Do not repeat the user's question.
- Do not give long explanations unless the user specifically asks.
- If the user asks for a detailed explanation, then provide more detail.
- Do not add unnecessary information.
- Sound friendly and natural.
"""


def ask_llm(text):
    """
    Send the user's question to Gemini and return
    a short, voice-friendly response.
    """

    # Check empty input
    if not text or not text.strip():
        return "I didn't receive a question."

    # Add user message to conversation history
    conversation_history.append(
        {
            "role": "user",
            "text": text.strip()
        }
    )

    # ---------------------------------------
    # Build conversation
    # ---------------------------------------
    conversation = SYSTEM_INSTRUCTION

    conversation += "\n\nConversation:\n"

    for message in conversation_history:

        if message["role"] == "user":
            conversation += f"\nUser: {message['text']}"

        elif message["role"] == "assistant":
            conversation += f"\nAssistant: {message['text']}"

    # ---------------------------------------
    # Send request to Gemini
    # ---------------------------------------
    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=conversation
        )

        # Get Gemini response
        answer = response.text

        # Check empty response
        if not answer:
            return "Sorry, I couldn't generate a response."

        answer = answer.strip()

        # ---------------------------------------
        # Save Gemini response to memory
        # ---------------------------------------
        conversation_history.append(
            {
                "role": "assistant",
                "text": answer
            }
        )

        return answer

    except Exception as error:

        print(f"Gemini API error: {error}")

        return (
            "Sorry, I'm having trouble connecting "
            "to the AI service."
        )


# ---------------------------------------
# Test the LLM directly
# ---------------------------------------
if __name__ == "__main__":

    print("Voice AI Assistant - Gemini Test")
    print("--------------------------------")

    question = "What is Python?"

    print(f"\nYou: {question}")

    answer = ask_llm(question)

    print(f"\nGemini: {answer}")
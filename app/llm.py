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
You are Riosa, a helpful voice AI assistant.

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
- If the user asks for a detailed explanation, provide more detail.
- Do not add unnecessary information.
- Sound friendly and natural.
"""


def ask_llm(text):

    # ---------------------------------------
    # Check empty input
    # ---------------------------------------

    if not text or not text.strip():
        return "I didn't receive a question."


    # ---------------------------------------
    # Add user message
    # ---------------------------------------

    user_message = text.strip()

    conversation_history.append(
        {
            "role": "user",
            "text": user_message
        }
    )


    # ---------------------------------------
    # Build conversation
    # ---------------------------------------

    conversation = SYSTEM_INSTRUCTION

    conversation += "\n\nConversation:\n"

    for message in conversation_history:

        if message["role"] == "user":

            conversation += (
                f"\nUser: {message['text']}"
            )

        elif message["role"] == "assistant":

            conversation += (
                f"\nAssistant: {message['text']}"
            )


    # ---------------------------------------
    # Send request to Gemini
    # ---------------------------------------

    try:

        print("🤖 Sending request to Gemini...")

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=conversation
        )

        answer = response.text


        # -----------------------------------
        # Check response
        # -----------------------------------

        if not answer:

            print("❌ Gemini returned an empty response.")

            return "Sorry, I couldn't generate a response."


        answer = answer.strip()


        # -----------------------------------
        # Save response
        # -----------------------------------

        conversation_history.append(
            {
                "role": "assistant",
                "text": answer
            }
        )


        print("✅ Gemini response received.")

        return answer


    except Exception as error:

        # IMPORTANT:
        # Show the REAL Gemini error in terminal.

        print("\n" + "=" * 60)
        print("❌ GEMINI API ERROR")
        print("=" * 60)

        print(f"Error type: {type(error).__name__}")
        print(f"Error details: {error}")

        print("=" * 60 + "\n")


        # Remove failed user message
        # so conversation memory does not become corrupted.

        if conversation_history:

            if (
                conversation_history[-1]["role"] == "user"
                and
                conversation_history[-1]["text"] == user_message
            ):
                conversation_history.pop()


        return (
            "Sorry, I'm having trouble connecting "
            "to the AI service."
        )


# ---------------------------------------
# Test Gemini directly
# ---------------------------------------

if __name__ == "__main__":

    print("=" * 50)
    print("Riosa Voice AI - Gemini Test")
    print("=" * 50)

    question = "What is Python?"

    print(f"\n👤 You: {question}")

    answer = ask_llm(question)

    print(f"\n🤖 Riosa: {answer}")
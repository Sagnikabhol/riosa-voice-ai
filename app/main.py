from speech_to_text import listen
from llm import ask_llm
from text_to_speech import speak


EXIT_COMMANDS = {
    "exit",
    "quit",
    "stop",
    "goodbye"
}


def main():

    print("=" * 45)
    print("        VOICE AI ASSISTANT")
    print("=" * 45)

    print("Say 'exit', 'quit', or 'stop' to close.\n")

    while True:

        # -----------------------------
        # Speech to Text
        # -----------------------------
        print("🎤 Your turn...")

        user_text = listen()

        if not user_text:
            print("Let's try again.\n")
            continue

        print(f"\n👤 You: {user_text}")

        # -----------------------------
        # Exit command
        # -----------------------------
        command = user_text.lower().strip()

        if command in EXIT_COMMANDS:

            print("👋 Goodbye!")

            speak("Goodbye!")

            break

        # -----------------------------
        # Gemini
        # -----------------------------
        print("\n🤖 Thinking...")

        response = ask_llm(user_text)

        print(f"\n🤖 Gemini:\n{response}")

        # -----------------------------
        # Text to Speech
        # -----------------------------
        print("\n🔊 Speaking...")

        speak(response)

        print("\n" + "-" * 45)
        print("Ready for your next question.\n")


if __name__ == "__main__":
    main()
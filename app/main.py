import sys
from speech_to_text import listen, is_microphone_available
from llm import ask_llm, clear_history
from text_to_speech import speak

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

EXIT_COMMANDS = {
    "exit",
    "quit",
    "stop",
    "goodbye",
    "bye"
}


def print_banner():
    print("=" * 60)
    print("       🤖 RIOSA - INTERACTIVE VOICE & TEXT AI ASSISTANT")
    print("=" * 60)
    print("Commands:")
    print("  • Type any question directly and press Enter")
    print("  • Type 'voice' or 'mic' (or press Enter on empty line) to speak")
    print("  • Type 'loop' to start continuous hands-free voice mode")
    print("  • Type 'mute' / 'unmute' to toggle spoken responses")
    print("  • Type 'clear' to reset conversation history")
    print("  • Type 'exit' or 'quit' to close")
    print("=" * 60 + "\n")


def run_continuous_voice(speak_enabled=True):
    """Hands-free continuous voice loop."""
    print("\n[🎙️ Starting continuous voice mode. Say 'exit' or 'stop' to return to menu.]\n")
    while True:
        print("🎤 Listening... (speak into microphone)")
        user_text = listen()

        if not user_text:
            print("No speech detected. Press Ctrl+C or say 'exit' to stop.\n")
            continue

        print(f"\n👤 You (voice): {user_text}")

        command = user_text.lower().strip()
        if command in EXIT_COMMANDS:
            print("👋 Returning to interactive menu...")
            if speak_enabled:
                speak("Goodbye from voice mode.")
            break

        print("\n🤖 Thinking...")
        response = ask_llm(user_text)
        print(f"\n🤖 Riosa:\n{response}\n")

        if speak_enabled:
            print("🔊 Speaking response...")
            speak(response)

        print("-" * 50)


def main():
    print_banner()

    speak_enabled = True
    mic_ready = is_microphone_available()

    if mic_ready:
        print("✅ Microphone detected and ready.")
    else:
        print("⚠️ No microphone detected. Running in text-first mode.")

    print()

    while True:
        try:
            prompt_indicator = "🔊" if speak_enabled else "🔇"
            user_input = input(f"[{prompt_indicator}] Ask Riosa (or press Enter to speak): ").strip()

            # Empty input -> trigger speech recognition if mic is available
            if not user_input:
                if not mic_ready:
                    print("⚠️ Microphone not detected. Please type your question.")
                    continue
                user_text = listen()
                if not user_text:
                    continue
            else:
                user_text = user_input

            command_lower = user_text.lower().strip()

            # Exit command
            if command_lower in EXIT_COMMANDS:
                print("\n👋 Goodbye! Thanks for chatting with Riosa.")
                if speak_enabled:
                    speak("Goodbye! Have a great day.")
                break

            # Help command
            if command_lower == "help":
                print_banner()
                continue

            # Clear memory command
            if command_lower == "clear":
                clear_history()
                print("🧹 Conversation memory cleared.\n")
                continue

            # Mute / unmute
            if command_lower in {"mute", "tts off", "quiet"}:
                speak_enabled = False
                print("🔇 Spoken voice output disabled.\n")
                continue

            if command_lower in {"unmute", "tts on", "speak"}:
                speak_enabled = True
                print("🔊 Spoken voice output enabled.\n")
                continue

            # Continuous voice mode
            if command_lower in {"loop", "continuous", "voice loop"}:
                run_continuous_voice(speak_enabled=speak_enabled)
                continue

            # Explicit mic command
            if command_lower in {"voice", "mic", "listen"}:
                user_text = listen()
                if not user_text:
                    continue

            # Process with Gemini
            print("\n🤖 Thinking...")
            response = ask_llm(user_text)
            print(f"\n🤖 Riosa:\n{response}\n")

            # Spoken response
            if speak_enabled:
                print("🔊 Speaking...")
                speak(response)

            print("-" * 50)

        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Session ended. Goodbye!")
            break
        except Exception as error:
            print(f"\n❌ Unexpected error: {error}\n")


if __name__ == "__main__":
    main()

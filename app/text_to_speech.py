import sys
import pyttsx3

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def speak(text, rate=170, volume=1.0):
    """
    Convert text into spoken audio using pyttsx3.
    """
    if not text:
        return

    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)
        engine.setProperty("volume", volume)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as error:
        print(f"Text-to-speech error: {error}")


if __name__ == "__main__":
    print("Testing text-to-speech...")
    speak("Hello! I am Riosa, your interactive voice AI assistant.")
    print("Done speaking.")

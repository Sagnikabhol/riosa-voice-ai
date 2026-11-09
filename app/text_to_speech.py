import sys
import threading
import pyttsx3

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_tts_lock = threading.Lock()


def _speak_worker(text, rate=170, volume=1.0):
    """Internal worker that runs pyttsx3 safely with Windows COM initialized."""
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception:
        pass

    try:
        with _tts_lock:
            engine = pyttsx3.init()
            engine.setProperty("rate", rate)
            engine.setProperty("volume", volume)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
    except Exception as error:
        print(f"Text-to-speech error: {error}")


def speak(text, rate=170, volume=1.0, async_mode=False):
    """
    Convert text into spoken audio.
    If async_mode is True, speaks in a background daemon thread so it never blocks callers.
    """
    if not text:
        return

    if async_mode:
        t = threading.Thread(
            target=_speak_worker,
            args=(text, rate, volume),
            daemon=True
        )
        t.start()
    else:
        _speak_worker(text, rate, volume)


if __name__ == "__main__":
    print("Testing text-to-speech...")
    speak("Hello! I am Riosa, your interactive voice AI assistant.", async_mode=False)
    print("Done speaking.")

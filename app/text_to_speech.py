import sys
import io
import threading

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_tts_lock = threading.Lock()


def generate_speech_audio(text: str) -> bytes | None:
    """
    Generate MP3 speech audio bytes using Google Text-to-Speech (gTTS).
    Works in all cloud environments (Streamlit Cloud, Linux, Docker) and mobile browsers.
    Returns raw MP3 bytes that can be played with st.audio(bytes, format='audio/mp3').
    """
    if not text or not text.strip():
        return None

    try:
        from gtts import gTTS
        buf = io.BytesIO()
        tts = gTTS(text=text.strip(), lang="en", slow=False)
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.getvalue()
    except Exception as error:
        print(f"gTTS audio generation error: {error}")
        return None


def _speak_local_worker(text, rate=170, volume=1.0):
    """Local offline speech synthesis using pyttsx3 (for desktop CLI)."""
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception:
        pass

    try:
        import pyttsx3
        with _tts_lock:
            engine = pyttsx3.init()
            engine.setProperty("rate", rate)
            engine.setProperty("volume", volume)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
    except Exception as error:
        print(f"Local pyttsx3 error: {error}")


def speak(text, rate=170, volume=1.0, async_mode=False):
    """
    Speak text using local system audio (CLI mode).
    If async_mode is True, runs in a daemon thread.
    """
    if not text:
        return

    if async_mode:
        t = threading.Thread(
            target=_speak_local_worker,
            args=(text, rate, volume),
            daemon=True
        )
        t.start()
    else:
        _speak_local_worker(text, rate, volume)


if __name__ == "__main__":
    print("Testing generate_speech_audio...")
    audio = generate_speech_audio("Hello! I am Riosa, your interactive voice AI.")
    print("Generated MP3 bytes:", len(audio) if audio else "Failed")

import sys
import io
import speech_recognition as sr

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.7
recognizer.phrase_threshold = 0.2
recognizer.non_speaking_duration = 0.4


def is_microphone_available():
    """Check if host microphone is available (for local CLI)."""
    try:
        devices = sr.Microphone.list_microphone_names()
        return len(devices) > 0
    except Exception:
        return False


def listen(timeout=5, phrase_time_limit=10):
    """
    Listen to local host microphone (CLI mode).
    """
    try:
        with sr.Microphone() as source:
            print("🎤 Listening... (speak now)")
            recognizer.adjust_for_ambient_noise(source, duration=0.3)

            try:
                audio = recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            except sr.WaitTimeoutError:
                print("⏱️ No speech detected within timeout.")
                return None

    except Exception as error:
        print(f"🎤 Microphone error: {error}")
        return None

    try:
        text = recognizer.recognize_google(audio)
        text = text.strip()
        if text:
            print(f"👤 You (voice): {text}")
            return text
        return None
    except Exception as error:
        print(f"Speech processing error: {error}")
        return None


def resolve_audio_mime(mime_type):
    """Normalize MIME types from mobile browsers (Safari/Chrome/Firefox)."""
    if not mime_type:
        return "audio/webm"
    m = mime_type.lower()
    if "webm" in m:
        return "audio/webm"
    if "mp4" in m or "m4a" in m or "aac" in m:
        return "audio/mp4"
    if "ogg" in m:
        return "audio/ogg"
    if "wav" in m:
        return "audio/wav"
    if "mp3" in m:
        return "audio/mp3"
    return "audio/webm"


def transcribe_audio_buffer(audio_bytes, mime_type="audio/wav"):
    """
    Transcribe audio recorded on phones or web browsers.
    Supports all mobile browser formats: WebM, MP4, AAC, OGG, WAV.
    Uses Google Gemini multimodal audio recognition with SpeechRecognition fallback.
    """
    if not audio_bytes:
        return None

    resolved_mime = resolve_audio_mime(mime_type)

    # 1. Primary: Google Gemini multimodal audio model (handles WebM, MP4, AAC from phones natively)
    try:
        from llm import get_client, DEFAULT_MODEL
        from google.genai import types

        client = get_client()
        if client:
            part = types.Part.from_bytes(data=audio_bytes, mime_type=resolved_mime)
            prompt = (
                "Transcribe the spoken audio precisely into text. "
                "Output ONLY the transcribed text. Do not add quotes, introductory phrases, or explanations. "
                "If the audio contains no discernible speech or only noise, reply with UNINTELLIGIBLE."
            )

            response = client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=[part, prompt]
            )

            if response.text and response.text.strip():
                result = response.text.strip()
                if "UNINTELLIGIBLE" in result.upper() and len(result) < 25:
                    return None
                return result
    except Exception as gemini_err:
        print(f"Gemini audio transcription fallback error: {gemini_err}")

    # 2. Secondary fallback: SpeechRecognition AudioFile (for WAV formats)
    try:
        buf = io.BytesIO(audio_bytes)
        with sr.AudioFile(buf) as source:
            recorded = recognizer.record(source)
            text = recognizer.recognize_google(recorded)
            if text and text.strip():
                return text.strip()
    except Exception:
        pass

    return None


if __name__ == "__main__":
    print("Microphone Available:", is_microphone_available())

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

# Calibrated settings for responsiveness
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.7
recognizer.phrase_threshold = 0.2
recognizer.non_speaking_duration = 0.4


def is_microphone_available():
    """Check if any microphone audio input device is available."""
    try:
        devices = sr.Microphone.list_microphone_names()
        return len(devices) > 0
    except Exception:
        return False


def listen(timeout=5, phrase_time_limit=10):
    """
    Listen to the host microphone and convert speech to text using Google Speech Recognition.
    Returns the recognized string, or None if no speech was detected.
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

    except OSError as error:
        print(f"🎤 Microphone device error: {error}")
        return None
    except Exception as error:
        print(f"🎤 Microphone error: {error}")
        return None

    # Convert speech to text
    try:
        print("🧠 Transcribing...")
        text = recognizer.recognize_google(audio)
        text = text.strip()
        if text:
            print(f"👤 You (voice): {text}")
            return text
        return None

    except sr.UnknownValueError:
        print("❌ Could not understand the audio.")
        return None
    except sr.RequestError as error:
        print(f"❌ Speech recognition service error: {error}")
        return None
    except Exception as error:
        print(f"❌ Speech processing error: {error}")
        return None


def transcribe_audio_buffer(audio_bytes, mime_type="audio/wav"):
    """
    Transcribe recorded audio bytes (from mobile browser or web audio input).
    First attempts SpeechRecognition WAV decoding; falls back to Gemini multimodal transcription.
    """
    if not audio_bytes:
        return None

    # 1. Attempt standard SpeechRecognition AudioFile
    try:
        buf = io.BytesIO(audio_bytes)
        with sr.AudioFile(buf) as source:
            recorded = recognizer.record(source)
            text = recognizer.recognize_google(recorded)
            if text and text.strip():
                return text.strip()
    except Exception:
        pass

    # 2. Fallback to Gemini multimodal audio model
    try:
        from llm import client, DEFAULT_MODEL
        from google.genai import types

        resolved_mime = mime_type if mime_type else "audio/wav"
        part = types.Part.from_bytes(data=audio_bytes, mime_type=resolved_mime)
        prompt = "Transcribe the spoken audio precisely into text. Output only the transcription, without any preamble or quotes."

        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=[part, prompt]
        )
        if response.text and response.text.strip():
            return response.text.strip()
    except Exception as err:
        print(f"Fallback audio transcription failed: {err}")

    return None


if __name__ == "__main__":
    print("Microphone Available:", is_microphone_available())
    print("Testing speech recognition (say something)...")
    result = listen()
    print("Recognized:", result)

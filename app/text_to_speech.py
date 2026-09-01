import pyttsx3


def speak(text):
    """
    Convert text into spoken audio.
    """

    if not text:
        return

    try:
        engine = pyttsx3.init()

        engine.setProperty("rate", 170)
        engine.setProperty("volume", 1.0)

        engine.say(text)
        engine.runAndWait()

        engine.stop()

    except Exception as error:
        print(f"Text-to-speech error: {error}")
import speech_recognition as sr


recognizer = sr.Recognizer()

# Faster response
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True

# Stop listening shortly after you stop speaking
recognizer.pause_threshold = 0.6

# Don't wait too long for speech
recognizer.phrase_threshold = 0.2

# Minimum non-speaking time before considering phrase complete
recognizer.non_speaking_duration = 0.4


def listen():
    """
    Listen to the microphone and convert speech to text.
    """

    try:
        with sr.Microphone() as source:

            print("🎤 Listening...")

            # Small calibration period
            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.3
            )

            try:

                audio = recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=8
                )

            except sr.WaitTimeoutError:

                print("⏱️ No speech detected.")
                return None

    except OSError as error:

        print(f"🎤 Microphone error: {error}")
        return None

    except Exception as error:

        print(f"Microphone error: {error}")
        return None


    # --------------------------------------------------------
    # Convert speech to text
    # --------------------------------------------------------

    try:

        print("🧠 Processing...")

        text = recognizer.recognize_google(audio)

        text = text.strip()

        if text:

            print(f"👤 You: {text}")

            return text

        return None


    except sr.UnknownValueError:

        print("❌ I couldn't understand that.")
        return None


    except sr.RequestError as error:

        print(
            f"❌ Speech recognition service error: {error}"
        )

        return None


    except Exception as error:

        print(f"❌ Speech processing error: {error}")
        return None
import threading
import queue
import speech_recognition as sr
import pyttsx3

from llm import ask_llm


# ============================================================
# EXIT COMMANDS
# ============================================================

EXIT_COMMANDS = {
    "exit",
    "quit",
    "bye",
    "goodbye",
    "stop",
    "shutdown"
}


# ============================================================
# VOICE ENGINE
# ============================================================

class RiosaVoiceEngine:

    def __init__(self):

        self.running = False

        self.stop_event = threading.Event()

        self.thread = None

        self.events = queue.Queue()

        self.engine_lock = threading.Lock()


    # ========================================================
    # START
    # ========================================================

    def start(self):

        if self.running:
            return

        self.running = True

        self.stop_event.clear()

        self.thread = threading.Thread(
            target=self._voice_loop,
            daemon=True
        )

        self.thread.start()


    # ========================================================
    # STOP
    # ========================================================

    def stop(self):

        self.running = False

        self.stop_event.set()

        try:

            if self.thread and self.thread.is_alive():

                self.thread.join(
                    timeout=1
                )

        except Exception:
            pass


    # ========================================================
    # SPEAK
    # ========================================================

    def speak(self, text):

        if not text:
            return

        if self.stop_event.is_set():
            return

        try:

            with self.engine_lock:

                engine = pyttsx3.init()

                engine.setProperty(
                    "rate",
                    175
                )

                engine.setProperty(
                    "volume",
                    1.0
                )

                engine.say(text)

                engine.runAndWait()

                engine.stop()

        except Exception as error:

            self.events.put(
                {
                    "type": "error",
                    "message": str(error)
                }
            )


    # ========================================================
    # LISTEN
    # ========================================================

    def listen(self):

        recognizer = sr.Recognizer()

        recognizer.energy_threshold = 300

        recognizer.dynamic_energy_threshold = True

        recognizer.pause_threshold = 0.8


        try:

            with sr.Microphone() as source:

                self.events.put(
                    {
                        "type": "status",
                        "value": "listening"
                    }
                )

                audio = recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=15
                )


            text = recognizer.recognize_google(
                audio
            )

            text = text.strip()

            if text:

                self.events.put(
                    {
                        "type": "user",
                        "message": text
                    }
                )

            return text


        except sr.WaitTimeoutError:

            return ""


        except sr.UnknownValueError:

            return ""


        except sr.RequestError as error:

            self.events.put(
                {
                    "type": "error",
                    "message": str(error)
                }
            )

            return ""


        except Exception as error:

            self.events.put(
                {
                    "type": "error",
                    "message": str(error)
                }
            )

            return ""


    # ========================================================
    # EXIT CHECK
    # ========================================================

    def is_exit_command(self, text):

        if not text:
            return False

        command = text.lower().strip()

        return command in EXIT_COMMANDS


    # ========================================================
    # MAIN VOICE LOOP
    # ========================================================

    def _voice_loop(self):

        try:

            while self.running and not self.stop_event.is_set():

                # --------------------------------------------
                # LISTEN
                # --------------------------------------------

                user_text = self.listen()


                if not user_text:

                    continue


                # --------------------------------------------
                # EXIT
                # --------------------------------------------

                if self.is_exit_command(user_text):

                    goodbye = (
                        "Goodbye! Have a great day."
                    )

                    self.events.put(
                        {
                            "type": "assistant",
                            "message": goodbye
                        }
                    )

                    self.events.put(
                        {
                            "type": "status",
                            "value": "speaking"
                        }
                    )

                    self.speak(goodbye)

                    self.running = False

                    self.events.put(
                        {
                            "type": "stopped"
                        }
                    )

                    break


                # --------------------------------------------
                # THINKING
                # --------------------------------------------

                self.events.put(
                    {
                        "type": "status",
                        "value": "thinking"
                    }
                )


                try:

                    response = ask_llm(
                        user_text
                    )

                except Exception:

                    response = (
                        "Sorry, I couldn't "
                        "process that. Please try again."
                    )


                # --------------------------------------------
                # SEND ANSWER TO UI
                # --------------------------------------------

                self.events.put(
                    {
                        "type": "assistant",
                        "message": response
                    }
                )


                # --------------------------------------------
                # SPEAK
                # --------------------------------------------

                self.events.put(
                    {
                        "type": "status",
                        "value": "speaking"
                    }
                )

                self.speak(response)


                # --------------------------------------------
                # AUTOMATICALLY CONTINUE
                # --------------------------------------------

                if self.running and not self.stop_event.is_set():

                    self.events.put(
                        {
                            "type": "status",
                            "value": "listening"
                        }
                    )


        finally:

            self.running = False


    # ========================================================
    # GET EVENTS
    # ========================================================

    def get_events(self):

        events = []

        while True:

            try:

                events.append(
                    self.events.get_nowait()
                )

            except queue.Empty:

                break

        return events
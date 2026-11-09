import sys
import threading
import queue
import speech_recognition as sr
import pyttsx3

from llm import ask_llm, clear_history as clear_llm_history

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


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
    """
    Background voice engine for continuous PC microphone listening.
    Communicates via thread-safe queue.
    """

    def __init__(self):
        self.running = False
        self.stop_event = threading.Event()
        self.thread = None
        self.events = queue.Queue()
        self.engine_lock = threading.Lock()
        self.speech_enabled = True
        self.speech_rate = 175
        self.speech_volume = 1.0

    def set_speech_enabled(self, enabled: bool):
        """Enable or disable spoken audio output."""
        self.speech_enabled = bool(enabled)

    def set_speech_rate(self, rate: int):
        """Adjust speech rate (speed)."""
        self.speech_rate = max(100, min(300, rate))

    # ========================================================
    # START / STOP
    # ========================================================
    def start(self):
        """Start the continuous voice loop in a background thread."""
        if self.running:
            return

        self.running = True
        self.stop_event.clear()

        self.thread = threading.Thread(
            target=self._voice_loop,
            daemon=True
        )
        self.thread.start()

    def stop(self):
        """Stop the background voice loop."""
        self.running = False
        self.stop_event.set()

        try:
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=1.0)
        except Exception:
            pass

        self.events.put({"type": "stopped"})

    # ========================================================
    # SPEAK (THREAD-SAFE & NON-BLOCKING)
    # ========================================================
    def speak(self, text):
        """Speak text using pyttsx3 in a thread-safe worker."""
        if not text or not self.speech_enabled or self.stop_event.is_set():
            return

        def _do_speak():
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception:
                pass

            try:
                with self.engine_lock:
                    engine = pyttsx3.init()
                    engine.setProperty("rate", self.speech_rate)
                    engine.setProperty("volume", self.speech_volume)
                    engine.say(text)
                    engine.runAndWait()
                    engine.stop()
            except Exception as error:
                self.events.put({
                    "type": "error",
                    "message": f"TTS Error: {error}"
                })

        threading.Thread(target=_do_speak, daemon=True).start()

    # ========================================================
    # LISTEN
    # ========================================================
    def listen(self):
        """Listen to microphone and convert to text."""
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8

        try:
            with sr.Microphone() as source:
                self.events.put({
                    "type": "status",
                    "value": "listening"
                })

                recognizer.adjust_for_ambient_noise(source, duration=0.25)
                audio = recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=15
                )

            text = recognizer.recognize_google(audio)
            text = text.strip()

            if text:
                self.events.put({
                    "type": "user",
                    "message": text
                })
            return text

        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as error:
            self.events.put({
                "type": "error",
                "message": f"Speech recognition service error: {error}"
            })
            return ""
        except Exception as error:
            self.events.put({
                "type": "error",
                "message": f"Microphone error: {error}"
            })
            return ""

    def is_exit_command(self, text):
        if not text:
            return False
        return text.lower().strip() in EXIT_COMMANDS

    # ========================================================
    # MAIN VOICE LOOP
    # ========================================================
    def _voice_loop(self):
        """Continuous background loop for speech recognition."""
        try:
            while self.running and not self.stop_event.is_set():
                user_text = self.listen()

                if not user_text:
                    continue

                if self.is_exit_command(user_text):
                    goodbye = "Goodbye! Have a great day."
                    self.events.put({
                        "type": "assistant",
                        "message": goodbye
                    })
                    self.events.put({
                        "type": "status",
                        "value": "speaking"
                    })
                    self.speak(goodbye)
                    self.running = False
                    self.events.put({"type": "stopped"})
                    break

                self.events.put({
                    "type": "status",
                    "value": "thinking"
                })

                try:
                    response = ask_llm(user_text)
                except Exception:
                    response = "Sorry, I couldn't process that. Please try again."

                self.events.put({
                    "type": "assistant",
                    "message": response
                })

                self.events.put({
                    "type": "status",
                    "value": "speaking"
                })
                self.speak(response)

                if self.running and not self.stop_event.is_set():
                    self.events.put({
                        "type": "status",
                        "value": "listening"
                    })

        finally:
            self.running = False

    def get_events(self):
        events = []
        while True:
            try:
                events.append(self.events.get_nowait())
            except queue.Empty:
                break
        return events

    def reset(self):
        clear_llm_history()
        while not self.events.empty():
            try:
                self.events.get_nowait()
            except queue.Empty:
                break

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
    Background engine for interactive voice and text processing.
    Handles microphone listening, LLM communication, TTS output,
    and event queuing for Streamlit or CLI frontends.
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
    # SPEAK
    # ========================================================
    def speak(self, text):
        """Speak text aloud using pyttsx3 in a thread-safe manner."""
        if not text or not self.speech_enabled:
            return

        if self.stop_event.is_set():
            return

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
        """Check if message is an exit command."""
        if not text:
            return False
        return text.lower().strip() in EXIT_COMMANDS

    # ========================================================
    # PROCESS DIRECT TEXT INPUT (Interactive Chat)
    # ========================================================
    def process_text(self, user_text):
        """
        Process a user text prompt synchronously.
        Emits appropriate events and optionally speaks the answer.
        """
        if not user_text or not user_text.strip():
            return None

        clean_text = user_text.strip()

        # Emit user message event
        self.events.put({
            "type": "user",
            "message": clean_text
        })

        if self.is_exit_command(clean_text):
            goodbye = "Goodbye! Have a wonderful day."
            self.events.put({
                "type": "assistant",
                "message": goodbye
            })
            if self.speech_enabled:
                self.speak(goodbye)
            return goodbye

        # Status thinking
        self.events.put({
            "type": "status",
            "value": "thinking"
        })

        try:
            response = ask_llm(clean_text)
        except Exception as err:
            response = f"Sorry, I encountered an issue: {err}"

        # Emit assistant response
        self.events.put({
            "type": "assistant",
            "message": response
        })

        # Speak if enabled
        if self.speech_enabled:
            self.events.put({
                "type": "status",
                "value": "speaking"
            })
            self.speak(response)

        self.events.put({
            "type": "status",
            "value": "ready"
        })

        return response

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

                # Thinking
                self.events.put({
                    "type": "status",
                    "value": "thinking"
                })

                try:
                    response = ask_llm(user_text)
                except Exception:
                    response = "Sorry, I couldn't process that. Please try again."

                # Send answer to UI
                self.events.put({
                    "type": "assistant",
                    "message": response
                })

                # Speak
                self.events.put({
                    "type": "status",
                    "value": "speaking"
                })
                self.speak(response)

                # Return to listening if still active
                if self.running and not self.stop_event.is_set():
                    self.events.put({
                        "type": "status",
                        "value": "listening"
                    })

        finally:
            self.running = False

    # ========================================================
    # GET EVENTS
    # ========================================================
    def get_events(self):
        """Drain and return all queued events."""
        events = []
        while True:
            try:
                events.append(self.events.get_nowait())
            except queue.Empty:
                break
        return events

    # ========================================================
    # RESET
    # ========================================================
    def reset(self):
        """Reset conversation memory and engine state."""
        clear_llm_history()
        while not self.events.empty():
            try:
                self.events.get_nowait()
            except queue.Empty:
                break

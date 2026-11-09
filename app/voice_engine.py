import sys
import os
import threading
import queue

# Ensure local app path is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

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


EXIT_COMMANDS = {
    "exit",
    "quit",
    "bye",
    "goodbye",
    "stop",
    "shutdown"
}


class RiosaVoiceEngine:
    def __init__(self):
        self.running = False
        self.stop_event = threading.Event()
        self.thread = None
        self.events = queue.Queue()
        self.engine_lock = threading.Lock()
        self.speech_enabled = True

    def start(self):
        """Start the continuous voice listening loop."""
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
        """Stop the continuous voice listening loop."""
        self.running = False
        self.stop_event.set()

        try:
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=1.0)
        except Exception:
            pass

        self.events.put({"type": "stopped"})

    def speak(self, text):
        """Speak text aloud using pyttsx3 in a thread-safe way."""
        if not text or self.stop_event.is_set():
            return

        def _worker():
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception:
                pass

            try:
                with self.engine_lock:
                    engine = pyttsx3.init()
                    engine.setProperty("rate", 175)
                    engine.setProperty("volume", 1.0)
                    engine.say(text)
                    engine.runAndWait()
                    engine.stop()
            except Exception as error:
                print(f"TTS Speech error: {error}")
                self.events.put({
                    "type": "error",
                    "message": f"TTS Error: {error}"
                })

        threading.Thread(target=_worker, daemon=True).start()

    def listen(self):
        """Listen to microphone and convert speech to text."""
        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.7
        recognizer.phrase_threshold = 0.2
        recognizer.non_speaking_duration = 0.4

        try:
            with sr.Microphone() as source:
                self.events.put({
                    "type": "status",
                    "value": "listening"
                })

                # Calibrate ambient noise so microphone picks up speech properly
                recognizer.adjust_for_ambient_noise(source, duration=0.3)

                try:
                    audio = recognizer.listen(
                        source,
                        timeout=5,
                        phrase_time_limit=12
                    )
                except sr.WaitTimeoutError:
                    return ""

            try:
                text = recognizer.recognize_google(audio)
                text = text.strip()

                if text:
                    self.events.put({
                        "type": "user",
                        "message": text
                    })
                return text

            except sr.UnknownValueError:
                # Speech detected but was not intelligible
                return ""
            except sr.RequestError as error:
                self.events.put({
                    "type": "error",
                    "message": f"Speech service error: {error}"
                })
                return ""

        except Exception as error:
            print(f"Microphone listen error: {error}")
            self.events.put({
                "type": "error",
                "message": f"Microphone error: {error}"
            })
            return ""

    def is_exit_command(self, text):
        if not text:
            return False
        return text.lower().strip() in EXIT_COMMANDS

    def process_text(self, text):
        """Process typed user text directly."""
        if not text or not text.strip():
            return None

        clean_text = text.strip()
        self.events.put({"type": "user", "message": clean_text})

        if self.is_exit_command(clean_text):
            goodbye = "Goodbye! Have a great day."
            self.events.put({"type": "assistant", "message": goodbye})
            self.speak(goodbye)
            return goodbye

        self.events.put({"type": "status", "value": "thinking"})

        try:
            response = ask_llm(clean_text)
        except Exception as err:
            response = f"Sorry, I had trouble processing that: {err}"

        self.events.put({"type": "assistant", "message": response})
        self.events.put({"type": "status", "value": "speaking"})
        self.speak(response)
        self.events.put({"type": "status", "value": "ready"})
        return response

    def _voice_loop(self):
        """Continuous background voice loop."""
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

                # Thinking status
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

                # Speak status & speech
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

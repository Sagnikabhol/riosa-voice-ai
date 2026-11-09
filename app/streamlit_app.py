import streamlit as st
import html
import json
import time
import socket
import os

from voice_engine import RiosaVoiceEngine
from speech_to_text import is_microphone_available, transcribe_audio_buffer

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Riosa - Voice & Interactive AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Detect local Wi-Fi IP for phone connection
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

local_ip = get_local_ip()
mobile_url = f"http://{local_ip}:8501"

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_engine" not in st.session_state:
    st.session_state.voice_engine = RiosaVoiceEngine()

if "voice_running" not in st.session_state:
    st.session_state.voice_running = False

if "status" not in st.session_state:
    st.session_state.status = "ready"

if "enable_tts" not in st.session_state:
    st.session_state.enable_tts = True

if "speech_rate" not in st.session_state:
    st.session_state.speech_rate = 175

if "last_spoken_id" not in st.session_state:
    st.session_state.last_spoken_id = -1

if "last_processed_audio_id" not in st.session_state:
    st.session_state.last_processed_audio_id = None

engine = st.session_state.voice_engine
engine.set_speech_enabled(st.session_state.enable_tts)
engine.set_speech_rate(st.session_state.speech_rate)

# ============================================================
# MOBILE-FIRST RESPONSIVE CYBERPUNK STYLING
# ============================================================
st.html("""
<style>
/* Global background */
html, body, [data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 50% 10%, rgba(55, 80, 150, 0.28), transparent 32%),
        radial-gradient(circle at 10% 85%, rgba(90, 40, 150, 0.18), transparent 30%),
        radial-gradient(circle at 90% 75%, rgba(20, 90, 150, 0.18), transparent 30%),
        #080a0f !important;
    min-height: 100vh;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
}

[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

footer {
    display: none !important;
}

/* Container responsive adjustments */
.block-container {
    max-width: 860px !important;
    padding-top: 15px !important;
    padding-bottom: 75px !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    position: relative;
    z-index: 1;
}

/* HEADER */
.header {
    text-align: center;
    margin-bottom: 18px;
}

.logo {
    width: 68px;
    height: 68px;
    margin: auto;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle, #29364e, #151b27);
    border: 1px solid #3d4f6b;
    font-size: 32px;
    box-shadow: 0 0 30px rgba(80,110,190,0.35);
    animation: float 4s ease-in-out infinite alternate;
}

@keyframes float {
    from { transform: translateY(0px); }
    to { transform: translateY(-5px); }
}

.title {
    color: #ffffff;
    font-size: 30px;
    font-weight: 700;
    margin-top: 8px;
    letter-spacing: 0.5px;
}

.subtitle {
    color: #8b97ac;
    font-size: 13px;
    margin-top: 3px;
}

.online-badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    margin-top: 10px;
    padding: 5px 12px;
    border-radius: 20px;
    background: rgba(15,20,29,0.85);
    border: 1px solid #293242;
    color: #a0abbd;
    font-size: 10.5px;
}

.dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #4ade80;
    box-shadow: 0 0 8px rgba(74,222,128,0.8);
    display: inline-block;
}

/* MOBILE CONNECTION PILL */
.mobile-pill {
    background: rgba(30, 42, 65, 0.45);
    border: 1px dashed rgba(80, 110, 180, 0.5);
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 16px;
    font-size: 12px;
    color: #9cb3d8;
    text-align: center;
}

.mobile-pill strong {
    color: #60a5fa;
    user-select: all;
}

/* VOICE CARD */
.voice-card {
    background: linear-gradient(145deg, rgba(18,23,33,0.96), rgba(10,14,21,0.96));
    border: 1px solid rgba(75,87,108,0.45);
    border-radius: 26px;
    padding: 28px 16px 24px 16px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.03);
    margin-bottom: 16px;
}

.mic-wrapper {
    width: 120px;
    height: 120px;
    margin: auto;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle, #34425c 0%, #202a3b 38%, #121824 68%, #0d1119 100%);
    border: 1px solid #46546b;
    box-shadow:
        0 0 0 8px rgba(80,100,140,0.04),
        0 0 0 16px rgba(80,100,140,0.02),
        0 0 40px rgba(80,110,190,0.25);
    transition: all 0.3s ease;
}

.mic-wrapper.listening {
    border-color: #38bdf8;
    box-shadow:
        0 0 0 10px rgba(56, 189, 248, 0.18),
        0 0 0 20px rgba(56, 189, 248, 0.08),
        0 0 55px rgba(56, 189, 248, 0.5);
    animation: pulse 1.5s infinite;
}

.mic-wrapper.thinking {
    border-color: #a855f7;
    box-shadow:
        0 0 0 10px rgba(168, 85, 247, 0.18),
        0 0 0 20px rgba(168, 85, 247, 0.08),
        0 0 55px rgba(168, 85, 247, 0.5);
}

.mic-wrapper.speaking {
    border-color: #4ade80;
    box-shadow:
        0 0 0 10px rgba(74, 222, 128, 0.18),
        0 0 0 20px rgba(74, 222, 128, 0.08),
        0 0 55px rgba(74, 222, 128, 0.5);
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

.mic {
    font-size: 46px;
    filter: drop-shadow(0 0 12px rgba(130,160,220,0.4));
}

.status {
    color: #ffffff;
    font-size: 19px;
    font-weight: 600;
    margin-top: 15px;
}

.status-description {
    color: #838e9f;
    font-size: 12.5px;
    margin-top: 5px;
    line-height: 1.4;
}

/* CONVERSATION BUBBLES */
.conversation-title {
    color: #aeb7c7;
    font-size: 14px;
    font-weight: 600;
    margin-top: 20px;
    margin-bottom: 10px;
}

.user-bubble {
    background: linear-gradient(135deg, rgba(27,40,61,0.95), rgba(20,31,48,0.95));
    border: 1px solid #2b3b54;
    padding: 12px 16px;
    border-radius: 18px 18px 4px 18px;
    margin: 8px 0 8px 12%;
    box-shadow: 0 3px 12px rgba(0,0,0,0.25);
    word-break: break-word;
}

.ai-bubble {
    background: linear-gradient(135deg, rgba(17,22,31,0.96), rgba(13,17,24,0.96));
    border: 1px solid #272f3c;
    padding: 12px 16px;
    border-radius: 18px 18px 18px 4px;
    margin: 8px 12% 8px 0;
    box-shadow: 0 3px 12px rgba(0,0,0,0.25);
    word-break: break-word;
}

.bubble-label {
    color: #707b8e;
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 0.8px;
    margin-bottom: 3px;
    display: flex;
    justify-content: space-between;
}

.bubble-message {
    color: #e9edf4;
    font-size: 14px;
    line-height: 1.5;
    white-space: pre-wrap;
}

/* QUICK PROMPT CHIPS */
.quick-prompt-title {
    color: #6d7788;
    font-size: 11.5px;
    margin-top: 12px;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    text-align: center;
}

/* FOOTER */
.footer {
    text-align: center;
    color: #4b5463;
    font-size: 11px;
    margin-top: 30px;
}

/* MOBILE SPECIFIC MEDIA QUERY */
@media (max-width: 600px) {
    .block-container {
        padding-top: 10px !important;
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
    }
    .title {
        font-size: 26px;
    }
    .logo {
        width: 60px;
        height: 60px;
        font-size: 28px;
    }
    .voice-card {
        padding: 22px 12px 18px 12px;
        border-radius: 20px;
    }
    .mic-wrapper {
        width: 105px;
        height: 105px;
    }
    .mic {
        font-size: 40px;
    }
    .status {
        font-size: 17px;
    }
    .user-bubble {
        margin: 6px 0 6px 5%;
        padding: 10px 14px;
    }
    .ai-bubble {
        margin: 6px 5% 6px 0;
        padding: 10px 14px;
    }
}
</style>
""")

# ============================================================
# SIDEBAR CONTROLS & MOBILE CONNECT
# ============================================================
with st.sidebar:
    st.markdown("### 📱 Connect on Phone")
    st.info(
        f"Connect your phone to the same Wi-Fi and open:\n\n"
        f"👉 **`{mobile_url}`**\n\n"
        "Works smoothly in Chrome, Safari, and Brave on iOS & Android!"
    )

    st.markdown("---")
    st.markdown("### ⚙️ Voice Settings")
    st.session_state.enable_tts = st.toggle(
        "🔊 Speak Responses",
        value=st.session_state.enable_tts,
        help="Plays spoken answers directly through your phone or computer speakers."
    )
    engine.set_speech_enabled(st.session_state.enable_tts)

    st.session_state.speech_rate = st.slider(
        "Voice Speed (Rate)",
        min_value=120,
        max_value=250,
        value=st.session_state.speech_rate,
        step=5
    )
    engine.set_speech_rate(st.session_state.speech_rate)

    st.markdown("---")
    st.markdown("### 🧹 Memory Management")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        engine.reset()
        st.session_state.status = "ready"
        st.success("Conversation cleared!")
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Status & Info")
    mic_status = "Available ✅" if is_microphone_available() else "Ready on Phone 📱"
    st.write(f"**Microphone:** {mic_status}")
    st.write(f"**Model:** `{os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite')}`")
    st.write(f"**Local IP:** `{local_ip}`")

# ============================================================
# HEADER
# ============================================================
st.html(f"""
<div class="header">
    <div class="logo">🤖</div>
    <div class="title">Riosa</div>
    <div class="subtitle">Interactive Voice & Text AI Assistant</div>
    <div class="online-badge">
        <span class="dot"></span>
        SYSTEM ONLINE • MOBILE & DESKTOP READY
    </div>
</div>
""")

# ============================================================
# PROCESS ENGINE EVENTS
# ============================================================
events = engine.get_events()
for event in events:
    event_type = event.get("type")

    if event_type == "status":
        st.session_state.status = event.get("value", "ready")

    elif event_type == "user":
        msg = event.get("message", "")
        if msg:
            st.session_state.messages.append({"role": "user", "content": msg})

    elif event_type == "assistant":
        msg = event.get("message", "")
        if msg:
            st.session_state.messages.append({"role": "assistant", "content": msg})

    elif event_type == "stopped":
        st.session_state.voice_running = False
        st.session_state.status = "ready"

if not engine.running:
    st.session_state.voice_running = False
    if st.session_state.status not in {"ready", "stopped"}:
        st.session_state.status = "ready"

# ============================================================
# STATUS CARD
# ============================================================
status = st.session_state.status

if status == "listening":
    mic_icon = "🎙️"
    title_text = "Listening..."
    desc_text = "Speak naturally. Riosa is listening."
    card_class = "listening"
elif status == "thinking":
    mic_icon = "🧠"
    title_text = "Thinking..."
    desc_text = "Gemini AI is processing your request."
    card_class = "thinking"
elif status == "speaking":
    mic_icon = "🔊"
    title_text = "Speaking..."
    desc_text = "Riosa is answering you."
    card_class = "speaking"
else:
    mic_icon = "🎤"
    title_text = "Ready to Talk or Type"
    desc_text = "Tap the mic, record from your phone, or type below."
    card_class = "ready"

st.html(f"""
<div class="voice-card">
    <div class="mic-wrapper {card_class}">
        <div class="mic">{mic_icon}</div>
    </div>
    <div class="status">{title_text}</div>
    <div class="status-description">{desc_text}</div>
</div>
""")

# ============================================================
# INTERACTIVE VOICE CONTROLS & PHONE MIC RECORDER
# ============================================================
tab_phone, tab_continuous = st.tabs(["📱 Phone / Browser Mic", "💻 Continuous PC Mic"])

with tab_phone:
    st.caption("Record voice directly using your phone's microphone:")
    recorded_audio = st.audio_input(
        label="Tap to record from your phone",
        key="phone_voice_recorder"
    )

    if recorded_audio is not None:
        # Check if this specific audio file was already processed
        audio_id = getattr(recorded_audio, "file_id", None) or recorded_audio.name
        if st.session_state.last_processed_audio_id != audio_id:
            st.session_state.last_processed_audio_id = audio_id
            with st.spinner("🧠 Transcribing your voice..."):
                audio_bytes = recorded_audio.read()
                transcribed = transcribe_audio_buffer(
                    audio_bytes,
                    mime_type=recorded_audio.type or "audio/wav"
                )

            if transcribed:
                st.session_state.status = "thinking"
                engine.process_text(transcribed)
                st.rerun()
            else:
                st.warning("Could not clearly transcribe the voice clip. Please try speaking again.")

with tab_continuous:
    st.caption("Hands-free continuous listening through host microphone:")
    col_c1, col_c2 = st.columns([3, 1])
    with col_c1:
        if not st.session_state.voice_running:
            if st.button("🎤 START CONTINUOUS LISTENING", use_container_width=True, type="primary"):
                st.session_state.voice_running = True
                st.session_state.status = "listening"
                engine.start()
                st.rerun()
        else:
            if st.button("🛑 STOP CONTINUOUS LISTENING", use_container_width=True):
                engine.stop()
                st.session_state.voice_running = False
                st.session_state.status = "ready"
                st.rerun()
    with col_c2:
        if st.button("🧹 Clear", use_container_width=True):
            st.session_state.messages = []
            engine.reset()
            st.session_state.status = "ready"
            st.rerun()

# ============================================================
# QUICK PROMPTS CHIPS (ONE-CLICK STARTERS)
# ============================================================
if not st.session_state.messages:
    st.html('<div class="quick-prompt-title">Quick Starter Prompts</div>')
    qc1, qc2, qc3 = st.columns(3)
    quick_choice = None
    with qc1:
        if st.button("✨ What is AI?", use_container_width=True):
            quick_choice = "What is AI and how does it work in simple words?"
    with qc2:
        if st.button("💡 Fun Fact", use_container_width=True):
            quick_choice = "Tell me an interesting fun fact about the universe."
    with qc3:
        if st.button("🐍 Why Python?", use_container_width=True):
            quick_choice = "Why is Python so popular for programming?"

    if quick_choice:
        engine.process_text(quick_choice)
        st.rerun()

# ============================================================
# CONVERSATION DISPLAY & IN-PHONE AUDIO SYNTHESIS
# ============================================================
if st.session_state.messages:
    st.html("""
    <div class="conversation-title">
        💬 Conversation History
    </div>
    """)

    for idx, item in enumerate(st.session_state.messages):
        role = item.get("role", "user")
        content_text = html.escape(str(item.get("content", "")))

        if role == "user":
            st.html(f"""
            <div class="user-bubble">
                <div class="bubble-label">YOU</div>
                <div class="bubble-message">{content_text}</div>
            </div>
            """)
        else:
            st.html(f"""
            <div class="ai-bubble">
                <div class="bubble-label">RIOSA</div>
                <div class="bubble-message">{content_text}</div>
            </div>
            """)

    # In-Browser Web Speech synthesis on Phone / Mobile Browser
    # Speaks the latest assistant response through the phone speaker
    last_idx = len(st.session_state.messages) - 1
    last_msg = st.session_state.messages[-1]
    if (
        st.session_state.enable_tts
        and last_msg.get("role") == "assistant"
        and st.session_state.last_spoken_id != last_idx
    ):
        st.session_state.last_spoken_id = last_idx
        safe_speech_text = json.dumps(str(last_msg.get("content", "")))
        st.html(f"""
        <script>
        (function() {{
            if ('speechSynthesis' in window) {{
                try {{
                    window.speechSynthesis.cancel();
                    var text = {safe_speech_text};
                    var utterance = new SpeechSynthesisUtterance(text);
                    utterance.rate = 1.0;
                    window.speechSynthesis.speak(utterance);
                }} catch (e) {{
                    console.log('Browser speech synthesis error:', e);
                }}
            }}
        }})();
        </script>
        """)

# ============================================================
# INTERACTIVE CHAT INPUT (PHONE & DESKTOP KEYBOARD)
# ============================================================
chat_input = st.chat_input("Type a message or question to Riosa...")
if chat_input:
    engine.process_text(chat_input)
    st.rerun()

# ============================================================
# AUTO REFRESH WHILE CONTINUOUS VOICE IS ACTIVE
# ============================================================
if st.session_state.voice_running:
    time.sleep(0.5)
    st.rerun()

st.html(f"""
<div class="footer">
    📱 Open on phone: <strong style="color: #60a5fa;">{mobile_url}</strong> • Powered by Google Gemini & Python
</div>
""")

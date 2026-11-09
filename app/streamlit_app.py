import streamlit as st
import html
import time
import os

from voice_engine import RiosaVoiceEngine
from speech_to_text import is_microphone_available

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Riosa - Voice & Interactive AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

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

engine = st.session_state.voice_engine
engine.set_speech_enabled(st.session_state.enable_tts)
engine.set_speech_rate(st.session_state.speech_rate)

# ============================================================
# FUTURISTIC CYBERPUNK STYLING
# ============================================================
st.html("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background:
        radial-gradient(
            circle at 50% 10%,
            rgba(55, 80, 150, 0.28),
            transparent 32%
        ),
        radial-gradient(
            circle at 10% 85%,
            rgba(90, 40, 150, 0.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 75%,
            rgba(20, 90, 150, 0.18),
            transparent 30%
        ),
        #080a0f !important;
    min-height: 100vh;
}

[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(255,255,255,0.018) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.018) 1px, transparent 1px);
    background-size: 55px 55px;
    pointer-events: none;
    z-index: 0;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

footer {
    display: none !important;
}

.block-container {
    max-width: 860px !important;
    padding-top: 20px !important;
    padding-bottom: 70px !important;
    position: relative;
    z-index: 1;
}

/* HEADER */
.header {
    text-align: center;
    margin-bottom: 24px;
}

.logo {
    width: 74px;
    height: 74px;
    margin: auto;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle, #29364e, #151b27);
    border: 1px solid #3d4f6b;
    font-size: 36px;
    box-shadow: 0 0 35px rgba(80,110,190,0.30);
    animation: float 4s ease-in-out infinite alternate;
}

@keyframes float {
    from { transform: translateY(0px); }
    to { transform: translateY(-6px); }
}

.title {
    color: #ffffff;
    font-size: 34px;
    font-weight: 700;
    margin-top: 10px;
    letter-spacing: 1px;
}

.subtitle {
    color: #8b97ac;
    font-size: 14px;
    margin-top: 4px;
}

.online-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-top: 12px;
    padding: 6px 14px;
    border-radius: 20px;
    background: rgba(15,20,29,0.85);
    border: 1px solid #293242;
    color: #a0abbd;
    font-size: 11px;
    letter-spacing: 0.5px;
}

.dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #4ade80;
    box-shadow: 0 0 10px rgba(74,222,128,0.8);
    display: inline-block;
}

/* VOICE CARD */
.voice-card {
    background: linear-gradient(145deg, rgba(18,23,33,0.96), rgba(10,14,21,0.96));
    border: 1px solid rgba(75,87,108,0.45);
    border-radius: 30px;
    padding: 36px 20px 30px 20px;
    text-align: center;
    box-shadow: 0 25px 80px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.03);
    margin-bottom: 20px;
}

.mic-wrapper {
    width: 140px;
    height: 140px;
    margin: auto;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle, #34425c 0%, #202a3b 38%, #121824 68%, #0d1119 100%);
    border: 1px solid #46546b;
    box-shadow:
        0 0 0 10px rgba(80,100,140,0.04),
        0 0 0 20px rgba(80,100,140,0.02),
        0 0 50px rgba(80,110,190,0.25);
    transition: all 0.3s ease;
}

.mic-wrapper.listening {
    border-color: #38bdf8;
    box-shadow:
        0 0 0 12px rgba(56, 189, 248, 0.15),
        0 0 0 24px rgba(56, 189, 248, 0.08),
        0 0 70px rgba(56, 189, 248, 0.45);
    animation: pulse 1.5s infinite;
}

.mic-wrapper.thinking {
    border-color: #a855f7;
    box-shadow:
        0 0 0 12px rgba(168, 85, 247, 0.15),
        0 0 0 24px rgba(168, 85, 247, 0.08),
        0 0 70px rgba(168, 85, 247, 0.45);
}

.mic-wrapper.speaking {
    border-color: #4ade80;
    box-shadow:
        0 0 0 12px rgba(74, 222, 128, 0.15),
        0 0 0 24px rgba(74, 222, 128, 0.08),
        0 0 70px rgba(74, 222, 128, 0.45);
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.04); }
    100% { transform: scale(1); }
}

.mic {
    font-size: 54px;
    filter: drop-shadow(0 0 14px rgba(130,160,220,0.4));
}

.status {
    color: #ffffff;
    font-size: 21px;
    font-weight: 600;
    margin-top: 18px;
}

.status-description {
    color: #838e9f;
    font-size: 13px;
    margin-top: 6px;
}

/* CONVERSATION BUBBLES */
.conversation-title {
    color: #aeb7c7;
    font-size: 15px;
    font-weight: 600;
    margin-top: 25px;
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.user-bubble {
    background: linear-gradient(135deg, rgba(27,40,61,0.95), rgba(20,31,48,0.95));
    border: 1px solid #2b3b54;
    padding: 14px 18px;
    border-radius: 18px 18px 4px 18px;
    margin: 8px 0 8px 15%;
    box-shadow: 0 4px 15px rgba(0,0,0,0.25);
}

.ai-bubble {
    background: linear-gradient(135deg, rgba(17,22,31,0.96), rgba(13,17,24,0.96));
    border: 1px solid #272f3c;
    padding: 14px 18px;
    border-radius: 18px 18px 18px 4px;
    margin: 8px 15% 8px 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.25);
}

.bubble-label {
    color: #707b8e;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    margin-bottom: 4px;
}

.bubble-message {
    color: #e9edf4;
    font-size: 14.5px;
    line-height: 1.55;
    white-space: pre-wrap;
}

/* QUICK PROMPTS */
.quick-prompt-title {
    color: #6d7788;
    font-size: 12px;
    margin-top: 14px;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    text-align: center;
}

/* FOOTER */
.footer {
    text-align: center;
    color: #4b5463;
    font-size: 11.5px;
    margin-top: 35px;
}
</style>
""")

# ============================================================
# SIDEBAR CONTROLS
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Riosa Assistant Controls")
    st.session_state.enable_tts = st.toggle(
        "🔊 Voice Responses (Spoken)",
        value=st.session_state.enable_tts,
        help="When enabled, Riosa speaks answers aloud using text-to-speech."
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
        st.success("Conversation history cleared!")
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 System Diagnostics")
    mic_status = "Available ✅" if is_microphone_available() else "Not Found ⚠️"
    st.write(f"**Microphone:** {mic_status}")
    st.write(f"**Model:** `{os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite')}`")
    st.write(f"**Engine State:** `{st.session_state.status.title()}`")

# ============================================================
# HEADER
# ============================================================
st.html("""
<div class="header">
    <div class="logo">🤖</div>
    <div class="title">Riosa</div>
    <div class="subtitle">Interactive Voice & Text AI Assistant</div>
    <div class="online-badge">
        <span class="dot"></span>
        SYSTEM ONLINE & READY
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
    desc_text = "Speak naturally. Riosa is listening to your microphone."
    card_class = "listening"
elif status == "thinking":
    mic_icon = "🧠"
    title_text = "Thinking..."
    desc_text = "Google Gemini is processing your query."
    card_class = "thinking"
elif status == "speaking":
    mic_icon = "🔊"
    title_text = "Speaking..."
    desc_text = "Riosa is speaking the answer."
    card_class = "speaking"
else:
    mic_icon = "🎤"
    title_text = "Ready to Talk or Type"
    desc_text = "Tap the button to start voice mode, or type your message below."
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
# CONTROL BUTTON (VOICE MODE TOGGLE)
# ============================================================
col_btn1, col_btn2 = st.columns([3, 1])

with col_btn1:
    if not st.session_state.voice_running:
        if st.button("🎤   START VOICE CONVERSATION", use_container_width=True, type="primary"):
            st.session_state.voice_running = True
            st.session_state.status = "listening"
            engine.start()
            st.rerun()
    else:
        if st.button("🛑   STOP VOICE CONVERSATION", use_container_width=True):
            engine.stop()
            st.session_state.voice_running = False
            st.session_state.status = "ready"
            st.rerun()

with col_btn2:
    if st.button("🧹 Clear", use_container_width=True, help="Clear chat"):
        st.session_state.messages = []
        engine.reset()
        st.session_state.status = "ready"
        st.rerun()

# ============================================================
# QUICK PROMPTS CHIPS
# ============================================================
if not st.session_state.messages:
    st.html('<div class="quick-prompt-title">Quick Suggestion Prompts</div>')
    qc1, qc2, qc3 = st.columns(3)
    quick_choice = None
    with qc1:
        if st.button("✨ What is AI?", use_container_width=True):
            quick_choice = "What is AI and how does it work in simple words?"
    with qc2:
        if st.button("💡 Tell me a fun fact", use_container_width=True):
            quick_choice = "Tell me an interesting fun fact about the universe."
    with qc3:
        if st.button("🐍 Why use Python?", use_container_width=True):
            quick_choice = "Why is Python so popular for programming?"

    if quick_choice:
        engine.process_text(quick_choice)
        st.rerun()

# ============================================================
# CONVERSATION DISPLAY
# ============================================================
if st.session_state.messages:
    st.html("""
    <div class="conversation-title">
        <span>💬 Conversation History</span>
    </div>
    """)

    for item in st.session_state.messages:
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

# ============================================================
# INTERACTIVE CHAT INPUT (TYPE DIRECTLY)
# ============================================================
chat_input = st.chat_input("Type a message to Riosa...")
if chat_input:
    # Synchronously process the typed query
    engine.process_text(chat_input)
    st.rerun()

# ============================================================
# AUTO REFRESH WHILE VOICE IS RUNNING
# ============================================================
if st.session_state.voice_running:
    time.sleep(0.5)
    st.rerun()

st.html("""
<div class="footer">
    Riosa Voice AI Assistant • Powered by Google Gemini & Python • Full Interactive Mode
</div>
""")

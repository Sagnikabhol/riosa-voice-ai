import streamlit as st
import html
import json
import time
import socket
import os

from llm import ask_llm, clear_history
from speech_to_text import is_microphone_available, transcribe_audio_buffer
from text_to_speech import speak

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Riosa - Interactive AI Assistant",
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

if "enable_tts" not in st.session_state:
    st.session_state.enable_tts = True

if "speech_rate" not in st.session_state:
    st.session_state.speech_rate = 1.0

if "latest_speech_text" not in st.session_state:
    st.session_state.latest_speech_text = None

if "last_processed_audio_id" not in st.session_state:
    st.session_state.last_processed_audio_id = None

# ============================================================
# MODERN INTERACTIVE CYBERPUNK STYLING
# ============================================================
st.html("""
<style>
/* Global background */
html, body, [data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 50% 8%, rgba(55, 80, 160, 0.32), transparent 36%),
        radial-gradient(circle at 10% 85%, rgba(90, 40, 160, 0.20), transparent 32%),
        radial-gradient(circle at 90% 75%, rgba(20, 90, 160, 0.20), transparent 32%),
        #080a0f !important;
    min-height: 100vh;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    -webkit-font-smoothing: antialiased;
}

[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(255,255,255,0.018) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.018) 1px, transparent 1px);
    background-size: 36px 36px;
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
    padding-bottom: 70px !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    position: relative;
    z-index: 1;
}

/* HEADER */
.header-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    margin-bottom: 20px;
}

.logo-orb {
    width: 72px;
    height: 72px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle, #2d3b56, #141b27);
    border: 1px solid #4a5c7d;
    font-size: 34px;
    box-shadow: 0 0 35px rgba(80,120,220,0.4);
    animation: floatOrb 3.5s ease-in-out infinite alternate;
}

@keyframes floatOrb {
    from { transform: translateY(0px) scale(1); }
    to { transform: translateY(-5px) scale(1.03); }
}

.main-title {
    color: #ffffff;
    font-size: 30px;
    font-weight: 700;
    margin-top: 10px;
    letter-spacing: 0.5px;
}

.sub-title {
    color: #8b99b0;
    font-size: 13.5px;
    margin-top: 3px;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    margin-top: 8px;
    padding: 5px 13px;
    border-radius: 20px;
    background: rgba(18,25,38,0.85);
    border: 1px solid #2d384c;
    color: #9cb0ce;
    font-size: 11px;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #34d399;
    box-shadow: 0 0 8px rgba(52,211,153,0.9);
    display: inline-block;
}

/* CHAT MESSAGES */
.chat-container {
    margin-top: 15px;
    margin-bottom: 15px;
}

.user-bubble {
    background: linear-gradient(135deg, rgba(29, 44, 69, 0.95), rgba(20, 31, 50, 0.95));
    border: 1px solid #334665;
    padding: 13px 17px;
    border-radius: 18px 18px 4px 18px;
    margin: 10px 0 10px 12%;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    word-break: break-word;
}

.ai-bubble {
    background: linear-gradient(135deg, rgba(18, 24, 34, 0.96), rgba(12, 17, 25, 0.96));
    border: 1px solid #283344;
    padding: 13px 17px;
    border-radius: 18px 18px 18px 4px;
    margin: 10px 12% 10px 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    word-break: break-word;
}

.bubble-meta {
    color: #6d7b93;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
    margin-bottom: 5px;
    display: flex;
    justify-content: space-between;
}

.bubble-text {
    color: #e9edf4;
    font-size: 14.5px;
    line-height: 1.55;
    white-space: pre-wrap;
}

/* FOOTER */
.footer-text {
    text-align: center;
    color: #4f5a6d;
    font-size: 11px;
    margin-top: 35px;
}

/* MOBILE RESPONSIVE ADJUSTMENTS */
@media (max-width: 600px) {
    .block-container {
        padding-top: 10px !important;
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
    }
    .main-title {
        font-size: 25px;
    }
    .logo-orb {
        width: 60px;
        height: 60px;
        font-size: 28px;
    }
    .user-bubble {
        margin: 8px 0 8px 4%;
        padding: 11px 14px;
    }
    .ai-bubble {
        margin: 8px 4% 8px 0;
        padding: 11px 14px;
    }
}
</style>
""")

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### 📱 Connect on Phone")
    st.info(
        f"Connect your phone to the same Wi-Fi network and open:\n\n"
        f"👉 **`{mobile_url}`**\n\n"
        "Works smoothly in Chrome, Safari, and Brave!"
    )

    st.markdown("---")
    st.markdown("### 🔊 Spoken Audio")
    st.session_state.enable_tts = st.toggle(
        "Voice Responses (Spoken)",
        value=st.session_state.enable_tts,
        help="Reads answers aloud using speech synthesis."
    )

    st.session_state.speech_rate = st.slider(
        "Voice Speed (Rate)",
        min_value=0.7,
        max_value=1.5,
        value=st.session_state.speech_rate,
        step=0.1
    )

    st.markdown("---")
    st.markdown("### 🧹 Conversation")
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        clear_history()
        st.success("Conversation reset!")
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 System Status")
    st.write(f"**Gemini Model:** `{os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite')}`")
    mic_status = "Available ✅" if is_microphone_available() else "Ready on Phone 📱"
    st.write(f"**Microphone:** {mic_status}")
    st.write(f"**Local IP:** `{local_ip}`")

# ============================================================
# HEADER
# ============================================================
st.html(f"""
<div class="header-container">
    <div class="logo-orb">🤖</div>
    <div class="main-title">Riosa</div>
    <div class="sub-title">Interactive Voice & Text AI Assistant</div>
    <div class="status-badge">
        <span class="status-dot"></span>
        ONLINE • READY TO TALK OR TYPE
    </div>
</div>
""")

# ============================================================
# VOICE RECORDER (PHONE & BROWSER MIC)
# ============================================================
with st.expander("🎙️ Tap to Record Voice (Phone or PC Microphone)", expanded=True):
    recorded_audio = st.audio_input(
        label="Press the record button below to speak:",
        key="voice_recorder_widget"
    )

    if recorded_audio is not None:
        audio_id = getattr(recorded_audio, "file_id", None) or recorded_audio.name
        if st.session_state.last_processed_audio_id != audio_id:
            st.session_state.last_processed_audio_id = audio_id
            with st.spinner("🧠 Transcribing voice recording..."):
                audio_bytes = recorded_audio.read()
                transcribed_text = transcribe_audio_buffer(
                    audio_bytes,
                    mime_type=recorded_audio.type or "audio/wav"
                )

            if transcribed_text:
                # Add user message
                st.session_state.messages.append({"role": "user", "content": transcribed_text})

                # Query Gemini directly
                with st.spinner("🤖 Riosa is thinking..."):
                    answer = ask_llm(transcribed_text)

                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.session_state.latest_speech_text = answer

                # Optional background server TTS
                if st.session_state.enable_tts:
                    speak(answer, async_mode=True)

                st.rerun()
            else:
                st.warning("Could not clearly detect speech in the audio. Please try speaking again.")

# ============================================================
# CONVERSATION DISPLAY
# ============================================================
if st.session_state.messages:
    col_t1, col_t2 = st.columns([4, 1])
    with col_t1:
        st.caption("💬 Conversation")
    with col_t2:
        if st.button("🧹 Clear", use_container_width=True, help="Reset conversation"):
            st.session_state.messages = []
            clear_history()
            st.rerun()

    for idx, item in enumerate(st.session_state.messages):
        role = item.get("role", "user")
        content_text = html.escape(str(item.get("content", "")))

        if role == "user":
            st.html(f"""
            <div class="user-bubble">
                <div class="bubble-meta"><span>YOU</span></div>
                <div class="bubble-text">{content_text}</div>
            </div>
            """)
        else:
            st.html(f"""
            <div class="ai-bubble">
                <div class="bubble-meta"><span>RIOSA</span></div>
                <div class="bubble-text">{content_text}</div>
            </div>
            """)

# In-Browser Web Speech synthesis for Phone & Computer speakers
if st.session_state.enable_tts and st.session_state.latest_speech_text:
    speech_payload = json.dumps(str(st.session_state.latest_speech_text))
    rate_val = float(st.session_state.speech_rate)
    st.session_state.latest_speech_text = None
    st.html(f"""
    <script>
    (function() {{
        if ('speechSynthesis' in window) {{
            try {{
                window.speechSynthesis.cancel();
                var msg = new SpeechSynthesisUtterance({speech_payload});
                msg.rate = {rate_val};
                window.speechSynthesis.speak(msg);
            }} catch (err) {{
                console.error('Speech synthesis error:', err);
            }}
        }}
    }})();
    </script>
    """)

# ============================================================
# INTERACTIVE CHAT INPUT (TYPE PROMPT DIRECTLY)
# ============================================================
user_prompt = st.chat_input("Type your question or message to Riosa...")
if user_prompt and user_prompt.strip():
    clean_prompt = user_prompt.strip()

    # Add user message
    st.session_state.messages.append({"role": "user", "content": clean_prompt})

    # Direct Gemini Call with spinner
    with st.spinner("🤖 Riosa is thinking..."):
        response = ask_llm(clean_prompt)

    # Add assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state.latest_speech_text = response

    # Optional background server TTS
    if st.session_state.enable_tts:
        speak(response, async_mode=True)

    st.rerun()

st.html(f"""
<div class="footer-text">
    📱 Open on phone: <strong style="color: #60a5fa;">{mobile_url}</strong> • Riosa Voice AI Assistant
</div>
""")

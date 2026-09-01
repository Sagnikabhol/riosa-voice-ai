import streamlit as st
import html
import time

from voice_engine import RiosaVoiceEngine


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Riosa - Voice AI Assistant",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_engine" not in st.session_state:
    st.session_state.voice_engine = RiosaVoiceEngine()

if "voice_running" not in st.session_state:
    st.session_state.voice_running = False

if "status" not in st.session_state:
    st.session_state.status = "ready"


engine = st.session_state.voice_engine


# ============================================================
# FUTURISTIC UI
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
        linear-gradient(
            rgba(255,255,255,0.018) 1px,
            transparent 1px
        ),
        linear-gradient(
            90deg,
            rgba(255,255,255,0.018) 1px,
            transparent 1px
        );

    background-size: 55px 55px;

    pointer-events: none;

    z-index: 0;
}


[data-testid="stHeader"] {
    display: none !important;
}


[data-testid="stToolbar"] {
    display: none !important;
}


footer {
    display: none !important;
}


#MainMenu {
    visibility: hidden;
}


.block-container {

    max-width: 850px !important;

    padding-top: 25px !important;

    padding-bottom: 50px !important;

    position: relative;

    z-index: 1;
}


/* ============================================================
   HEADER
   ============================================================ */

.header {

    text-align: center;

    margin-bottom: 28px;
}


.logo {

    width: 70px;
    height: 70px;

    margin: auto;

    border-radius: 50%;

    display: flex;

    align-items: center;
    justify-content: center;

    background:
        radial-gradient(
            circle,
            #29364e,
            #151b27
        );

    border: 1px solid #39475c;

    font-size: 34px;

    box-shadow:
        0 0 35px rgba(80,110,190,0.20);
}


.title {

    color: #ffffff;

    font-size: 34px;

    font-weight: 700;

    margin-top: 10px;

    letter-spacing: 1px;
}


.subtitle {

    color: #778194;

    font-size: 14px;

    margin-top: 4px;
}


.online {

    display: inline-flex;

    align-items: center;

    gap: 7px;

    margin-top: 12px;

    padding: 6px 13px;

    border-radius: 20px;

    background: rgba(15,20,29,0.8);

    border: 1px solid #293242;

    color: #929bad;

    font-size: 11px;
}


.dot {

    width: 7px;
    height: 7px;

    border-radius: 50%;

    background: #4ade80;

    box-shadow:
        0 0 10px rgba(74,222,128,0.7);
}


/* ============================================================
   VOICE CARD
   ============================================================ */

.voice-card {

    background:
        linear-gradient(
            145deg,
            rgba(18,23,33,0.96),
            rgba(10,14,21,0.96)
        );

    border: 1px solid rgba(75,87,108,0.45);

    border-radius: 34px;

    padding: 48px 25px 40px 25px;

    text-align: center;

    box-shadow:
        0 25px 80px rgba(0,0,0,0.35),
        inset 0 1px 0 rgba(255,255,255,0.025);
}


.mic-wrapper {

    width: 170px;
    height: 170px;

    margin: auto;

    border-radius: 50%;

    display: flex;

    align-items: center;
    justify-content: center;

    background:
        radial-gradient(
            circle,
            #34425c 0%,
            #202a3b 38%,
            #121824 68%,
            #0d1119 100%
        );

    border: 1px solid #46546b;

    box-shadow:
        0 0 0 12px rgba(80,100,140,0.035),
        0 0 0 25px rgba(80,100,140,0.02),
        0 0 60px rgba(80,110,190,0.20);
}


.mic {

    font-size: 62px;

    filter:
        drop-shadow(
            0 0 12px rgba(130,160,220,0.35)
        );
}


.status {

    color: #ffffff;

    font-size: 23px;

    font-weight: 600;

    margin-top: 23px;
}


.status-description {

    color: #788294;

    font-size: 13px;

    margin-top: 7px;
}


/* ============================================================
   BUTTON
   ============================================================ */

div.stButton > button {

    width: 100%;

    height: 64px;

    margin-top: 25px;

    border-radius: 20px;

    border: 1px solid #46546b;

    background:
        linear-gradient(
            135deg,
            #1b2535,
            #151c29
        );

    color: #ffffff;

    font-size: 18px;

    font-weight: 700;

    letter-spacing: 0.5px;

    box-shadow:
        0 10px 30px rgba(0,0,0,0.25);

    transition: all 0.2s ease;
}


div.stButton > button:hover {

    background:
        linear-gradient(
            135deg,
            #26344b,
            #1b2535
        );

    border-color: #667791;

    box-shadow:
        0 10px 35px rgba(70,100,170,0.18);

    transform: translateY(-2px);
}


/* ============================================================
   CONVERSATION
   ============================================================ */

.conversation-title {

    color: #aeb7c7;

    font-size: 15px;

    font-weight: 600;

    margin-top: 35px;

    margin-bottom: 14px;
}


.user-bubble {

    background:
        linear-gradient(
            135deg,
            rgba(27,40,61,0.95),
            rgba(20,31,48,0.95)
        );

    border: 1px solid #2b3b54;

    padding: 15px 18px;

    border-radius:
        20px 20px 5px 20px;

    margin:
        10px 0 10px 18%;
}


.ai-bubble {

    background:
        linear-gradient(
            135deg,
            rgba(17,22,31,0.96),
            rgba(13,17,24,0.96)
        );

    border: 1px solid #272f3c;

    padding: 15px 18px;

    border-radius:
        20px 20px 20px 5px;

    margin:
        10px 18% 10px 0;
}


.label {

    color: #707b8e;

    font-size: 10px;

    font-weight: 700;

    letter-spacing: 1px;

    margin-bottom: 6px;
}


.message {

    color: #e9edf4;

    font-size: 15px;

    line-height: 1.55;
}


.hint {

    text-align: center;

    color: #545e70;

    font-size: 12px;

    margin-top: 18px;
}


.footer {

    text-align: center;

    color: #414957;

    font-size: 11px;

    margin-top: 35px;
}

</style>
""")


# ============================================================
# HEADER
# ============================================================

st.html("""
<div class="header">

    <div class="logo">
        🤖
    </div>

    <div class="title">
        Riosa
    </div>

    <div class="subtitle">
        Your Personal Voice AI Assistant
    </div>

    <div class="online">
        <span class="dot"></span>
        SYSTEM ONLINE
    </div>

</div>
""")


# ============================================================
# READ ENGINE EVENTS
# ============================================================

events = engine.get_events()

for event in events:

    event_type = event.get("type")


    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if event_type == "status":

        st.session_state.status = (
            event.get("value", "ready")
        )


    # --------------------------------------------------------
    # USER MESSAGE
    # --------------------------------------------------------

    elif event_type == "user":

        message = event.get("message", "")

        if message:

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": message
                }
            )


    # --------------------------------------------------------
    # ASSISTANT MESSAGE
    # --------------------------------------------------------

    elif event_type == "assistant":

        message = event.get("message", "")

        if message:

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": message
                }
            )


    # --------------------------------------------------------
    # STOPPED
    # --------------------------------------------------------

    elif event_type == "stopped":

        st.session_state.voice_running = False

        st.session_state.status = "ready"


# ============================================================
# ENGINE STATUS
# ============================================================

if not engine.running:

    st.session_state.voice_running = False

    if st.session_state.status not in {
        "ready",
        "stopped"
    }:

        st.session_state.status = "ready"


# ============================================================
# STATUS DISPLAY
# ============================================================

status = st.session_state.status


if status == "listening":

    mic = "🎙️"

    title = "Listening..."

    description = (
        "Speak naturally. I'm listening."
    )


elif status == "thinking":

    mic = "🧠"

    title = "Thinking..."

    description = (
        "Riosa is preparing your answer."
    )


elif status == "speaking":

    mic = "🔊"

    title = "Speaking..."

    description = (
        "Riosa is answering you."
    )


else:

    mic = "🎤"

    title = "Ready to talk"

    description = (
        'Tap once to start. Say "exit" to finish.'
    )


# ============================================================
# VOICE CARD
# ============================================================

st.html(f"""
<div class="voice-card">

    <div class="mic-wrapper">

        <div class="mic">
            {mic}
        </div>

    </div>

    <div class="status">
        {title}
    </div>

    <div class="status-description">
        {description}
    </div>

</div>
""")


# ============================================================
# CONTROL BUTTON
# ============================================================

if not st.session_state.voice_running:

    if st.button(
        "🎤   TAP TO TALK",
        use_container_width=True
    ):

        st.session_state.voice_running = True

        st.session_state.status = "listening"

        engine.start()

        st.rerun()

else:

    if st.button(
        "🛑   END CONVERSATION",
        use_container_width=True
    ):

        engine.stop()

        st.session_state.voice_running = False

        st.session_state.status = "ready"

        st.rerun()


# ============================================================
# AUTO REFRESH WHILE VOICE ENGINE IS ACTIVE
# ============================================================

if st.session_state.voice_running:

    time.sleep(0.5)

    st.rerun()


# ============================================================
# CONVERSATION
# ============================================================

if st.session_state.messages:

    st.html("""
    <div class="conversation-title">
        💬 Conversation
    </div>
    """)


    for item in st.session_state.messages:

        text = html.escape(
            str(item["content"])
        )


        if item["role"] == "user":

            st.html(f"""
            <div class="user-bubble">

                <div class="label">
                    YOU
                </div>

                <div class="message">
                    {text}
                </div>

            </div>
            """)


        else:

            st.html(f"""
            <div class="ai-bubble">

                <div class="label">
                    RIOSA
                </div>

                <div class="message">
                    {text}
                </div>

            </div>
            """)


# ============================================================
# HINT
# ============================================================

st.html("""
<div class="hint">

    🎤 Tap once to start
    &nbsp; • &nbsp;
    Keep talking naturally
    &nbsp; • &nbsp;
    Say "exit" to finish

</div>

<div class="footer">

    Riosa • Python • Gemini • Speech Recognition • Streamlit

</div>
""")
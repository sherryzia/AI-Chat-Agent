import streamlit as st
import time
import os
import threading
import pickle
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_d1dc9bfa2e9314960d67672ce2ba2cbae3a469479e1ec06e")
AGENT_ID = os.getenv("AGENT_ID", "agent_01jzv0hz3ae9nssega9g28td90")

st.set_page_config(
    page_title="AI Voice Assistant",
    page_icon="🎙️",
    layout="centered"
)

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'conversation_active' not in st.session_state:
    st.session_state.conversation_active = False
if 'show_chat' not in st.session_state:
    st.session_state.show_chat = False

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #1f4037, #99f2c8);
    }

    .main-container {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem auto;
        max-width: 750px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
        font-family: 'Segoe UI', sans-serif;
    }

    .title {
        font-size: 2.8rem;
        color: #1f4037;
        margin-bottom: 0.5rem;
        font-weight: bold;
    }

    .subtitle {
        color: #555;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

message_file = "messages.pkl"
current_conversation = None

def save_messages_to_file(messages):
    try:
        with open(message_file, 'wb') as f:
            pickle.dump(messages, f)
    except:
        pass

def load_messages_from_file():
    try:
        with open(message_file, 'rb') as f:
            return pickle.load(f)
    except:
        return []

def add_message(msg_type, text):
    timestamp = time.strftime("%H:%M:%S")
    message = {'type': msg_type, 'text': text, 'timestamp': timestamp}
    messages = load_messages_from_file()
    messages.append(message)
    save_messages_to_file(messages)
    return message

def user_spoke(transcript):
    add_message('user', transcript)

def agent_responded(response):
    add_message('agent', response)

def start_conversation_thread():
    global current_conversation
    try:
        add_message('system', "🎙️ Conversation started - Listening...")
        client = ElevenLabs(api_key=API_KEY)
        current_conversation = Conversation(
            client,
            AGENT_ID,
            requires_auth=True,
            audio_interface=DefaultAudioInterface(),
            callback_user_transcript=user_spoke,
            callback_agent_response=agent_responded
        )
        current_conversation.start_session()
        conv_id = current_conversation.wait_for_session_end()
        add_message('system', f"🛑 Conversation ended: {conv_id}")
    except Exception as e:
        add_message('system', f"❌ Error: {str(e)}")
    finally:
        current_conversation = None

def stop_conversation():
    global current_conversation
    if current_conversation:
        try:
            current_conversation.end_session()
            add_message('system', "⏹️ Conversation stopped")
        except:
            pass
        current_conversation = None

st.markdown('<div class="main-container">', unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center;">
    <div class="title">🎙️ AI Voice Assistant</div>
    <div class="subtitle">Talk to your personal AI — real-time, responsive, and human-like.</div>
</div>
""", unsafe_allow_html=True)

if st.session_state.conversation_active:
    st.success("🟢 Listening — Speak into your microphone.")
else:
    st.info("🔴 Click 'Start Conversation' to begin.")

if st.session_state.conversation_active:
    if st.button("⏹️ Stop Conversation", use_container_width=True):
        st.session_state.conversation_active = False
        st.session_state.show_chat = True
        stop_conversation()
        st.rerun()
else:
    if st.button("🎙️ Start Conversation", use_container_width=True):
        st.session_state.conversation_active = True
        st.session_state.show_chat = True
        save_messages_to_file([])
        st.session_state.conversation_history = []
        thread = threading.Thread(target=start_conversation_thread, daemon=True)
        thread.start()
        st.rerun()

file_messages = load_messages_from_file()
if len(file_messages) != len(st.session_state.conversation_history):
    st.session_state.conversation_history = file_messages

if st.session_state.show_chat:
    if st.session_state.conversation_history:
        st.markdown("### 💬 Conversation History")
        for msg in st.session_state.conversation_history:
            if msg['type'] == 'user':
                st.markdown(f"""
                <div style="text-align: right; margin: 10px 0;">
                    <div style="display: inline-block; background: #1f78ff; color: white; padding: 10px 15px; border-radius: 20px 20px 5px 20px; max-width: 75%; box-shadow: 0 3px 8px rgba(0,0,0,0.2);">
                        👤 {msg['text']}<br><small style='opacity: 0.7;'>{msg['timestamp']}</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif msg['type'] == 'agent':
                st.markdown(f"""
                <div style="text-align: left; margin: 10px 0;">
                    <div style="display: inline-block; background: #28a745; color: white; padding: 10px 15px; border-radius: 20px 20px 20px 5px; max-width: 75%; box-shadow: 0 3px 8px rgba(0,0,0,0.2);">
                        🤖 {msg['text']}<br><small style='opacity: 0.7;'>{msg['timestamp']}</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif msg['type'] == 'system':
                st.markdown(f"""
                <div style="text-align: center; margin: 10px 0; color: #555; font-style: italic;">
                    📋 {msg['text']} <small>({msg['timestamp']})</small>
                </div>
                """, unsafe_allow_html=True)
        if st.button("🗑️ Clear Chat History"):
            st.session_state.conversation_history = []
            save_messages_to_file([])
            st.rerun()
    else:
        st.warning("No messages yet. Speak to start chatting with your AI assistant!")
else:
    st.markdown("""
    ### 👋 Welcome
    Get started by clicking the **Start Conversation** button above.

    **What you can do:**
    - Ask questions
    - Get help or summaries
    - Chat with realistic voice

    Make sure your **microphone** is allowed in the browser!
    """)

st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.conversation_active:
    time.sleep(1.5)
    st.rerun()

st.markdown("""
<div style="text-align: center; margin-top: 2rem; color: rgba(255,255,255,0.85); font-size: 0.85rem;">
    Built with ❤️ using Streamlit & ElevenLabs
</div>
""", unsafe_allow_html=True)

import streamlit as st
import uuid
from datetime import datetime
from main import (
    speak_response,
    get_microphone_list,
    listen_for_speech,
    find_preferred_microphone,
    get_therapy_response,
    create_user_profile,
    create_session_id,
    test_api_keys,
    initialize_elevenlabs
)
from langchain.schema import HumanMessage, AIMessage

st.set_page_config(
    page_title="AI Therapy Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp {
    background-color: #1e1e1e;
    color: #ffffff;
}

.main-header {
    text-align: center;
    padding: 1.5rem 0;
    background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
    color: #ffffff;
    border-radius: 12px;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.chat-message {
    padding: 1rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    max-width: 75%;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.user-message {
    background-color: #2d5a87;
    margin-left: 25%;
    border-left: 4px solid #4299e1;
    color: #ffffff;
}

.assistant-message {
    background-color: #553c4e;
    margin-right: 25%;
    border-left: 4px solid #9f7aea;
    color: #ffffff;
}

.session-info {
    background-color: #2d3748;
    color: #ffffff;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    border: 1px solid #4a5568;
}

.voice-controls {
    background-color: #2d3748;
    color: #ffffff;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    border-left: 4px solid #ed8936;
}

.api-setup {
    background-color: #2d3748;
    color: #ffffff;
    padding: 1.5rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    border-left: 4px solid #48bb78;
}

.listening-indicator {
    background-color: #1a202c;
    color: #63b3ed;
    padding: 0.8rem;
    border-radius: 8px;
    text-align: center;
    font-weight: bold;
    border: 2px solid #63b3ed;
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0% { 
        opacity: 1; 
        border-color: #63b3ed;
    }
    50% { 
        opacity: 0.7; 
        border-color: #90cdf4;
    }
    100% { 
        opacity: 1; 
        border-color: #63b3ed;
    }
}

.stButton > button {
    background-color: #4a5568;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    font-weight: 500;
}

.stButton > button:hover {
    background-color: #2d3748;
    color: #ffffff;
}

.stTextInput > div > div > input {
    background-color: #2d3748;
    color: #ffffff;
    border: 1px solid #4a5568;
    border-radius: 8px;
}

.stSelectbox > div > div > div {
    background-color: #2d3748;
    color: #ffffff;
}

.css-1d391kg {
    background-color: #1a202c;
}

.css-1y4p8pa {
    background-color: #2d3748;
}
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False
    if 'selected_mic' not in st.session_state:
        st.session_state.selected_mic = None
    if 'tts_enabled' not in st.session_state:
        st.session_state.tts_enabled = True
    if 'listening' not in st.session_state:
        st.session_state.listening = False

    if 'api_keys_set' not in st.session_state:
        st.session_state.api_keys_set = False
    if 'openai_key' not in st.session_state:
        st.session_state.openai_key = ""
    if 'elevenlabs_key' not in st.session_state:
        st.session_state.elevenlabs_key = ""
    if 'elevenlabs_client' not in st.session_state:
        st.session_state.elevenlabs_client = None

def setup_api_keys():
    st.sidebar.header("🔑 API Keys Setup")
    
    if not st.session_state.api_keys_set:
        st.sidebar.markdown("""
        **Required API Keys:**
        - **OpenAI**: For AI therapist responses
        - **ElevenLabs**: For voice responses
        """)
        

        openai_key = st.sidebar.text_input(
            "OpenAI API Key:",
            type="password",
            placeholder="sk-..."
        )
        
        elevenlabs_key = st.sidebar.text_input(
            "ElevenLabs API Key:",
            type="password",
            placeholder="..."
        )
        
        if st.sidebar.button("🔑 Validate & Set Keys"):
            if openai_key.strip() and elevenlabs_key.strip():
                with st.spinner("Testing API keys..."):
                    valid, errors = test_api_keys(openai_key.strip(), elevenlabs_key.strip())
                
                if valid:
                    elevenlabs_client, tts_success, tts_message = initialize_elevenlabs(elevenlabs_key.strip())
                    
                    st.session_state.openai_key = openai_key.strip()
                    st.session_state.elevenlabs_key = elevenlabs_key.strip()
                    st.session_state.elevenlabs_client = elevenlabs_client
                    st.session_state.api_keys_set = True
                    
                    if tts_success:
                        st.sidebar.success("✅ API keys validated successfully!")
                    else:
                        st.sidebar.warning(f"⚠️ OpenAI key valid, but TTS issue: {tts_message}")
                    
                    st.rerun()
                else:
                    st.sidebar.error("❌ API key validation failed:")
                    for error in errors:
                        st.sidebar.error(f"• {error}")
            else:
                st.sidebar.error("Please enter both API keys.")
        

        with st.sidebar.expander("🔗 How to get API keys"):
            st.markdown("""
            **OpenAI API Key:**
            1. Go to [platform.openai.com](https://platform.openai.com)
            2. Sign up/Login
            3. Go to API Keys section
            4. Create new key
            
            **ElevenLabs API Key:**
            1. Go to [elevenlabs.io](https://elevenlabs.io)
            2. Sign up/Login  
            3. Go to Profile → API Keys
            4. Copy your key
            """)
        
        return False
    else:
        st.sidebar.success("✅ API Keys Set")
        st.sidebar.write(f"OpenAI: {'*' * 8}{st.session_state.openai_key[-4:]}")
        st.sidebar.write(f"ElevenLabs: {'*' * 8}{st.session_state.elevenlabs_key[-4:]}")
        
        if st.sidebar.button("🔄 Change API Keys"):
            st.session_state.api_keys_set = False
            st.session_state.openai_key = ""
            st.session_state.elevenlabs_key = ""
            st.session_state.elevenlabs_client = None
            st.rerun()
        
        return True

def authenticate_user():
    st.sidebar.header("👤 User Profile")
    
    if not st.session_state.is_authenticated:
        user_option = st.sidebar.radio(
            "Choose an option:",
            ["New User", "Returning User"]
        )
        
        if user_option == "New User":
            user_name = st.sidebar.text_input("Enter your name:")
            if st.sidebar.button("Create Profile"):
                if user_name.strip():
                    user_id = create_user_profile(user_name)
                    st.session_state.user_id = user_id
                    st.session_state.session_id = create_session_id(user_id)  # Using main.py function
                    st.session_state.is_authenticated = True
                    st.sidebar.success(f"Profile created! Welcome {user_name}!")
                    st.rerun()
                else:
                    st.sidebar.error("Please enter a valid name.")
        
        else:
            user_id = st.sidebar.text_input("Enter your User ID:")
            if st.sidebar.button("Login"):
                if user_id.strip():
                    st.session_state.user_id = user_id.strip()
                    st.session_state.session_id = create_session_id(user_id)  # Using main.py function
                    st.session_state.is_authenticated = True
                    st.sidebar.success("Welcome back!")
                    st.rerun()
                else:
                    st.sidebar.error("Please enter a valid User ID.")
        
        return False
    
    else:

        st.sidebar.success(f"Logged in as: {st.session_state.user_id}")
        st.sidebar.write(f"Session: {st.session_state.session_id[:20]}...")
        
        if st.sidebar.button("Logout"):

            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        return True

def setup_voice_controls():
    st.sidebar.header("🎙️ Voice Controls")
    

    mic_names = get_microphone_list()
    if mic_names:

        default_index = find_preferred_microphone(mic_names, "OnePlus Buds 3")
        if default_index is None:
            default_index = 0
        
        selected_mic_name = st.sidebar.selectbox(
            "Select Microphone:",
            mic_names,
            index=default_index
        )
        st.session_state.selected_mic = mic_names.index(selected_mic_name)
    else:
        st.sidebar.warning("No microphones detected")
        st.session_state.selected_mic = None
    

    st.session_state.tts_enabled = st.sidebar.checkbox(
        "🔊 Enable Voice Response", 
        value=st.session_state.tts_enabled
    )

def get_ai_response(user_message):
    response, success = get_therapy_response(
        user_message, 
        st.session_state.conversation_history, 
        st.session_state.user_id, 
        st.session_state.session_id,
        st.session_state.openai_key
    )
    return response, success

def display_chat_history():
    if st.session_state.conversation_history:
        for message in st.session_state.conversation_history:
            if isinstance(message, HumanMessage):
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>You:</strong> {message.content}
                </div>
                """, unsafe_allow_html=True)
            elif isinstance(message, AIMessage):
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>AI Therapist:</strong> {message.content}
                </div>
                """, unsafe_allow_html=True)

def main():
    initialize_session_state()
    

    st.markdown("""
    <div class="main-header">
        <h1>🧠 AI Therapy Assistant</h1>
        <p>Your confidential space for mental health support with voice interaction</p>
    </div>
    """, unsafe_allow_html=True)
    

    if not setup_api_keys():
        st.markdown("""
        <div class="api-setup">
            <h3>🔑 Setup Required</h3>
            <p><strong>Welcome to AI Therapy Assistant!</strong></p>
            <p>To get started, please provide your API keys in the sidebar:</p>
            <ul>
                <li><strong>OpenAI API Key</strong> - Powers the AI therapist responses</li>
                <li><strong>ElevenLabs API Key</strong> - Enables voice responses</li>
            </ul>
            <p>Your API keys are stored securely in your browser session only and are never saved to our servers.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        ## Features Available After Setup:
        
        - 🎙️ **Voice Input**: Speak your thoughts naturally
        - 🔊 **Voice Output**: Hear responses from the AI therapist  
        - 🧠 **Memory**: Remembers your previous conversations
        - 💬 **Flexible**: Type or speak - your choice
        - 🔒 **Private**: All conversations stored locally with encryption
        """)
        return
    

    if not authenticate_user():
        st.markdown("""
        ## Welcome to AI Therapy Assistant
        
        **A safe, confidential space for mental health support**
        
        ### Your API Keys Are Set! ✅
        
        Now please authenticate in the sidebar to begin your therapy session.
        
        **This app features:**
        - 🎙️ **Voice Input**: Speak your thoughts naturally
        - 🔊 **Voice Output**: Hear responses from the AI therapist  
        - 🧠 **Memory**: Remembers your previous conversations
        - 💬 **Flexible**: Type or speak - your choice
        """)
        return
    

    setup_voice_controls()
    

    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 💬 Chat with AI Therapist")
        

        st.markdown("""
        <div class="voice-controls">
            <h4>🎙️ Voice Interaction</h4>
        </div>
        """, unsafe_allow_html=True)
        

        col_listen, col_stop = st.columns([1, 1])
        
        with col_listen:
            if st.button("🎙️ Start Listening", use_container_width=True, disabled=st.session_state.listening):
                if st.session_state.selected_mic is not None:
                    st.session_state.listening = True
                    

                    listening_placeholder = st.empty()
                    listening_placeholder.markdown("""
                    <div class="listening-indicator">
                        🎙️ Listening... Speak now!
                    </div>
                    """, unsafe_allow_html=True)
                    

                    with st.spinner("Processing speech..."):
                        speech_text, success, message = listen_for_speech(st.session_state.selected_mic)
                    
                    listening_placeholder.empty()
                    st.session_state.listening = False
                    
                    if success:

                        with st.spinner("AI Therapist is thinking..."):
                            response, ai_success = get_ai_response(speech_text)
                        

                        if st.session_state.tts_enabled and ai_success and st.session_state.elevenlabs_client:
                            with st.spinner("Speaking response..."):
                                speak_response(response, st.session_state.elevenlabs_client)
                        
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please select a microphone first!")
        
        with col_stop:
            if st.button("⏹️ Stop", use_container_width=True, disabled=not st.session_state.listening):
                st.session_state.listening = False
                st.rerun()
        

        chat_container = st.container()
        with chat_container:
            display_chat_history()
        

        st.markdown("#### Type your message:")
        user_input = st.text_input(
            "",
            placeholder="How are you feeling today?",
            key="user_input"
        )
        
        col_send, col_clear, col_speak = st.columns([1, 1, 1])
        
        with col_send:
            if st.button("💬 Send Text", use_container_width=True):
                if user_input.strip():
                    with st.spinner("AI Therapist is thinking..."):
                        response, success = get_ai_response(user_input)
                    

                    if st.session_state.tts_enabled and success and st.session_state.elevenlabs_client:
                        with st.spinner("Speaking response..."):
                            speak_response(response, st.session_state.elevenlabs_client)
                    
                    st.rerun()
                else:
                    st.warning("Please enter a message.")
        
        with col_clear:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.conversation_history = []
                st.rerun()
        
        with col_speak:
            if st.button("🔊 Replay Last", use_container_width=True):
                if st.session_state.conversation_history and st.session_state.tts_enabled and st.session_state.elevenlabs_client:
                    last_msg = st.session_state.conversation_history[-1]
                    if isinstance(last_msg, AIMessage):
                        with st.spinner("Speaking..."):
                            speak_response(last_msg.content, st.session_state.elevenlabs_client)
                else:
                    st.warning("No AI response to replay or TTS disabled.")
    
    with col2:
        st.markdown("### 📊 Session Info")
        
        st.markdown(f"""
        <div class="session-info">
            <strong>User:</strong> {st.session_state.user_id.split('_')[0] if st.session_state.user_id else 'Unknown'}<br>
            <strong>Messages:</strong> {len(st.session_state.conversation_history)}<br>
            <strong>Session Started:</strong> {datetime.now().strftime("%H:%M")}<br>
            <strong>Voice:</strong> {'🔊 Enabled' if st.session_state.tts_enabled else '🔇 Disabled'}<br>
            <strong>APIs:</strong> {'✅ Ready' if st.session_state.api_keys_set else '❌ Missing'}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🆘 Emergency Resources")
        st.markdown("""
        **Crisis Support:**
        - **988** - Suicide & Crisis Lifeline
        - **741741** - Crisis Text Line
        - **911** - Emergency Services
        """)
        
        st.markdown("### 💡 Tips")
        with st.expander("Voice & Chat Tips"):
            st.markdown("""
            - Speak clearly in a quiet environment
            - Wait for the listening indicator
            - Toggle voice response as needed
            - Use text backup if voice fails
            - Your API keys are secure in browser only
            """)

if __name__ == "__main__":
    main() 
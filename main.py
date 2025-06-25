import speech_recognition as sr
from graph import app as therapy_app
import os
import pygame
from elevenlabs.client import ElevenLabs
from langchain.schema import HumanMessage, AIMessage
import uuid

pygame.mixer.init()

def initialize_elevenlabs(api_key):
    try:
        client = ElevenLabs(api_key=api_key)
        return client, True, "ElevenLabs initialized successfully"
    except Exception as e:
        return None, False, f"Failed to initialize ElevenLabs: {str(e)}"

def speak_response(text: str, elevenlabs_client=None, elevenlabs_api_key=None):
    try:

        if elevenlabs_client is None and elevenlabs_api_key:
            elevenlabs_client, success, message = initialize_elevenlabs(elevenlabs_api_key)
            if not success:
                return False
        
        if elevenlabs_client is None:
            return False
        

        audio = elevenlabs_client.text_to_speech.convert(
            voice_id="pNInz6obpgDQGcFmaJgB",
            output_format="mp3_22050_32",
            text=text,
            model_id="eleven_turbo_v2"
        )
        

        temp_file = f"temp_response_{uuid.uuid4().hex[:8]}.mp3"
        with open(temp_file, "wb") as f:
            for chunk in audio:
                if chunk:
                    f.write(chunk)
        

        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()
        

        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        

        pygame.mixer.music.unload()
        

        try:
            os.remove(temp_file)
        except:
            pass
        
        return True
    except Exception as e:
        return False

def get_microphone_list():
    try:
        mic_names = sr.Microphone.list_microphone_names()
        return mic_names
    except:
        return []

def listen_for_speech(mic_index=None, timeout=10):
    try:
        r = sr.Recognizer()
        

        if mic_index is not None:
            microphone = sr.Microphone(device_index=mic_index)
        else:
            microphone = sr.Microphone()
        
        with microphone as source:
            r.adjust_for_ambient_noise(source, duration=1)
            r.pause_threshold = 1
            

            audio = r.listen(source, timeout=timeout, phrase_time_limit=10)
            

            text = r.recognize_google(audio)
            return text, True, "Success"
            
    except sr.UnknownValueError:
        return "", False, "Could not understand audio"
    except sr.RequestError as e:
        return "", False, f"Speech recognition error: {e}"
    except sr.WaitTimeoutError:
        return "", False, "Listening timeout - no speech detected"
    except Exception as e:
        return "", False, f"Error: {e}"

def find_preferred_microphone(mic_names, preferred="OnePlus Buds 3"):
    for index, name in enumerate(mic_names):
        if preferred in name:
            return index
    return None

def set_api_keys_in_env(openai_key=None, elevenlabs_key=None):
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    if elevenlabs_key:
        os.environ["ELEVENLABS_API_KEY"] = elevenlabs_key

def test_api_keys(openai_key, elevenlabs_key):
    errors = []
    

    if openai_key:
        try:
            os.environ["OPENAI_API_KEY"] = openai_key

        except Exception as e:
            errors.append(f"OpenAI key error: {str(e)}")
    else:
        errors.append("OpenAI API key is required")
    

    if elevenlabs_key:
        try:
            client, success, message = initialize_elevenlabs(elevenlabs_key)
            if not success:
                errors.append(f"ElevenLabs key error: {message}")
        except Exception as e:
            errors.append(f"ElevenLabs key error: {str(e)}")
    else:
        errors.append("ElevenLabs API key is required")
    
    return len(errors) == 0, errors

def get_therapy_response(user_message, conversation_history, user_id, session_id, openai_api_key=None):
    try:

        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        

        conversation_history.append(HumanMessage(content=user_message))
        

        state = {
            "messages": conversation_history,
            "user_id": user_id
        }
        

        config = {"configurable": {"thread_id": session_id}}
        

        therapist_response = None
        try:

            for event in therapy_app.stream(state, config=config, stream_mode="values"):
                if "messages" in event and event["messages"]:
                    last_msg = event["messages"][-1]
                    if hasattr(last_msg, 'content'):
                        therapist_response = last_msg.content
        except Exception:

            try:
                for event in therapy_app.stream(state, stream_mode="values"):
                    if "messages" in event and event["messages"]:
                        last_msg = event["messages"][-1]
                        if hasattr(last_msg, 'content'):
                            therapist_response = last_msg.content
            except Exception:
                therapist_response = "I apologize, but I'm having technical difficulties. Please check your OpenAI API key and try again."
        
        if therapist_response:

            conversation_history.append(AIMessage(content=therapist_response))
            return therapist_response, True
        else:
            return "I apologize, but I'm having technical difficulties. Please check your API key and try again.", False
    
    except Exception as e:
        return "I'm experiencing some technical issues. Please check your API keys and try again later.", False

def create_user_profile(user_name):
    user_id = f"{user_name.strip()}_{str(uuid.uuid4())[:8]}"
    return user_id

def save_user_identity(user_id):
    user_file = "user_identity.txt"
    with open(user_file, "w") as f:
        f.write(user_id)

def load_user_identity():
    user_file = "user_identity.txt"
    if os.path.exists(user_file):
        with open(user_file, "r") as f:
            return f.read().strip()
    return None

def create_session_id(user_id):
    return f"session_{user_id}_{str(uuid.uuid4())[:8]}"

def get_user_identity():
    user_id = load_user_identity()
    
    if user_id:
        print(f"Welcome back! Your user ID: {user_id}")
        return user_id
    else:
        print("First time user detected!")
        user_name = input("Please enter your name: ").strip()
        user_id = create_user_profile(user_name)
        save_user_identity(user_id)
        print(f"Created new user profile: {user_id}")
        return user_id

def get_api_keys_from_user():
    print("\n" + "="*50)
    print("🔑 API KEYS REQUIRED")
    print("="*50)
    print("To use this AI Therapy Assistant, you need:")
    print("1. OpenAI API Key (for the AI therapist)")
    print("2. ElevenLabs API Key (for voice responses)")
    print()
    
    openai_key = input("Enter your OpenAI API Key: ").strip()
    elevenlabs_key = input("Enter your ElevenLabs API Key: ").strip()
    
    print("\nTesting API keys...")
    valid, errors = test_api_keys(openai_key, elevenlabs_key)
    
    if valid:
        print("✅ API keys are valid!")
        set_api_keys_in_env(openai_key, elevenlabs_key)
        return openai_key, elevenlabs_key, True
    else:
        print("❌ API key validation failed:")
        for error in errors:
            print(f"   - {error}")
        return None, None, False

def console_main():
    print("🧠 AI Therapy Assistant - Console Version")
    print("="*50)
    

    openai_key, elevenlabs_key, keys_valid = get_api_keys_from_user()
    if not keys_valid:
        print("Please check your API keys and try again.")
        return
    

    elevenlabs_client, tts_ready, tts_message = initialize_elevenlabs(elevenlabs_key)
    if not tts_ready:
        print(f"⚠️ Text-to-speech not available: {tts_message}")
    

    user_id = get_user_identity()
    

    session_id = create_session_id(user_id)
    
    print("-" * 50)
    

    mic_names = get_microphone_list()
    mic_index = find_preferred_microphone(mic_names, "OnePlus Buds 3")
    
    if mic_index is not None:
        print(f"Using microphone: {mic_names[mic_index]}")
    else:
        print("OnePlus Buds 3 microphone not found, using default microphone")


    conversation_messages = []
    print("Therapist AI with Memory is ready. Say 'quit' or 'exit' to end the session.")
    print("-" * 50)


    r = sr.Recognizer()
    while True:
        try:
            print("Listening...")
            text, success, message = listen_for_speech(mic_index)
            
            if not success:
                print(f"Error: {message}")
                continue
                
            print(f"You: {text}")
            

            if text.lower() in ['quit', 'exit', 'goodbye', 'bye']:
                goodbye_text = "Take care of yourself. Remember, I'm here whenever you need support. Your progress and our conversations are saved for next time."
                print(f"Therapist: {goodbye_text}")
                if tts_ready:
                    speak_response(goodbye_text, elevenlabs_client)
                break


            response, success = get_therapy_response(text, conversation_messages, user_id, session_id, openai_key)
            
            if success:
                print(f"Therapist: {response}")
                if tts_ready:
                    speak_response(response, elevenlabs_client)
            else:
                print(f"Error: {response}")
            
            print("-" * 50)
                
        except KeyboardInterrupt:
            print("\nSession ended by user.")
            break
        except Exception as e:
            print("Something went wrong. Please try again.")

if __name__ == "__main__":
    console_main()










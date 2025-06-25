# AI Therapy Chatbot with Memory

A voice-enabled AI therapy chatbot with persistent memory and conversation history.

## Features

- 🎙️ **Voice Input**: Speech-to-text using Google Speech Recognition
- 🔊 **Voice Output**: Text-to-speech using ElevenLabs API
- 🧠 **Persistent Memory**: Remembers conversations across sessions using mem0 + QdrantDB
- 💬 **Contextual Responses**: References past sessions for personalized therapy
- 🔄 **Session Management**: Automatic checkpointing and conversation history

## Requirements

- Python 3.8+
- OpenAI API key
- ElevenLabs API key
- QdrantDB (Docker recommended)

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Setup
Create a `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### 3. Start QdrantDB
```bash
# Using Docker (recommended)
docker run -p 6333:6333 qdrant/qdrant

# Or with persistence
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

### 4. Run the Application
```bash
python main.py
```

## Usage

1. **First time**: Enter your name to create a user profile
2. **Voice commands**: Speak naturally to the AI therapist
3. **Exit**: Say "quit", "exit", "goodbye", or "bye" to end session
4. **Memory**: The AI remembers your conversations for personalized therapy

## Architecture

- `main.py` - Main application with voice interface
- `graph.py` - LangGraph workflow with memory integration
- `requirements.txt` - Python dependencies

## Production Notes

- Ensure QdrantDB is running as a persistent service
- Use environment variables for API keys
- Consider using a microphone array for better voice recognition
- Monitor memory usage and implement cleanup policies if needed

## Troubleshooting

- **No microphone detected**: Check audio device permissions
- **QdrantDB connection error**: Ensure QdrantDB is running on port 6333
- **TTS not working**: Verify ElevenLabs API key and credits
- **Memory not working**: Check OpenAI API key and QdrantDB connection 
import os
import httpx 
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import httpx
from fastapi import FastAPI, HTTPException
import logging
import json
import base64
import uvicorn
from dotenv import load_dotenv
load_dotenv()

# Load API Keys from Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("VOICE_ID")  


if not VOICE_ID:
    raise ValueError("VOICE_ID is not set in the environment variables.")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI API key is not set in the environment variables.")
if not ELEVENLABS_API_KEY:
    raise ValueError("ElevenLabs API key is not set in the environment variables.")
app = FastAPI()
# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def speech_to_text(audio_data: bytes):
    """ Convert speech to text using OpenAI Whisper """
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    files = {"file": ("audio.wav", audio_data, "audio/wav")}
    data = {"model": "whisper-1", "language": "en"}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers=headers,
            files=files,
            data=data
        )
    
    return response.json().get("text", "")

async def chat_gpt(prompt: str) -> str:
    """ Gets a short response from OpenAI GPT-3.5 """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": "gpt-3.5-turbo", 
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 50 
                },
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except httpx.RequestError as e:
            logger.error(f"Error with the GPT API: {e}")
            raise HTTPException(status_code=500, detail="Error with the AI response")

async def text_to_speech(text: str):
    """ Convert text to speech using ElevenLabs """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
    
    return response.content if response.status_code == 200 else None

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """ WebSocket for real-time voice interaction """
    await websocket.accept()
    print("INFO: WebSocket connection opened")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if "audio" in message:
                print("INFO: Received audio data from client")

                # Decode received base64 audio
                audio_bytes = base64.b64decode(message["audio"])

                # Convert Speech to Text (STT)
                text = await speech_to_text(audio_bytes)
                print(f"DEBUG: Transcribed text: {text}")

                # Get AI Response
                ai_response = await chat_gpt(text)
                print(f"DEBUG: AI Response: {ai_response}")

                # Convert AI Response to Speech (TTS)
                audio_output = await text_to_speech(ai_response)

                if audio_output:
                    print("INFO: Audio successfully generated from AI response")
                    # Encode audio back to base64 and send
                    encoded_audio = base64.b64encode(audio_output).decode("utf-8")
                    await websocket.send_text(json.dumps({"audio": encoded_audio}))
                    print("INFO: Audio response sent to client")

    except WebSocketDisconnect:
        print("INFO: WebSocket client disconnected")
    except Exception as e:
        print(f"ERROR: {e}")
        await websocket.close()


if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
    )

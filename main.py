import os
import httpx
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging
import io
import httpx
from tenacity import retry, wait_fixed, stop_after_attempt, RetryError

# Load environment variables
from dotenv import load_dotenv
load_dotenv(override=True)

# Configure API keys and other settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("VOICE_ID")  

# print(ELEVENLABS_API_KEY)

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

# Define API response model
class AIResponse(BaseModel):
    text: str
# input audio to text
async def speech_to_text(audio_data: bytes) -> str:
    """ Converts speech to text using OpenAI Whisper """
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    files = {"file": ("audio.wav", audio_data, "audio/wav")}
    data = {"model": "whisper-1", "language": "en"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                files=files,
                data=data
            )
            response.raise_for_status()
            return response.json().get("text", "")
        except httpx.RequestError as e:
            logger.error(f"Error with the speech-to-text API: {e}")
            raise HTTPException(status_code=500, detail="Error processing speech-to-text")
# LLM response
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


# Retry logic with tenacity
@retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
async def request_with_retry(url: str, method: str = "POST", data: dict = None, headers: dict = None, files: dict = None):
    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "POST":
                response = await client.post(url, json=data, headers=headers, files=files)
            else:
                response = await client.get(url, headers=headers)

            # Check for unsuccessful status codes and raise an error
            response.raise_for_status()

            return response
        except httpx.HTTPStatusError as e:
            # Do not retry on Unauthorized (401)
            if e.response.status_code == 401:
                print("Error: Unauthorized access. Check your API key.")
                raise e  # Don't retry
            # Retry on other 5xx or network-related errors
            raise e
# TTS
async def text_to_speech(text: str):
    """ Convert text to speech using ElevenLabs with retry logic """
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
    
    try:
        response = await request_with_retry(url, data=data, headers=headers)
        return response.content  # Return the audio content if successful
    except RetryError:
        print("Error: Failed to get a response after retries.")
        return None  


@app.post("/upload-audio/")
async def process_audio(file: UploadFile = File(...)):
    """ Accept audio file, process, and return AI-generated response """
    try:
        # Load the audio file
        audio_data = await file.read()

        # Step 1: Convert speech to text
        logger.info("Converting speech to text...")
        text = await speech_to_text(audio_data)
        logger.info(f"Text extracted from speech: {text}")

        # Step 2: Get AI response from GPT
        logger.info("Generating AI response...")
        ai_response = await chat_gpt(text)
        logger.info(f"AI Response: {ai_response}")

        # Step 3: Convert AI response to speech
        logger.info("Converting AI response to speech...")
        audio_response = await text_to_speech(ai_response)
        if not audio_response:
            logger.error("Failed to generate speech.")
            raise HTTPException(status_code=500, detail="Failed to generate speech response.")

        # Save the generated audio locally
        with open("response.mp3", "wb") as audio_file:
            audio_file.write(audio_response)

        logger.info("Generated audio saved as response.mp3")

        # Step 4: Return the generated audio as a response
        return StreamingResponse(io.BytesIO(audio_response), media_type="audio/mpeg")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

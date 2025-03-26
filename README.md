
# AI Audio Processing System

This is an AI-powered audio processing system that accepts audio file uploads, converts speech to text, generates AI responses, and converts the responses to speech.

## Clone the Repository

First, clone this repository to your local machine:

```bash
git clone https://github.com/sherazrazadev/STT-TTS-voice-assistant-python-app.git
cd STT-TTS-voice-assistant-python-app
```
## Install Requirements
Create a virtual environment (optional but recommended):

For Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```
For Windows:

```bash
python -m venv venv
venv\Scripts\activate
```
### Install the required dependencies:

```bash
pip install -r requirements.txt
```
## Set Up Environment Variables
Create a .env file in the root of the project and add the following environment variables:
```bash
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
VOICE_ID=your_elevenlabs_voice_id
```
Make sure to replace the placeholder values with your actual API keys from OpenAI and ElevenLabs.

## Run the Server
- To run the FastAPI server locally, execute the following command:
- For normal STT-TTS llm response and upload audio file input i used main.py and for websocket voice conversation i used server.py and test_send.py to send audio file to websocket and it will receive and save in same directory.

```bash
uvicorn main:app --reload
```
For Server websockets
```bash
uvicorn server:app --reload
```
The server will start at http://127.0.0.1:8000.

You can access the API documentation (Swagger UI) at http://127.0.0.1:8000/docs.

## API Endpoints
POST /upload-audio/: Upload an audio file (MP3/WAV), which will be processed and responded to with generated speech.

## Error Handling & Retries
The system implements retry logic for API failures using the tenacity library. If an API request fails, the system will automatically retry up to 3 times with a 2-second delay between retries.
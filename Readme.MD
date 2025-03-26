# AI Audio Processing System

This is an AI-powered audio processing system that accepts audio file uploads, converts speech to text, generates AI responses, and converts the responses to speech.

## Clone the Repository

First, clone this repository to your local machine:

```bash
git clone https://github.com/your-username/ai-audio-processing.git
cd ai-audio-processing
```

### create environment
```bash
python -m venv venv
 .\venv\bin\activate
```
### install required dependencies
```bash
pip install -r requirements.txt
```

### setup .env api keys
```bash
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
VOICE_ID=your_elevenlabs_voice_id
```

## Run the Server
To run the FastAPI server locally, execute the following command:
```bash
uvicorn main:app --reload
```
The server will start at http://127.0.0.1:8000.

You can access the API documentation (Swagger UI) at http://127.0.0.1:8000/docs.

### API Endpoints
POST /upload-audio/: Upload an audio file (MP3/WAV), which will be processed and responded to with generated speech.

### Error Handling & Retries
The system implements retry logic for API failures using the tenacity library. If an API request fails, the system will automatically retry up to 3 times with a 2-second delay between retries.
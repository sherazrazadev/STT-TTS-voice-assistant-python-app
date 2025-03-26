import asyncio
import websockets
import json
import base64

async def send_audio():
    uri = "ws://127.0.0.1:8000/ws"

    async with websockets.connect(uri) as websocket:
        # Load and encode audio
        with open("tester.wav", "rb") as f:
            audio_data = f.read()
        
        encoded_audio = base64.b64encode(audio_data).decode("utf-8")

        # Send audio data
        await websocket.send(json.dumps({"audio": encoded_audio}))

        # Receive AI-generated speech
        response = await websocket.recv()
        response_data = json.loads(response)

        # Decode received audio
        with open("response.mp3", "wb") as f:
            f.write(base64.b64decode(response_data["audio"]))

        print("Response audio saved as response.mp3")

asyncio.run(send_audio())

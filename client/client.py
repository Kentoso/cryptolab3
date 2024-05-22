import asyncio
import websockets
import json


async def send_messages():
    uri = "ws://localhost:8090"
    async with websockets.connect(uri) as websocket:
        # Send identifying information upon connection
        user_info = {"username": "user123", "info": "Additional info if needed"}
        await websocket.send(json.dumps(user_info))

        while True:
            await websocket.send("Hello world!")
            message = await websocket.recv()
            print(f"Received: {message}")
            await asyncio.sleep(5)  # Wait for 5 seconds before sending the next message


if __name__ == "__main__":
    asyncio.run(send_messages())

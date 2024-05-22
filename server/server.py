import asyncio
import websockets
import json

connected_users = {}

lobbyState = "lobby"
preparingState = "preparing"
chatState = "chat"

current_state = lobbyState


async def handler(websocket: websockets.WebSocketServerProtocol, path: str):
    global current_state
    try:
        # Receive initial message containing user info
        user_info = await websocket.recv()
        user_info = json.loads(user_info)
        connected_users[websocket] = user_info
        print(f"User connected: {user_info}")

        async for message in websocket:
            data = json.loads(message)
            if current_state == chatState:
                await broadcast(data, websocket)
            elif current_state == preparingState:
                await websocket.send(json.dumps({"error": "Chat is preparing"}))
            else:
                await websocket.send(json.dumps({"error": "Chat has not started yet"}))
    except websockets.ConnectionClosed as e:
        print(
            f"Client disconnected: {websocket.remote_address} with code {e.code} and reason: {e.reason}"
        )
    finally:
        if websocket in connected_users:
            print(f"Connection with {connected_users[websocket]} closed")
            del connected_users[websocket]


async def broadcast(message, sender=None):
    if connected_users:  # Check if there are any connected users
        destinations = [
            user.send(message) for user in connected_users if user != sender
        ]
        if destinations:
            await asyncio.wait(destinations)


async def handle_start_command():
    global current_state
    current_state = preparingState
    await broadcast(json.dumps({"state": current_state}))


async def terminal_input(stop_event):
    while True:
        command = await asyncio.to_thread(input, "")
        if command.lower() == "start" and current_state == "lobby":
            await handle_start_command()
            print("Transitioning to chat state...")
        if command.lower() == "stop":
            print("Stopping server...")
            stop_event.set()
            break
        else:
            print(f"Unknown command: {command}")


async def main():
    stop_event = asyncio.Event()
    server = await websockets.serve(handler, "localhost", 8090)
    input_task = asyncio.create_task(terminal_input(stop_event))

    await stop_event.wait()
    server.close()
    await server.wait_closed()
    await input_task


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped by user")

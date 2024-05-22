import asyncio
import websockets


async def handler(websocket):
    async for message in websocket:
        await websocket.send(message)


async def main():
    async with websockets.serve(handler, "localhost", 8090):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import websockets
import json

# A set to store all connected WebSocket clients
connected_clients = set()

async def register(websocket):
    """
    Adds a new client to the set of connected clients.
    """
    connected_clients.add(websocket)
    print(f"New client connected. Total clients: {len(connected_clients)}")
    try:
        # Keep the connection open
        await websocket.wait_closed()
    finally:
        # Remove the client when the connection is closed
        connected_clients.remove(websocket)
        print(f"Client disconnected. Total clients: {len(connected_clients)}")

async def send_to_all(message):
    """
    Sends a message to all connected clients.
    """
    if connected_clients:
        # Create a list of tasks to send the message to all clients
        tasks = [client.send(message) for client in connected_clients]
        await asyncio.gather(*tasks)

async def main():
    """
    Starts the WebSocket server.
    """
    host = "localhost"
    port = 8766
    print(f"Starting WebSocket server on ws://{host}:{port}")
    async with websockets.serve(register, host, port):
        await asyncio.Future()  # Run forever

def run_server():
    """
    Runs the WebSocket server in a separate thread.
    """
    asyncio.run(main())

if __name__ == "__main__":
    run_server()

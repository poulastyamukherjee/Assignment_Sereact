import asyncio
import websockets
import json

# A set to store all connected WebSocket clients
connected_clients = set()

def get_connected_clients_count():
    """
    Returns the number of connected clients.
    """
    return len(connected_clients)

def has_connected_clients():
    """
    Returns True if there are connected clients.
    """
    return len(connected_clients) > 0

async def handle_message(websocket, message):
    """
    Handle incoming WebSocket messages
    """
    try:
        data = json.loads(message)
        # Handle different message types here if needed
        print(f"Received WebSocket message: {data}")
        
        # Echo back or process the message
        response = {"status": "received", "data": data}
        await websocket.send(json.dumps(response))
    except json.JSONDecodeError:
        print(f"Invalid JSON received: {message}")
    except Exception as e:
        print(f"Error handling message: {e}")

async def register(websocket):
    """
    Adds a new client to the set of connected clients.
    """
    global connected_clients
    connected_clients.add(websocket)
    print(f"New client connected. Total clients: {len(connected_clients)}")
    try:
        # Listen for messages from this client
        async for message in websocket:
            await handle_message(websocket, message)
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
    finally:
        # Remove the client when the connection is closed
        connected_clients.discard(websocket)
        print(f"Client disconnected. Total clients: {len(connected_clients)}")

async def send_to_all(message):
    """
    Sends a message to all connected clients.
    """
    global connected_clients
    if not connected_clients:
        return
        
    # Create a copy of the set to avoid modification during iteration
    clients_copy = connected_clients.copy()
    disconnected = set()
    
    for client in clients_copy:
        try:
            await client.send(message)
        except websockets.exceptions.ConnectionClosed:
            disconnected.add(client)
        except Exception as e:
            print(f"Error sending to client: {e}")
            disconnected.add(client)
    
    # Remove disconnected clients
    connected_clients -= disconnected

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

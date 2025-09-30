import asyncio
import websockets
import requests
import threading
import time

def trigger_movement():
    """
    Sends a POST request to the /move endpoint to start the movement.
    """
    time.sleep(1) # Give the websocket time to connect
    print("Triggering robot movement...")
    try:
        response = requests.post("http://localhost:5001/move")
        response.raise_for_status()
        print(f"Response from /move: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error calling /move endpoint: {e}")

async def listen_to_robot():
    """
    Connects to the WebSocket server and listens for messages.
    """
    uri = "ws://localhost:8766"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to WebSocket server at {uri}")
            
            # Start the movement trigger in a separate thread
            threading.Thread(target=trigger_movement, daemon=True).start()

            message_count = 0
            try:
                # Listen for messages
                async for message in websocket:
                    print(f"Received message: {message}")
                    message_count += 1
                    if message_count > 5: # Limit the number of messages for this test
                        break
            except websockets.exceptions.ConnectionClosed:
                print("Connection to WebSocket server closed.")
            
            print(f"\nTest finished. Received {message_count} messages.")

    except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError) as e:
        print(f"Could not connect to WebSocket server at {uri}. Error: {e}")
        print("Please ensure the backend server is running.")

if __name__ == "__main__":
    asyncio.run(listen_to_robot())

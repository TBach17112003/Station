import asyncio
import websockets
import cv2
import time
import numpy as np

async def manage_pings(websocket):
    """Send pings and handle pongs asynchronously."""
    print('Rcv ping')
    await websocket.send(bytearray([1]))

async def listen_for_messages(websocket):
    """Listen for messages and pongs asynchronously."""
    try:
        # cap = cv2.VideoCapture(0)
        while True:
            msg = await websocket.recv()
            # print(type(msg), msg)
            # msg = msg.encode()
            if msg == '1':
                print('ping pong')
                await manage_pings(websocket)
                continue
            # nparr = np.frombuffer(msg, np.uint8)
            # img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # recv_time = time.time()
            # img_data = base64.b64decode(data)
            # separator_index = msg.rfind(b';')
            # img_data = msg[:separator_index]
            # timestamp_bytes = msg[separator_index + 1:]
            # timestamp = int.from_bytes(timestamp_bytes, byteorder='big')
            # print('Time: ',recv_time * 1000 - timestamp)
            nparr = np.frombuffer(msg, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            cv2.imshow('Received Image', img)
        # Wait for a key press indefinitely or for a specified amount of time
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except websockets.exceptions.ConnectionClosed:
        print("WebSocket connection closed by server.")

async def websocket_client():
    uri = "ws://begvn.home:9090/realtime/streaming"
    async with websockets.connect(uri) as websocket:
        # Create tasks for managing pings and receiving messages
        # ping_task = asyncio.create_task(manage_pings(websocket))
        listen_task = asyncio.create_task(listen_for_messages(websocket))

        # Wait for either task to complete
        done, pending = await asyncio.wait(
            [ listen_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        # If here, one of the tasks has completed, cancel the others
        for task in pending:
            task.cancel()
        if listen_task in done:
        #     # Handle specific completion, if needed
            print("Message listening task completed")

#Run the client
asyncio.run(websocket_client())

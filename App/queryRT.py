import asyncio
import websockets
import cv2
import numpy as np
import time
import json
import ssl
from datetime import datetime
from data_store import DataStore

#from utils.Security import Security



max_delay = 0


async def manage_pings(websocket):
    """Send pings and handle pongs asynchronously."""
    # print('Rcv ping')
    await websocket.send(bytearray([1]))

async def listen_for_messages(websocket):
    """Listen for messages and pongs asynchronously."""
    try:
        # cap = cv2.VideoCapture(0)
        global max_delay
        prev_time = time.time()
        while True:
            msg = await websocket.recv()
            print("msg: ", msg)
            # print(type(msg), msg)
            # msg = msg.encode()
            if msg == '1':
                # print('ping pong')
                await manage_pings(websocket)
                continue
            # cur_time = time.time()
            # print('Period: ',(cur_time - prev_time) * 1000)
            # # print(msg)
            # # getTime = time.time()
            # prev_time = cur_time
            # start_time = time.time()
            # dec_msg = Security.Verify_Decrypt_SW(msg)
            # stop_time = time.time()
            # print('Enc time: ',stop_time - start_time)
            # if (dec_msg == None):
            #     continue
            # print(dec_msg)
            msgObj = json.loads(msg)
            print(msgObj["recordTime"])

            # Extract values
            DataStore.yaw = msgObj["Orientation"]["yaw"]
            DataStore.pitch = msgObj["Orientation"]["pitch"]
            DataStore.roll = msgObj["Orientation"]["roll"]
            DataStore.accel_x = msgObj["Accelerator"]["x"]
            DataStore.accel_y = msgObj["Accelerator"]["y"]
            DataStore.accel_z = msgObj["Accelerator"]["z"]
            DataStore.gyro_x = msgObj["Gyroscope"]["x"]
            DataStore.gyro_y = msgObj["Gyroscope"]["y"]
            DataStore.gyro_z = msgObj["Gyroscope"]["z"]
            # iso_date_string = "2024-08-06T17:56:23.691"

            # Parse the ISO 8601 date string to a datetime object
            # date_time_obj = datetime.strptime(msgObj["recordTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
            # # print('Date time: ',date_time_obj)
            # # # # Convert the datetime object to milliseconds since the Unix epoch
            # epoch = datetime(1970, 1, 1,7,0,0,0)
            # # # # print('date: ',epoch)
            # milliseconds_since_epoch = int((date_time_obj - epoch).total_seconds() * 1000)
            # # # print('record: ',milliseconds_since_epoch)
            # # # print('current: ',time.time())
            # delay_ms = cur_time * 1000 - milliseconds_since_epoch
            # print('delay: ',delay_ms)
            # if delay_ms > max_delay:
            #     max_delay = delay_ms
        # Wait for a key press indefinitely or for a specified amount of time
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break
    except websockets.exceptions.ConnectionClosed:
        print(max_delay)
        print("WebSocket connection closed by server.")

async def websocket_client():
    try: 
        uri = "wss://begvn.home:9090/realtime/data"
        context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
        # # context.options &= ~ssl.OP_NO_SSLv3
        context.load_verify_locations(cafile=r'C:\Users\HOB6HC\Code_Source\FOTA_Station_Up1-main\App\ca.crt')
        # context.minimum_version = ssl.TLSVersion.TLSv1
        async with websockets.connect(uri=uri,ssl=context) as websocket:
            # Create tasks for managing pings and receiving messages
            # ping_task = asyncio.create_task(manage_pings(websocket))
            print('Connected')
            listen_task = asyncio.create_task(listen_for_messages(websocket))

            # Wait for either task to complete
            done, pending = await asyncio.wait(
                [ listen_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # print(max_delay)
            # If here, one of the tasks has completed, cancel the others
            for task in pending:
                task.cancel()
            if listen_task in done:
            #     # Handle specific completion, if needed
                print("Message listening task completed")
    except ssl.SSLError as e:
        print('SSL error: ',e)
# Run the client

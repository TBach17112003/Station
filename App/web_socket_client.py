import asyncio
import websockets
import json
import ssl
from data_store import DataStore

class WebSocketClient:
    def __init__(self, uri, cert_path):
        self.uri = uri
        self.cert_path = cert_path
        self.data_store = DataStore()
        self._stop_event = asyncio.Event()  # Event to signal stopping
        self._websocket = None  # To store the websocket connection

    async def listen_for_messages(self, websocket):
        self._websocket = websocket
        try:
            while not self._stop_event.is_set():
                try:
                    msg = await websocket.recv()
                except websockets.exceptions.ConnectionClosed:
                    print("WebSocket connection closed by server.")
                    break
                
                if msg == '1':
                    await self.manage_pings(websocket)
                    continue
                
                msgObj = json.loads(msg)
                # Update the shared data store with received values
                self.data_store.yaw = msgObj["Orientation"]["yaw"]
                self.data_store.pitch = msgObj["Orientation"]["pitch"]
                self.data_store.roll = msgObj["Orientation"]["roll"]
                self.data_store.accel_x = msgObj["Accelerator"]["x"]
                self.data_store.accel_y = msgObj["Accelerator"]["y"]
                self.data_store.accel_z = msgObj["Accelerator"]["z"]
                self.data_store.gyro_x = msgObj["Gyroscope"]["x"]
                self.data_store.gyro_y = msgObj["Gyroscope"]["y"]
                self.data_store.gyro_z = msgObj["Gyroscope"]["z"]
                self.data_store.battery = msgObj["Battery"]["Capacity"]
                self.data_store.temperature = msgObj["Battery"]["Temperature"]

        finally:
            if websocket:
                await websocket.close()
    
    async def manage_pings(self, websocket):
        await websocket.send(bytearray([1]))

    async def connect(self):
        context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations(cafile=self.cert_path)
        
        async with websockets.connect(uri=self.uri, ssl=context) as websocket:
            await self.listen_for_messages(websocket)

    def start(self):
        self._stop_event.clear()  # Ensure the stop event is not set
        asyncio.run(self.connect())
    
    def stop(self):
        self._stop_event.set()  # Signal the event loop to stop
        if self._websocket is not None:
            asyncio.run(self._websocket.close())  # Close the WebSocket connection

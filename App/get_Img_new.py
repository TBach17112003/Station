# get_Img.py
import asyncio
import websockets
import cv2
import numpy as np
import ssl

class WebSocketCameraClient:
    def __init__(self, uri,capath):
        self.uri = uri
        self.capath = capath
        self.frame = None
        self.running = True

    async def manage_pings(self, websocket):
        await websocket.send(bytearray([1]))

    async def listen_for_messages(self, websocket):
        try:
            while self.running:
                msg = await websocket.recv()
                if msg == '1':
                    await self.manage_pings(websocket)
                    continue
                nparr = np.frombuffer(msg, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                self.frame = img
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed by server.")

    async def start(self):
        context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
        # # context.options &= ~ssl.OP_NO_SSLv3
        context.load_verify_locations(cafile=self.capath)
        # context.minimum_version = ssl.TLSVersion.TLSv1
        async with websockets.connect(uri=self.uri,ssl=context) as websocket:
            listen_task = asyncio.create_task(self.listen_for_messages(websocket))
            await listen_task

    def stop(self):
        self.running = False

    def get_frame(self):
        return self.frame

# For testing purpose
if __name__ == "__main__":
    uri = "ws://begvn.home:9090/realtime/streaming"
    client = WebSocketCameraClient(uri)
    asyncio.run(client.start())

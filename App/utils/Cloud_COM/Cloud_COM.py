import ftplib
import time
import ssl
import os
import io
import sys
import paho.mqtt.client as mqtt
import threading
from utils.Cloud_COM.Security import Security
import time
import re

File_path = os.path.abspath(__file__)
Folder_Dir = os.path.dirname(File_path)
sys.path.append(Folder_Dir)
print(sys.path)

class MyFTP_TLS(ftplib.FTP_TLS):
    """Explicit FTPS, with shared TLS session"""
    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(conn,
                                            server_hostname=self.host,
                                            session=self.sock.session)  # this is the fix
        return conn, size
    

class Cloud_COM:
    def __init__(self) -> None:
        self.host = 'begvn.home'
        self.FTPport = 21
        self.MQTTPort = 8883
        self.MQTTProtocol = "tcp"
        self.user = 'user1'
        self.passwd = '123456'
        self.acct = 'Normal'
        self.ca_cert_path = Folder_Dir + '/certs/ca.crt'
        self.ssl_context = ssl.create_default_context(cafile=self.ca_cert_path)
        self.ftps = MyFTP_TLS(context=self.ssl_context)
        # self.ftps.context
        self.ftps.set_debuglevel(0)
        self.MQTTclient = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                    protocol=mqtt.MQTTv5,
                    transport=self.MQTTProtocol)
        self.MQTTclient.tls_set(ca_certs=self.ca_cert_path)
        self.isFTPConnected = False
        self.isMQTTConnected = False
        self.sending_in_progress = False
        self.SendStatus = False
        self.isSendDone = False
        self.SWType_list = ['FOTA_Master_Boot','FOTA_Master_App','FOTA_Client']
        self.Version_list = {
            'FOTA_Master_Boot': {
                'Major': 0,
                'Minor': 0
            },
            'FOTA_Master_App': {
                'Major': 0,
                'Minor': 0
            },
            'FOTA_Client': {
                'Major': 0,
                'Minor': 0
            }
        }
        self.SWTopic_list = ['SW/Jetson/FOTA_Master_Boot','SW/Jetson/FOTA_Master_App','SW/Jetson/FOTA_Client']
        # self.isReceiveResponse = False

    def startConnect(self):
        try:
            if not self.isFTPConnected:
                self.FTP_Connect()
            if not self.isMQTTConnected:
                self.MQTT_Connect()
            return True, ""
        except Exception as e:
            print("Failed to connect",e)
            return False, str(e)

    def __del__(self):
        self.FTP_Disconnect()

    def FTP_Connect(self):
        try:
            self.ftps.connect(self.host, self.FTPport)

            # print(self.ftps.getwelcome())
            # print(self.ftps.sock)

            self.ftps.auth()

            self.ftps.login(self.user, self.passwd, self.acct)

            self.ftps.set_pasv(True)
            self.ftps.prot_p()
            self.ftps.cwd("SW")
            self.isFTPConnected = True
        except:
            print("FTP Connect failed")
            return

    def FTP_Disconnect(self):
        if self.isFTPConnected == True:
            self.ftps.quit()
            self.isFTPConnected = False

    def MQTT_Connect(self):
        self.MQTTclient.username_pw_set(self.user, self.passwd)
        self.MQTTclient.connect(self.host,self.MQTTPort)
        self.MQTTclient.loop_start()
        for SWTopic in self.SWTopic_list:
            StatusCode = self.MQTTclient.subscribe(SWTopic,qos=1)
            # print(StatusCode)
        self.MQTTclient.on_message = self.MQTT_On_message
        self.isMQTTConnected = True

    def MQTT_Disconnect(self):
        # self.MQTTclient.loop_stop()
        if self.isMQTTConnected == True:
            self.MQTTclient.disconnect()
            self.isMQTTConnected = False

    def MQTT_On_message(self,client, userdata, message: mqtt.MQTTMessage):
        print(message.payload.decode())
        payload = message.payload.decode()
        topic = message.topic
        if topic == 'SWUpload':
            print('Upload: ',payload)
            if payload == 'Done':
                self.SendStatus = True
                self.isSendDone = True
            elif payload == "Fail":
                self.SendStatus = False
                self.isSendDone = True

            else:
                return
        # elif topic == 'SW/Jetson/FOTA_Master_Boot':
        #     self.MasterBoot_SW = payload
        # elif topic == 'SW/Jetson/FOTA_Master_App':
        #     self.MasterApp_SW = payload
        # elif topic == 'SW/Jetson/FOTA_Master_Client':
        #     self.Client_SW = payload
        elif topic in self.SWTopic_list:
            self.recvSW_Ver(payload)
        # self.MQTT_Disconnect()

    def recvSW_Ver(self,SWName):
        match = re.match(r"v_(.*)_v([\d]+)\.([\d]+)", SWName)
        if match == None:
            return 
        SWType,MajorVer,MinorVer = match.groups()
        if not SWType in self.SWType_list:
            return 
        self.Version_list[SWType]['Major'] = MajorVer
        self.Version_list[SWType]['Major'] = MajorVer
        # print('Version: ',self.Version_list)

    def getSW_Ver(self,SWType: str):
        if SWType in self.SWType_list:
            return self.Version_list[SWType]
        return None

    def isSendingInProgress(self):
        return self.sending_in_progress
    
    def SendSW(self, SWpath,SendSWCB):
        if self.sending_in_progress:
            SendSWCB(os.path.basename(SWpath), False)
            return

        self.sending_in_progress = True
        thread = threading.Thread(target=self._send_sw_thread, args=(SWpath, SendSWCB,))
        thread.start()


    def _send_sw_thread(self, SWpath,SendSWCB):
        connect_Status = self.startConnect()
        if connect_Status == False:
            SendSWCB(SWname,False)
            return 
        # self.isSendDone.clear()
        SWfile = os.path.basename(SWpath)
        SWname,SWextension = os.path.splitext(SWfile)
        print("Name: ",SWname)
        try:
            with open(SWpath, "rb") as SW:
                start_time = time.time()
                enc_SW = Security.Sign_Encrypt(SW.read())
                start_time_without_enc = time.time()
                enc_SW_IO = io.BytesIO(enc_SW)
                # print("Len: ",len(enc_SW))
                self.ftps.storbinary("STOR " + SWname, enc_SW_IO)
                end_time = time.time()
                print(f'send time: {end_time-start_time}')
                print(f'send enc time: {end_time-start_time_without_enc}')
                self.FTP_Disconnect()
                self.MQTTclient.publish('SWUpload', SWname, qos=2)
                status = self.MQTTclient.subscribe('SWUpload', qos=2)
                # print('Sub status: ',status)
                # self.MQTTclient.loop_forever()
                startTimeout = time.time()
                while self.isSendDone == False:
                    if time.time() - startTimeout > 60:
                        break
                SendSWCB(SWname,self.SendStatus)
                self.SendStatus = False
                self.isSendDone = False
        except Exception as e:
            print("Send error: ", e)
            SendSWCB(SWname, False)
        finally:
            self.sending_in_progress = False
            self.FTP_Disconnect()
            self.MQTT_Disconnect()

    def _wait_for_upload_status(self):
        self.isSendDone.wait()  # This will block until the MQTT message is received
        if self.isSendDone.is_set():
            print("Upload succeeded")
        else:
            print("Upload failed")

import paho.mqtt.client as mqtt
import time
import random
import json
import datetime
#from Security import Security

MQTTClient = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                    protocol=mqtt.MQTTv5,
                    transport='tcp')

# MQTTClient = mqtt.Client()

MQTTClient.tls_set(ca_certs=r'C:\Users\HOB6HC\Code_Source\FOTA_Station_Up1-main\App\ca.crt')

def getISODatestring():
    now = datetime.datetime.now()
    # print(now)
    ISODate_String = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z'
    # print(ISODate_String)
    return ISODate_String


MQTTClient.username_pw_set('user1','123456')
MQTTClient.connect('begvn.home',8883)
MQTTClient.loop_start()
data = {
    'deviceId': 'jetson',
    'Accelerator': {
        'x': random.randint(10,1000),
        'y': random.randint(10,1000),
        'z': random.randint(10,1000)
    },
    'Gyroscope': {
        'x': random.randint(10,1000),
        'y': random.randint(10,1000),
        'z': random.randint(10,1000)
    },
    'Orientation': {
        'yaw': random.randint(-180, 180),
        'pitch': random.randint(-90, 90),
        'roll': random.randint(-180, 180)
    },
    'recordTime': '2024-08-06T04:00:31.477Z'
}
date = getISODatestring()
print(date)
try:
    for i in range(0,1000):
        if i % 10 ==0:
            data['Orientation']['yaw'] = random.randint(-50,50)
        data['Orientation']['pitch'] = 0
        data['Orientation']['roll'] = 0
        data['Accelerator']['x'] = random.randint(-50,50)
        data['Accelerator']['y'] = random.randint(-50,50)
        data['Accelerator']['z'] = random.randint(-50,50)
        data['Gyroscope']['x'] =   random.randint(10,1000)
        data['Gyroscope']['y'] =   random.randint(10,1000)
        data['Gyroscope']['z'] =   random.randint(10,1000)
        # data['Orientation'] = data['Accelerator']
        data['Gesture'] = data['Gyroscope']        
        # getTime = time.time()
        data['recordTime'] = getISODatestring()
        # recvTime = time.time()
        # print('Get time: ',recvTime - getTime)
        dataJSON = json.dumps(data).encode('utf-8')
        # print("Len: ",len(dataJSON))
        # print(dataJSON)
        # enc_data = Security.Sign_Encrypt_SW(dataJSON)
        # break
        status = MQTTClient.publish('jetson/jetsonano/imu',dataJSON,
                        qos=1)
                        
        # # print('publishing')
        time.sleep(0.01)
    # status = MQTTClient.publish('jetson/jetsonano/imu','end',
    #                     qos=1)
    print('End pub', time.time(), status)
except Exception as e:
    # MQTTClient.loop_stop()
    # exit()
    print('Error: ',e)
    pass
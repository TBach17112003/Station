# Why use Singleton --> Use to access many same variables, like sensor values
# What is Singleton --> Mean there is only ONE instance created during running program
# Singleton implementation
class DataStore:
    _instance = None
    
    #cls represent for current class, when call __new__, python will make this class to be first instance
    def __new__(cls): #create a new instance of class
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.reset()
        return cls._instance #return new instance
    
    def reset(self):
        self.yaw = 0
        self.pitch = 0
        self.roll = 0
        self.accel_x = 0
        self.accel_y = 0
        self.accel_z = 0
        self.gyro_x = 0
        self.gyro_y = 0
        self.gyro_z = 0
        self.battery_status = 100
        self.battery_temp = 0
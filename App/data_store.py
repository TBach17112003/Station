class DataStore:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.reset()
        return cls._instance
    
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
        self.battery = 0
        self.temperature = 0

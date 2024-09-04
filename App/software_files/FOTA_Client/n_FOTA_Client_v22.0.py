import sys
import hub
from hub import port         # Port module to set / get Port from LEGO hub
from hub import display      # Display module to control LEGO hub Display Screen
from hub import Image        # Image module to use built-in image
from hub import button       # To use Button on LEGO hub
from hub import led          # To control LED on LEGO hub
from hub import motion       # For current motion status on LEGO hub
from hub import sound
from hub import USB_VCP
from utime import sleep_ms, ticks_ms  # Import delay function and ticks for timing
import mindstorms
from mindstorms import *
import micropython

MotorA = port.A.motor        # MotorA defines the port A of Hub
MotorB = port.B.motor        # MotorB defines the port B of Hub
MotorB.default(max_power = 100, stop = 2)



while True:
    MotorB.run_at_speed(-10)
    sleep_ms(2000)
    MotorB.pwm(0)
    sleep_ms(2000)    

 

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
# Setup Ports, Motors, Sensors
MotorA = port.A.motor        # MotorA defines the port A of Hub
MotorB = port.B.motor        # MotorB defines the port B of Hub
MotorB.default(max_power = 50, stop = 2)

# Setup necessary Variables
command = bytes([])
message = bytes([])
new_SW = False          #Check new SW available
safe_State = True       #Safe_State for flashing new SW
start_time = ticks_ms() #Initialize Start time
motor_running = False   #Check if any motor is busy
motor_end_time = 0      #The limit time for running car to stop
angle = 0               #Setup Angle for reset and go forward
direct = 0
safe_period = 0         #Set time to maintain Safe_state
vcp = USB_VCP(0)        #Set USB Virtual ComPort
vcp.setinterrupt(-1)

while True:
    MotorB.run_for_time(300, speed = -50)
    sleep_ms(400)


 

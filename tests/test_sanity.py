import os
import can
import numpy as np
import time

import core.CANHelper
from core.CanJointMotor import CanJointMotor
from core.CanScrewMotor import CanScrewMotor
from core.CanUJoint import CanUJoint
from core.CanArduinoSensors import CanArduinoSensors

if __name__ == "__main__":
  core.CANHelper.init("can0")
  
  can0 = can.ThreadSafeBus(channel='can0', bustype='socketcan')
  # deviceId = 0x01
  # sensor = CanArduinoSensors(can0, deviceId)

  # screw1 = CanScrewMotor(can0, 0x141)
  joint1 = CanUJoint(can0, 0x141)
  # joint2 = CanUJoint(can0, 0x143)

  try:
  
    for _ in range(1000):
        # print('screw1',screw1.read_position())
        print('joint1',joint1.read_position())
        #print('joint2',joint2.read_position())
        # print(sensor.readHumidityAndTemperature())
        time.sleep(0.1)

  except (KeyboardInterrupt, ValueError) as e: # Kill with ctrl + c
    print(e)

  # screw1.motor_stop()
  joint1.motor_stop()
  #joint2.motor_stop()

  core.CANHelper.cleanup("can0")
import can
import core.CANHelper
from core.CanUJoint import CanUJoint
from core.CanScrewMotor import CanScrewMotor
import time
import matplotlib.pyplot as plt

if __name__ == "__main__":
  core.CANHelper.init("can0") # Intiailize can0
  can0 = can.ThreadSafeBus(channel='can0', bustype='socketcan') # Create can bus object 

  testMotor = CanUJoint(can0, 0, 1) # Initialize motor with can bus object 
  # testMotor.speed_ctrl(2*2*3.14)

  # time.sleep(2)
  # testMotor.motor_stop()
  # time.sleep(2)

  t = []
  y = []
  startTime = time.time()
  try:
    while True:
      ElapsedTime = time.time()-startTime
      t.append(ElapsedTime)
      y.append(testMotor.read_speed())  
      time.sleep(0.01)
     

  except(KeyboardInterrupt) as e:
    print(e)

  testMotor.motor_stop()

  print('Done')

  plt.plot(t, y)
  plt.ylabel('Speed (rad/s)')
  plt.xlabel('Time(s)')
  plt.show()
  core.CANHelper.cleanup("can0")
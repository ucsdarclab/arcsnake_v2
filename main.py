import os
import can
import math
import time
import matplotlib.pyplot as plt
from datetime import datetime
from pyinstrument import Profiler

from CanMotor import CanMotor
from CanUtils import CanUtils

def init():
    os.system('sudo ifconfig can0 down')
    os.system('sudo ip link set can0 type can bitrate 1000000')
    os.system('sudo ifconfig can0 up')

def cleanup():
    os.system('sudo ifconfig can0 down')

def profile(screw):
    profiler = Profiler()
    profiler.start()

    for i in range(1000):
        screw.pos_ctrl(0x00, 0x41, 0x00, 0x00)
        screw.read_encoder()

    profiler.stop()
    print(profiler.output_text(unicode=True, color=True))

if __name__ == "__main__":
    init()

    screw = CanMotor()
    utils = CanUtils()
    
    start = datetime.now()
    x = []
    y = []
    z = []
    time.sleep(5)

    for i in range(800):
        try:
            time_since_start = datetime.now() - start
            x.append(time_since_start.total_seconds())
            
            to_pos = (-1) ** (2/(1/10*time_since_start.total_seconds())) * 2 * math.pi
            print(to_pos)

            z.append(to_pos)
            screw.pos_ctrl(to_pos)

            (_, speed, _) = screw.read_motor_status()
            y.append(speed)

            loop_dur = datetime.now() - start - time_since_start
            # 10ms for each loop
            time.sleep(max(0, 0.01 - loop_dur.total_seconds()))
        except (KeyboardInterrupt, ValueError) as e:
            print(e)
            break

    screw.motor_stop()
    plt.plot(x,y,'b-')
    plt.plot(x,z,'r-')
    
    plt.xlabel('time (s)')
    plt.ylabel('speed (rad/s)')
    plt.legend(["encoder speed", "set speed"])
    plt.show()

    cleanup()
from asyncore import loop
from audioop import mul
from cProfile import run
from doctest import run_docstring_examples
from os.path import dirname, realpath
from pdb import post_mortem
import sys
from unittest import mock

from more_itertools import sample
arcsnake_v2_path = dirname(dirname(realpath(__file__)))
sys.path.append(arcsnake_v2_path)

import os
import can
import math as m
import numpy as np
import time
import matplotlib.pyplot as plt
from datetime import datetime
from pyinstrument import Profiler

import core.CANHelper
from core.CanUJoint import CanUJoint
from core.CanMotor import CanMotor
from core.CanScrewMotor import CanScrewMotor


if __name__ == "__main__":
    core.CANHelper.init("can0")
    can0 = can.ThreadSafeBus(channel='can0', bustype='socketcan')

    gear_ratio = 11
    joint1 = CanMotor(can0, 1, gear_ratio)
    joint2 = CanMotor(can0, 3, gear_ratio)
    joint3 = CanMotor(can0, 4, gear_ratio)
    joint4 = CanMotor(can0, 6, gear_ratio)
    screw1 = CanMotor(can0, 0, 1)
    screw2 = CanMotor(can0, 2, 1)
    screw3 = CanMotor(can0, 5, 1)
    
    try:

        input('Press Enter to hold joints at current pos')
        (joint1_torque, joint1_speed, joint1_pos) = joint1.read_motor_status() # read pos
        (joint2_torque, joint2_speed, joint2_pos) = joint2.read_motor_status() # read pos
        (joint3_torque, joint3_speed, joint3_pos) = joint3.read_motor_status() # read pos
        (joint4_torque, joint4_speed, joint4_pos) = joint4.read_motor_status() # read pos
        print('Joint 1 pos: ', joint1_pos)
        print('Joint 2 pos: ', joint2_pos)
        print('Joint 3 pos: ', joint3_pos)
        print('Joint 4 pos: ', joint4_pos)
        joint1.pos_ctrl(joint1_pos) # set read pos
        joint2.pos_ctrl(joint2_pos) # set read pos
        joint3.pos_ctrl(joint3_pos) # set read pos
        joint4.pos_ctrl(joint4_pos) # set read pos

        input('Press Enter to spin screw motors')
        screw1.speed_ctrl(1)
        screw2.speed_ctrl(-1)
        screw3.speed_ctrl(1)

    except(KeyboardInterrupt) as e:
        print(e)

    joint1.motor_stop()
    joint2.motor_stop()
    joint3.motor_stop()
    joint4.motor_stop()
    screw1.motor_stop()
    screw2.motor_stop()
    screw3.motor_stop()

    print('Done')

    core.CANHelper.cleanup("can0")

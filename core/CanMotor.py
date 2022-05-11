import can
import math
from .CanUtils import CanUtils
from .timeout import timeout
import time

class CanMotor(object):
    def __init__(self, bus, motor_id, gear_ratio, MIN_POS = -999 * 2 * math.pi, MAX_POS = 999 * 2 * math.pi):
        """Intializes motor with CAN communication 
        -

        Args:
            bus (can0 or can1): CAN Bus that the motor is connected to
            motor_id (int) Set motor_id from 0-31. Can be determined by decimal number of the dip switches 
                Ex: If the dip switches are set to 0000, the motor_id would be 0. Since 0000 in binary to decimal is 0. 
            gear_ratio (int): Set gear ratio between motor -> output. 
                Ex: RMD X8 Motor has a 6:1 planteary gear ratio so this value would be 6
            MIN_POS (RAD, optional): Set MIN_POS of motor. Used in pos_ctrl function. Defaults to -999*2*math.pi.
            MAX_POS (RAD, optional): Set MAX_POS of motor. Used in pos_ctrl function. Defaults to 999*2*math.pi.
        """        
        self.canBus = bus
        self.utils = CanUtils()
        self.gear_ratio = gear_ratio
        id = "0x"
        id += (str(141 + motor_id))
        self.id = eval(id)
        self.min_pos = MIN_POS
        self.max_pos = MAX_POS

        # For some reason, the screw motor in one our debug sessions
        # required two of these to be sent in order to recieve new commands...
        self.motor_start()
        self.motor_start()

        self.motor_stop()
    

    '''
    Basic CANBus send command:
        - data is of the form: [0x{Register}, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            - To convert a 32 unsigned integer to bytes for this, use toBytes in CanUtils
        - If wait_for_response is True, then this a "read" CANBus send. If False, then this is only a "send" command
            - To decode the return message, use readBytesList or readByte in CanUtils
    '''
    @timeout(1)
    def send(self, data, wait_for_response = False):
        msg = can.Message(arbitration_id=self.id, data=data, is_extended_id=False)
        self.canBus.send(msg)

        if wait_for_response:
            while True:
                # Checking canbus message recieved with keyboard interrupt saftey
                try:
                    msg = self.canBus.recv()
                    if msg.arbitration_id == self.id:
                        break
                except (KeyboardInterrupt, ValueError) as e:
                    print(e)
                    break
            return msg
        else:
            return None



    def read_motor_err_and_voltage(self):
        msg = self.send([0x9a, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], wait_for_response=True)

        temp      = msg.data[1]
        voltage   = self.utils.readBytes(msg.data[4], msg.data[3]) / 10
        err_state = msg.data[7]

        return (temp, 
                voltage, 
                err_state)

    '''
    returns motor encoder readings in units of:
    torque current 
        bit range: -2048~2048 ==> real range: -33A~33A
    speed
        1 degree/s/LSB ==> 1 rad/s/LSB
    position
        14-bit range: 0~16383 deg ==> rad
    '''
    def read_motor_status(self, returnTime = False):
        """Reads motor Torque, Speed, and Position from the motor.
        -

        Returns:
            (AMPs, RAD/S, RAD): Returns tuple of motor torque, speed, and position
        """
        msg = self.send([0x9c, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], wait_for_response=True)

        # encoder readings are in (high byte, low byte)
        torque   = self.utils.readBytes(msg.data[3], msg.data[2])
        speed    = self.utils.readBytes(msg.data[5], msg.data[4]) / self.gear_ratio
        position = self.utils.readBytes(msg.data[7], msg.data[6]) / self.gear_ratio

        if returnTime:
            return (self.utils.encToAmp(torque), 
                self.utils.degToRad(speed), 
                self.utils.degToRad(self.utils.toDegrees(position)), time.time())
        else:
            return (self.utils.encToAmp(torque), 
                self.utils.degToRad(speed), 
                self.utils.degToRad(self.utils.toDegrees(position)))
        


    def read_singleturn_position(self):
        """ Get single-turn position reading from encoder in radians. 
        -
        """
        (_, _, p) = self.read_motor_status()
        return p

    def read_raw_position(self):
        """Get raw position of encoder from -32768 to 32768 
        -
        """        
        msg = self.send([0x9c, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], wait_for_response=True)
        position = self.utils.readBytes(msg.data[7], msg.data[6]) 
        return position


    def read_multiturn_position(self):
        ''' Get multi-turn position reading from encoder in radians
        -
        '''
        msg = self.send([0x92, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], wait_for_response=True)
        
        # CANNOT USE msg.data directly because it is not iterable for some reason...
        # This is a hack to fix the bug
        byte_list = []
        for idx in range(1, 8):
            byte_list.append(msg.data[idx])
        byte_list.reverse()
        decimal_position = self.utils.readBytesList(byte_list)

        # Note: 0.01 scale is taken from dataset to convert multi-turn bits to degrees
        return self.utils.degToRad(0.01*decimal_position/self.gear_ratio)

    def read_speed(self):
        ''' Get speed reading from the encoder in rad/s
        -
        '''
        (_, s, _) = self.read_motor_status()
        return s
    

    def read_torque(self):
        ''' Get torque reading from the encoder in Amps
        -
        '''
        (t, _, _) = self.read_motor_status()
        return t

    def read_motor_pid(self):
        ''' Returns P and I values for pos, speed, and torque, can't get 'd' for some reason
        -

        Returns:
            (pos_p, pos_i, speed_p, speed_i, torque_p, torque_i): Returns tuple of P and I values
        '''
        msg = self.send([0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], wait_for_response=True)

        pos_p    = msg.data[2]
        pos_i    = msg.data[3]
        speed_p  = msg.data[4]
        speed_i  = msg.data[5]
        torque_p = msg.data[6]
        torque_i = msg.data[7]

        return (pos_p,    pos_i, 
                speed_p,  speed_i,
                torque_p, torque_i)

 
    def pos_ctrl(self, to_rad, max_speed = 999 * 2 * math.pi):
        """Set multiturn position control
        -

        Args:
            to_rad (RAD): Desired multi-turn angle in Radians
            max_speed (RAD/s, optional): Set max speed in rad/s. Defaults to 999*2*math.pi.
        """        
        if (to_rad < self.min_pos):
            to_rad = self.min_pos
        
        if (to_rad >= self.max_pos):
            to_rad = self.max_pos
        
        # The least significant bit represents 0.01 degrees per second.
        to_deg = 100 * self.utils.radToDeg(to_rad) * self.gear_ratio
        max_speed = self.utils.radToDeg(max_speed) * self.gear_ratio

        s_byte1, s_byte2 = self.utils.int_to_bytes(int(max_speed), 2)

        byte1, byte2, byte3, byte4 = self.utils.int_to_bytes(int(to_deg), 4)

        self.send([0xa4, 0x00, s_byte2, s_byte1, byte4, byte3, byte2, byte1])

    def override_PI_values(self, pos_p = None, pos_i = None, speed_p = None, speed_i = None, torque_p = None, torque_i = None): #UNTESTED!!!
        """Overrites the specified P and I values in the ROM with new values. Still valid for next boot.
        -
        """        
        # read other values first
        msg = self.send([0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], wait_for_response=True) 
        if (pos_p is None):
            pos_p = msg.data[2]
        if (pos_i is None):
            pos_i = msg.data[3]    
        if (speed_p is None):
            speed_p = msg.data[4]
        if (speed_i is None):
            speed_i = msg.data[5] 
        if (torque_p is None):
            torque_p = msg.data[6]
        if (torque_i is None):
            torque_i = msg.data[7]

        self.send([0x32, 0x00, pos_p, pos_i, speed_p, speed_i, torque_p, torque_i])

    def set_PI_values(self, pos_p = None, pos_i = None, speed_p = None, speed_i = None, torque_p = None, torque_i = None): #UNTESTED!!!
        """Overrites the specified P and I values in the RAM with new values. Lost on reboot.
        -
        """        
        # read other values first
        msg = self.send([0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], wait_for_response=True)
        if (pos_p is None):
            pos_p = msg.data[2]
        if (pos_i is None):
            pos_i = msg.data[3]    
        if (speed_p is None):
            speed_p = msg.data[4]
        if (speed_i is None):
            speed_i = msg.data[5] 
        if (torque_p is None):
            torque_p = msg.data[6]
        if (torque_i is None):
            torque_i = msg.data[7]

        self.send([0x31, 0x00, pos_p, pos_i, speed_p, speed_i, torque_p, torque_i])

    def speed_ctrl(self, to_rad, max_speed=20*2*math.pi):
        """Set speed in rad/s 
        -

        Args:
            to_rad (RAD): Set speed
            max_speed (RAD/s, optional): Set max allowable speed. Defaults to 20*2*math.pi.

        Returns:
            RAD/s: Returns current speed
        """        
        if to_rad > max_speed:
            to_rad = max_speed
        if to_rad < -max_speed:
            to_rad = -max_speed

        to_dps = self.gear_ratio * 100 * self.utils.radToDeg(to_rad)
        byte1, byte2, byte3, byte4 = self.utils.int_to_bytes(int(to_dps), 4)
        msg = self.send([0xa2, 0x00, 0x00, 0x00, byte4, byte3, byte2, byte1], wait_for_response=True)
        return self.utils.degToRad(self.utils.readBytes(msg.data[5], msg.data[4])) / self.gear_ratio

    def torque_ctrl(self, to_Amp): # ONLY SORTA TESTED!!
        """Set the torque current output of the motor from -32A to 32A

        Args:
            to_Amp (AMP): Set torque current of motor
        """        
        if to_Amp > 32:
            to_Amp = 32
        if to_Amp < -32:
            to_Amp = -32

        to_Amp *= 2000/32 # Value range is -2000 to 2000
        byte1, byte2 = self.utils.int_to_bytes(int(to_Amp), 2)

        self.send([0xa1, 0x00, 0x00, 0x00, byte2, byte1, 0x00, 0x00])

    def setmultiTurnZeroOffset(self, offset, InvertDirection = None): # NOT COMPATIBLE WITH V1.6 MOTOR FIRMWARE!!
        byte1, byte2, byte3, byte4, byte5, byte6 = self.utils.int_to_bytes(offset, 6)

        if InvertDirection is None:
            self.send([0x63, byte6, byte5, byte4, byte3, byte2, byte1, 1], wait_for_response=True)
        else:
            self.send([0x63, byte6, byte5, byte4, byte3, byte2, byte1, 0], wait_for_response=True)
    

    def read_multiTurnZeroOffset(self): # NOT COMPATIBLE WITH V1.6 MOTOR FIRMWARE!!
        msg = self.send([0x22, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], wait_for_response=True)
        
        # CANNOT USE msg.data directly because it is not iterable for some reason...
        # This is a hack to fix the bug
        byte_list = []
        for idx in range(1, 6):
            byte_list.append(msg.data[idx])
        byte_list.reverse()
        
        return self.utils.readBytesList(byte_list)

    def motor_start(self):
        """Starts the motor 
        -
        """
        self.send([0x88, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], wait_for_response=True)
    
    def motor_stop(self):
        """Stops the motor. Useful for allowing motor to be turned by hand
        -
        """
        self.send([0x81, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], wait_for_response=True)
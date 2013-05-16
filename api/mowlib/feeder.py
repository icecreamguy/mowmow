import config
import time
import serial
from serial.serialutil import SerialException, portNotOpenError

class feeder():
    # Support for different types of shitty feeder hardware!
    feeder_type = config.feeder_type
    serial_port = serial.Serial()
    def init(self):
        if self.serial_port.isOpen():
            print("Using existing serial connection")
        else:
            self.serial_port.baudrate = 115200
            self.serial_port.port = config.serial_port
            try:
                print("initializing serial port")
                self.serial_port.open()
                print("port initialized")
            except (SerialException, portNotOpenError):
                return "Serial port unavailable!"
            else:
                print("sleeping")
                time.sleep(2)
    def shutdown(self):
        print("shutting down serial port")
        try:
            self.serial_port.close()
        except (SerialException, portNotOpenError):
            return "Serial port unavailable!"
        else:
            return "OK"
    def feed(self):
        self.init()
        print("Activating feeder")
        if self.feeder_type == 'arduino':
            # My little code chunk is in slot 4 of the Arduino comm struct, just # need to send "4;" to the device to activate it
            if self.serial_port.isOpen():
                self.serial_port.write('4;')
            else:
                return "Serial port not open!"
        elif self.feeder_type == 'sain_relay':
            # Open and close the relay 4 times - this will press the "test feed"
            # on my commercial pet feeder
            self.serial_port.write('\xff\x01\x01')
            time.sleep(1)
            self.serial_port.write('\xff\x01\x00')
            time.sleep(1)
            self.serial_port.write('\xff\x01\x01')
            time.sleep(1)
            self.serial_port.write('\xff\x01\x00')
        return self.shutdown()

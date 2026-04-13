#!python3
from ast import arg
import serial
from serial.serialutil import SerialException
from sys import argv
from time import sleep
import glob
import os
from zaber.serial import AsciiDevice, AsciiSerial

ntc_read_cmd = "S\n" # reads temperature from channel 0. will be A number if it's an ntc arduino
daq_read_cmd = "T:0\n" # reads loop delay. will also work on ntc arduino. so that one is filtered out first
nan = float("nan")

def is_zaber_stage(port : str) -> bool:
    # cheks whether the given port has a zaber stage attached to it
    # key criterion: zaber_serial library can connect to it and get some params
    try:
        port_obj = AsciiSerial(port)

        try:
            dev = AsciiDevice(port_obj, 1)
            axis = dev.axis(1)
            axis.get_position()
            port_obj.close()
            return True
        except Exception as _:
            pass
            port_obj.close()
    except Exception as __:
        pass
    return False


def is_ntc_arduino(port: str) -> bool:
    # ntc arduino will respond to a serial connection and
    # report some value for temeperature measure command
    try:
        serial_port = serial.Serial(port, 115200, timeout=2)
        __ = serial_port.read() # cleans the serial buffer from old junk
        serial_port.write(ntc_read_cmd.encode())
        sres = serial_port.readline().decode("utf-8")
        res = float(sres)
        serial_port.close()
        if res != nan:
            return True
    except Exception as _:
        pass
    return False


def is_daq_board(port: str) -> bool:
    # daq board arduino will respond to a serial con and... well that's a good question i guess
    try:
        serial_port = serial.Serial(port, 115200, timeout=2)
        __ = serial_port.read() # cleans the serial buffer from old junk
        serial_port.write(daq_read_cmd.encode())
        sres = serial_port.readline().decode("utf-8")
        res = float(sres)
        serial_port.close()
        if res != nan:
            return True
    except Exception as _:
        pass
    return False


def categorize_port(port: str) -> str:
    # first check if port has zaber stage, then ntc and daq arduinos
    if is_zaber_stage(port):
        #print(f"-> found zaber stage on {port}")
        return "zaber"
    if is_ntc_arduino(port):
        #print(f"-> found ntc arduino on {port}")
        return "ntc"
    if is_daq_board(port):
        #print(f"-> found daq arduino on {port}")
        return "daq"
    return "other"


def main():
    #portlist = ["/dev/ttyUSB" + str(i) for i in range(16)] # do theses exist even sometimes?
    portlist = glob.glob("/dev/serial/by-id/*")

    devices = {
        "zaber" : "",
        "ntc": "",
        "daq": "",
        "other": ""
    }

    for port in portlist:
        #print(f"checking {port}")
        devices[categorize_port(port)] = port

    # print(devices)

    config = {
        "daq": "Arduino-Readout-Board",
        "ntc": "Arduino-NTC-Readout",
        "zaber": "Zaber-Controller-X-MCC3"
    }

    for device in devices:
        if device == "other":
            continue
        if devices[device] == "":
            print(f"{device} not found")
            continue
        if "link" in argv:
            print(f"symlinking {devices[device]} to {config[device]}")
            os.symlink(f"/dev/serial/by-id/{devices[device]}", f"/dev/{config[device]}")
        elif "shell" in argv:
            print(f"ln -s {devices[device]} /dev/{config[device]}")


if __name__ == "__main__":
    main()

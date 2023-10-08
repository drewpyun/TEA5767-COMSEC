#!/usr/bin/env python3
# run sudo i2cdetect -y 1 to find the I2C address of the receiver
# used for testing the control of the receiver using TEA5767 on the raspberry pi through I2C

import smbus2
import subprocess
import time
import curses

# I2C setup
i2c = smbus2.SMBus(1)
i2c_address = 0x60
high_cut_enabled = False
low_cut_enabled = False

def init_radio(address):
    i2c.write_byte(address, 0)
    time.sleep(0.1)

def set_freq(address, freq):
    global high_cut_enabled, low_cut_enabled
    freq14bit = round(int(4 * (freq * 1000000 + 225000) / 32768), 1)
    freqH = freq14bit >> 8
    freqL = freq14bit & 0xFF

    data = [freqL, 0xB0, 0x10, 0x00]

    if high_cut_enabled:
        data[2] |= 0x04
    if low_cut_enabled:
        data[2] |= 0x08

    try:
        i2c.write_i2c_block_data(address, freqH, data)
        print(f"Frequency set to {freq} MHz\r", end='')
    except IOError:
        subprocess.call(['i2cdetect', '-y', '1'])
        print("Error setting frequency\r", end='')

def mute(address):
    data = [0x00, 0x00, 0x00, 0x00]
    try:
        i2c.write_i2c_block_data(address, 0x80, data)
        print("Muted\r", end='')
    except IOError:
        subprocess.call(['i2cdetect', '-y', '1'])
        print("Error muting\r", end='')

if __name__ == '__main__':
    init_radio(i2c_address)
    frequency = 101.1

    stdscr = curses.initscr()
    curses.noecho()

    try:
        while True:
            c = stdscr.getch()
            if c == ord('w'):
                frequency += 1
                set_freq(i2c_address, frequency)
            elif c == ord('s'):
                frequency -= 1
                set_freq(i2c_address, frequency)
            elif c == ord('e'):
                frequency += 0.1
                set_freq(i2c_address, frequency)
            elif c == ord('d'):
                frequency -= 0.1
                set_freq(i2c_address, frequency)
            elif c == ord('h'):
                high_cut_enabled = not high_cut_enabled
                set_freq(i2c_address, frequency)
            elif c == ord('l'):
                low_cut_enabled = not low_cut_enabled
                set_freq(i2c_address, frequency)
            elif c == ord('m'):
                mute(i2c_address)
            elif c == ord('u'):
                set_freq(i2c_address, frequency)
            elif c == ord('q'):
                mute(i2c_address)
                curses.endwin()

    except KeyboardInterrupt:
        pass
    finally:
        curses.endwin()
#!/usr/bin/env python3

import smbus2
import subprocess
import time
import curses

i2c = smbus2.SMBus(1)
i2c_address = 0x60

high_cut_enabled = False
low_cut_enabled = False

def init_radio(address):
    i2c.write_byte(address, 0)
    time.sleep(0.1)

def set_freq(address, freq):
    global high_cut_enabled, low_cut_enabled
    freq = round(freq, 1)
    freq14bit = int(round(4 * (freq * 1e6 + 225000) / 32768))
    freqH = freq14bit >> 8
    freqL = freq14bit & 0xFF
    
    data = [0, 0xB0, 0x10, 0x00]
    if high_cut_enabled:
        data[2] |= 0x04
    if low_cut_enabled:
        data[3] |= 0x08

    try:
        i2c.write_i2c_block_data(address, freqH, data)
        print("Frequency set to {} MHz".format(freq), end="\r")
    except IOError:
        subprocess.call(['i2cdetect', '-y', '1'])
        print("Error setting frequency", end="\r")

def mute(address):
    data = [0, 0xB0, 0x10, 0x00]
    try:
        i2c.write_i2c_block_data(address, 0x80, data)
        print("Muted", end="\r")
    except IOError:
        subprocess.call(['i2cdetect', '-y', '1'])
        print("Error muting", end="\r")

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
            elif c == ord('m'):
                mute(i2c_address)
            elif c == ord('h'):
                high_cut_enabled = not high_cut_enabled
                set_freq(i2c_address, frequency)
            elif c == ord('l'):
                low_cut_enabled = not low_cut_enabled
                set_freq(i2c_address, frequency)
            elif c == ord('q'):
                mute(i2c_address)
                curses.endwin()
                break
    except KeyboardInterrupt:
        pass
    finally:
        curses.endwin()

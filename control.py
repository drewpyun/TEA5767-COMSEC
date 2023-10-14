#!/usr/bin/env python3
# run "sudo i2cdetect -y 1" to find the I2C address of the receiver
# used for testing the control of the receiver using TEA5767 on the raspberry pi through I2C
# meant to run on the raspberry pi -- as such will not work on Windows, untested on Mac 

import smbus2  # Import SMBus module of I2C
import subprocess  # To run shell commands
import time  # Import time module
import curses  # Import curses module to get keyboard input

# I2C setup
i2c = smbus2.SMBus(1)  # SMBVus instance (1 for newer Pi's usually)
i2c_address = 0x60  # I2C Accress of the TEA5767 usually
high_cut_enabled = False  # High-cut control flag
low_cut_enabled = False  # Low-cut control flag 

# Initialize the radio by writing a byte to the I2C address
def init_radio(address):  
    i2c.write_byte(address, 0)  # Write 0 to initiate I2C comms
    time.sleep(0.1)  # Wait 100ms for the radio to initialize

# Set the frequency of the radio
def set_freq(address, freq):
    global high_cut_enabled, low_cut_enabled  # Use global variables
    freq = round(freq, 1)  # necessary for python logic where the float has trailing numbers
    freq14bit = round(int(4 * (freq * 1000000 + 225000) / 32768), 1)  # Calculate the 14-bit frequency word
    freqH = freq14bit >> 8  # Extract high 8 bits
    freqL = freq14bit & 0xFF  # Extract low 8 bits

    # Base configuration byte array
    data = [freqL, 0xB0, 0x10, 0x00]  

    # If high-cut or low-cut is enabled, set the appropriate bit
    if high_cut_enabled:
        data[2] |= 0x04
    if low_cut_enabled:
        data[2] |= 0x08

    try:  # Try to write the data to the I2C address
        i2c.write_i2c_block_data(address, freqH, data)
        print(f"Frequency set to {freq} MHz\r", end='')
    except IOError:  #  Handle I/O Errors
        subprocess.call(['i2cdetect', '-y', '1'])
        print("Error setting frequency\r", end='')

# Mute the radio
def mute(address):
    data = [0x00, 0x00, 0x00, 0x00]  # Data to mute
    try:
        i2c.write_i2c_block_data(address, 0x80, data)
        print("Muted\r", end='')
    except IOError:
        subprocess.call(['i2cdetect', '-y', '1'])
        print("Error muting\r", end='')

# Main function
if __name__ == '__main__':
    init_radio(i2c_address)  # Initialize the radio
    frequency = 106.7  # Set the initial frequency   

    # Initialize curses for keyboard input
    stdscr = curses.initscr()
    curses.noecho()

    try:
        while True:
            c = stdscr.getch()  # Get keyboard input
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
                curses.endwin()  # End curses

    except KeyboardInterrupt:  # Handle keyboard interrupt
        pass
    finally:
        curses.endwin()  # End curses on exit
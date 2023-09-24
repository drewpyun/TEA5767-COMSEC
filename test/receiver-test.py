#!/usr/bin/env python3
# run sudo i2cdetect -y 1 to find the I2C address of the receiver
# used for testing the control of the receiver using TEA5767 on the raspberry pi through I2C
import smbus2 # used for I2C communication
import subprocess # used for calling the i2cdetect command and getting the I2C address
import time # used for sleeping between commands to the receiver
import curses # used for getting user input from the terminal
import curses.textpad # used for getting user input from the terminal

# I2C channel 1 is connected to the GPIO pins
i2c = smbus2.SMBus(1) # create an I2C object
i2c_address = 0x60 # common address for raspberry pi

# initialize the receiver
def init_radio(address):
    i2c.write_byte(address, 0)
    time.sleep(0.1)

# set the frequency of the receiver
def set_freq(address, freq):
    freq = round(freq, 1)
    freq14bit = round(int(4 * (freq * 1000000 + 225000) / 32768), 1) # calculate the 14 bit frequency
    freqH = freq14bit >> 8 # get the high byte -- stores the most significant 8 bits of the frequency -- int (freq14bit / 256)
    freqL = freq14bit & 0xFF # get the low byte -- stores the least significant 8 bits of the frequency

    data = [0 for i in range(4)] # Descriptions of the 4 bytes sent to the receiver - viz. catalog sheets
    init = freqH
    data[0] = freqL # set the first byte to the low byte of the frequency
    data[1] = 0xB0 # set the second byte to 0xB0 - #0b10110000
    data[2] = 0x10 # set the third byte to 0x00  - #0b00010000
    data[3] = 0x00 # set the fourth byte to 0x10 - #0b00000000
    try:
        i2c.write_i2c_block_data(address, init, data) # write the data to the receiver
        print("Frequency set to " + str(freq) + " MHz\r")
    except IOError:
        subprocess.call(['i2cdetect', '-y', '1']) # print the I2C address if there is an error
        print("Error setting frequency\r")

# sets the freequency to 0 MHz and uses the mute bit to mute the receiver
def mute(address, freq):
    freq14bit = int(4 * (freq * 1000000 + 225000) / 32768) # calculate the 14 bit frequency
    freqL = freq14bit & 0xFF # get the low byte
    data = [0 for i in range(4)] # create a list of 4 bytes to send to the receiver to set the frequency
    init = 0x80
    data[0] = freqL # set the first byte to the low byte of the frequency
    data[1] = 0xB0 # set the second byte to 0xB0
    data[2] = 0x10 # set the third byte to 0x10
    data[3] = 0x00 # set the fourth byte to 0x00
    try:
        i2c.write_i2c_block_data(address, init, data) # write the data to the receiver
        print("Muted\r")
    except IOError:
        subprocess.call(['i2cdetect', '-y', '1']) # print the I2C address if there is an error
        print("Error muting\r")


if __name__ == '__main__':
    init_radio(i2c_address)
    frequency = 101.1 # sample starting frequency
    # terminal user input infinite loop
    stdscr = curses.initscr()
    curses.noecho()
    try:
        while True:
            c = stdscr.getch()
            if c == ord('w'): # increment by 1
                frequency += 1
                set_freq(i2c_address, frequency)
                time.sleep(.1)
            elif c == ord('s'): # decrement by 1
                frequency -= 1
                set_freq(i2c_address, frequency)
                time.sleep(.1)
            elif c == ord('e'): # increment by 0.1
                frequency += 0.1
                set_freq(i2c_address, frequency)
                time.sleep(.1)
            elif c == ord('d'): # decrement by 0.1
                frequency -= 0.1
                set_freq(i2c_address, frequency)
                time.sleep(.1)
            elif c == ord('m'): # mute
                mute(i2c_address, 0)
                time.sleep(.1)
            elif c == ord('u'): # unmute
                set_freq(i2c_address, frequency)
                time.sleep(.1)
            elif c == ord('q'): # exit script and cleanup
                mute(i2c_address)
                curses.endwin()

    except KeyboardInterrupt:
        pass

    finally:
        curses.endwin()

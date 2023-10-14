# TEA5767-COMSEC
Encryption and packetization of TEA5767 serial data across a TCP/IP network

## Introduction
The TEA5767 is a FM Module that can be communicated through the I2C bus. 
It is connected to a Raspberry Pi, and the 3.5mm out is connected to a compatible device.
The control.py script is used to control the TEA5767 FM module (such as FM frequency).

There are three separate folders, one for testing, one for unencrypted tranmission, and one for encrypted transmission using TLS 1.3. 
All scripts needed to be run will be inside each according folder.

The database.py script is used to store the server IP addresses to a simple flask database.
The server.py script when run will send the IP address to the database, and the client.py script will pull the server IP address from the database.

Once the server and client are connected, the server will stream the data from the TEA5767 module to the client, which will then play the audio and have the ability to save as a .wav file. 

It is not necessary to have a TEA5767 FM module to test these scripts as at its core it will take any audio input (such as a microphone) and stream it to the client.

## Install
pip install -r requirements.txt

## Usage
Run the database.py script first. 
Run the server.py script next.
Run the client.py script last.

## Certificates
Self signed certificates are pre-created and pre-configured for the server, client and the database.
Please do not use these certificates and SSL settings for production use.

## Dependencies
This was run on python 3.11.0, and the following libraries can be installed using "pip install -r requirements.txt"


## Issues 
There might be a problem installing the pyaudio library. 
You may have to install portaudio on macOS using homebrew. 
For Windows you may have to install pipwin and then install pyaudio using pipwin.
pip install pipwin -> pipwin install pyaudio

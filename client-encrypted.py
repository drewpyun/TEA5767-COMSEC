import socket
import wave
import datetime
import json
import threading

CHUNK = 1024
CHANNELS = 1
RATE = 44100
frames = []

# Ask user for the server's IP address
HOST = input("Enter the IP address of the server: ")
PORT = 65432

def receive_data(s):
    print('Receiving data... Enter "Stop", "Quit", or create a KeyboardInterrupt to stop recording.')
    while True:
        data = s.recv(CHUNK)
        if not data:
            break
        frames.append(data)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print(f"Connected to server {HOST}:{PORT}")

    devices = json.loads(s.recv(4096).decode('utf-8'))
    for device in devices:
        print(f"Input Device id {device['index']} - {device['name']}")
    device_index = input("\nEnter the ID of the input device you want to use: ")
    s.sendall(device_index.encode('utf-8'))

    t = threading.Thread(target=receive_data, args=(s,))
    t.start()

    try:
        while True:
            command = input()
            if command.lower() == 'stop' or command.lower() == 'q' or command.lower() == 'quit':
                s.sendall('stop'.encode('utf-8'))
                t.join()
                break
    except KeyboardInterrupt:
        s.sendall('stop'.encode('utf-8'))
        t.join()
        print("Recording complete. Data saved.")

# Save audio file with current date and time as filename
now = datetime.datetime.now()
filename = now.strftime("%Y-%m-%d_%H-%M-%S") + ".wav"
with wave.open(filename, 'wb') as wf:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(2)
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))

print(f"Recording saved as {filename}")

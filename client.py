import socket
import wave
import pyaudio

HOST = '10.0.1.108'  # The server's IP
PORT = 65432  # The port used by the server

frames = []
sample_format = pyaudio.paInt16
channels = 1
fs = 44100

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print(f"Connected to server {HOST}:{PORT}")
    input("Press 'q' and Enter to stop recording on server and receive data...")
    s.sendall(b'q')

    # Receive the recorded audio from the server
    while True:
        data = s.recv(1024)
        if not data:
            break
        frames.append(data)

# Save audio file with current date and time as filename
import datetime
now = datetime.datetime.now()
filename = now.strftime("%Y-%m-%d_%H-%M-%S") + ".wav"
with wave.open(filename, 'wb') as wf:
    wf.setnchannels(channels)
    wf.setsampwidth(2)  # pyaudio.paInt16 corresponds to 2 bytes
    wf.setframerate(fs)
    wf.writeframes(b''.join(frames))

print("Recording saved as", filename)

import socket
import wave
import datetime

# Client setup
host = 'localhost'  # Change to your server IP
port = 65432
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, port))

frames = []
print("Receiving data...")

while True:
    data = client.recv(1024)
    if not data: break  # Close if no data is received
    frames.append(data)

# Save the received frames to a WAV file
now = datetime.datetime.now()
filename = now.strftime("%Y-%m-%d_%H-%M-%S") + ".wav"
with wave.open(filename, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)  # Assuming paInt16 format
    wf.setframerate(44100)
    wf.writeframes(b''.join(frames))

print(f"Saved recording as {filename}")
client.close()

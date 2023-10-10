import pyaudio
import socket
import threading

# Server setup
host = '10.0.1.108'  # Change to your server IP
port = 65432
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen(1)
print(f"Listening on {host}:{port}")
conn, addr = server.accept()

# Audio setup
p = pyaudio.PyAudio()
chunk = 1024
sample_format = pyaudio.paInt16
channels = 1
fs = 44100

# Open stream
stream = p.open(format=sample_format, channels=channels, rate=fs, frames_per_buffer=chunk, input=True)

def record_and_send():
    print("Recording...")
    while not stop_recording.is_set():
        data = stream.read(chunk)
        conn.sendall(data)
    stream.stop_stream()
    stream.close()
    conn.close()

stop_recording = threading.Event()
recording_thread = threading.Thread(target=record_and_send)
recording_thread.start()

input("Press Enter to stop recording...")
stop_recording.set()
recording_thread.join()

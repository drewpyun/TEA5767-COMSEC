import socket
import ssl
import json
import threading
import pyaudio
import requests
import wave
import time
from queue import Queue

def get_input_devices():
    p = pyaudio.PyAudio()
    devices = [{"index": i, "name": p.get_device_info_by_index(i)["name"]} for i in range(p.get_device_count()) if p.get_device_info_by_index(i).get('maxInputChannels') > 0]
    p.terminate()
    return devices

def receive_data(conn, volume_multiplier, audio_queue):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, output=True, frames_per_buffer=1024)
    print("Receiving audio...")
    while True:
        data = conn.recv(1024)
        if not data:
            break
        adjusted_data = bytearray()
        for i in range(0, len(data), 2):
            sample = int.from_bytes(data[i:i+2], byteorder='little', signed=True)
            adjusted_sample = int(sample * volume_multiplier)
            adjusted_data.extend(adjusted_sample.to_bytes(2, byteorder='little', signed=True))
        stream.write(bytes(adjusted_data))
        audio_queue.put(bytes(adjusted_data))
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Stopped receiving audio.")

def save_audio_file(frames):
    if not frames:
        return
    timestamp = time.strftime("%Y%m%d%H%M%S")
    filename = f"recorded_audio_{timestamp}.wav"
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(b''.join(frames))
    print(f"Audio saved as {filename}")

def main():
    context = ssl.create_default_context()
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations('server.crt')  # Changed to 'server.crt'
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        with open('user-settings.txt', 'r') as f:
            database_ips = f.read().splitlines()
    except FileNotFoundError:
        database_ips = []

    print("Stored database IPs:")
    for i, ip in enumerate(database_ips):
        print(f"{i+1}. {ip}")

    choice = input("Enter the number of a stored database IP or 'n' to enter a new one: ")
    if choice.lower() == 'n':
        database_ip = input("Enter the IP of the database server: ")
        with open('user-settings.txt', 'a') as f:
            f.write(f"{database_ip}\n")
    else:
        database_ip = database_ips[int(choice) - 1]

    try:
        response = requests.get(f"https://{database_ip}:8000/get_ips", verify=False)
        available_server_ips = response.json()['ips']
    except requests.exceptions.JSONDecodeError:
        print("Received an invalid JSON from the server. Exiting.")
        exit(1)

    print("Available server IPs:")
    for i, ip in enumerate(available_server_ips):
        print(f"{i+1}. {ip}")

    server_choice = input("Enter the number of the server IP you want to connect to or 'm' for manual entry: ")
    if server_choice.lower() == 'm':
        HOST = input("Enter the IP of the server: ")
    else:
        HOST = available_server_ips[int(server_choice) - 1]

    PORT = 65432
    volume_multiplier = float(input("Enter the volume multiplier (e.g., 0.5 for lower volume): "))
    audio_queue = Queue()

    with socket.create_connection((HOST, PORT)) as s:
        conn = context.wrap_socket(s, server_hostname=HOST)

        device_data = json.loads(conn.recv(1024).decode('utf-8'))
        for i, device in enumerate(device_data):
            print(f"{i+1}. {device['name']}")

        device_choice = int(input("Choose an input device: "))
        device_index = device_data[device_choice - 1]['index']
        conn.sendall(str(device_index).encode('utf-8'))

        t = threading.Thread(target=receive_data, args=(conn, volume_multiplier, audio_queue))
        t.start()

        while True:
            command = input("Enter 'stop' to stop or 'save' to save audio: ")
            if command == 'stop':
                conn.sendall(b'stop')
                t.join()
                break
            elif command == 'save':
                frames_to_save = []
                while not audio_queue.empty():
                    frames_to_save.append(audio_queue.get())
                save_audio_file(frames_to_save)

if __name__ == "__main__":
    main()

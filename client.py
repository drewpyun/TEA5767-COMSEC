import socket
import json
import threading
import pyaudio
import requests

def get_input_devices():
    p = pyaudio.PyAudio()
    devices = [{"index": i, "name": p.get_device_info_by_index(i)["name"]} for i in range(p.get_device_count()) if p.get_device_info_by_index(i).get('maxInputChannels') > 0]
    p.terminate()
    return devices

def receive_data(conn):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, output=True, frames_per_buffer=1024)
    print("Receiving audio...")
    while True:
        data = conn.recv(1024)
        if not data:
            break
        stream.write(data)
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Stopped receiving audio.")

def main():
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
        response = requests.get(f"http://{database_ip}:8000/get_ips")
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
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        
        device_data = json.loads(s.recv(1024).decode('utf-8'))
        for i, device in enumerate(device_data):
            print(f"{i+1}. {device['name']}")
        
        device_choice = int(input("Choose an input device: "))
        device_index = device_data[device_choice - 1]['index']
        s.sendall(str(device_index).encode('utf-8'))

        t = threading.Thread(target=receive_data, args=(s,))
        t.start()

        while True:
            command = input("Enter 'stop' to stop: ")
            if command == 'stop':
                s.sendall(b'stop')
                break

if __name__ == "__main__":
    main()

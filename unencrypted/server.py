import socket
import pyaudio
import json
import threading
import psutil
import requests
import os

is_recording = False

def get_input_devices():
    p = pyaudio.PyAudio()
    devices = [{"index": i, "name": p.get_device_info_by_index(i)["name"]} for i in range(p.get_device_count()) if p.get_device_info_by_index(i).get('maxInputChannels') > 0]
    p.terminate()
    return devices

def record_and_send(conn, device_index):
    global is_recording
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024, input_device_index=device_index)
    print("Recording started.")
    while is_recording:
        data = stream.read(1024, exception_on_overflow=False)
        conn.sendall(data)
    stream.stop_stream()
    stream.close()
    p.terminate()

def get_network_interfaces():
    interfaces = psutil.net_if_addrs()
    available_ips = []
    for interface, addrs in interfaces.items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                available_ips.append((interface, addr.address))
    return available_ips

def main():
    # Check for saved database IP in server-settings.txt
    if os.path.exists("server-settings.txt"):
        with open("server-settings.txt", "r") as f:
            database_server_ip = f.read().strip()
    else:
        database_server_ip = input("Enter the database server IP: ")
        with open("server-settings.txt", "w") as f:
            f.write(database_server_ip)

    available_ips = get_network_interfaces()
    print("Available Network Interfaces and IP addresses:")
    for i, (interface, ip) in enumerate(available_ips):
        print(f"{i+1}. {interface} - {ip}")

    ip_choice = int(input("Enter the number of the IP you want to use: "))
    HOST = available_ips[ip_choice - 1][1]
    PORT = 65432

    # Sending the chosen IP to the database server
    response = requests.post(f'http://{database_server_ip}:8000/add/{HOST}')
    if response.status_code == 200:
        print("Successfully stored IP in the database.")
    else:
        print(f"Failed to store IP in the database. Response code: {response.status_code}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Listening on {HOST}:{PORT}")

        while True:
            global is_recording
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                devices = get_input_devices()
                conn.sendall(json.dumps(devices).encode('utf-8'))
                device_index = int(conn.recv(1024).decode('utf-8'))
                is_recording = True
                t = threading.Thread(target=record_and_send, args=(conn, device_index))
                t.start()

                try:
                    while is_recording:
                        if conn.recv(1024).decode('utf-8') == 'stop':
                            is_recording = False
                            t.join()
                            print("Recording stopped. Waiting for another connection...")
                except:
                    is_recording = False
                    t.join()

if __name__ == "__main__":
    main()
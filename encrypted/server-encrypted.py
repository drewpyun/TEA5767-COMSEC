# create a server SSL/TLS certificate using the following command:
# openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -keyout server.key -out server.crt

import socket
import ssl
import pyaudio
import json
import threading
import psutil
import requests
import os

is_recording = False  # Global flag to indicate if recording is happening

# Function to get all input (microphone) devices
def get_input_devices():
    p = pyaudio.PyAudio()  # Initialize PyAudio
    devices = [{"index": i, "name": p.get_device_info_by_index(i)["name"]} for i in range(p.get_device_count()) if p.get_device_info_by_index(i).get('maxInputChannels') > 0]
    p.terminate()
    return devices

# Function to record audio and send it over a secure connection
def record_and_send(conn, device_index):
    global is_recording  # Declare global variable
    p = pyaudio.PyAudio()  # Initialize PyAudio
    # Opens audio stream
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024, input_device_index=device_index)
    print("Recording started.")
    while is_recording:  # While recording flag is True
        data = stream.read(1024, exception_on_overflow=False)  # Read audio data
        conn.sendall(data)  # Send audio data over connection
    stream.stop_stream()
    stream.close()
    p.terminate()

# Function to get available network interfaces
def get_network_interfaces():
    interfaces = psutil.net_if_addrs()
    available_ips = []
    for interface, addrs in interfaces.items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                available_ips.append((interface, addr.address))
    return available_ips

# Main function
def main():
    # Database SSL context
    database_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    database_context.load_cert_chain(certfile='database.crt', keyfile='database.key')
    database_context.check_hostname = False
    database_context.verify_mode = ssl.CERT_NONE

    # Server SSL context
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(certfile='server.crt', keyfile='server.key')

    # Check for saved database IP in server-settings.txt
    if os.path.exists("server-settings.txt"):
        with open("server-settings.txt", "r") as f:
            database_server_ip = f.read().strip()
    else:
        database_server_ip = input("Enter the database server IP: ")
        with open("server-settings.txt", "w") as f:
            f.write(database_server_ip)

    # Fetch and display available network interfaces
    available_ips = get_network_interfaces()
    print("Available Network Interfaces and IP addresses:")
    for i, (interface, ip) in enumerate(available_ips):
        print(f"{i+1}. {interface} - {ip}")

    # User selects an IP address
    ip_choice = int(input("Enter the number of the IP you want to use: "))
    HOST = available_ips[ip_choice - 1][1]
    PORT = 65432

    # Sending the chosen IP to the database server
    response = requests.post(f'https://{database_server_ip}:8000/add/{HOST}', verify=False)
    if response.status_code == 200:
        print("Successfully stored IP in the database.")
    else:
        print(f"Failed to store IP in the database. Response code: {response.status_code}")

    # Creates and binds the socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Listening on {HOST}:{PORT}")

        while True:  # Main server loop
            global is_recording  # Declare global variable
            conn, addr = s.accept()
            with server_context.wrap_socket(conn, server_side=True) as secure_conn:  # Wrap the socket for SSL/TLS
                print(f"Connected by {addr}")
                devices = get_input_devices()

                # Convert devices list to JSON and find its length
                devices_json = json.dumps(devices)  
                length_str = str(len(devices_json)).zfill(4)  # Finds the json length

                # Send the length of JSON data first
                secure_conn.sendall(length_str.encode('utf-8'))

                # Now, send the actual JSON data
                secure_conn.sendall(devices_json.encode('utf-8'))

                device_index = int(secure_conn.recv(1024).decode('utf-8'))  # Receive selected device index from the client
                is_recording = True  # Set the recording flag to True
                # Starts recording in a new thread
                t = threading.Thread(target=record_and_send, args=(secure_conn, device_index))
                t.start()

                try:
                    while is_recording:  # Loop to listen for 'stop' command
                        if secure_conn.recv(1024).decode('utf-8') == 'stop': 
                            is_recording = False  # Stop recording if 'stop' is received
                            t.join()  # Wait for the thread to finish
                            print("Recording stopped. Waiting for another connection...")
                except:
                    is_recording = False  # Stop recording in case of an exception
                    t.join()  # wait for the thread to finish

# main function call
if __name__ == "__main__":
    main()

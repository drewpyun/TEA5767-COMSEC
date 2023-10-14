import socket
import json
import threading
import pyaudio
import requests
import wave
import time
from queue import Queue

# Function to get available input devices
def get_input_devices():
    p = pyaudio.PyAudio()
    # Collect the device information only if maxInputChannels > 0 (i.e., it can record audio).
    devices = [{"index": i, "name": p.get_device_info_by_index(i)["name"]} for i in range(p.get_device_count()) if p.get_device_info_by_index(i).get('maxInputChannels') > 0]
    p.terminate()  # Close the PyAudio stream
    return devices

# Function to receive audio data from the server and play it back
def receive_data(conn, volume_multiplier, audio_queue):
    p = pyaudio.PyAudio()
    # Initialize a new audio stream to play received audio.
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, output=True, frames_per_buffer=1024)
    print("Receiving audio...")
    while True:
        # Receive data from the server
        data = conn.recv(1024)

        # Break the loop if no data is received.
        if not data:
            break

        # Create an empty bytearray to store adjusted audio data.
        adjusted_data = bytearray()

        for i in range(0, len(data), 2):
            # Extract each audio sample, which is 2 bytes long.
            sample = int.from_bytes(data[i:i+2], byteorder='little', signed=True)

            # Adjust the audio sample by the volume_multiplier.
            adjusted_sample = int(sample * volume_multiplier)

            # Append the adjusted sample to the adjusted_data array.
            adjusted_data.extend(adjusted_sample.to_bytes(2, byteorder='little', signed=True))

        # Write the adjusted audio data to the audio stream for playback.    
        stream.write(bytes(adjusted_data))  

        # Add the adjusted audio data to the queue for potential saving.
        audio_queue.put(bytes(adjusted_data))

    # Cleanup after loop ends.    
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Stopped receiving audio.")

# Function to ensure that we receive the complete data payload.
def receive_complete_data(sock, expected_length):
    received_data = b""
    while len(received_data) < expected_length:
        # Calculate how much more data needs to be received.
        remaining_length = expected_length - len(received_data)

        # Receive the remaining data or 1024 bytes, whichever is smaller.
        new_data = sock.recv(min(remaining_length, 1024))

        # If no new data is received, consider the connection as broken and raise an exception.
        if not new_data:
            raise ConnectionError("Socket connection broken")
        
        # Append the newly received data to the existing data.
        received_data += new_data
    return received_data.decode('utf-8')

# Function to save audio data as a .wav file
def save_audio_file(frames):
    if not frames:
        return
    timestamp = time.strftime("%Y%m%d%H%M%S")
    filename = f"recorded_audio_{timestamp}.wav"

    # Create a new .wav file and write frames into it.
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(b''.join(frames))

    print(f"Audio saved as {filename}")

# Main function where the program execution starts
def main():
    try:  # Attempt to read previously used database IPs from a file.
        with open('user-settings.txt', 'r') as f:
            database_ips = f.read().splitlines()
    except FileNotFoundError:  # If the file doesn't exist, initialize an empty list.
        database_ips = []

    print("Stored database IPs:")
    for i, ip in enumerate(database_ips):
        print(f"{i+1}. {ip}")

    # User interface to select or input a new database IP.
    choice = input("Enter the number of a stored database IP or 'n' to enter a new one: ")
    if choice.lower() == 'n':
        database_ip = input("Enter the IP of the database server: ")
        # Save the new IP into the user-settings file for future use.
        with open('user-settings.txt', 'a') as f:
            f.write(f"{database_ip}\n")
    else:  # Use the previously stored IP as selected by the user.
        database_ip = database_ips[int(choice) - 1]

    try:  # Fetch the list of available server IPs from the database server.
        response = requests.get(f"http://{database_ip}:8000/get_ips")
        available_server_ips = response.json()['ips']
    except requests.exceptions.JSONDecodeError:
        print("Received an invalid JSON from the server. Exiting.")
        exit(1)

    print("Available server IPs:")
    for i, ip in enumerate(available_server_ips):
        print(f"{i+1}. {ip}")

    # User interface to select or input a new server IP.
    server_choice = input("Enter the number of the server IP you want to connect to or 'm' for manual entry: ")
    if server_choice.lower() == 'm':
        HOST = input("Enter the IP of the server: ")
    else:   # Use the selected available server IP.
        HOST = available_server_ips[int(server_choice) - 1]

    PORT = 65432  # The port on which the server is running.

    # Ask for a volume multiplier from the user.
    volume_multiplier = float(input("Enter the volume multiplier (e.g., 0.5 for lower volume): "))

    # Initialize a Queue to hold audio frames for possible saving.
    audio_queue = Queue()

    # Create a new socket and connect to the server.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        # Fetch and parse the list of available input devices from the server.
        length_str = s.recv(4).decode('utf-8')
        expected_length = int(length_str)

        json_str = receive_complete_data(s, expected_length)
        device_data = json.loads(json_str)

        for i, device in enumerate(device_data):
            print(f"{i+1}. {device['name']}")

        # User interface to select an input device.
        device_choice = int(input("Choose an input device: "))
        device_index = device_data[device_choice - 1]['index']

        # Send the selected device index back to the server.
        s.sendall(str(device_index).encode('utf-8'))

        # Start the thread that receives and plays audio.
        t = threading.Thread(target=receive_data, args=(s, volume_multiplier, audio_queue))
        t.start()

        # User interface for stopping the audio or saving it.
        while True:
            command = input("Enter 'stop' to stop or 'save' to save audio: ")
            if command == 'stop':
                s.sendall(b'stop')
                t.join()
                break
            elif command == 'save':
                frames_to_save = []
                while not audio_queue.empty():
                    frames_to_save.append(audio_queue.get())
                save_audio_file(frames_to_save)

if __name__ == "__main__":
    main()  # Main program

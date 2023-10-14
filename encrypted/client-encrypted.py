import socket
import ssl
import json
import threading
import pyaudio
import requests
import wave
import time
from queue import Queue

# Function to get available input audio devices
def get_input_devices():
    # initialize the audio library
    p = pyaudio.PyAudio()
    # List devices that have maxInputChannels > 0, meaning they can record audio
    devices = [{"index": i, "name": p.get_device_info_by_index(i)["name"]} for i in range(p.get_device_count()) if p.get_device_info_by_index(i).get('maxInputChannels') > 0]
    # terminates the audio library session
    p.terminate()
    return devices

# Function to receive audio data over SSL connection and play it
def receive_data(conn, volume_multiplier, audio_queue):
    # initialize the Audio library
    p = pyaudio.PyAudio()
    # Creates an audio stream
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, output=True, frames_per_buffer=1024)
    print("Receiving audio...")

    while True:
        # Receive 1024 bytes of audio data
        data = conn.recv(1024)
        # Breaks loop if data is empty
        if not data:
            break

        #Initializes a bytearray to store the adjusted audio data
        adjusted_data = bytearray()

        # Loop through each audio sample in the received data
        for i in range(0, len(data), 2):  # Converts 2 bytes to a single 16-bit audio sample
            sample = int.from_bytes(data[i:i+2], byteorder='little', signed=True)
            # Adjusts the volume of the audio sample
            adjusted_sample = int(sample * volume_multiplier)
            # Add the ajdusted audio sample back to the bytearray
            adjusted_data.extend(adjusted_sample.to_bytes(2, byteorder='little', signed=True))

        # write the adjusted data to the audio output  
        stream.write(bytes(adjusted_data))
        # Put the adjusted data into a queue for potential saving later
        audio_queue.put(bytes(adjusted_data))

    # Close the audio stream and terminate the audio session
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Stopped receiving audio.")

# Function to save audio data to a WAV file
def save_audio_file(frames):
    if not frames:  # Do nothing if there are no frames to save
        return
    # create a filename based on timestamp
    timestamp = time.strftime("%Y%m%d%H%M%S")
    filename = f"recorded_audio_{timestamp}.wav"
    # Open a new WAV file for writing
    with wave.open(filename, 'wb') as wf:
        # save audio parameters
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        # Write audio frames to the file
        wf.writeframes(b''.join(frames))
    print(f"Audio saved as {filename}")

# Main function of the program
def main():
    # Create a new SSL context using the TLS 1.3 protocol
    context = ssl.create_default_context()
    # Load the server's certificate into the SSL context (This would usually be verified)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations('server.crt')
    context.check_hostname = False  # These settings are insecure but are for self signed certificates
    context.verify_mode = ssl.CERT_NONE

    # Try to read the list of stored databas IPs 
    try:
        with open('user-settings.txt', 'r') as f:
            database_ips = f.read().splitlines()
    except FileNotFoundError:
        database_ips = []

    # Display stored database IPs
    print("Stored database IPs:")
    for i, ip in enumerate(database_ips):
        print(f"{i+1}. {ip}")

    # Let the user select or input a new database IP
    choice = input("Enter the number of a stored database IP or 'n' to enter a new one: ")
    if choice.lower() == 'n':
        database_ip = input("Enter the IP of the database server: ")
        with open('user-settings.txt', 'a') as f:
            f.write(f"{database_ip}\n")
    else:  # Retrieve the IP from the database 
        database_ip = database_ips[int(choice) - 1]

    # Make an HTTPS request to fetch available server IPs
    try:
        response = requests.get(f"https://{database_ip}:8000/get_ips", verify=False)
        available_server_ips = response.json()['ips']
    except requests.exceptions.RequestException:
        print("Received an invalid JSON from the server. Exiting.")
        exit(1)

    # Display available server IPs
    print("Available server IPs:")
    for i, ip in enumerate(available_server_ips):
        print(f"{i+1}. {ip}")

    # Let the user select or input a new server IP
    server_choice = input("Enter the number of the server IP you want to connect to or 'm' for manual entry: ")
    if server_choice.lower() == 'm':
        HOST = input("Enter the IP of the server: ")
    else:  # Retrieve the selected server IP
        HOST = available_server_ips[int(server_choice) - 1]

    PORT = 65432  # Server Port to connect to

    # Ask the user for the volume multiplier
    volume_multiplier = float(input("Enter the volume multiplier (e.g., 0.5 for lower volume): "))
    # Initialize a queue to store audio data
    audio_queue = Queue()

    # Create a socket connection
    with socket.create_connection((HOST, PORT)) as s:
        # Wrap the socket with SSl
        conn = context.wrap_socket(s, server_hostname=HOST)

        # Receive 4-byte length string and convert to integer
        length_str = conn.recv(4).decode('utf-8')
        length = int(length_str)

        # Receive exactly 'length' bytes for the JSON data
        device_data_bytes = conn.recv(length)
        device_data = json.loads(device_data_bytes.decode('utf-8'))

        # Display the available input devices
        for i, device in enumerate(device_data):
            print(f"{i+1}. {device['name']}")

        # Let the user select an input device
        device_choice = int(input("Choose an input device: "))
        # Retrieve the index of the selected device
        device_index = device_data[device_choice - 1]['index']
        # Send the selected device index back to the server
        conn.sendall(str(device_index).encode('utf-8'))

        # Create a thread to handle audio reception
        t = threading.Thread(target=receive_data, args=(conn, volume_multiplier, audio_queue))
        # Starts the thread
        t.start()

        # Main loop to handle user commands
        while True:
            command = input("Enter 'stop' to stop or 'save' to save audio: ")
            # Send 'stop' to stop the server and join thread to main thread
            if command == 'stop':
                conn.sendall(b'stop')
                t.join()
                break
            # Save the received audio data to a file
            elif command == 'save':
                frames_to_save = []
                # Empty the audio queue intop frames_to_save
                while not audio_queue.empty():
                    frames_to_save.append(audio_queue.get())
                # call the function to save the audio frames to a file
                save_audio_file(frames_to_save)

# main function call
if __name__ == "__main__":
    main()

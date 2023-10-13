import socket
import pyaudio
import json
import threading

is_recording = False

def get_input_devices():
    p = pyaudio.PyAudio()
    devices = [{"index": i, "name": p.get_device_info_by_index(i)["name"]} for i in range(p.get_device_count()) if p.get_device_info_by_index(i).get('maxInputChannels') > 0]
    p.terminate()
    return devices

def record_and_send(conn, device_index):
    global is_recording
    frames = []
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024, input_device_index=device_index)
    print("Recording started.")
    while is_recording:
        data = stream.read(1024, exception_on_overflow=False)
        conn.sendall(data)
    stream.stop_stream()
    stream.close()
    p.terminate()
    
def get_available_ips():
    # This function fetches all available IP addresses on the machine
    ips = []
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    ips.append(ip_address)
    return ips

def main():
    # Get all available IPs
    available_ips = get_available_ips()
    print("Available IPs:")
    for index, ip in enumerate(available_ips, 1):
        print(f"{index}. {ip}")

    # Ask the user to select an IP
    selected = int(input("Enter the number of the IP you want to use: "))
    HOST = available_ips[selected - 1]
    
    PORT = 65432

    # ... [rest of your code remains unchanged]

if __name__ == "__main__":
    main()
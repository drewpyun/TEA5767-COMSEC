import socket
import pyaudio
import json
import threading
import netifaces

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
    ips = []
    for iface in netifaces.interfaces():
        if netifaces.AF_INET in netifaces.ifaddresses(iface):
            for link in netifaces.ifaddresses(iface)[netifaces.AF_INET]:
                ips.append(link['addr'])
    return ips

def main():
    available_ips = get_available_ips()
    for idx, ip in enumerate(available_ips):
        print(f"{idx}. {ip}")
    chosen_ip_index = int(input("Enter the index of the IP you want to host on: "))
    HOST = available_ips[chosen_ip_index]
    PORT = 65432

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

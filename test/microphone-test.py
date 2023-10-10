import pyaudio
import wave
import datetime
import threading

# Ask user for microphone input device
p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
devices = [p.get_device_info_by_host_api_device_index(0, i) for i in range(numdevices)]
input_devices = [device for device in devices if device.get('maxInputChannels') > 0]

for idx, device in enumerate(input_devices):
    print(f"Input Device id {idx} - {device.get('name')}")

device_idx = int(input("\nEnter the index of the input device you want to use: "))
device_id = input_devices[device_idx]['index']

# Set up audio stream parameters
chunk = 1024
sample_format = pyaudio.paInt16
channels = 1
fs = 44100
frames = []

# Record audio in a separate thread
def record_audio():
    stream = p.open(format=sample_format, channels=channels, rate=fs, frames_per_buffer=chunk, input=True, input_device_index=device_id)
    print("Recording... Press 'q' to stop.")
    while not stop_recording.is_set():
        data = stream.read(chunk, exception_on_overflow=False)
        frames.append(data)
    stream.stop_stream()
    stream.close()

stop_recording = threading.Event()
recording_thread = threading.Thread(target=record_audio)
recording_thread.start()

# Wait for 'q' to stop recording
input("Press 'q' and Enter to stop recording...")
stop_recording.set()
recording_thread.join()

# Save audio file with current date and time as filename
now = datetime.datetime.now()
filename = now.strftime("%Y-%m-%d_%H-%M-%S") + ".wav"
with wave.open(filename, 'wb') as wf:
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)
    wf.writeframes(b''.join(frames))

print("Recording saved as", filename)

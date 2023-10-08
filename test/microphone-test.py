import sounddevice as sd
import numpy as np
import wavio
import datetime

# Parameters for recording
RATE = 44100  # samples per second
CHANNELS = 1  # mono recording
DTYPE = np.int16  # data type
VOLUME = 0.5  # volume level, range [0.0, 1.0]

def generate_filename():
    current_time = datetime.datetime.now()
    return current_time.strftime("%Y-%m-%d_%H-%M-%S") + ".wav"

def record_and_save(filename, volume=1.0, device=None):
    print("Recording... Press CTRL+C to stop.")
    try:
        with sd.InputStream(samplerate=RATE, channels=CHANNELS, device=device) as stream:
            audio_frames = []
            while True:
                audio_chunk, overflowed = stream.read(RATE)  # Record 1 second chunks
                audio_frames.append(audio_chunk * volume)
    except KeyboardInterrupt:
        print("Recording stopped.")
    finally:
        audio_data = np.concatenate(audio_frames, axis=0)
        wavio.write(filename, audio_data.astype(DTYPE), RATE, sampwidth=2)

if __name__ == '__main__':
    # List all audio devices
    print(sd.query_devices())
    mic_device = int(input("Enter the device ID for the microphone you want to use: "))
    volume_level = float(input("Enter the volume level (range [0.0, 1.0]): "))
    filename = generate_filename()
    print(f"Recording will be saved to {filename}")
    record_and_save(filename, volume=volume_level, device=mic_device)
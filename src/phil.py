#! /usr/bin/env python

# sourcery skip: replace-interpolation-with-fstring
import pyaudio
import noisereduce as nr
import sys
import numpy as np
import aubio
import datetime
import rumps
import threading

import os
from dotenv import load_dotenv
load_dotenv()

with open("/tmp/phil_env.txt", "w") as f:
    f.write(os.getenv("PHIL_ENV"))

import detections

class statusBarApp(rumps.App):
    
    def __init__(self, name):
        super(statusBarApp, self).__init__(name)
        self.menu = ["Preferences", "About"]
    
    @rumps.clicked("Preferences")
    def preferences(self, _):
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        os.system(f"open -a TextEdit {env_path}")
    
    @rumps.clicked("About")
    def about(self, _):
        readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")
        os.system(f"open -a TextEdit {readme_path}")


def react():    
    # initialise pyaudio
    p = pyaudio.PyAudio()
    global detections
    # INFO See the detections.py module
    detections = detections.detections
    # SECTION Settings
    verbose = os.getenv("verbose")
    debug = os.getenv("debug")
    detection_volume_mode = os.getenv("detection_volume_mode")
    treshold = float(os.getenv("treshold"))
    buffer_size = int(os.getenv("buffer_size"))
    pyaudio_format = pyaudio.paFloat32
    n_channels = int(os.getenv("n_channels"))
    samplerate = int(os.getenv("samplerate"))
    tolerance = float(os.getenv("tolerance"))
    win_s = int(os.getenv("win_s")) # fft size
    hop_s = int(os.getenv("hop_s")) # hop size
    # INFO The following is a reentrancy guard
    is_locked = False
    # INFO This is used to avoid sustain repetition
    last_note = None
    last_detection_time_treshold = float(os.getenv("last_detection_time_treshold"))
    last_detection_time = 0.0000000

    # INFO Experimental confidence threshold
    # NOTE You can change the confidence threshold here
    # Please note that increasing the treshold will result in a more accurate but slower detection
    confidence_score = 0.000
    confidence_treshold = float(os.getenv("confidence_treshold")) # How many seconds of consistence to consider a note to be effective (set to 0 to disable)
    last_confidence_note = None

    # INFO Opening the stream
    stream = p.open(format=pyaudio_format,
                    channels=n_channels,
                    rate=samplerate,
                    input=True,
                    frames_per_buffer=buffer_size)

    # INFO And preparing the pitch detection object
    pitch_o = aubio.pitch("default", win_s, hop_s, samplerate)
    pitch_o.set_unit("midi")
    pitch_o.set_tolerance(tolerance)

    # REVIEW Argument support is still not yet implemented
    if len(sys.argv) > 1:
        print(sys.argv)
    else:
        # run forever
        outputsink = None
        record_duration = None

    # SECTION Main Loop
    print("*** starting recording")
    while True:
        try:
            audiobuffer = stream.read(buffer_size)
            #signal = np.fromstring(audiobuffer, dtype=np.float32)
            signal = np.frombuffer(audiobuffer, dtype=np.float32)

            # Getting pre noise reduction volume
            original_volume = np.sum(signal**2)/len(signal)

            # Noise reduction
            signal = nr.reduce_noise(signal, samplerate)

            pitch = pitch_o(signal)[0]
            confidence = pitch_o.get_confidence()

            # Getting post noise reduction volume
            volume = np.sum(signal**2)/len(signal)

            # INFO You can change the detection volume here
            if detection_volume_mode == "original":
                detection_volume = original_volume
            else:
                detection_volume = volume

            show_info = False

            rounded_pitch = round(pitch)

            # INFO Iterating through detections and acting accordingly
            for key, value in detections.items():
                timestamp = datetime.datetime.now().timestamp()
                if abs(rounded_pitch) == int(key) and detection_volume > treshold:
                    
                    # INFO Trying to improve confidence
                    if last_confidence_note is not None and last_confidence_note == rounded_pitch:
                        confidence_score += 0.001
                    else:
                        confidence_score = 0.000
                    # Registering the note as the last we heard
                    last_confidence_note = rounded_pitch
                    # We need a consistent note to detect
                    if confidence_score < confidence_treshold:
                        continue
                    #print(confidence_score)
                    
                    # INFO If the detection keeps staying in our timeframe, skip it
                    time_since_last_detection = timestamp - last_detection_time
                    # NOTE This ensures that the time window is updated accordingly
                    last_detection_time = timestamp
                    if time_since_last_detection < last_detection_time_treshold:
                        continue
                    #print(last_detection_time_treshold)
                    #print(time_since_last_detection)
                    
                    
                    
                    # INFO If the note is the same as the previous one, skip it
                    # REVIEW While this assures that sustain is not repeated, see below todo
                    # TODO Add a temporal (or volume) enclosure of incoming identical audio samples
                    if rounded_pitch == last_note:
                        continue
                    last_note = rounded_pitch
                    
                    # Ensure the detection is locked
                    if is_locked:
                        break
                    is_locked = True
                    
                    # Logging
                    log_path = "/tmp/log_phil.txt"
                    with open(log_path, "a") as f:
                        f.write(f"{str(datetime.datetime.now().timestamp())} {str(rounded_pitch)} {str(confidence)}\n")
                    
                    if type(value) == str:
                        if debug:
                            show_info = True
                        print(f"*** detected {value}")
                    else:
                        # If value is a function, it will be called
                        value(key)
                    
                    # Unlock the detection
                    is_locked = False
                
                # INFO The only purpose of this is to help preventing sustain repetition while allowing two distinct notes to be detected
                else:
                    last_note = None

            # INFO Dumping infos on the detection, can be disabled in the config above
            if show_info and verbose:
                print("*** pitch: %.2f" % pitch)
                print("*** confidence: %.2f" % confidence) 
                volume = "{:6f}".format(volume)
                print(f"*** volume: {volume}")
                original_volume = "{:6f}".format(original_volume)
                print(f"*** original volume: {original_volume}")
                print("\n")

        except KeyboardInterrupt:
            print("*** Ctrl+C pressed, exiting")
            break
        
        except Exception as e:
            print("Uh, we should exit NOW")
            print(e)
            break

    print("*** done recording")
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    
# NOTE Not only is a good practice, but is also necessary to prevent py2app from crashing
if __name__ == "__main__":
    status_thread = threading.Thread(target=react, daemon=True)
    status_thread.start()
    statusBarApp("Phil").run()
import sounddevice as sd
import queue
import sys
import json
import uuid
import requests
from vosk import Model, KaldiRecognizer
from domain.speaker_role import SpeakerRole

BACKEND_URL = "http://127.0.0.1:8000"
SAMPLE_RATE = 48000
MODEL_PATH = "models/vosk-model-es-0.42"

call_id = str(uuid.uuid4())

def audio_callback(indata, frames, time, status, audio_queue):
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(bytes(indata))

def main():

    audio_queue = queue.Queue()

    model = Model(MODEL_PATH)
    recognizer = KaldiRecognizer(model, SAMPLE_RATE)

    def callback(indata, frames, time, status):
        audio_queue.put(bytes(indata))

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=48000,
        dtype="int16",
        channels=1,
        callback=callback
    ):
        print("Grabando...")

        while True:
            try:
                data = audio_queue.get(timeout=1)
            except queue.Empty:
                continue
            
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()

                if text:
                    print("Texto:", text)

                    payload = {
                        "call_id": call_id,
                        "text": text,
                        "speaker": SpeakerRole.UNKNOWN.value,
                        "ts": int(__import__("time").time())
                    }

                    response = requests.post(
                        f"{BACKEND_URL}/ingest",
                        json=payload
                    )

                    print("Risk:", response.json().get("risk_score"))

            else:
                partial = json.loads(recognizer.PartialResult())
                print("Partial:", partial.get("partial"))

if __name__ == "__main__":
    main()


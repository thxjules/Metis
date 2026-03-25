import sounddevice as sd
import queue
import sys
import json
import uuid
import requests
import time
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
        callback=callback,
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
                        "chunk_id": str(uuid.uuid4()),
                        "text": text,
                        "speaker": SpeakerRole.UNKNOWN.value,
                        "ts": int(time.time()),
                        "is_final": True,
                        "confidence": 1.0,
                    }

                    response = requests.post(f"{BACKEND_URL}/ingest", json=payload)

                    if response.status_code == 200:
                        res_data = response.json()
                        
                        print(f"Risk: {res_data.get('risk_score')} | Interest: {res_data.get('interest_score')}")

                        if res_data.get("event") == "RISK_ALERT":
                            print("ALERTA: Umbral de riesgo superado en el servidor")
                        
                        if res_data.get("event") == "INTEREST_ALERT":
                            print("ALERTA: Umbral de interés superado en el servidor")
                        
                        if res_data.get("events", {}).get("extreme_hostility"):
                            print(f"ALERTA: Hostilidad extrema detectada ({res_data['events']['extreme_hostility']})")

                        if res_data.get("events", {}).get("call_closing"):
                            print("ALERTA: Cierre de llamada detectado")
                    else:
                        print(f"Error en el servidor: {response.status_code}")

            else:
                partial = json.loads(recognizer.PartialResult())
                # Solo imprimimos partial si hay algo realmente
                if partial.get("partial"):
                    print("Partial:", partial.get("partial"))

if __name__ == "__main__":
    main()

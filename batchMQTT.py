import os
import time
import json
import random
import uuid
import numpy as np
import boto3
from botocore.exceptions import ClientError

# Configurazione
BUCKET_NAME = 'batchdataheartbeatcopy'
DEVICE_ID   = "IoTSimulator"
NUM_RECORDS = 10
OUTPUT_KEY  = f"{DEVICE_ID}/{int(time.time()*1000)}.json"

# Inizializza client S3 (usa credenziali automatiche di CloudShell)
s3_client = boto3.client('s3', region_name='us-east-1')

# Genera la lista di record [ts, [bpm_values]]
records = []
# Partiamo da un BPM umano plausibile
current_bpm = random.randint(60, 100)
for _ in range(NUM_RECORDS):
    ts = int(time.time() * 1000)
    bpm_values = []
    for _ in range(5):
        current_bpm += random.randint(-3, 3)
        current_bpm = max(20, min(180, current_bpm))
        bpm_values.append(current_bpm)
    records.append([ts, bpm_values])
    time.sleep(0.1)  # piccolo delay per variare il timestamp

# Prepara il payload completo
payload = {
    "deviceId": DEVICE_ID,
    "records": records
}

# Salva su file temporaneo
local_path = "/tmp/heartbeat_payload.json"
with open(local_path, 'w') as f:
    json.dump(payload, f)

print(f"[INFO] File JSON generato: {local_path}")
print(f"[INFO] Payload summary: deviceId={DEVICE_ID}, records={len(records)}")

# Carica il file su S3
try:
    s3_client.upload_file(local_path, BUCKET_NAME, OUTPUT_KEY)
    print(f"[INFO] File caricato con successo su s3://{BUCKET_NAME}/{OUTPUT_KEY}")
except ClientError as e:
    print(f"[ERROR] Upload fallito: {e}")
    raise


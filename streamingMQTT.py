import os
import time
import json
import random
import numpy as np
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder

# Path assoluti
base     = os.path.dirname(os.path.realpath(__file__))
endpoint = "a3cpext04j621i-ats.iot.us-east-1.amazonaws.com"
port     = 8883
client_id = "IoTSimulator"
topic = "IoTSimulator/bpm"

# Callback di debug
def on_connection_interrupted(conn, error, **kwargs):
    print(f"[MQTT] Connessione interrotta: {error}")

def on_connection_resumed(conn, return_code, session_present, **kwargs):
    print(f"[MQTT] Connessione ripresa: return_code={return_code}, session_present={session_present}")

# 1) Costruisci la connessione MQTT basata su CRT (TLSv1.2+)
evt_loop  = io.EventLoopGroup(1)
resolver  = io.DefaultHostResolver(evt_loop)
bootstrap = io.ClientBootstrap(evt_loop, resolver)

mqtt_conn = mqtt_connection_builder.mtls_from_path(
    endpoint=endpoint,
    port=port,
    cert_filepath=os.path.join(base, "device-cert.pem"),
    pri_key_filepath=os.path.join(base, "device-key.pem"),
    ca_filepath=os.path.join(base, "root-CA.pem"),
    client_bootstrap=bootstrap,
    client_id=client_id,
    clean_session=False,
    keep_alive_secs=30,
    on_connection_interrupted=on_connection_interrupted,
    on_connection_resumed=on_connection_resumed
)

# 2) Connetti
print("[MQTT] Connettendo…")
try:
    mqtt_conn.connect().result()
    print("[MQTT] Connesso!")
except Exception as e:
    print(f"[ERROR] Fallita connessione MQTT: {e}")
    exit(1)

# 3) Pubblica un messaggio di test
# punto di partenza plausibile per un battito umano
current_bpm = random.randint(60, 100)
 
# genera 5 BPM con piccole variazioni successive
bpm_values = []
for _ in range(5):
    # variazione casuale fra -5 e +5
    current_bpm += random.randint(-5, 5)
    # mantieni il valore nel range 20–180
    current_bpm = max(20, min(180, current_bpm))
    bpm_values.append(current_bpm)
 
payload = {
    "deviceId": client_id,
    "ts":       int(time.time() * 1000),
    "bpm":      bpm_values
}
 
# esempio di stampa per verifica
print("[MQTT] Pubblico payload:", payload)
try:
    # publish() restituisce un Future-like; in alcune versioni restituisce un int identificativo
    pub_result = mqtt_conn.publish(
        topic=topic,
        payload=json.dumps(payload),
        qos=mqtt.QoS.AT_LEAST_ONCE
    )
    # Se è un Future, gestiamolo; altrimenti è già l’ID
    if hasattr(pub_result, "result"):
        pub_id = pub_result.result()
    else:
        pub_id = pub_result
    print(f"[MQTT] Messaggio inviato con successo! packet_id={pub_id}")
except Exception as e:
    print(f"[ERROR] Fallito publish: {e}")

# 4) Disconnetti
try:
    print("[MQTT] Disconnettendo…")
    mqtt_conn.disconnect().result()
    print("[MQTT] Disconnesso.")
except Exception as e:
    print(f"[ERROR] Fallita disconnessione: {e}")

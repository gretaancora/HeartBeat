import json
from typing import List, Dict, Any

def extract_mean_feature(
    patient_id: str,
    bpm_values: List[float],
    age: int = None,
    sex: str = None,
    ts: str = None
) -> Dict[str, Any]:
    """
    Estrae unicamente la media dei BPM inviati e restituisce
    un payload JSON-ready per la Step Function.
    """
    count = len(bpm_values)
    if count == 0:
        raise ValueError("bpm_values non può essere vuoto")

    bpm_mean = sum(bpm_values) / count

    result: Dict[str, Any] = {
        'patient_id': patient_id,
        'bpm_mean': bpm_mean,
        'bpm_values': str(bpm_values),
        'ts': ts
    }
    # Aggiungo metadata opzionali se forniti
    if age is not None:
        result['age'] = age
    if sex is not None:
        result['sex'] = sex.upper()

    return result


def lambda_handler(event, context):
    """
    AWS Lambda handler che si aspetta un JSON in `event` con i campi:
    patient_id, bpm_values, (opzionali: age, sex).
    Restituisce un dizionario di output con solo il campo bpm_mean.
    """
    # Se l'evento è una stringa JSON, parsalo
    if isinstance(event, str):
        event = json.loads(event)

    patient_id = event.get('patient_id')
    bpm_values = event.get('bpm_values', [])
    age = event.get('age')
    sex = event.get('sex')
    ts = event.get('ts')

    if not patient_id or not bpm_values:
        raise ValueError("patient_id e bpm_values sono obbligatori")

    return extract_mean_feature(
        patient_id=patient_id,
        bpm_values=bpm_values,
        age=age,
        sex=sex,
        ts=ts
    )

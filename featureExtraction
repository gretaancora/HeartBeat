import json
import logging
from typing import Any, Dict

# Configura il logger
type JsonDict = Dict[str, Any]
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def handler(event: JsonDict, context: Any) -> JsonDict:
    """
    Prima funzione Lambda di un flusso Step Functions.
    Prende in input un JSON con campi 'patientid' e 'data', moltiplica per 10^3 i valori numerici in 'data'
    e restituisce in output il patientid e i dati modificati.

    :param event: Dizionario in ingresso, es. {'patientid': 'paziente-123', 'data': {...}}
    :param context: Contesto Lambda (non utilizzato)
    :return: Dizionario con 'patientid' e dati processati, es. {'patientid': 'paziente-123', 'data': {...}}
    """
    # Estrai patientid
    patient_id = event.get('patientid')
    if patient_id is None:
        logger.error("Chiave 'patientid' non trovata nell'evento")
        raise ValueError("Chiave 'patientid' mancante nell'evento Lambda")

    # Estrai sezione data
    raw_data = event.get('data')
    if raw_data is None or not isinstance(raw_data, dict):
        logger.error("Chiave 'data' assente o non un dict nell'evento")
        raise ValueError("Sezione 'data' mancante o in formato errato nell'evento Lambda")

    # Moltiplica ogni valore numerico per 10^3
    processed: JsonDict = {}
    for key, value in raw_data.items():
        if isinstance(value, (int, float)):
            processed[key] = value * 10**3
        else:
            processed[key] = value  # Copia senza modifiche

    logger.info(f"Dati processati per patient {patient_id}: {processed}")

    # Restituisci il patientid e i dati processati
    return {
        'patientid': patient_id,
        'data': processed
    }

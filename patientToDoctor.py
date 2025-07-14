import json
import os
import boto3
from typing import Dict, Any
from boto3.dynamodb.conditions import Key

# Environment variable for DynamoDB table name
TABLE_NAME = os.getenv('DOCTOR_PATIENT_TABLE', 'DoctorPatient')

# Initialize DynamoDB resource
_dynamodb_resource = boto3.resource('dynamodb')
_table = _dynamodb_resource.Table(TABLE_NAME)

def matchPatientToDoctor(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Core logic to match a patient to their doctor by querying
    the DoctorPatient DynamoDB table. Expects 'doctor_id' in the event.

    Returns a dict with:
      - doctor_id: the provided doctor ID
      - patient_id: the matched patient ID from the table
    Raises ValueError on missing or invalid parameters, or if no match found.
    """
    # If event is JSON string, parse it
    if isinstance(event, str):
        event = json.loads(event)

    patient_id = event.get('patient_id')
    if not patient_id:
        raise ValueError("Occorre specificare patient_id nell'evento")

    # Query DynamoDB table by doctor_id
    try:
        response = _table.query(
            KeyConditionExpression=Key('patient').eq(patient_id)
        )
    except Exception as e:
        raise RuntimeError(f"Errore durante l'accesso a DynamoDB: {e}")

    items = response.get('Items', [])
    if not items:
        raise LookupError(f"Nessun dottore trovato per il paziente {patient_id}")

    # Assuming one-to-one mapping; take the first match
    doctor_id = items[0].get('doctor')
    if not doctor_id:
        raise LookupError(f"Item trovato ma senza attributo 'doctor' per paziente {patient_id}")

    return {
        'doctor_id': doctor_id,
        'patient_id': patient_id
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler entry point. Delegates to matchPatientToDoctor.
    Accepts event (dict or JSON string) and context, returns JSON-serializable dict.
    """
    result = matchPatientToDoctor(event)
    # Optionally, add metadata like request ID or timestamp
    return result

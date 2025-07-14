import os
import json
import boto3
from botocore.exceptions import ClientError

# Client AWS
dynamo = boto3.client('dynamodb')
sfn    = boto3.client('stepfunctions')

# Configurazione da env vars
IOTPATIENT_TABLE        = os.environ.get('IOTPATIENT_TABLE', '')
# ARN della State Machine di AWS Step Functions (stessa per tutti i dispositivi)
STATE_MACHINE_ARN       = os.environ.get('STATE_MACHINE_ARN', '')


def lambda_handler(event, context):
    """
    AWS Lambda handler che processa un evento SQS con più records,
    avvia esecuzioni di Step Functions e restituisce un JSON in output.

    In output, restituisce per ciascun record:
      - patient_id: str
      - bpm_values: List[float]
      - age: int
      - sex: str

    Output (JSON string):
    {
      "statusCode": 200,
      "processed": [
        {
          "patient_id": "...",
          "bpm_values": [...],
          "age": 30,
          "sex": "M"
        },
        ...
      ]
    }
    """
    results = []

    # Verifica ARN State Machine
    if not STATE_MACHINE_ARN:
        raise RuntimeError("STATE_MACHINE_ARN non configurato")

    for record in event.get('Records', []):
        try:
            # Parse SQS body
            body = json.loads(record.get('body', '{}'))
            device_id = body.get('deviceId')

            # Recupera patient info da DynamoDB
            db = dynamo.get_item(
                TableName=IOTPATIENT_TABLE,
                Key={'deviceId': {'S': device_id}}
            )
            if 'Item' not in db:
                raise KeyError(f"Device {device_id} non trovato in DynamoDB")
            item = db['Item']
            patient_id = item['patientId']['S']
            sex        = item.get('sex', {}).get('S', '').upper()
            age_str    = item.get('age', {}).get('N', '0')
            try:
                age = int(age_str)
            except ValueError:
                age = 0

            # Estrai vettore bpm_values
            bpm_values = body.get('bpm_values', [])

            # Avvia Step Function
            payload = {
                "deviceId":   device_id,
                "patientId":  patient_id,
                "age":        age,
                "sex":        sex,
                "bpm_values": bpm_values,
                "ts":         str(body.get('ts', ''))
            }
            exec_name = f"{device_id}-{payload['ts']}"
            try:
                sfn.start_execution(
                    stateMachineArn=STATE_MACHINE_ARN,
                    name=exec_name,
                    input=json.dumps(payload)
                )
            except ClientError as e:
                if e.response.get('Error', {}).get('Code') != 'ExecutionAlreadyExists':
                    raise

            # Aggiungi al risultato solo i campi richiesti
            results.append({
                'patient_id': patient_id,
                'bpm_values': bpm_values,
                'age': age,
                'sex': sex,
                'ts': str(body.get('ts', ''))
            })

        except Exception as e:
            print(f"Errore processing record {record.get('messageId')}: {e}")
            # In caso di errore, includi comunque l'ID paziente se disponibile
            results.append({
                'patient_id': item.get('patientId', {}).get('S', 'unknown') if 'item' in locals() else 'unknown',
                'error': str(e)
            })

    response = {
        'statusCode': 200,
        'processed': results
    }
    return json.dumps(response)

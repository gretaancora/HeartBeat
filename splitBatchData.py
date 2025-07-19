import os
import json
import uuid
import boto3
import logging
from botocore.exceptions import ClientError

# Client AWS
s3_client   = boto3.client('s3')
dynamo      = boto3.client('dynamodb')
sf_client   = boto3.client('stepfunctions')

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Configurazione da env vars
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN')
DDB_TABLE_NAME    = os.environ.get('DDB_TABLE_NAME')

def lambda_handler(event, context):
    logger.debug(">>> ENTER LAMBDA HANDLER <<<")
    logger.debug(f"Raw event: {json.dumps(event)}")

    # 1. Estrai bucket e key dall'evento S3
    record0 = event['Records'][0]
    bucket  = record0['s3']['bucket']['name']
    key     = record0['s3']['object']['key']

    # 2. Scarica e legge il file
    try:
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        payload_json = json.loads(obj['Body'].read())
    except ClientError as e:
        logger.error(f"Errore scaricando {bucket}/{key}: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Formato JSON non valido in {key}: {e}")
        raise

    # 3. Estrai deviceId e lista di record
    device_id = payload_json.get("deviceId")
    records   = payload_json.get("records", [])
    if not device_id or not isinstance(records, list):
        raise ValueError("File JSON deve contenere 'deviceId' e 'records' (lista).")

    # 4. Interroga DynamoDB per age, patientId e sex (low-level client)
    try:
        resp = dynamo.get_item(
            TableName=DDB_TABLE_NAME,
            Key={'deviceId': {'S': device_id}}
        )
    except ClientError as e:
        logger.error(f"Errore DynamoDB get_item: {e}")
        raise

    item = resp.get('Item')
    if not item:
        raise KeyError(f"Nessun record in DynamoDB per deviceId={device_id}")

    # Estrai e converti i campi
    patient_id = item['patientId']['S']
    sex        = item.get('sex', {}).get('S', '').upper()
    age_str    = item.get('age', {}).get('N', '0')
    try:
        age = int(age_str)
    except ValueError:
        age = 0

    # 5. Per ogni record, invoca la State Machine
    processed = 0
    for record in records:
        try:
            ts, bpm_values = record
        except (ValueError, TypeError):
            logger.warning(f"Record malformato: {record}, skipping.")
            continue

        sf_payload = {
            "deviceId":   device_id,
            "patientId":  patient_id,
            "age":        age,
            "sex":        sex,
            "bpm_values": bpm_values,
            "ts":         str(ts)
        }

        execution_name = f"{device_id}-{uuid.uuid4()}"
        try:
            sf_client.start_execution(
                stateMachineArn=STATE_MACHINE_ARN,
                name=execution_name,
                input=json.dumps(sf_payload)
            )
            logger.info(f"Triggered execution {execution_name}")
        except ClientError as e:
            code = e.response.get('Error', {}).get('Code')
            # Ignora esecuzioni duplicate, rilancia per altri errori
            if code != 'ExecutionAlreadyExists':
                logger.error(f"Errore start_execution {execution_name}: {e}")
                raise
            else:
                logger.warning(f"ExecutionAlreadyExists for {execution_name}")

        processed += 1

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Elaborazione completata",
            "deviceId": device_id,
            "records_processed": processed
        })
    }

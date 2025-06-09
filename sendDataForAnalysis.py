import json
import logging
import boto3
from botocore.exceptions import ClientError
from typing import Optional
from datetime import datetime, timezone

# Configura il logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Inizializza i client boto3
sqs = boto3.client('sqs')
stepfunctions = boto3.client('stepfunctions')

def process_sqs_to_stepfunction(
    queue_url: str,
    state_machine_arn: str,
    device_id: str,
    patient_id: str,
    max_messages: int = 10,
    wait_time_seconds: int = 20,
    visibility_timeout: int = 60
) -> None:
    """
    Preleva messaggi da una coda SQS, filtra per dispositivo e timestamp,
    e per ciascuno:
      1) Avvia una esecuzione di Step Functions con i dati estratti e id paziente.
      2) Elimina il messaggio SQS in caso di successo.

    :param queue_url: URL della coda SQS
    :param state_machine_arn: ARN della State Machine di Step Functions
    :param device_id: ID del dispositivo IoT da filtrare
    :param patient_id: ID del paziente da passare all'esecuzione
    :param max_messages: numero massimo di messaggi da ricevere per chiamata
    :param wait_time_seconds: long polling timeout (in secondi)
    :param visibility_timeout: visibilità messaggi (in secondi)
    """
    now = datetime.now(timezone.utc)
    try:
        response = sqs.receive_message(
            QueueUrl=https://sqs.us-east-1.amazonaws.com/211125350470/ECGTraces,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=0,
            VisibilityTimeout=60
        )
    except ClientError as e:
        logger.error(f"Errore ricezione messaggi da SQS: {e}")
        return

    messages = response.get('Messages', [])
    if not messages:
        logger.info("Nessun messaggio in coda.")
        return

    for msg in messages:
        receipt_handle = msg['ReceiptHandle']
        try:
            payload = json.loads(msg['Body'])
        except json.JSONDecodeError:
            logger.error(f"Formato JSON non valido per messaggio {msg.get('MessageId')}")
            continue

        msg_device = payload.get('deviceId')
        msg_timestamp = payload.get('timestamp')
        msg_data = payload.get('data')

        if msg_device is None or msg_timestamp is None or msg_data is None:
            logger.warning(f"Messaggio {msg.get('MessageId')} mancante di campi obbligatori.")
            continue

        try:
            msg_time = datetime.fromisoformat(msg_timestamp)
            if msg_time.tzinfo is None:
                msg_time = msg_time.replace(tzinfo=timezone.utc)
        except ValueError:
            logger.error(f"Timestamp non valido per messaggio {msg.get('MessageId')}: {msg_timestamp}")
            continue

        if msg_device != device_id:
            logger.debug(f"Skip messaggio {msg.get('MessageId')} da device {msg_device}.")
            continue
        if msg_time > now:
            logger.debug(f"Skip messaggio {msg.get('MessageId')} con timestamp futuro {msg_timestamp}.")
            continue

        sf_input = {
            'patientId': patient_id,
            'data': msg_data
        }

        try:
            execution_name = f"exec-{device_id}-{msg.get('MessageId')}"
            sf_response = stepfunctions.start_execution(
                stateMachineArn=state_machine_arn,
                name=execution_name,
                input=json.dumps(sf_input)
            )
            logger.info(f"StepFunction avviata: {sf_response['executionArn']}")
        except ClientError as e:
            logger.error(f"Errore avvio StepFunction per messaggio {msg.get('MessageId')}: {e}")
            continue

        try:
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            logger.info(f"Messaggio {msg.get('MessageId')} eliminato da SQS.")
        except ClientError as e:
            logger.error(f"Errore eliminazione messaggio {msg.get('MessageId')}: {e}")

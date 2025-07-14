import os
import json
import logging
import traceback
import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamo = boto3.client('dynamodb')
sqs = boto3.client('sqs')

# Read environment variables
# Ensure you have set in Lambda env vars:
#   QUEUE_URL=https://sqs.us-east-1.amazonaws.com/832059618623/ECGTraces.fifo
#   IOTPATIENT_TABLE=IoTPatient
QUEUE_URL = os.environ['QUEUE_URL']
IOTPATIENT_TABLE = os.environ['IOTPATIENT_TABLE']

def lambda_handler(event, context):
    """
    AWS Lambda handler: process IoT Core MQTT payload,
    lookup clientId in DynamoDB, and forward to SQS FIFO.
    """
    try:
        # 1) Extract payload
        payload = event
        device_id = payload.get('deviceId')
        ts = payload.get('ts')
        if not device_id or ts is None:
            raise ValueError("Invalid payload: 'deviceId' or 'ts' missing")
        logger.info(f"Payload received: deviceId={device_id}, ts={ts}")

        # 2) DynamoDB lookup
        resp = dynamo.get_item(
            TableName=IOTPATIENT_TABLE,
            Key={'deviceId': {'S': device_id}}
        )
        if 'Item' not in resp:
            raise KeyError(f"Device '{device_id}' not found in table {IOTPATIENT_TABLE}")
        patient_id = resp['Item']['patientId']['S']
        logger.info(f"Found clientId={patient_id} for deviceId={device_id}")

        # 3) Prepare SQS message
        message_body = {
            "patientId": patient_id,
            "deviceId": device_id,
            "ts": ts,
            "payload": payload
        }

        # 4) Send message to SQS FIFO
        send_resp = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message_body),
            MessageAttributes={
                "topic": {
                    "DataType": "String",
                    "StringValue": f"ecg/{device_id}"
                }
            },
            MessageGroupId=device_id,
            MessageDeduplicationId=str(ts)
        )
        logger.info(f"Sent to SQS: MessageId={send_resp.get('MessageId')}")

        return {
            "status": "sent",
            "patientId": patient_id,
            "deviceId": device_id,
            "ts": ts
        }

    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}\n{traceback.format_exc()}")
        # Propagate error
        raise

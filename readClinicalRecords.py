import json
import boto3
import os

# Inizializza il client DynamoDB
dynamodb = boto3.client('dynamodb')
TABLE_NAME = os.environ.get('TABLE_NAME')


def lambda_handler(event, context):
    """
    Lambda function per leggere i record dalla tabella DynamoDB.
    Restituisce direttamente un JSON puro con 'items' e, se presente, 'lastKey'.

    Query parameters via queryStringParameters:
      - patient: filtra i record per paziente
      - limit: numero massimo di elementi da restituire (default: 100)
      - lastKey: chiave di partenza per la paginazione (JSON string)
    """
    try:
        params = event.get('queryStringParameters') or {}
        patient_id = params.get('patient')
        limit = int(params.get('limit', '100'))
        last_key = params.get('lastKey')

        exclusive_start_key = json.loads(last_key) if last_key else None

        if patient_id:
            query_args = {
                'TableName': TABLE_NAME,
                'KeyConditionExpression': 'patient = :pid',
                'ExpressionAttributeValues': {':pid': {'S': patient_id}},
                'Limit': limit
            }
            if exclusive_start_key:
                query_args['ExclusiveStartKey'] = exclusive_start_key
            response = dynamodb.query(**query_args)
        else:
            scan_args = {'TableName': TABLE_NAME, 'Limit': limit}
            if exclusive_start_key:
                scan_args['ExclusiveStartKey'] = exclusive_start_key
            response = dynamodb.scan(**scan_args)

        items = response.get('Items', [])
        last_evaluated_key = response.get('LastEvaluatedKey')

        # Restituisci JSON puro
        return {
            'items': items,
            'lastKey': last_evaluated_key
        }

    except Exception as e:
        # Restituisci errore in JSON puro
        return {'error': str(e)}

import os
import json
import logging
import boto3
from botocore.exceptions import ClientError
import hmac
import hashlib
import base64

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
USER_POOL_ID = 'us-east-1_MMIaRW7by'
DOCTOR_GROUP = 'Doctor'
APP_CLIENT_ID = '7behact4mbieppe861t2lc869h'
APP_CLIENT_SECRET = '371943ja3iknc6pqsj5g77ujj3udae2cngpjqo6jus2vn8qhsrr'

# Initialize AWS Cognito Identity Provider client
cognito_client = boto3.client('cognito-idp')

def get_secret_hash(username: str) -> str:
    """
    Compute the secret hash for Cognito calls on a client with a secret.
    """
    message = username + APP_CLIENT_ID
    dig = hmac.new(
        APP_CLIENT_SECRET.encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()


def lambda_handler(event, context):
    """
    AWS Lambda handler for user self-registration via email and password,
    auto-confirming the user and adding them to the 'Doctor' group.

    Expected event format (JSON):
    {
        "email": "user@example.com",
        "password": "P@ssw0rd!"
    }
    """


    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        logger.error("Invalid JSON format in request body")
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Invalid JSON'})
        }

    email = body.get('email')
    password = body.get('password')




    """
    email = event.get('email')
    password = event.get('password')
    """
    
    if not email or not password:
        logger.error("Missing required parameters: email or password")
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Both email and password are required'})
        }

    try:
        # Compute secret hash for the client
        secret_hash = get_secret_hash(email)

        # Sign up the user
        signup_response = cognito_client.sign_up(
            ClientId=APP_CLIENT_ID,
            Username=email,
            Password=password,
            SecretHash=secret_hash,
            UserAttributes=[
                {'Name': 'email', 'Value': email}
            ]
        )
        logger.info(f"Sign-up initiated for {email}")

        # Auto-confirm the user
        cognito_client.admin_confirm_sign_up(
            UserPoolId=USER_POOL_ID,
            Username=email
        )
        logger.info(f"User {email} auto-confirmed")

        # Add the user to the 'Doctor' group
        cognito_client.admin_add_user_to_group(
            UserPoolId=USER_POOL_ID,
            Username=email,
            GroupName=DOCTOR_GROUP
        )
        logger.info(f"User {email} added to group {DOCTOR_GROUP}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'User {email} registered, confirmed, and added to group {DOCTOR_GROUP}'
            })
        }

    except ClientError as e:
        logger.error(f"Cognito error: {e.response['Error']['Message']}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error', 'error': e.response['Error']['Message']})
        }

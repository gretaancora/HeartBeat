# Serverless Heart Rate Streaming And Batch Processing Architecture
This repository contains the final project for the course of Distributed Systems and Cloud Computing of the University of Rome Tor Vergata (faculty Computer Engineering).

To execute the project follow the next steps:

## Create the AWS Environment
1. Create a bucket and upload the Lambda zip to it -> heart-beat-lambda-deployment (leave all settings at default)

2. In the Swagger file find ID 216698350696 and replace it with your own

3. Create a bucket for the REST API and upload the Swagger to it -> heart-beat-rest-api (leave all settings at default)

4. Create a Cognito user pool ->

    Traditional web application

    Application name -> HeartBeat

    Sign-in identifiers options -> email

    Required sign-in attributes -> email

5. In Cognito -> App client -> Edit -> enable all authentication flows -> save changes

6. Replace the pool ID you created in Cognito in CognitoTemplate (UserPoolId) and replace the RoleArn by putting the one you will use for creating the stack in CloudFormation

7. Create a stack with the new resources from the CognitoTemplate in CloudFormation

    Note: for CloudFormation -> Template source: upload a template file -> submit

8. If you want to test the admin features you need to manually add a user to Cognito and assign them the Admin role -> do this via the app client in Cognito and click “View sign-in page” so that the user is already confirmed

9. Create a stack with the new resources from the BatchBucketTemplate in CloudFormation

10. Create a stack with the new resources from the RestAPITemplate in CloudFormation

11. In HeartBeatTemplate change ->

    ARN of the role with which you want to instantiate the services

    Find ID 216698350696 and replace it with your own

    Put the new pool ID, client ID, and client secret in the Lambda environment variables

    Insert the ARN of the API you created

    For the functions checkPatientGroupAuth, checkDoctorGroupAuth, and checkAdminGroupAuth in SourceArn:
    "arn:aws:execute-api:us-east-1:216698350696:3we4sfdvrh/authorizers/vy1o5f"
    replace 216698350696 with your own ID, 3we4sfdvrh with the API ID, and vy1o5f with the authorizer ID for the specific authorizer

12. Create a stack with the new resources from the HeartBeatTemplate in CloudFormation

13. Manually add an S3 trigger for the splitBatchData Lambda function ->

    On splitBatchData click the “Add trigger” button

    Select S3

    Select bucket batchdataheartbeatcopy

    Select event type PUT

    Accept using the S3 bucket for both input and output

14. Modify the HTTP calls to API Gateway in the HTML files

15. Put the HTML files into the frontend bucket, select them all, and via Actions make all pages public using ACL

## Run the code
1. If you want to test the streamingMQTT.py script

    Generate and download the certificates for the already instantiated thing

    Rename the certificates as follows: device certificate -> device-cert.pem, private key file -> device-key.pem, Amazon Root CA 1 certificate -> root-CA.pem

    Attach the IoTSimulator policy to the certificate

    Modify the endpoint in the script to the one created in IoT Core

    Run the script from a directory containing the certificates as well

2. If you want to test the batchMQTT.py script run it inside CloudShell
Note: for the scripts data to be processed there must be an entry in the IoTPatient DynamoDB table with deviceId=IoTSimulator

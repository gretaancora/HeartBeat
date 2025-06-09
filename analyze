import os
import json
import boto3
from typing import Any, Dict, List, Union

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Union[str, bool, List[Any]]]:
    """
    Second step Lambda in Step Functions state machine.
    Expects the input event to contain 'patientid' and 'data' (4096x12 tensor).
    Invokes a pre-trained SageMaker endpoint and returns a dict with:
      - 'patientid': forwarded patient ID
      - 'flag': True if any of the 6 output values >= 0.3
      - 'input': the original tensor
      - 'output_values': list of 6 floats returned by the model
    """
    # Extract patientid
    patient_id = event.get('patientid')
    if patient_id is None:
        raise ValueError("Missing required 'patientid' in event")

    # Extract data tensor
    input_tensor = event.get('data')
    if input_tensor is None:
        raise ValueError("Missing required 'data' in event")

    # Serialize only the data tensor for SageMaker
    try:
        body = json.dumps(input_tensor)
    except (TypeError, ValueError) as e:
        raise Exception(f"Failed to serialize data tensor: {e}")

    # Initialize SageMaker runtime client
    sm_runtime = boto3.client('sagemaker-runtime')
    endpoint_name = os.environ.get('ENDPOINT_NAME')
    if not endpoint_name:
        raise Exception('Missing required environment variable: ENDPOINT_NAME')

    # Invoke the endpoint
    response = sm_runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType='application/json',
        Body=body
    )

    # Read and parse the inference result
    result_bytes = response['Body'].read()
    try:
        result_str = result_bytes.decode('utf-8')
        output_values = json.loads(result_str)
    except Exception:
        raise Exception("Failed to parse inference response")

    # Validate output_values
    if not isinstance(output_values, list) or len(output_values) != 6:
        raise Exception(f"Expected list of 6 output values, got: {output_values}")

    # Compute boolean flag
    flag = any(v >= 0.3 for v in output_values)

    # Return results including patientid
    return {
        'patientid': patient_id,
        'flag': flag,
        'input': input_tensor,
        'output_values': output_values
    }

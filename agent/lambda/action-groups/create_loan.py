import os
import io
import re
import json
import time
import boto3
import base64
import random
import string
import decimal
import requests

# DynamoDB boto3 resource and variable
dynamodb = boto3.resource('dynamodb',region_name=os.environ['AWS_REGION'])
loans_table_name = os.environ['LOAN_TABLE_NAME']

# SNS boto3 clients and variables
sns_topic_arn = os.environ['SNS_TOPIC_ARN']
sns_client = boto3.client('sns')

# URL
url = os.environ['CUSTOMER_WEBSITE_URL']

def get_named_parameter(event, name):
    try:
        return next(item for item in event['parameters'] if item['name'] == name)['value']
    except (KeyError, StopIteration):
        return None

def get_named_property(event, name):
  try:
    return next(item for item in event['requestBody']['content']['application/json']['properties'] if item['name'] == name)['value']
  except (KeyError, StopIteration):
    return None

def Loan_generator():
    print("Generating Loan ID")

    # Generate random characters and digits
    digits = ''.join(random.choice(string.digits) for _ in range(4))  # Generating 4 random digits
    chars = ''.join(random.choice(string.ascii_lowercase) for _ in range(3))  # Generating 3 random characters
    
    # Construct the pattern (1a23b-4c)
    # pattern = f"{digits[0]}{chars[0]}{digits[1:3]}{chars[1]}-{digits[3]}{chars[2]}"
    # Construct the pattern (ab-xy)
    pattern = f"{chars[0]}{chars[1]}-{chars[2]}{chars[3]}"
    return pattern

def collect_documents(Loan_id):
    print("Collecting Loan Documents")

    subject = "New Loan ID: " + Loan_id
    message = "Please upload your Loan evidence and required documents in the AnyCompany Mortgage Portal: " + url

    sns_client.publish(
        TopicArn=sns_topic_arn,
        Subject=subject,
        Message=message,
    )

def create_Loan(event):
    print("Creating Loan")

    # TODO: Loan creation logic
    generated_Loan = Loan_generator()
    mls_id = get_named_property(event, 'mls_id')
    income = get_named_property(event, 'income')
    liabilities = get_named_property(event, 'total_debt')
    loan_amount = get_named_property(event, 'loan_amount')
    # Update Excel data as needed (for example, add a new row with a new Loan)
    new_Loan_data = {'loan_id': generated_Loan, 'mls_id': mls_id, 'income': income, 'liabilities': liabilities, 'loan_amount': loan_amount, 'status': 'Pending', 'pendingDocuments': ['Drivers License', 'W2', 'Pay Stubs']}  # Update column names and values

    # Update DynamoDB
    print("Updating DynamoDB")

    # Convert JSON document to DynamoDB format
    dynamodb_item = json.loads(json.dumps(new_Loan_data), parse_float=decimal.Decimal)
    existing_Loans_table = dynamodb.Table(loans_table_name)
    response = existing_Loans_table.put_item(
        Item=dynamodb_item
    ) 

    collect_documents(generated_Loan)

    return {
        "response": [new_Loan_data]   
    }
 
def lambda_handler(event, context):
    response_code = 200
    action_group = event['actionGroup']
    api_path = event['apiPath']
    # dump event object
    print(json.dumps(event))
    # API path routing
    if api_path == '/create-loan':
        body = create_Loan(event)
    else:
        response_code = 400
        body = {"{}::{} is not a valid api, try another one.".format(action_group, api_path)}

    response_body = {
        'application/json': {
            'body': str(body)
        }
    }
    
    # Bedrock action group response format
    action_response = {
        "messageVersion": "1.0",
        "response": {
            'actionGroup': action_group,
            'apiPath': api_path,
            'httpMethod': event['httpMethod'],
            'httpStatusCode': response_code,
            'responseBody': response_body
        }
    }
 
    return action_response
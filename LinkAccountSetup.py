import boto3
import re

# Get the username details for the specified AWS account
sts_client = boto3.client("sts")
account_id = sts_client.get_caller_identity().get("Account")

# Get input parameters from user
region = 'us-east-1'


# Prompt the user to enter the value for the CimaBusArn parameter
cima_bus_arn = input("Enter the value for CimaBusArn parameter: ")

def deploy_cloudformation_template(template_path, parameters):
    cloudformation = boto3.client('cloudformation',region)
    
    with open(template_path, 'r') as file:
        template_body = file.read()
    
    stack_name = "CimaLink{}".format(account_id)
    
    try:
        response = cloudformation.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Parameters=parameters,
            Capabilities=['CAPABILITY_NAMED_IAM']
        )
        print("CloudFormation stack creation initiated. Stack ID:", response['StackId'])
    except Exception as e:
        print("Failed to create CloudFormation stack:", str(e))

# Specify the path to the CloudFormation YAML template
template_path = 'src/Cimatemplates/Cima-LinkAccSetup.yaml'

# Input parameter values
parameters = [{'ParameterKey': 'CimaBusArn','ParameterValue': cima_bus_arn}]

deploy_cloudformation_template(template_path, parameters)

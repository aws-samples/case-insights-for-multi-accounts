import boto3
import subprocess
from botocore.exceptions import ClientError
import os

#Get Current Account ID
def get_account_id():
    # Get the AWS account ID for Unique names
    sts_client = boto3.client("sts")
    account_id = sts_client.get_caller_identity().get("Account")
    return account_id

#Get yes or no for modules
def ask_yes_no(prompt):
    while True:
        user_input = input(f"{prompt} (yes/no): ").lower()
        if user_input == 'yes':
            return True
        elif user_input == 'no':
            return False
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")
#Print pretty Box
def print_boxed_text(text):
    lines = text.strip().split('\n')
    max_length = max(len(line) for line in lines)
    
    print('═' * (max_length + 2))
    for line in lines:
        print(f' {line.ljust(max_length)} ')
    print('═' * (max_length + 2))

#Save Input to file for future use
def save_output_to_file(output):
    with open('utils/ParametersMember.txt', 'w') as file:
        file.write(output + '\n')

#deploy stack
def deploy_stack(command):
    try:
        subprocess.call(command, shell=True)
    except Exception as e:
        print("An error occurred:", e)

#User Input Data
def get_user_input():
    DeploymentRegionHealth = ""
    DeploymentRegionCases = ""
    EnableHealthModule = ask_yes_no("Do you want to enable the AWS Health Module? This Option must be NO if you have already enabled health in delegated health admin account")
    if EnableHealthModule:
        DeploymentRegionHealth = input("  Enter comma-separated Region names for AWS health data collection: ")
    EnableCaseModule = ask_yes_no("Do you want to enable the Support Case Module?")
    if EnableCaseModule:
        DeploymentRegionCases = input("  Enter Region names for Cases Data Collection(MUST BE 'us-east-1' or 'us-west-2): ") or "us-east-1"
    EnableTAModule = ask_yes_no("Do you want to enable the Trusted Advisor Module?")
    if EnableTAModule:
        DeploymentRegionTA = input("  Enter Region names for TA Data Collection(MUST BE 'us-east-1' or 'us-west-2): ") or "us-east-1"
    print_boxed_text("Data Collection Account Parameters")
    DataCollectionAccountID = input("Enter Data Collection Account ID: ") 
    DataCollectionRegion = input("Enter Data Collection Region ID: ")
    MultiAccountRoleName = input("Enter MultiAccountRoleName, Hit enter to use default (MultiAccountRole): ") or "MultiAccountRole"
    ResourcePrefix = input("Enter ResourcePrefix, Hit enter to use default (Heidi-): ") or "Heidi-"

    return (
        "yes" if EnableHealthModule else "no",
        "yes" if EnableCaseModule else "no",
        DataCollectionAccountID, DataCollectionRegion, DeploymentRegionHealth, DeploymentRegionCases,
        MultiAccountRoleName, ResourcePrefix,
        "yes" if EnableTAModule else "no", DeploymentRegionTA
    )

def save_variables_to_file(variables):
    output = "\n".join([
        f"#Deploy AWS Health Events Intelligence Dashboards and Insights (HEIDI)\nEnableHealthModule: {variables[0]}\n",
        f"#Deploy Case Insights for Multi Accounts (CIMA)\nEnableCaseModule: {variables[1]}\n",
        f"#Deploy Trusted Advisor Insight Module\nEnableTAModule: {variables[8]}\n",
        f"#Data Collection Region\nDataCollectionAccountID: {variables[2]}\n",
        f"#Data Collection Account\nDataCollectionRegion: {variables[3]}\n",
        f"#Region to deploy for Health\nDeploymentRegionHealth: {variables[4]}\n",
        f"#Region to deploy for Cases\nDeploymentRegionCases: {variables[5]}\n",
        f"#Region to deploy for Trusted Advisor\nDeploymentRegionTA: {variables[9]}\n",
        f"#MultiAccount Rolename, DO NOT CHANGE\nMultiAccountRoleName: {variables[6]}\n",
        f"#Resource prefix, DO NOT CHANGE\nResourcePrefix: {variables[7]}\n"
    ])
    save_output_to_file(output)

def read_parameters(file_path):
    # Define a dictionary to store the parameters
    parameters = {}

    # Read the file and extract parameters
    with open(file_path, 'r') as file:
        for line in file:
            # Skip comments and empty lines
            if line.startswith('#') or not line.strip():
                continue
            
            # Split each line into key and value
            key, value = map(str.strip, line.split(':', 1))
            
            # Store in the dictionary
            parameters[key] = value

    # Access the variables
    enable_health_module = parameters.get('EnableHealthModule', '')
    enable_case_module = parameters.get('EnableCaseModule', '')
    enable_ta_module = parameters.get('EnableTAModule', '')
    data_collection_account_id = parameters.get('DataCollectionAccountID', '')
    data_collection_region = parameters.get('DataCollectionRegion', '')
    region_to_deploy_health = parameters.get('DeploymentRegionHealth', '')
    region_to_deploy_cases = parameters.get('DeploymentRegionCases', '')
    region_to_deploy_ta = parameters.get('DeploymentRegionTA', '')
    multi_account_role_name = parameters.get('MultiAccountRoleName', '')
    resource_prefix = parameters.get('ResourcePrefix', '')

    # Return the variables as a dictionary
    return {
        'EnableHealthModule': enable_health_module,
        'EnableCaseModule': enable_case_module,
        'EnableTAModule': enable_ta_module,
        'DataCollectionRegion': data_collection_region,
        'DataCollectionAccountID': data_collection_account_id,
        'DeploymentRegionHealth': region_to_deploy_health,
        'DeploymentRegionCases': region_to_deploy_cases,
        'DeploymentRegionTA': region_to_deploy_ta,
        'MultiAccountRoleName': multi_account_role_name,
        'ResourcePrefix': resource_prefix,
    }

def setup():
    file_path = 'utils/ParametersMember.txt'

    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            print_boxed_text(f"./utils/ParametersMember.txt  found with previously saved parameters")
            print(f"{file.read()}")
        reinput = ask_yes_no("Do you want to re-input parameters?")
        if reinput:
            variables = get_user_input()
            save_variables_to_file(variables)
        else:
            print("Skipping re-input. Using existing variables.")
    else:
        variables = get_user_input()
        save_variables_to_file(variables)
        print_boxed_text(f"\nDeployment will use these parameters. Update ./utils/ParametersMember.txt file for additional changes")
        with open(file_path, 'r') as file:
            print(f"{file.read()}")

    #Read dictionary for parameeters
    parameters_dict = read_parameters('utils/ParametersMember.txt')

    #Create Parameters
    parameters = f"DataCollectionAccountID={parameters_dict['DataCollectionAccountID']} \
                DataCollectionRegion={parameters_dict['DataCollectionRegion']}\
                EnableTAModule={parameters_dict['EnableTAModule']} \
                EnableHealthModule={parameters_dict['EnableHealthModule']} \
                EnableCaseModule={parameters_dict['EnableCaseModule']}\
                MultiAccountRoleName={parameters_dict['MultiAccountRoleName']} \
                ResourcePrefix={parameters_dict['ResourcePrefix']}"

    if parameters_dict['EnableHealthModule'] == 'yes':
        for region in parameters_dict.get('DeploymentRegionHealth', '').split(','):
            stack_name = f"Heidi-HealthModule-{get_account_id()}-{region}"
            command= f"sam deploy --stack-name {stack_name} --region {region} --parameter-overrides {parameters}\
                --template-file ../HealthModule/HealthModuleCollectionSetup.yaml --capabilities CAPABILITY_NAMED_IAM --disable-rollback"
            #Deploy Stack
            deploy_stack(command)

    if parameters_dict['EnableCaseModule'] == 'yes':
        region = parameters_dict['DeploymentRegionCases']
        stack_name = f"Heidi-SupportCaseModule-{get_account_id()}-{region}"
        command= f"sam deploy --stack-name {stack_name} --region {region} --parameter-overrides {parameters}\
            --template-file ../SupportCaseModule/SupportCaseModuleCollectionSetup.yaml --capabilities CAPABILITY_NAMED_IAM --disable-rollback"
        #Deploy Stack
        deploy_stack(command)

    if  parameters_dict['EnableTAModule'] == 'yes':
        region = parameters_dict['DeploymentRegionTA']
        stack_name = f"Heidi-TAModule-{get_account_id()}-{region}"
        command= f"sam deploy --stack-name {stack_name} --region {region} --parameter-overrides {parameters}\
            --template-file ../TrustedAdvisorModule/TAModuleCollectionSetup.yaml --capabilities CAPABILITY_NAMED_IAM --disable-rollback"
        #Deploy Stack
        deploy_stack(command)

if __name__ == "__main__":
    setup()



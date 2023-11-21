import boto3
import subprocess
from botocore.exceptions import ClientError
import os


#Get Current Region
def get_default_region():
    # Get the default AWS region from the current session
    session = boto3.Session()
    region = input(f"Enter region name (Hit enter to use default: {session.region_name}): ") or session.region_name
    return region

#Get Current Account ID
def get_account_id():
    # Get the AWS account ID for Unique names
    sts_client = boto3.client("sts")
    account_id = sts_client.get_caller_identity().get("Account")
    return account_id

#Get current AWS Organization ID
def get_organization_details():
    # Get the ID of the AWS organization for event bus
    org_client = boto3.client('organizations')
    POrgID = org_client.describe_organization()['Organization']['Id']
    return POrgID

#Create or update user with bucket KMS
def create_or_get_s3_bucket(account_id, region):
    #create bucket or upload file if bucket is supplied by user
    bucket_name = input(f"Enter S3 bucket name for Primary Region (Hit enter to use default: awseventhealth-{account_id}-{region}): ") or f"awseventhealth-{account_id}-{region}"
    try:
        s3_client = boto3.client('s3', region_name=region)
        s3_client.head_bucket(Bucket=bucket_name)
        response = s3_client.get_bucket_encryption(Bucket=bucket_name)
        encryption = response['ServerSideEncryptionConfiguration']['Rules'][0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
        if encryption != "AES256":
            try:
                bucketkmsarn = response['ServerSideEncryptionConfiguration']['Rules'][0]['ApplyServerSideEncryptionByDefault']['KMSMasterKeyID']
                print(f"Skip Creating: S3 bucket {bucket_name} exists and encrypted with kms {bucketkmsarn}")
            except KeyError:
                bucketkmsarn = input(f"Enter kms Key Arn for {bucket_name}: ")
        else:
            bucketkmsarn = "na"
            print(f"Skip Creating: S3 bucket {bucket_name} already exists")
    except ClientError as e:
        if region == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name)
            bucketkmsarn = "na"
        else:
            location = {'LocationConstraint': region}
            s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)
            bucketkmsarn = "na"
        s3_client.get_waiter("bucket_exists").wait(Bucket=bucket_name)
        print(f"S3 bucket {bucket_name} has been created")
    return bucket_name, bucketkmsarn

#Upload CFN and Metadatafiles
def sync_cfnfiles(bucket_name):
    #Sync cloudformation and metadata files
    try:
        aws_sync_command = f"aws s3 sync ../../src/ s3://{bucket_name}/DataCollection-metadata"
        subprocess.call(aws_sync_command.split())
    except ClientError as e:
        print("Error while syncing S3. Check if deployer role has required S3 and KMS permissions.")
        exit()

#Get QuickSight Author User
def get_quicksight_user(account_id, qsregion):
    #get quicksight user. ES user can have multiplenamespaces
    try:
        quicksight_client = boto3.client('quicksight', region_name=qsregion)
        response = quicksight_client.list_namespaces(AwsAccountId=account_id)
        namespaces = [namespace['Name'] for namespace in response['Namespaces']]
        qsusernames = []
    except:
        print("Error while listing namespaces. Check if QuickSight is an enterprise plan.")
        exit()
    try:
        for namespace in namespaces:
            response = quicksight_client.list_users(AwsAccountId=account_id, Namespace=namespace, MaxResults=100)
            qsusernames.extend([user['Arn'] for user in response['UserList']])
    except ClientError as q:
        print("Wrong QuickSight Identity region.")
        print(q)
        exit()
    print("\nAvailable QuickSight Users")
    try:
        for i, qsusername in enumerate(qsusernames, 1):
            print("{}. {}".format(i, qsusername))
        print()
        while True:
            quicksight_number = input("Enter the number corresponding to the QuickSight username from the list: ")
            quicksight_user = qsusernames[int(quicksight_number) - 1] if quicksight_number.isdigit() and 1 <= int(quicksight_number) <= len(qsusernames) else None
            if quicksight_user:
                return quicksight_user
            else: 
                print("Invalid Option") 
    except ClientError as q:
        print("Something went wrong, Check Quicksight settings")

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
    with open('utils/ParametersDataCollection.txt', 'w') as file:
        file.write(output + '\n')

#deploy stack
def deploy_stack(command):
    try:
        subprocess.call(command, shell=True)
    except Exception as e:
        print("An error occurred:", e)

#User Input Data
def get_user_input():
    SlackChannelId = "na"
    SlackWorkspaceId = "na"
    TeamId = "na"
    TeamsTenantId = "na"
    TeamsChannelId = "na"
    print_boxed_text("Module Selection")
    EnableHealthModule = ask_yes_no("Do you want to enable the AWS Health Module?")
    EnableCaseModule = ask_yes_no("Do you want to enable the Support Case Module?")
    EnableTAModule = ask_yes_no("Do you want to enable the Trusted Advisor Module?")
    EnableNotificationModule = ask_yes_no("Do you want to enable the Notification Module?")
    if EnableNotificationModule:
        print_boxed_text("Notification Module can setup notification for MS Teams and/Or slack")
        EnableSlack = ask_yes_no("Do you want to enable the Notification for Slack Channel?")
        if EnableSlack:
            SlackChannelId = input("    Provide Slack Channel Id (Note: Slack Channel must be private and you must invite aws@ to the channel): ") or "na"
            SlackWorkspaceId = input("    Provide Workspace ID: ") or "na"
        EnableTeams = ask_yes_no("Do you want to enable the Notification for Teams Channel?")
        if EnableTeams:
            TeamId = input("    Provide TeamId: ") or "na"
            TeamsTenantId = input("    Provide TeamsTenantId: ") or "na"
            TeamsChannelId = input("    Provide TeamsChannelId: ") or "na"
    region = get_default_region()
    account_id = get_account_id()
    AWSOrganizationID = get_organization_details()
    DataCollectionBucket, DataCollectionBucketKmsArn = create_or_get_s3_bucket(account_id, region)
    qsregion = input(f"Enter QuickSight Identity Region, Hit enter to use default {region}: ") or region
    QuickSightAnalysisAuthor = get_quicksight_user(account_id, qsregion)
    AthenaResultBucket = input("Enter AthenaResultBucket, Hit enter to use default (aws-athena-query-results-*): ") or "aws-athena-query-results-*"
    AthenaBucketKmsArn = input("Enter AthenaBucketKmsArn, Hit enter to use default (na): ") or "na"
    QuicksightServiceRole = input("Hit enter to use default (aws-quicksight-service-role-v0): ") or "aws-quicksight-service-role-v0"
    MultiAccountRoleName = input("Enter MultiAccountRoleName, Hit enter to use default (MultiAccountRole): ") or "MultiAccountRole"
    ResourcePrefix = input("Enter ResourcePrefix, Hit enter to use default (Heidi-): ") or "Heidi-"

    return (
        "yes" if EnableCaseModule else "no",
        "yes" if EnableHealthModule else "no",
        region, account_id, AWSOrganizationID,
        DataCollectionBucket, DataCollectionBucketKmsArn, QuickSightAnalysisAuthor,
        AthenaResultBucket, AthenaBucketKmsArn, QuicksightServiceRole,
        MultiAccountRoleName, ResourcePrefix, 
        "yes" if EnableNotificationModule else "no",
        SlackChannelId, SlackWorkspaceId, TeamId, TeamsTenantId, TeamsChannelId, qsregion,
         "yes" if EnableTAModule else "no" 
    )

def save_variables_to_file(variables): #last variable is variables[20], increment from here and also update this comment.
    output = "\n".join([
        f"#Deploy AWS Health Events Intelligence Dashboards and Insights (HEIDI)\nEnableHealthModule: {variables[1]}\n",
        f"#Deploy Case Insights for Multi Accounts (CIMA)\nEnableCaseModule: {variables[0]}\n",
        f"#Deploy Trusted Advisor Insight Module\nEnableTAModule: {variables[20]}\n",
        f"#Deploy Notification module\nEnableNotificationModule: {variables[13]}\n",
        f"#Data Collection Region\nDataCollectionRegion: {variables[2]}\n",
        f"#Data Collection Account\nDataCollectionAccountID: {variables[3]}\n",
        f"#AWS Organization ID which can send events to Data Collection Account\nAWSOrganizationID: {variables[4]}\n",
        f"#QuickSight Analysis Author\nQuickSightAnalysisAuthor: {variables[7]}\n",
        f"#Bucket which would collection data from various members\nDataCollectionBucket: {variables[5]}\n",
        f"#Update here if Collection bucket is encrypted with KMS otherwise na\nDataCollectionBucketKmsArn: {variables[6]}\n",
        f"#Update here if Athena result bucket is not default\nAthenaResultBucket: {variables[8]}\n",
        f"#Update here Athena bucket is encrypted with KMS otherwise na\nAthenaBucketKmsArn: {variables[9]}\n",
        f"#Update here if QuicksightServiceRole is not default\nQuicksightServiceRole: {variables[10]}\n",
        f"#MultiAccount Rolename, DO NOT CHANGE\nMultiAccountRoleName: {variables[11]}\n",
        f"#Resource prefix, DO NOT CHANGE\nResourcePrefix: {variables[12]}\n",
        f"#If EnableNotificationModule, Provide SlackChannelId for slack\nSlackChannelId: {variables[14]}\n",
        f"#If EnableNotificationModule, Provide SlackWorkspaceId for slack\nSlackWorkspaceId: {variables[15]}\n",
        f"#If EnableNotificationModule, Provide TeamId for MS Teams\nTeamId: {variables[16]}\n",
        f"#If EnableNotificationModule, Provide TeamsTenantId for MS Teams\nTeamsTenantId: {variables[17]}\n",
        f"#If EnableNotificationModule, Provide TeamsChannelId for MS Teams\nTeamsChannelId: {variables[18]}\n"
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
    enable_notification_module = parameters.get('EnableNotificationModule', '')
    data_collection_region = parameters.get('DataCollectionRegion', '')
    data_collection_account_id = parameters.get('DataCollectionAccountID', '')
    aws_organization_id = parameters.get('AWSOrganizationID', '')
    quicksight_analysis_author = parameters.get('QuickSightAnalysisAuthor', '')
    data_collection_bucket = parameters.get('DataCollectionBucket', '')
    data_collection_bucket_kms_arn = parameters.get('DataCollectionBucketKmsArn', 'na')
    athena_result_bucket = parameters.get('AthenaResultBucket', 'aws-athena-query-results-*')
    athena_bucket_kms_arn = parameters.get('AthenaBucketKmsArn', 'na')
    quicksight_service_role = parameters.get('QuicksightServiceRole', 'aws-quicksight-service-role-v0')
    multi_account_role_name = parameters.get('MultiAccountRoleName', '')
    resource_prefix = parameters.get('ResourcePrefix', '')
    slack_channel_id = parameters.get('SlackChannelId', '')
    Slack_Workspace_Id = parameters.get('SlackWorkspaceId', '')
    team_id = parameters.get('TeamId', '')
    Teams_Tenant_Id = parameters.get('TeamsTenantId', '')
    Teams_Channel_Id = parameters.get('TeamsChannelId', '')

    # Return the variables as a dictionary
    return {
        'EnableHealthModule': enable_health_module,
        'EnableCaseModule': enable_case_module,
        'EnableNotificationModule': enable_notification_module,
        'DataCollectionRegion': data_collection_region,
        'DataCollectionAccountID': data_collection_account_id,
        'AWSOrganizationID': aws_organization_id,
        'QuickSightAnalysisAuthor': quicksight_analysis_author,
        'DataCollectionBucket': data_collection_bucket,
        'DataCollectionBucketKmsArn': data_collection_bucket_kms_arn,
        'AthenaResultBucket': athena_result_bucket,
        'AthenaBucketKmsArn': athena_bucket_kms_arn,
        'QuicksightServiceRole': quicksight_service_role,
        'MultiAccountRoleName': multi_account_role_name,
        'ResourcePrefix': resource_prefix,
        'SlackChannelId': slack_channel_id,
        'SlackWorkspaceId': Slack_Workspace_Id,
        'TeamId': team_id,
        'TeamsTenantId': Teams_Tenant_Id,
        'TeamsChannelId': Teams_Channel_Id,
        'EnableTAModule': enable_ta_module
    }

def setup():
    file_path = 'utils/ParametersDataCollection.txt'

    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            print(f"./ParametersDataCollection.txt found with previously saved parameters")
            print_boxed_text(f"{file.read()}")
        reinput = ask_yes_no("Do you want to re-input parameters?")
        if reinput:
            variables = get_user_input()
            save_variables_to_file(variables)
        else:
            print("Skipping re-input. Using existing variables.")
    else:
        variables = get_user_input()
        save_variables_to_file(variables)
        print_boxed_text(f"\nDeployment will use these parameters. Update ./utils/ParametersDataCollection.txt file for additional changes")
        with open(file_path, 'r') as file:
            print(f"{file.read()}")

    #Read dictionary for parameeters
    parameters_dict = read_parameters('utils/ParametersDataCollection.txt')
    #sync cfn template files
    sync_cfnfiles(parameters_dict['DataCollectionBucket'])

    # Create or update the CloudFormation stack
    stack_name = f"Heidi-{parameters_dict['DataCollectionAccountID']}-{parameters_dict['DataCollectionRegion']}"

    parameters = f"AWSOrganizationID={parameters_dict['AWSOrganizationID']} " \
                f"DataCollectionBucket={parameters_dict['DataCollectionBucket']} " \
                f"DataCollectionBucketKmsArn={parameters_dict['DataCollectionBucketKmsArn']} " \
                f"AthenaBucketKmsArn={parameters_dict['AthenaBucketKmsArn']} " \
                f"QuicksightServiceRole={parameters_dict['QuicksightServiceRole']} " \
                f"QuickSightAnalysisAuthor={parameters_dict['QuickSightAnalysisAuthor']} " \
                f"MultiAccountRoleName={parameters_dict['MultiAccountRoleName']} " \
                f"ResourcePrefix={parameters_dict['ResourcePrefix']} " \
                f"SlackChannelId={parameters_dict['SlackChannelId']} " \
                f"SlackWorkspaceId={parameters_dict['SlackWorkspaceId']} " \
                f"TeamId={parameters_dict['TeamId']} " \
                f"TeamsTenantId={parameters_dict['TeamsTenantId']} " \
                f"TeamsChannelId={parameters_dict['TeamsChannelId']} " \
                f"EnableHealthModule={parameters_dict['EnableHealthModule']} " \
                f"EnableCaseModule={parameters_dict['EnableCaseModule']} " \
                f"EnableNotificationModule={parameters_dict['EnableNotificationModule']} " \
                f"EnableTAModule={parameters_dict['EnableTAModule']}"

    command= f"sam deploy --stack-name {stack_name} --region {parameters_dict['DataCollectionRegion']} --parameter-overrides {parameters}\
        --template-file ../DataCollectionModule/HeidiRoot.yaml --capabilities CAPABILITY_NAMED_IAM --disable-rollback"
    
    #Deploy Stack
    deploy_stack(command)

if __name__ == "__main__":
    setup()



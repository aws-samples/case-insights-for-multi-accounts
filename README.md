# What is this solution indented for?

AWS-CIMA (Case Insights for Multi-Accounts) presents a comprehensive visualization dashboard that simplifies the task of overseeing and tracking cases acorss multiple accounts within an organization. This dashboard streamlines the process of monitoring cases, making it effortless and efficient. Customers can conveniently manage and track the status and progress of all cases without the hassle of logging in separately to each individual AWS account.

**Key Features:**

* Centralized Visualization Dashboard : CIMA offers a centralized platform that presents a visual representation of case data from various accounts within an organization.  This dashboard serves as a single point of access, enabling users to view and analyze case information in a centralized and intuitive manner.

* Streamlined Case Monitoring : With CIMA, the process of monitoring cases is optimized and made more efficient. The dashboard provides a streamlined interface where users can easily track the status, progress and key metrics of all cases across multiple accounts, eliminating the need for manual tracking or logging into each account separately. 

* Real-time Updates: The visualization dashboard in CIMA ensures that users have access to real-time updates on cases status and progress. This timeline information empowers organizations to make informed decisions and take necessary actions promptly, leading improved efficiency and customer satisfaction.

<div align="center">
  <img src="img/sampleDashboard.jpg" alt="Sample Dashboard">
</div>

# Solution architecture
The following architecture shows a multi-account structure.  These accounts can be standalone or associated with different or the same AWS organizations. To simplify, we will refer to the central account as the account which will receive events from all link account and the link account as the account enhancing and sending the events to central account.  
 ![ALT](img/cima-arch.jpg)

**Central Account Overview** Central Account architecture consist of EventBridge Custom bus, EventBridge rule, Lambda function and Amazon DynamoDB. The presentation layer included, Amazon Quicksight  and Amazon Athena. 
1.	The EventBridge custom bus receives events from linked accounts. When an event match pattern `({"source": ["aws.Cima"]})`, an EventBridge rule triggers a Lambda function, which put the event in DynamoDB table.
2.	Amazon QuickSight connects to DynamoDB table though Amazon Athena federated query and present the data in one single dashboard. 

**Link Account Overview** Link Account architecture consist of AWS Lambda function, two Eventbridge rules, and AWS Support Service.
1.	When case is opened, updated, or closed, AWS Support service emits an event and puts the event in the default event bus associated with the account. 
2.	First EventBridge rule on the default bus triggers a Lambda function when the event matched with  pattern `({"source": ["aws.support"]})` and pass case-id to the lambda function.
3.	The Lambda function invokes the AWS Support API, enhances the event by appending a user-friendly message, and subsequently put the enriched event to the default bus with source as "Cima."
4.	The second EventBridge rule on the default bus publishes an event to the default bus of the central account when it matches  pattren `({"source": ["aws.Cima"]})`

# Prerequisite
To setup this solution, You need basic familiarity with the AWS Management Console, an AWS account:
1.	Before you use the AWS support APIs, you need to have a Business Support, Enterprise On-Ramp or Enterprise Support plan from AWS Support. 
2.	Sign up for Amazon QuickSight if you have never used it in this account. To use the forecast capability in QuickSight, sign up for the Enterprise Edition. 
3.	Verify Amazon QuickSight service has access to Amazon Athena. To enable, go to security and permissions under manage QuickSight. 
4.	This solution uses SPICE to hold data. Go to SPICE capacity under manage QuickSight and verify you have required space.

# Deploying the solution
In this section, we will go through the steps to set up components for both the central and member accounts.

**Central Account Setup**
This blog post provides a sample code that demonstrates how to set up all the essential components needed to receive case data from various accounts. 
1.	To start, login to your AWS account and launch AWS CloudShell.
2.	 Clone Case-Insights-for-Multi-accounts repo. 

`git clone https://github.com/aws-samples/case-insights-for-multi-accounts.git`

3.	Go to Clone Case-Insights-for-Multi-accounts directory and run setup script.

`cd case-insights-for-multi-accounts`

`python3 CentralAccountSetup.py`

**Link Account Setup**
Once central account setup is complete, proceed with link account setup. You have two deployment options as follows.

**Option 1:** Using setup script.
1.	Setup AWS credentials for desired account. If you are using AWS CloudShell, Clone repo again to the link account.
2.	Go to Case-Insights-for-Multi-accounts directory and run following setup script.

`python3 LinkAccountSetup.py`

**Option 2:** Bulk deployment via StackSet:
1.	Go to CloudFormation Console and create a stackset with new resources from the template file Cima-LinkAccSetup.yaml  in Case-Insights-for-Multi-accounts/src/CimaTemplates directory.
2.	Input the central account EventBridge custom bus ARN. 
3.	Select deployment targets (Deploy to OU or deploy to organization).
4.	Select us-east-1 regions to deploy.
5.	Submit.
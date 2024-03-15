# Deployment Guide
---

## Content
- [Pre-Implementation](#pre-Implementation)
- [Create Knowledge Base](#create-knowledge-base-for-amazon-bedrock)
- [Create Agent](#create-agent-for-amazon-bedrock)
- [Testing and Validation](#testing-and-validation)

## Pre-Implementation
By default, AWS CloudFormation uses a temporary session that it generates from your user credentials for stack operations. If you specify a service role, CloudFormation will instead use that role's credentials.

To deploy this solution, your IAM user/role or service role must have permissions to deploy the resources specified in the CloudFormation template. For more details on AWS Identity and Access Management (IAM) with CloudFormation, please refer to the [AWS CloudFormation User Guide](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-template.html).

You must also have [AWS CLI](https://aws.amazon.com/cli/) installed. For instructions on installing AWS CLI, please see [Installing, updating, and uninstalling the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html).

### Clone [bedrock-loan-app-automation](https://gitlab.aws.dev/rrkasthu/bedrock-loan-app-automation/) Repository
1. Create a local copy of the **bedrock-loan-app-automation** repository using _git clone_:


#### Optional - Run Security Scan on the CloudFormation Templates
To run a security scan on the [AWS CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html) templates using [`cfn_nag`](https://github.com/stelligent/cfn_nag) (recommended), you have to install `cfn_nag`:

```sh
brew install ruby brew-gem
brew gem install cfn-nag
```

To initiate the security scan, run the following command:
```sh
cfn_nag_scan --input-path cfn/create-customer-resources.yml
```

### Deploy CloudFormation Stack to Emulate Existing Customer Resources 
To emulate the existing customer resources utilized by the agent, this solution uses the [create-customer-resources.sh](../shell/create-customer-resources.sh) shell script to automate provisioning of the parameterized CloudFormation template, [bedrock-customer-resources.yml](../cfn/bedrock-customer-resources.yml), to deploy the following resources:

> - [Amazon DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html) tables populated with synthetic [loan data](../agent/lambda/data-loader/loan.json) and [property data](../agent/lambda/data-loader/property.json).
> - Three [AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html) functions that represent customer business logic for creating the loan, looking up an property based on the MLS ID and a custom maximum affordable loan calculator.
> - [Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html) bucket containing API documentation in OpenAPI schema format for the preceding Lambda functions and FAQs and the Seling guide from Fannie Mae [knowledge base data source assets](../agents/insurance-lifecycle-automation/agent/knowledge-base-assets).
> - [Amazon Simple Notification Service (SNS)](https://docs.aws.amazon.com/sns/latest/dg/welcome.html) topic to which policy holders' emails are subscribed for email alerting of claim status and pending actions.
> - [AWS Identity and Access Management (IAM)](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html) permissions for the preceding resources.

CloudFormation prepopulates stack parameters with the default values provided in the template. To provide alternative input values, you can specify parameters as environment variables that are referenced in the `ParameterKey=<ParameterKey>,ParameterValue=<Value>` pairs in the _provision-customer-resources.sh_ shell script's `aws cloudformation create-stack` command. 

1. Before you run the shell script, navigate to the directory where you cloned the _amazon-bedrock-samples_ repository and modify the shell script permissions to executable:

```sh
# If not already cloned, clone the remote repository (https://github.com/aws-samples/amazon-bedrock-samples) and change working directory to shell folder:
cd shell/
chmod u+x provision-customer-resources.sh
```

1. Set your CloudFormation stack name, SNS email, and evidence upload URL environment variables. The SNS email can be used for notifications and the evidence upload URL will be shared with borrowers to upload their loan related documents. 

```sh
export STACK_NAME=<YOUR-STACK-NAME> # Stack name must be lower case for S3 bucket naming convention
export SNS_EMAIL=<YOUR-POLICY-HOLDER-EMAIL> # Email used for SNS notifications
export EVIDENCE_UPLOAD_URL=<YOUR-EVIDENCE-UPLOAD-URL> # URL provided by the agent to the policy holder for evidence upload
```

3. Run the _provision-customer-resources.sh_ shell script to deploy the emulated customers resources defined in the _create-customer-resources.yml_ CloudFormation template. These are the resources on which the agent and knowledge base will be built:

```sh
source ./provision-customer-resources.sh -t create-stack
```



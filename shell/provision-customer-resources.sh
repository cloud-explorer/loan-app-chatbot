# If not already cloned, clone the remote repository (https://github.com/aws-samples/amazon-bedrock-samples) and change working directory to insurance agent shell folder
# cd amazon-bedrock-samples/agents/insurance-claim-lifecycle-automation/shell/
# chmod u+x create-customer-resources.sh
# export STACK_NAME=<YOUR-STACK-NAME> # Stack name must be lower case for S3 bucket naming convention
# export SNS_EMAIL=<YOUR-POLICY-HOLDER-EMAIL> # Email used for SNS notifications
# export EVIDENCE_UPLOAD_URL=<YOUR-EVIDENCE-UPLOAD-URL> # URL provided by the agent to the policy holder for evidence upload
# source ./create-customer-resources.sh

while getopts t: option
do
 case "${option}"
 in
 t) EXE_TYPE=${OPTARG};;
 esac
done

export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ARTIFACT_BUCKET_NAME=$STACK_NAME-customer-resources
export DATA_LOADER_KEY="agent/lambda/data-loader/loader_deployment_package.zip"
export CREATE_LOAN_KEY="agent/lambda/action-groups/create_loan.zip"
export LOAN_CALCULATOR_KEY="agent/lambda/action-groups/loan_calculator.zip"
export MLS_LOOKUP_KEY="agent/lambda/action-groups/mls_lookup.zip"
export GATHER_EVIDENCE_KEY="agent/lambda/action-groups/gather_evidence.zip"
export SEND_REMINDER_KEY="agent/lambda/action-groups/send_reminder.zip"

echo ${ARTIFACT_BUCKET_NAME}

# remove all zip file in the action-groups folder
rm ../agent/lambda/action-groups/*.zip
#create a zip of all .py file in the action-groups folder and store it in the action-groups folder
zip -r -j ../agent/lambda/action-groups/create_loan.zip ../agent/lambda/action-groups/create_loan.py
zip -r -j ../agent/lambda/action-groups/gather_evidence.zip ../agent/lambda/action-groups/gather_evidence.py
zip -r -j ../agent/lambda/action-groups/send_reminder.zip ../agent/lambda/action-groups/send_reminder.py
zip -r -j ../agent/lambda/action-groups/loan_calculator.zip ../agent/lambda/action-groups/loan_calculator.py
zip -r -j ../agent/lambda/action-groups/mls_lookup.zip ../agent/lambda/action-groups/mls_lookup.py


# remove all zip file in the action-groups folder
#create a single zip of all files in the data-loader folder (with name loader_deployment_package.zip) and store it in the data-loader folder
(cd ../agent/lambda/data-loader && rm loader_deployment_package.zip && zip -r loader_deployment_package.zip *)

# check is a bucket with name in the variable ARTIFACT_BUCKET_NAME exists else create one using s3api
if aws s3api head-bucket --bucket $ARTIFACT_BUCKET_NAME 2>/dev/null
then
    echo "Bucket $ARTIFACT_BUCKET_NAME already exists. Skipping bucket creation."
else
    echo "Bucket $ARTIFACT_BUCKET_NAME does not exist. Creating bucket..."
    aws s3api create-bucket --bucket $ARTIFACT_BUCKET_NAME --region us-east-1
fi
# upload all files in the agent folder to the bucket with name in the variable ARTIFACT_BUCKET_NAME
aws s3 cp ../agent/ s3://${ARTIFACT_BUCKET_NAME}/agent/ --recursive --exclude ".DS_Store"

export BEDROCK_AGENTS_LAYER_ARN=$(aws lambda publish-layer-version \
    --layer-name bedrock-agents \
    --description "Agents for Bedrock Layer" \
    --license-info "MIT" \
    --content S3Bucket=${ARTIFACT_BUCKET_NAME},S3Key=agent/lambda/lambda-layer/bedrock-agents-layer.zip \
    --compatible-runtimes python3.11 \
    --query LayerVersionArn --output text)

eval `aws cloudformation ${EXE_TYPE} \
--stack-name ${STACK_NAME} \
--template-body file://../cfn/create-customer-resources.yml \
--parameters \
ParameterKey=ArtifactBucket,ParameterValue=${ARTIFACT_BUCKET_NAME} \
ParameterKey=DataLoaderKey,ParameterValue=${DATA_LOADER_KEY} \
ParameterKey=CreateLoanKey,ParameterValue=${CREATE_LOAN_KEY} \
ParameterKey=LoanCalculatorKey,ParameterValue=${LOAN_CALCULATOR_KEY} \
ParameterKey=MLSLookupKey,ParameterValue=${MLS_LOOKUP_KEY} \
ParameterKey=GatherEvidenceKey,ParameterValue=${GATHER_EVIDENCE_KEY} \
ParameterKey=SendReminderKey,ParameterValue=${SEND_REMINDER_KEY} \
ParameterKey=BedrockAgentsLayerArn,ParameterValue=${BEDROCK_AGENTS_LAYER_ARN} \
ParameterKey=SNSEmail,ParameterValue=${SNS_EMAIL} \
ParameterKey=EvidenceUploadUrl,ParameterValue=${EVIDENCE_UPLOAD_URL} \
--capabilities CAPABILITY_NAMED_IAM`

aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].StackStatus"
aws cloudformation wait stack-create-complete --stack-name $STACK_NAME
#!/bin/bash
# Automated AWS deployment script for Krugerrand Discord Bot
# Requires: AWS CLI configured with appropriate permissions

set -e

FUNCTION_NAME="krugerrand-bot"
API_NAME="krugerrand-bot-api"
REGION="${AWS_REGION:-us-east-1}"
RUNTIME="python3.11"
HANDLER="lambda_function.lambda_handler"
ZIP_FILE="lambda_function.zip"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting AWS deployment...${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed.${NC}"
    echo "Install it from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if zip file exists
if [ ! -f "$ZIP_FILE" ]; then
    echo -e "${YELLOW}Deployment package not found. Creating it...${NC}"
    ./deploy_lambda.sh
fi

# Check if Lambda function exists
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" &> /dev/null; then
    echo -e "${YELLOW}Updating existing Lambda function: $FUNCTION_NAME${NC}"
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://$ZIP_FILE" \
        --region "$REGION" > /dev/null
    echo -e "${GREEN}Lambda function code updated${NC}"
else
    echo -e "${YELLOW}Creating new Lambda function: $FUNCTION_NAME${NC}"
    
    # Check for required environment variables
    if [ -z "$DISCORD_PUBLIC_KEY" ] || [ -z "$DISCORD_APPLICATION_ID" ]; then
        echo -e "${RED}Error: DISCORD_PUBLIC_KEY and DISCORD_APPLICATION_ID must be set${NC}"
        echo "Export them first:"
        echo "  export DISCORD_PUBLIC_KEY='your_public_key'"
        echo "  export DISCORD_APPLICATION_ID='your_app_id'"
        exit 1
    fi
    
    # Create IAM role (simplified - you may need to create this manually)
    ROLE_ARN=$(aws iam get-role --role-name lambda-execution-role --query 'Role.Arn' --output text 2>/dev/null || echo "")
    
    if [ -z "$ROLE_ARN" ]; then
        echo -e "${YELLOW}Creating IAM role for Lambda...${NC}"
        # Create trust policy
        cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
        
        aws iam create-role \
            --role-name lambda-execution-role \
            --assume-role-policy-document file:///tmp/trust-policy.json \
            --region "$REGION" > /dev/null
        
        # Attach basic Lambda execution policy
        aws iam attach-role-policy \
            --role-name lambda-execution-role \
            --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
            --region "$REGION"
        
        sleep 5  # Wait for role to propagate
        
        ROLE_ARN=$(aws iam get-role --role-name lambda-execution-role --query 'Role.Arn' --output text --region "$REGION")
    fi
    
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --role "$ROLE_ARN" \
        --handler "$HANDLER" \
        --zip-file "fileb://$ZIP_FILE" \
        --timeout 30 \
        --memory-size 256 \
        --environment "Variables={DISCORD_PUBLIC_KEY=$DISCORD_PUBLIC_KEY,DISCORD_APPLICATION_ID=$DISCORD_APPLICATION_ID}" \
        --region "$REGION" > /dev/null
    
    echo -e "${GREEN}Lambda function created${NC}"
fi

# Get function ARN
FUNCTION_ARN=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" --query 'Configuration.FunctionArn' --output text)

echo -e "${GREEN}Lambda function ARN: $FUNCTION_ARN${NC}"

# API Gateway setup (simplified - manual setup recommended for first time)
echo -e "${YELLOW}Note: API Gateway setup is complex. Please follow the manual steps in DEPLOYMENT.md${NC}"
echo -e "${YELLOW}Or use AWS Console to create API Gateway and connect it to your Lambda function${NC}"

echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Create API Gateway in AWS Console"
echo "2. Connect it to Lambda function: $FUNCTION_NAME"
echo "3. Deploy the API"
echo "4. Copy the Invoke URL to Discord Developer Portal"
echo ""
echo "See DEPLOYMENT.md for detailed instructions"

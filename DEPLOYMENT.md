# AWS Lambda Deployment Guide

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI installed and configured (optional, for automated deployment)
3. Discord Application ID and Public Key from Discord Developer Portal

## Step 1: Get Discord Credentials

1. Go to https://discord.com/developers/applications
2. Select your application
3. Go to **General Information**:
   - Copy **Application ID** → This is your `DISCORD_APPLICATION_ID`
   - Copy **Public Key** → This is your `DISCORD_PUBLIC_KEY`

## Step 2: Create Deployment Package

The deployment package (`lambda_function.zip`) has already been created. If you need to recreate it:

```bash
cd krugerrand-bot
bash deploy_lambda.sh
```

## Step 3: Create Lambda Function (AWS Console)

### Option A: Using AWS Console (Recommended for first-time setup)

1. **Go to AWS Lambda Console**
   - Navigate to: https://console.aws.amazon.com/lambda/
   - Click **"Create function"**

2. **Configure Function**
   - Choose: **"Author from scratch"**
   - Function name: `krugerrand-bot` (or any name you prefer)
   - Runtime: **Python 3.11** or **Python 3.12**
   - Architecture: **x86_64**
   - Click **"Create function"**

3. **Upload Deployment Package**
   - Scroll down to **"Code source"** section
   - Click **"Upload from"** → **".zip file"**
   - Select `lambda_function.zip` from your `krugerrand-bot` directory
   - Click **"Save"**

4. **Configure Handler**
   - In **"Runtime settings"**, click **"Edit"**
   - Handler: `lambda_function.lambda_handler`
   - Click **"Save"**

5. **Set Environment Variables**
   - Go to **"Configuration"** → **"Environment variables"**
   - Click **"Edit"** → **"Add environment variable"**
   - Add:
     - Key: `DISCORD_PUBLIC_KEY`, Value: `[Your Discord Public Key]`
     - Key: `DISCORD_APPLICATION_ID`, Value: `[Your Discord Application ID]`
   - Click **"Save"**

6. **Increase Timeout**
   - Go to **"Configuration"** → **"General configuration"**
   - Click **"Edit"**
   - Timeout: Set to **30 seconds** (API calls can take time)
   - Click **"Save"**

## Step 4: Create API Gateway

1. **Go to API Gateway Console**
   - Navigate to: https://console.aws.amazon.com/apigateway/
   - Click **"Create API"**

2. **Choose API Type**
   - Select **"REST API"** → **"Build"**
   - Choose **"New API"**
   - API name: `krugerrand-bot-api`
   - Click **"Create API"**

3. **Create Resource and Method**
   - Click **"Actions"** → **"Create Resource"**
   - Resource Name: `discord` (or leave blank for root)
   - Click **"Create Resource"**
   - With the resource selected, click **"Actions"** → **"Create Method"**
   - Select **POST** from dropdown
   - Click the checkmark
   - Integration type: **Lambda Function**
   - Check **"Use Lambda Proxy Integration"**
   - Lambda Function: `krugerrand-bot` (or your function name)
   - Click **"Save"** → **"OK"** (when prompted to give API Gateway permission)

4. **Deploy API**
   - Click **"Actions"** → **"Deploy API"**
   - Deployment stage: **"New Stage"**
   - Stage name: `prod` (or `dev`)
   - Click **"Deploy"**

5. **Copy Invoke URL**
   - After deployment, you'll see the **"Invoke URL"**
   - Copy this URL (it looks like: `https://xxxxx.execute-api.region.amazonaws.com/prod`)
   - This is your Discord Interactions Endpoint URL

## Step 5: Configure Discord Interactions Endpoint

1. **Go to Discord Developer Portal**
   - Navigate to: https://discord.com/developers/applications
   - Select your application

2. **Set Interactions Endpoint**
   - Go to **"General Information"**
   - Scroll to **"Interactions Endpoint URL"**
   - Paste your API Gateway Invoke URL
   - Click **"Save Changes"**
   - Discord will verify the endpoint (it should show a green checkmark)

## Step 6: Test Your Bot

1. Go to your Discord server
2. Try the slash commands:
   - `/goldprice`
   - `/krugerrandprice`
   - `/krugerrandfact`

## Troubleshooting

### Lambda Function Errors

- **Check CloudWatch Logs**: Go to Lambda function → **"Monitor"** → **"View CloudWatch logs"**
- **Check timeout**: Make sure timeout is at least 30 seconds
- **Check environment variables**: Verify `DISCORD_PUBLIC_KEY` and `DISCORD_APPLICATION_ID` are set correctly

### API Gateway Issues

- **Check CORS**: If you get CORS errors, you may need to enable CORS in API Gateway
- **Check Lambda integration**: Verify the Lambda function name matches
- **Check deployment**: Make sure you've deployed the API after creating the method

### Discord Verification Fails

- **Check URL**: Make sure the Interactions Endpoint URL is exactly your API Gateway URL
- **Check Lambda response**: Lambda must return status 200 for Discord's verification ping
- **Check logs**: Look at CloudWatch logs to see what Discord is sending

## Option B: Using AWS CLI (Advanced)

If you have AWS CLI configured, you can use the `deploy_to_aws.sh` script:

```bash
./deploy_to_aws.sh
```

This will:
1. Create/update the Lambda function
2. Create/update API Gateway
3. Deploy the API
4. Output the endpoint URL

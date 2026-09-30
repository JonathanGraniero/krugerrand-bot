#!/bin/bash
# Simple deployment script for AWS Lambda
# This creates a deployment package for the Discord bot

echo "Creating Lambda deployment package..."

# Create a temporary directory
mkdir -p lambda_package
cd lambda_package

# Copy Python files
cp ../bot.py .
cp ../lambda_function.py .

# Install dependencies
pip install -r ../requirements.txt -t . --quiet

# Remove unnecessary files
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
find . -type d -name "*.dist-info" -exec rm -r {} + 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true

# Create zip file
zip -r ../lambda_function.zip . -q

# Cleanup
cd ..
rm -rf lambda_package

echo "Deployment package created: lambda_function.zip"
echo "Upload this file to AWS Lambda and set the handler to: lambda_function.lambda_handler"

# PowerShell deployment script for AWS Lambda
# This creates a deployment package for the Discord bot

Write-Host "Creating Lambda deployment package..." -ForegroundColor Green

# Create a temporary directory
$tempDir = "lambda_package"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null
Set-Location $tempDir

# Copy Python files
Copy-Item ..\bot.py .
Copy-Item ..\lambda_function.py .

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r ..\requirements.txt -t . --quiet

# Remove unnecessary files
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -File -Filter "*.pyc" | Remove-Item -Force
Get-ChildItem -Recurse -Directory -Filter "*.dist-info" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Directory -Filter "*.egg-info" | Remove-Item -Recurse -Force

# Create zip file
Write-Host "Creating zip file..." -ForegroundColor Yellow
Compress-Archive -Path * -DestinationPath ..\lambda_function.zip -Force

# Cleanup
Set-Location ..
Remove-Item -Recurse -Force $tempDir

Write-Host "Deployment package created: lambda_function.zip" -ForegroundColor Green
Write-Host "Upload this file to AWS Lambda and set the handler to: lambda_function.lambda_handler" -ForegroundColor Cyan

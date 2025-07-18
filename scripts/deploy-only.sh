#!/bin/bash

# Simple deployment script that uses existing service principal credentials
set -e

# Load environment variables from .env file
if [ -f ".env" ]; then
    export $(cat .env | grep -v '#' | sed 's/\r$//' | awk '/=/ {print $1}' )
    echo "Loaded environment variables from .env file"
else
    echo "No .env file found. Please create one with your Azure credentials."
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Required environment variables
REQUIRED_VARS=("AZURE_SUBSCRIPTION_ID" "AZURE_RESOURCE_GROUP" "AZURE_CLIENT_ID" "AZURE_CLIENT_SECRET" "AZURE_TENANT_ID")

# Check if all required variables are set
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        print_message $RED "Error: $var is not set in .env file"
        exit 1
    fi
done

# Login with service principal
print_message $YELLOW "Logging in to Azure with service principal..."
az login --service-principal \
    --username "$AZURE_CLIENT_ID" \
    --password "$AZURE_CLIENT_SECRET" \
    --tenant "$AZURE_TENANT_ID"

# Set subscription
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
print_message $GREEN "Successfully logged in and set subscription"

# Deploy infrastructure
print_message $YELLOW "Deploying infrastructure to resource group: $AZURE_RESOURCE_GROUP"
az deployment group create \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --template-file ./infra/main.bicep \
    --parameters ./infra/parameters.json \
    --parameters containerImage="${IMAGE_NAME:-ghcr.io/maxali/pyrunner:latest}" \
    --output table

if [ $? -eq 0 ]; then
    print_message $GREEN "Infrastructure deployed successfully!"
    
    # Get the Container App URL
    CONTAINER_APP_URL=$(az containerapp show \
        --name "${AZURE_RESOURCE_GROUP#*-}" \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --query "properties.configuration.ingress.fqdn" \
        --output tsv 2>/dev/null)
    
    if [ -n "$CONTAINER_APP_URL" ]; then
        print_message $GREEN "Container App URL: https://$CONTAINER_APP_URL"
        
        # Test the deployment
        print_message $YELLOW "Testing deployment..."
        sleep 30  # Give it time to start
        
        if curl -s -f "https://$CONTAINER_APP_URL/health" > /dev/null; then
            print_message $GREEN "Health check passed! 🎉"
        else
            print_message $YELLOW "Health check failed, but deployment completed. The app may still be starting up."
        fi
    else
        print_message $YELLOW "Could not retrieve Container App URL. Check Azure portal."
    fi
else
    print_message $RED "Deployment failed!"
    exit 1
fi
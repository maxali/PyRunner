#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}PyRunner Azure Deployment with Azure Container Registry${NC}"
echo -e "${YELLOW}This will create an ACR and build the container image in Azure${NC}\n"

# Check if logged in to Azure
if ! az account show &>/dev/null; then
    echo -e "${RED}Error: Not logged in to Azure${NC}"
    echo "Please run: az login"
    exit 1
fi

# Variables
RESOURCE_GROUP="pyrunner-rg"
LOCATION="westeurope"
CONTAINER_APP_NAME="pyrunner"

# Show current subscription
SUBSCRIPTION=$(az account show --query name -o tsv)
echo -e "${BLUE}Current subscription:${NC} $SUBSCRIPTION"

# Create resource group if it doesn't exist
echo -e "\n${BLUE}Creating resource group...${NC}"
if az group exists --name $RESOURCE_GROUP | grep -q false; then
    az group create --name $RESOURCE_GROUP --location $LOCATION
    echo -e "${GREEN}Resource group created${NC}"
else
    echo -e "${YELLOW}Resource group already exists${NC}"
fi

# Deploy the Bicep template with ACR
echo -e "\n${BLUE}Deploying infrastructure with Azure Container Registry...${NC}"
DEPLOYMENT_OUTPUT=$(az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file infra/main-acr.bicep \
    --parameters containerAppName=$CONTAINER_APP_NAME \
    --query "properties.outputs" \
    -o json)

# Extract outputs
CONTAINER_APP_URL=$(echo $DEPLOYMENT_OUTPUT | jq -r '.containerAppUrl.value')
CONTAINER_APP_FQDN=$(echo $DEPLOYMENT_OUTPUT | jq -r '.containerAppFQDN.value')
ACR_NAME=$(echo $DEPLOYMENT_OUTPUT | jq -r '.acrName.value')
ACR_LOGIN_SERVER=$(echo $DEPLOYMENT_OUTPUT | jq -r '.acrLoginServer.value')

echo -e "\n${GREEN}Infrastructure deployed!${NC}"
echo -e "${BLUE}ACR Name:${NC} $ACR_NAME"
echo -e "${BLUE}ACR Login Server:${NC} $ACR_LOGIN_SERVER"

# Build and push Docker image to ACR
echo -e "\n${BLUE}Building and pushing Docker image to ACR...${NC}"

# Login to ACR
echo -e "${BLUE}Logging in to ACR...${NC}"
az acr login --name $ACR_NAME

# Build the image
echo -e "${BLUE}Building Docker image...${NC}"
docker build -t $ACR_LOGIN_SERVER/pyrunner:latest .

# Push to ACR
echo -e "${BLUE}Pushing image to ACR...${NC}"
docker push $ACR_LOGIN_SERVER/pyrunner:latest

# Update Container App with the new image
echo -e "\n${BLUE}Updating Container App with new image...${NC}"
az containerapp update \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_APP_NAME \
    --image $ACR_LOGIN_SERVER/pyrunner:latest

echo -e "\n${GREEN}Deployment complete!${NC}"
echo -e "${BLUE}Container App URL:${NC} $CONTAINER_APP_URL"

# Test the deployment
echo -e "\n${BLUE}Waiting for app to be ready...${NC}"
sleep 30  # Give the app time to start with new image

echo -e "\n${BLUE}Testing deployment...${NC}"
if curl -s --fail --max-time 10 "https://$CONTAINER_APP_FQDN/health" > /dev/null; then
    echo -e "${GREEN}Health check passed!${NC}"
    
    # Test a simple execution
    echo -e "\n${BLUE}Testing code execution...${NC}"
    RESPONSE=$(curl -s -X POST "https://$CONTAINER_APP_FQDN/run" \
        -H "Content-Type: application/json" \
        -d '{"code": "print(\"Hello from Azure!\")", "timeout": 5}')
    
    echo -e "${BLUE}Response:${NC} $RESPONSE"
else
    echo -e "${YELLOW}Warning: Health check failed. The app might still be starting up.${NC}"
    echo -e "Try accessing: https://$CONTAINER_APP_FQDN/health"
fi
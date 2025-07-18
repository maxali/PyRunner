#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}PyRunner Azure Deployment (No Role Assignments)${NC}"
echo -e "${YELLOW}This deployment will not create role assignments. You'll need to set them up manually.${NC}\n"

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

# Deploy the Bicep template
echo -e "\n${BLUE}Deploying Bicep template...${NC}"
DEPLOYMENT_OUTPUT=$(az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file infra/main-no-roles.bicep \
    --parameters containerAppName=$CONTAINER_APP_NAME \
    --query "properties.outputs" \
    -o json)

# Extract outputs
CONTAINER_APP_URL=$(echo $DEPLOYMENT_OUTPUT | jq -r '.containerAppUrl.value')
CONTAINER_APP_FQDN=$(echo $DEPLOYMENT_OUTPUT | jq -r '.containerAppFQDN.value')
PRINCIPAL_ID=$(echo $DEPLOYMENT_OUTPUT | jq -r '.systemAssignedIdentityPrincipalId.value')

echo -e "\n${GREEN}Deployment successful!${NC}"
echo -e "${BLUE}Container App URL:${NC} $CONTAINER_APP_URL"
echo -e "${BLUE}Container App FQDN:${NC} $CONTAINER_APP_FQDN"
echo -e "${BLUE}System Identity Principal ID:${NC} $PRINCIPAL_ID"

# Manual steps notification
echo -e "\n${YELLOW}=== MANUAL STEPS REQUIRED ===${NC}"
echo -e "${YELLOW}If you're using a private container registry (like ghcr.io), you need to:${NC}"
echo -e "1. Have an Azure admin grant the AcrPull role to the system identity:"
echo -e "   ${BLUE}az role assignment create \\${NC}"
echo -e "   ${BLUE}  --assignee $PRINCIPAL_ID \\${NC}"
echo -e "   ${BLUE}  --role AcrPull \\${NC}"
echo -e "   ${BLUE}  --scope /subscriptions/<subscription-id>${NC}"
echo -e "\n2. Update the Container App with registry credentials"
echo -e "\n${YELLOW}For public Docker Hub images, no additional steps are needed.${NC}"

# Test the deployment
echo -e "\n${BLUE}Testing deployment...${NC}"
sleep 10  # Give the app time to start

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

echo -e "\n${GREEN}Deployment complete!${NC}"
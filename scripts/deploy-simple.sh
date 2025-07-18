#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}PyRunner Simple Azure Deployment${NC}"

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
CONTAINER_APP_ENV="pyrunner-env"

# Create resource group
echo -e "\n${BLUE}Creating resource group...${NC}"
az group create --name $RESOURCE_GROUP --location $LOCATION --output none || true

# Create Container App Environment
echo -e "\n${BLUE}Creating Container App Environment...${NC}"
az containerapp env create \
    --name $CONTAINER_APP_ENV \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --output none || true

# Create Container App with a simple Python image
echo -e "\n${BLUE}Creating Container App...${NC}"
az containerapp create \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINER_APP_ENV \
    --image python:3.11-slim \
    --target-port 8000 \
    --ingress external \
    --cpu 1 \
    --memory 2 \
    --min-replicas 1 \
    --max-replicas 10 \
    --command "/bin/sh" \
    --args "-c" "echo 'Container started but no app code deployed yet'" \
    --output none

# Get the app URL
FQDN=$(az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    -o tsv)

echo -e "\n${GREEN}Deployment complete!${NC}"
echo -e "${BLUE}Container App URL:${NC} https://$FQDN"
echo -e "\n${YELLOW}Note: This is a placeholder deployment. To deploy your actual app:${NC}"
echo -e "1. Build and push your image to a registry"
echo -e "2. Update the container app with: az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --image <your-image>"
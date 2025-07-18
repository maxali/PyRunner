#!/bin/bash

# Setup script for Azure Container Apps deployment
set -e

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '#' | sed 's/\r$//' | awk '/=/ {print $1}' )
    echo "Loaded environment variables from .env file"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration - use environment variables if available, otherwise defaults
SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID:-}"
RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-pyrunner-rg}"
RESOURCE_GROUP_PROD="${AZURE_RESOURCE_GROUP_PROD:-pyrunner-rg-prod}"
LOCATION="${AZURE_LOCATION:-eastus}"
APP_NAME="pyrunner"
SERVICE_PRINCIPAL_NAME="pyrunner-sp"
CLIENT_ID="${AZURE_CLIENT_ID:-}"
CLIENT_SECRET="${AZURE_CLIENT_SECRET:-}"
TENANT_ID="${AZURE_TENANT_ID:-}"

# Function to print colored output
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if Azure CLI is installed
check_azure_cli() {
    if ! command -v az &> /dev/null; then
        print_message $RED "Azure CLI is not installed. Please install it first."
        exit 1
    fi
}

# Function to login to Azure
azure_login() {
    print_message $YELLOW "Logging in to Azure..."
    
    # Try service principal login first if credentials are available
    if [ -n "$CLIENT_ID" ] && [ -n "$CLIENT_SECRET" ] && [ -n "$TENANT_ID" ]; then
        print_message $YELLOW "Using service principal authentication..."
        az login --service-principal --username "$CLIENT_ID" --password "$CLIENT_SECRET" --tenant "$TENANT_ID"
    else
        print_message $YELLOW "Using interactive login..."
        az login
    fi
    
    if [ -z "$SUBSCRIPTION_ID" ]; then
        print_message $YELLOW "Please select your subscription:"
        az account list --output table
        read -p "Enter your subscription ID: " SUBSCRIPTION_ID
    fi
    
    az account set --subscription "$SUBSCRIPTION_ID"
    print_message $GREEN "Successfully set subscription: $SUBSCRIPTION_ID"
}

# Function to create resource groups
create_resource_groups() {
    print_message $YELLOW "Creating resource groups..."
    
    # Dev resource group
    az group create \
        --name "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --output table
    
    # Prod resource group
    az group create \
        --name "$RESOURCE_GROUP_PROD" \
        --location "$LOCATION" \
        --output table
    
    print_message $GREEN "Resource groups created successfully"
}

# Function to create service principal
create_service_principal() {
    print_message $YELLOW "Creating service principal for GitHub Actions..."
    
    # Create service principal
    SP_OUTPUT=$(az ad sp create-for-rbac \
        --name "$SERVICE_PRINCIPAL_NAME" \
        --role contributor \
        --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_PROD")
    
    print_message $GREEN "Service principal created successfully"
    print_message $YELLOW "Please add the following secrets to your GitHub repository:"
    echo ""
    echo "AZURE_CREDENTIALS (entire JSON output below):"
    echo "$SP_OUTPUT"
    echo ""
    
    # Extract individual values
    SP_CLIENT_ID=$(echo "$SP_OUTPUT" | jq -r '.clientId')
    SP_CLIENT_SECRET=$(echo "$SP_OUTPUT" | jq -r '.clientSecret')
    SP_TENANT_ID=$(echo "$SP_OUTPUT" | jq -r '.tenantId')
    
    echo "Individual secrets:"
    echo "AZURE_CLIENT_ID: $SP_CLIENT_ID"
    echo "AZURE_TENANT_ID: $SP_TENANT_ID"
    echo "AZURE_SUBSCRIPTION_ID: $SUBSCRIPTION_ID"
    echo "AZURE_RESOURCE_GROUP: $RESOURCE_GROUP"
    echo "AZURE_RESOURCE_GROUP_PROD: $RESOURCE_GROUP_PROD"
    echo ""
    echo "For future script runs, add these to your .env file:"
    echo "AZURE_CLIENT_ID=$SP_CLIENT_ID"
    echo "AZURE_CLIENT_SECRET=$SP_CLIENT_SECRET"
    echo "AZURE_TENANT_ID=$SP_TENANT_ID"
    echo "AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID"
    echo "AZURE_RESOURCE_GROUP=$RESOURCE_GROUP"
    echo "AZURE_RESOURCE_GROUP_PROD=$RESOURCE_GROUP_PROD"
}

# Function to enable required Azure providers
enable_providers() {
    print_message $YELLOW "Enabling required Azure providers..."
    
    az provider register --namespace Microsoft.App
    az provider register --namespace Microsoft.OperationalInsights
    az provider register --namespace Microsoft.ManagedIdentity
    
    print_message $GREEN "Providers enabled successfully"
}

# Function to deploy initial infrastructure
deploy_infrastructure() {
    print_message $YELLOW "Deploying initial infrastructure..."
    
    # Deploy to dev environment
    az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --template-file ./infra/main.bicep \
        --parameters ./infra/parameters.json \
        --parameters containerImage="ghcr.io/gbmoalab/pyrunner:latest" \
        --output table
    
    print_message $GREEN "Infrastructure deployed successfully"
    
    # Get the Container App URL
    CONTAINER_APP_URL=$(az containerapp show \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.configuration.ingress.fqdn" \
        --output tsv)
    
    print_message $GREEN "Container App URL: https://$CONTAINER_APP_URL"
}

# Function to test the deployment
test_deployment() {
    print_message $YELLOW "Testing the deployment..."
    
    CONTAINER_APP_URL=$(az containerapp show \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.configuration.ingress.fqdn" \
        --output tsv)
    
    if [ -n "$CONTAINER_APP_URL" ]; then
        print_message $YELLOW "Testing health endpoint..."
        if curl -s "https://$CONTAINER_APP_URL/health" > /dev/null; then
            print_message $GREEN "Health check passed!"
        else
            print_message $RED "Health check failed. Please check the deployment."
        fi
    else
        print_message $RED "Could not retrieve Container App URL"
    fi
}

# Main execution
main() {
    print_message $GREEN "Starting Azure Container Apps setup..."
    
    check_azure_cli
    azure_login
    enable_providers
    create_resource_groups
    
    if [ -n "$CLIENT_ID" ] && [ -n "$CLIENT_SECRET" ] && [ -n "$TENANT_ID" ]; then
        print_message $YELLOW "Using existing service principal credentials"
    else
        print_message $YELLOW "No existing service principal credentials found, creating a new one..."
        create_service_principal
    fi    
    
    # Only ask to deploy if we're not using existing service principal
    if [ -z "$CLIENT_ID" ] || [ -z "$CLIENT_SECRET" ]; then
        read -p "Do you want to deploy the infrastructure now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            deploy_infrastructure
            test_deployment
        else
            print_message $YELLOW "Skipping infrastructure deployment. You can run it later with:"
            print_message $YELLOW "az deployment group create --resource-group $RESOURCE_GROUP --template-file ./infra/main.bicep --parameters ./infra/parameters.json"
        fi
    else
        print_message $YELLOW "Deploying infrastructure with existing service principal..."
        deploy_infrastructure
        test_deployment
    fi
    
    print_message $GREEN "Setup completed successfully!"
    print_message $YELLOW "Next steps:"
    print_message $YELLOW "1. Add the GitHub secrets shown above to your repository"
    print_message $YELLOW "2. Push your code to trigger the GitHub Actions workflow"
    print_message $YELLOW "3. Monitor the deployment in the GitHub Actions tab"
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
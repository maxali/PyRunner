# Azure Deployment Without Role Assignments

This guide helps you deploy PyRunner to Azure Container Apps when you don't have permissions to create role assignments.

## Problem

The standard deployment fails with:
```
The client with object id 'xxx' does not have permission to perform action 'Microsoft.Authorization/roleAssignments/write'
```

## Solution

Use the modified deployment that doesn't create role assignments:

```bash
./scripts/deploy-no-roles.sh
```

## What This Does

1. Creates a Container App with a system-assigned managed identity
2. Deploys using a public Docker Hub image
3. Skips role assignment creation
4. Outputs the identity principal ID for manual role assignment

## Post-Deployment Steps

### Option 1: Use Public Docker Hub Images

No additional steps needed. Update the Bicep template to use your Docker Hub image:
```bicep
param containerImage string = 'yourdockerhub/pyrunner:latest'
```

### Option 2: Use Private Registry (Requires Admin)

Have an Azure admin run:
```bash
# Get the principal ID from deployment output
PRINCIPAL_ID="<from-deployment-output>"

# Grant AcrPull role
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role AcrPull \
  --scope /subscriptions/<subscription-id>
```

## Alternative: Use Existing Service Principal

Instead of creating new identities each deployment, use an existing service principal:

1. Create a service principal once (admin required):
```bash
az ad sp create-for-rbac --name pyrunner-sp --role AcrPull
```

2. Use it in your deployments by modifying the Bicep template to use user-assigned identity.

## Deployment Command

```bash
# Deploy without role assignments
./scripts/deploy-no-roles.sh

# Or use Azure CLI directly
az deployment group create \
  --resource-group pyrunner-rg \
  --template-file infra/main-no-roles.bicep \
  --parameters containerAppName=pyrunner
```
# Deployment Guide

This guide explains how to deploy PyRunner to Azure Container Apps using GitHub Actions.

## Prerequisites

1. **Azure CLI** - Install from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
2. **Azure Subscription** - Active Azure subscription
3. **GitHub Repository** - Fork or clone this repository
4. **Docker** - For local testing (optional)

## Quick Start

### 1. Run the Setup Script

```bash
./scripts/setup-azure.sh
```

This script will:
- Create Azure resource groups
- Set up service principal for GitHub Actions
- Configure Azure providers
- Optionally deploy initial infrastructure

### 2. Configure GitHub Secrets

Add the following secrets to your GitHub repository (Settings → Secrets and variables → Actions):

**Required Secrets:**
- `AZURE_CLIENT_ID` - Service principal client ID
- `AZURE_TENANT_ID` - Azure tenant ID
- `AZURE_SUBSCRIPTION_ID` - Azure subscription ID
- `AZURE_RESOURCE_GROUP` - Dev resource group name (e.g., `pyrunner-rg`)
- `AZURE_RESOURCE_GROUP_PROD` - Prod resource group name (e.g., `pyrunner-rg-prod`)

**Optional Secrets:**
- `CODECOV_TOKEN` - For code coverage reporting

### 3. Deploy

Push to the `main` branch to trigger automatic deployment to the dev environment:

```bash
git push origin main
```

For production deployment, use the manual workflow dispatch:
1. Go to GitHub Actions tab
2. Select "Deploy to Azure Container Apps"
3. Click "Run workflow"
4. Select "prod" environment

## Infrastructure Details

### Architecture

```
GitHub Actions → Azure Container Registry → Azure Container Apps
                                        ↓
                                Log Analytics Workspace
```

### Resources Created

**Development Environment:**
- Resource Group: `pyrunner-rg`
- Container App: `pyrunner`
- Container App Environment: `pyrunner-env`
- Log Analytics Workspace: `pyrunner-logs`
- Managed Identity: `pyrunner-identity`

**Production Environment:**
- Resource Group: `pyrunner-rg-prod`
- Container App: `pyrunner-prod`
- Container App Environment: `pyrunner-env-prod`
- Log Analytics Workspace: `pyrunner-prod-logs`
- Managed Identity: `pyrunner-prod-identity`

### Configuration

#### Development Environment
- **CPU**: 1.0 cores
- **Memory**: 2Gi
- **Replicas**: 1-10 (auto-scaling)
- **Ingress**: External, HTTPS only

#### Production Environment
- **CPU**: 2.0 cores
- **Memory**: 4Gi
- **Replicas**: 2-20 (auto-scaling)
- **Ingress**: External, HTTPS only

### Auto-scaling Rules

1. **HTTP Requests**: Scale up when >10 concurrent requests
2. **CPU Utilization**: Scale up when >70% CPU usage
3. **Memory Utilization**: Scale up when >80% memory usage

## Manual Deployment

### Deploy Infrastructure Only

```bash
# Deploy to dev
az deployment group create \
  --resource-group pyrunner-rg \
  --template-file ./infra/main.bicep \
  --parameters ./infra/parameters.json \
  --parameters containerImage="ghcr.io/gbmoalab/pyrunner:latest"

# Deploy to prod
az deployment group create \
  --resource-group pyrunner-rg-prod \
  --template-file ./infra/main.bicep \
  --parameters ./infra/parameters.prod.json \
  --parameters containerImage="ghcr.io/gbmoalab/pyrunner:latest"
```

### Update Container App Image

```bash
# Update dev
az containerapp update \
  --name pyrunner \
  --resource-group pyrunner-rg \
  --image ghcr.io/gbmoalab/pyrunner:latest

# Update prod
az containerapp update \
  --name pyrunner-prod \
  --resource-group pyrunner-rg-prod \
  --image ghcr.io/gbmoalab/pyrunner:latest
```

## Monitoring and Logging

### View Application Logs

```bash
# Dev environment
az containerapp logs show \
  --name pyrunner \
  --resource-group pyrunner-rg \
  --follow

# Prod environment
az containerapp logs show \
  --name pyrunner-prod \
  --resource-group pyrunner-rg-prod \
  --follow
```

### Check Application Status

```bash
# Dev environment
az containerapp show \
  --name pyrunner \
  --resource-group pyrunner-rg \
  --query "properties.runningStatus"

# Prod environment
az containerapp show \
  --name pyrunner-prod \
  --resource-group pyrunner-rg-prod \
  --query "properties.runningStatus"
```

### Access Application

Once deployed, your application will be available at:
- **Dev**: `https://pyrunner.<random>.eastus.azurecontainerapps.io`
- **Prod**: `https://pyrunner-prod.<random>.eastus.azurecontainerapps.io`

Get the exact URL:
```bash
# Dev
az containerapp show \
  --name pyrunner \
  --resource-group pyrunner-rg \
  --query "properties.configuration.ingress.fqdn" \
  --output tsv

# Prod
az containerapp show \
  --name pyrunner-prod \
  --resource-group pyrunner-rg-prod \
  --query "properties.configuration.ingress.fqdn" \
  --output tsv
```

## Health Checks

The application includes health check endpoints:
- `/health` - Basic health check
- `/health/detailed` - Detailed health information

## Security

### Container Registry Access

The deployment uses GitHub Container Registry (ghcr.io) with:
- Managed Identity for secure access
- AcrPull role assignment
- No stored credentials in Container Apps

### Network Security

- HTTPS only ingress
- No direct file system access
- Isolated execution environment
- Resource limits enforced

### Security Scanning

GitHub Actions includes:
- Vulnerability scanning with Trivy
- Code coverage reporting
- Dependency checking

## Troubleshooting

### Common Issues

1. **Deployment Fails with "Resource not found"**
   - Ensure resource groups exist
   - Check service principal permissions
   - Verify subscription ID is correct

2. **Container App Won't Start**
   - Check container logs: `az containerapp logs show`
   - Verify container image exists and is accessible
   - Check resource limits aren't too restrictive

3. **GitHub Actions Fails**
   - Verify all required secrets are set
   - Check service principal has contributor access
   - Ensure resource groups exist

4. **Application Returns 503**
   - Container may be starting up (allow 1-2 minutes)
   - Check if resource limits are exceeded
   - Verify health check endpoint is responding

### Debug Commands

```bash
# Get container app details
az containerapp show --name pyrunner --resource-group pyrunner-rg

# List all revisions
az containerapp revision list --name pyrunner --resource-group pyrunner-rg

# Get ingress details
az containerapp ingress show --name pyrunner --resource-group pyrunner-rg

# Check managed identity
az identity show --name pyrunner-identity --resource-group pyrunner-rg
```

## Cost Optimization

### Resource Scaling

Container Apps automatically scale to zero when not in use, minimizing costs:
- **Dev**: Minimum 1 replica for availability
- **Prod**: Minimum 2 replicas for high availability

### Resource Limits

Resources are sized appropriately:
- **Dev**: Lower resource allocation for testing
- **Prod**: Higher resource allocation for production workloads

### Monitoring

Use Azure Cost Management to monitor spending:
```bash
az consumption usage list --top 10
```

## Environment Variables

The following environment variables are configured:

| Variable | Dev Value | Prod Value | Description |
|----------|-----------|------------|-------------|
| `PYTHONUNBUFFERED` | 1 | 1 | Real-time output |
| `PYTHONDONTWRITEBYTECODE` | 1 | 1 | No .pyc files |
| `LOG_LEVEL` | DEBUG | INFO | Logging level |
| `HOST` | 0.0.0.0 | 0.0.0.0 | Bind address |
| `PORT` | 8000 | 8000 | Service port |

## Next Steps

1. **Set up monitoring** - Configure Azure Monitor alerts
2. **Add custom domain** - Configure custom domain for production
3. **Implement secrets management** - Use Azure Key Vault for secrets
4. **Set up staging environment** - Add staging deployment pipeline
5. **Configure backup** - Set up backup strategy if needed
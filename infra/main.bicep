@description('The name of the Container App')
param containerAppName string = 'pyrunner'

@description('The name of the Container App Environment')
param containerAppEnvironmentName string = 'pyrunner-env'


@description('The location for all resources')
param location string = resourceGroup().location

@description('The container image to deploy')
param containerImage string = 'ghcr.io/maxali/pyrunner:latest'

@description('The minimum number of replicas')
param minReplicas int = 1

@description('The maximum number of replicas')
param maxReplicas int = 10

@description('The target port for the container')
param targetPort int = 8000

@description('The CPU allocation for the container')
param cpu string = '1.0'

@description('The memory allocation for the container')
param memory string = '2Gi'

@description('Environment (dev, staging, prod)')
param environment string = 'dev'

// Container Apps Environment
resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerAppEnvironmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
}

// Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${containerAppName}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Managed Identity for Container Registry access
resource containerRegistryIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${containerAppName}-identity'
  location: location
}

// Container App
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${containerRegistryIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: targetPort
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: [
        {
          server: 'ghcr.io'
          identity: containerRegistryIdentity.id
        }
      ]
    }
    template: {
      revisionSuffix: 'v${uniqueString(deployment().name)}'
      containers: [
        {
          name: containerAppName
          image: containerImage
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: [
            {
              name: 'PYTHONUNBUFFERED'
              value: '1'
            }
            {
              name: 'PYTHONDONTWRITEBYTECODE'
              value: '1'
            }
            {
              name: 'LOG_LEVEL'
              value: environment == 'prod' ? 'INFO' : 'DEBUG'
            }
            {
              name: 'HOST'
              value: '0.0.0.0'
            }
            {
              name: 'PORT'
              value: string(targetPort)
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: targetPort
              }
              initialDelaySeconds: 30
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: targetPort
              }
              initialDelaySeconds: 5
              periodSeconds: 5
              timeoutSeconds: 3
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-requests'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
          {
            name: 'cpu-utilization'
            custom: {
              type: 'cpu'
              metadata: {
                type: 'Utilization'
                value: '70'
              }
            }
          }
          {
            name: 'memory-utilization'
            custom: {
              type: 'memory'
              metadata: {
                type: 'Utilization'
                value: '80'
              }
            }
          }
        ]
      }
    }
  }
}

// Role assignment for Container Registry access
resource containerRegistryRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistryIdentity.id, 'AcrPull')
  dependsOn: [
    containerRegistryIdentity
  ]
  properties: {
    principalId: containerRegistryIdentity.properties.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output containerAppFQDN string = containerApp.properties.configuration.ingress.fqdn
output containerAppName string = containerApp.name
output containerAppEnvironmentName string = containerAppEnvironment.name
output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output logAnalyticsWorkspaceName string = logAnalyticsWorkspace.name
output managedIdentityId string = containerRegistryIdentity.id

// Databricks Premium workspace (Unity Catalog) + Access Connector so Databricks can read/write the
// existing ADLS Gen2 bronze storage account (from main.bicep) without any storage keys or SAS tokens.

@description('Short prefix used to name resources')
param namePrefix string = 'clickstream'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Name of the existing bronze ADLS Gen2 storage account created by main.bicep')
param bronzeStorageAccountName string

var uniqueSuffix = uniqueString(resourceGroup().id)
var workspaceName = '${namePrefix}-dbx-${uniqueSuffix}'
var accessConnectorName = '${namePrefix}-dbx-ac-${uniqueSuffix}'
var managedResourceGroupName = '${namePrefix}-dbx-managed-${uniqueSuffix}'

resource accessConnector 'Microsoft.Databricks/accessConnectors@2023-05-01' = {
  name: accessConnectorName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
}

resource workspace 'Microsoft.Databricks/workspaces@2024-05-01' = {
  name: workspaceName
  location: location
  sku: {
    name: 'premium'
  }
  properties: {
    managedResourceGroupId: subscriptionResourceId('Microsoft.Resources/resourceGroups', managedResourceGroupName)
  }
}

resource bronzeStorage 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: bronzeStorageAccountName
}

// ---------- RBAC: Access Connector's managed identity can read/write the bronze storage account ----------
resource storageBlobDataContributorRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  scope: subscription()
  name: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe' // Storage Blob Data Contributor
}

resource accessConnectorStorageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(bronzeStorage.id, accessConnector.id, storageBlobDataContributorRole.id)
  scope: bronzeStorage
  properties: {
    principalId: accessConnector.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: storageBlobDataContributorRole.id
  }
}

output workspaceName string = workspace.name
output workspaceUrl string = 'https://${workspace.properties.workspaceUrl}'
output workspaceId string = workspace.properties.workspaceId
output accessConnectorId string = accessConnector.id
output accessConnectorPrincipalId string = accessConnector.identity.principalId

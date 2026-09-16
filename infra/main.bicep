// Clickstream ingestion architecture - Sources -> Python -> Function -> Event Hubs -> ADLS Gen2 (Bronze)
// Deploys: ADLS Gen2 (bronze) storage, Function App runtime storage, Event Hubs namespace/hubs with Capture,
// a Python Function App, Application Insights, and the RBAC role assignments that let the Function App and
// Event Hubs Capture write data without any secrets in code.

@description('Short prefix used to name every resource, e.g. clickstream')
param namePrefix string = 'clickstream'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Event Hubs throughput units (Standard tier)')
param eventHubThroughputUnits int = 1

var uniqueSuffix = uniqueString(resourceGroup().id)
var shortSuffix = substring(uniqueSuffix, 0, 8)
var bronzeStorageName = toLower('csbrz${shortSuffix}')
var funcStorageName = toLower('csfunc${shortSuffix}')
var eventHubNamespaceName = '${namePrefix}-ehns-${uniqueSuffix}'
var functionAppName = '${namePrefix}-func-${uniqueSuffix}'
var appServicePlanName = '${namePrefix}-plan-${uniqueSuffix}'
var appInsightsName = '${namePrefix}-appi-${uniqueSuffix}'
var bronzeContainerName = 'bronze'

var eventHubs = [
  {
    name: 'events'
    capturePrefix: 'events/{Year}/{Month}/{Day}/{Hour}/'
  }
  {
    name: 'item-properties'
    capturePrefix: 'item-properties/{Year}/{Month}/{Day}/{Hour}/'
  }
  {
    name: 'category-tree'
    capturePrefix: 'category-tree/{Year}/{Month}/{Day}/{Hour}/'
  }
]

// ---------- ADLS Gen2 storage (Bronze landing zone) ----------
resource bronzeStorage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: bronzeStorageName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    isHnsEnabled: true
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
  }
}

resource bronzeBlobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: bronzeStorage
  name: 'default'
}

resource bronzeContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: bronzeBlobService
  name: bronzeContainerName
  properties: {
    publicAccess: 'None'
  }
}

// Unity Catalog managed table storage for the clickstream lakehouse catalog (databricks.bicep's
// clickstream_bronze_credential storage credential covers the whole storage account, so this
// container just needs to exist - the catalog's storage_root points here).
resource unityCatalogContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: bronzeBlobService
  name: 'unity-catalog'
  properties: {
    publicAccess: 'None'
  }
}

// ---------- Function App runtime storage (must be non-HNS: Consumption plan needs Azure Files content share) ----------
resource funcStorage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: funcStorageName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
  }
}

// ---------- Event Hubs namespace (Standard tier required for Capture) ----------
resource eventHubNamespace 'Microsoft.EventHub/namespaces@2023-01-01-preview' = {
  name: eventHubNamespaceName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
    capacity: eventHubThroughputUnits
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    isAutoInflateEnabled: false
    minimumTlsVersion: '1.2'
  }
}

resource eventHubEntities 'Microsoft.EventHub/namespaces/eventhubs@2023-01-01-preview' = [for hub in eventHubs: {
  parent: eventHubNamespace
  name: hub.name
  properties: {
    messageRetentionInDays: 3
    partitionCount: 2
    captureDescription: {
      enabled: true
      encoding: 'Avro'
      intervalInSeconds: 300
      sizeLimitInBytes: 314572800
      skipEmptyArchives: true
      destination: {
        name: 'EventHubArchive.AzureBlockBlob'
        properties: {
          storageAccountResourceId: bronzeStorage.id
          blobContainer: bronzeContainerName
          archiveNameFormat: '${hub.capturePrefix}{Namespace}-{EventHub}-{PartitionId}-{Year}{Month}{Day}{Hour}{Minute}{Second}'
        }
      }
    }
  }
}]

// ---------- Application Insights ----------
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    IngestionMode: 'ApplicationInsights'
  }
}

// ---------- Consumption plan + Python Function App ----------
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  kind: 'functionapp'
  properties: {
    reserved: true
  }
}

resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${funcStorage.name};AccountKey=${funcStorage.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'EVENTHUB_FQDN'
          value: '${eventHubNamespace.name}.servicebus.windows.net'
        }
        {
          name: 'EVENTHUB_EVENTS_NAME'
          value: 'events'
        }
        {
          name: 'EVENTHUB_ITEM_PROPERTIES_NAME'
          value: 'item-properties'
        }
        {
          name: 'EVENTHUB_CATEGORY_TREE_NAME'
          value: 'category-tree'
        }
      ]
    }
  }
}

// ---------- RBAC: Function App managed identity can send to Event Hubs (no connection strings) ----------
resource eventHubsDataSenderRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  scope: subscription()
  name: '2b629674-e913-4c01-ae53-ef4638d8f975' // Azure Event Hubs Data Sender
}

resource functionSendRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(eventHubNamespace.id, functionApp.id, eventHubsDataSenderRole.id)
  scope: eventHubNamespace
  properties: {
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: eventHubsDataSenderRole.id
  }
}

// ---------- RBAC: Event Hubs Capture's managed system identity can write to the bronze storage account ----------
resource storageBlobDataContributorRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  scope: subscription()
  name: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe' // Storage Blob Data Contributor
}

resource captureStorageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(bronzeStorage.id, eventHubNamespace.id, storageBlobDataContributorRole.id)
  scope: bronzeStorage
  properties: {
    principalId: eventHubNamespace.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: storageBlobDataContributorRole.id
  }
}

output bronzeStorageAccountName string = bronzeStorage.name
output bronzeContainerNameOut string = bronzeContainerName
output eventHubNamespaceFqdn string = '${eventHubNamespace.name}.servicebus.windows.net'
output functionAppName string = functionApp.name
output functionAppDefaultHostName string = functionApp.properties.defaultHostName

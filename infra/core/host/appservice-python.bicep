param environmentName string
param location string = resourceGroup().location

param allowedOrigins array = []
param appCommandLine string = ''
param applicationInsightsName string
param appServicePlanId string
param appSettings object = {}
param keyVaultName string = ''
param linuxFxVersion string = 'PYTHON|3.8'
param managedIdentity bool = !(empty(keyVaultName))
param scmDoBuildDuringDeployment bool = true
param serviceName string

module appService 'appservice.bicep' = {
  name: '${serviceName}-appservice-python'
  params: {
    environmentName: environmentName
    location: location
    allowedOrigins: allowedOrigins
    appCommandLine: appCommandLine
    applicationInsightsName: applicationInsightsName
    appServicePlanId: appServicePlanId
    appSettings: appSettings
    keyVaultName: keyVaultName
    linuxFxVersion: linuxFxVersion
    managedIdentity: managedIdentity
    scmDoBuildDuringDeployment: scmDoBuildDuringDeployment
    serviceName: serviceName
  }
}

output identityPrincipalId string = appService.outputs.identityPrincipalId
output name string = appService.outputs.name
output uri string = appService.outputs.uri

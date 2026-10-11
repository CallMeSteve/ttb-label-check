# Deploys the app to Azure Container Apps. Builds the image in Azure Container Registry,
# so no local Docker is needed. Safe to re-run: every step creates or updates in place.
param(
  [string]$Rg = "rg-ttb-label-check",
  [string]$Loc = "eastus",
  [string]$Acr = "ttblabelcheck",
  [string]$Env = "cae-ttb-label-check",
  [string]$App = "ttb-label-check",
  [string]$Src = (Split-Path -Parent $PSScriptRoot)
)
$ErrorActionPreference = "Stop"
$az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
function Step($msg) { Write-Output "[$(Get-Date -Format HH:mm:ss)] $msg" }

function WaitFor($ns) {
  while ((& $az provider show -n $ns --query registrationState -o tsv) -ne "Registered") { Step "waiting for $ns"; Start-Sleep 30 }
}
WaitFor "Microsoft.ContainerRegistry"
& $az group create -n $Rg -l $Loc -o none
& $az acr create -n $Acr -g $Rg --sku Basic -o none
Step "registry ready"
$tag = (git -C $Src rev-parse --short HEAD)
& $az acr build -r $Acr -t "${App}:$tag" -t "${App}:latest" $Src --no-logs -o none
Step "image built: ${App}:$tag"
WaitFor "Microsoft.App"
WaitFor "Microsoft.OperationalInsights"
Step "providers registered"
& $az extension add -n containerapp --upgrade --only-show-errors
$envExists = & $az containerapp env show -n $Env -g $Rg --query name -o tsv 2>$null
if (-not $envExists) { & $az containerapp env create -n $Env -g $Rg -l $Loc --logs-destination none -o none }
Step "environment ready"
$appExists = & $az containerapp show -n $App -g $Rg --query name -o tsv 2>$null
if (-not $appExists) {
  & $az containerapp create -n $App -g $Rg --environment $Env --image "$Acr.azurecr.io/${App}:$tag" `
    --registry-server "$Acr.azurecr.io" --registry-identity system `
    --target-port 8000 --ingress external --cpu 2 --memory 4Gi --min-replicas 1 --max-replicas 2 `
    --env-vars OCR_THREADS=2 BATCH_WORKERS=1 -o none
} else {
  & $az containerapp update -n $App -g $Rg --image "$Acr.azurecr.io/${App}:$tag" -o none
}
$fqdn = & $az containerapp show -n $App -g $Rg --query properties.configuration.ingress.fqdn -o tsv
Step "DEPLOYED https://$fqdn"

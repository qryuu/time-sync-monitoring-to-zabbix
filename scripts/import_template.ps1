<#
.SYNOPSIS
    Imports time synchronization accuracy templates to Zabbix Server 7.0/6.0.
.DESCRIPTION
    Supports bilingual templates (_ja.yaml / _en.yaml), automatic OS language detection,
    and automatic host creation (host.create) to prevent reusing unrelated hosts.
.PARAMETER ZabbixUrl
    Base URL of Zabbix Web (e.g. http://localhost/zabbix)
.PARAMETER ApiToken
    Zabbix API Token
.PARAMETER TemplateType
    NTP or Chrony (default: Chrony)
.PARAMETER Language
    Auto, JA, or EN (default: Auto)
.PARAMETER HostName
    Optional host name to link template to. If the host does not exist, it is created automatically.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ZabbixUrl,

    [Parameter(Mandatory = $true)]
    [string]$ApiToken,

    [ValidateSet("Chrony", "NTP")]
    [string]$TemplateType = "Chrony",

    [ValidateSet("Auto", "JA", "EN")]
    [string]$Language = "Auto",

    [string]$HostName = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 1. Resolve Language
if ($Language -eq "Auto") {
    $culture = (Get-Culture).TwoLetterISOLanguageName
    if ($culture -eq "ja") {
        $ResolvedLang = "ja"
    } else {
        $ResolvedLang = "en"
    }
} else {
    $ResolvedLang = $Language.ToLower()
}

Write-Host "[INFO] Target template: $TemplateType, Language: $ResolvedLang" -ForegroundColor Cyan

# 2. Locate Template File
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir

if ($TemplateType -eq "Chrony") {
    $TemplateFile = Join-Path $RepoRoot "chrony\templates\template_chrony_accuracy_$ResolvedLang.yaml"
    $TemplateTechName = "template_chrony_accuracy"
} else {
    $TemplateFile = Join-Path $RepoRoot "ntp\templates\template_ntp_accuracy_$ResolvedLang.yaml"
    $TemplateTechName = "template_ntp_accuracy"
}

if (-not (Test-Path $TemplateFile)) {
    throw "Template file not found: $TemplateFile"
}

$TemplateContent = Get-Content -Path $TemplateFile -Raw -Encoding UTF8

# 3. Helper to call Zabbix API
function Invoke-ZabbixApi {
    param([string]$Method, [object]$Params)
    $body = @{
        jsonrpc = "2.0"
        method  = $Method
        params  = $Params
        auth    = $ApiToken
        id      = 1
    } | ConvertTo-Json -Depth 10

    $apiUrl = $ZabbixUrl.TrimEnd('/') + "/api_jsonrpc.php"
    $response = Invoke-RestMethod -Uri $apiUrl -Method Post -ContentType "application/json-rpc" -Body $body
    if ($response.error) {
        throw "Zabbix API Error ($Method): $($response.error.message) - $($response.error.data)"
    }
    return $response.result
}

# 4. Check for existing or legacy templates
Write-Host "[INFO] Checking existing templates on Zabbix Server..." -ForegroundColor Cyan
try {
    $existingTmpl = Invoke-ZabbixApi -Method "template.get" -Params @{
        filter = @{ host = @($TemplateTechName) }
        selectHosts = @("hostid", "host")
    }
    if ($existingTmpl -and $existingTmpl.Count -gt 0) {
        $linkedCount = if ($existingTmpl[0].hosts) { $existingTmpl[0].hosts.Count } else { 0 }
        Write-Host "[INFO] Existing template '$TemplateTechName' found (currently linked to $linkedCount host(s)). Updating safely with historical data preserved..." -ForegroundColor Yellow
    }

    # Also check for legacy template names
    $legacyNames = @("chrony_Monitoring-Japanese", "NTP_Monitoring-Japanese", "NTP-remote-Japanese")
    $legacyTmpl = Invoke-ZabbixApi -Method "template.get" -Params @{
        filter = @{ host = $legacyNames }
        selectHosts = @("hostid", "host")
    }
    if ($legacyTmpl -and $legacyTmpl.Count -gt 0) {
        foreach ($lt in $legacyTmpl) {
            $lCount = if ($lt.hosts) { $lt.hosts.Count } else { 0 }
            Write-Host "[NOTICE] Legacy template '$($lt.host)' detected ($lCount linked host(s)). It will safely coexist without interference. Consider re-linking hosts to '$TemplateTechName'." -ForegroundColor Cyan
        }
    }
} catch {
    Write-Host "[WARN] Pre-import template check skipped: $_" -ForegroundColor DarkGray
}

# 5. Import Configuration (using strict Zabbix 7.0 camelCase templateDashboards)
Write-Host "[INFO] Importing template: $(Split-Path -Leaf $TemplateFile)..." -ForegroundColor Cyan
$importRules = @{
    template_groups    = @{ createMissing = $true; updateExisting = $true }
    templates          = @{ createMissing = $true; updateExisting = $true }
    items              = @{ createMissing = $true; updateExisting = $true }
    triggers           = @{ createMissing = $true; updateExisting = $true }
    discoveryRules     = @{ createMissing = $true; updateExisting = $true }
    graphs             = @{ createMissing = $true; updateExisting = $true }
    templateDashboards = @{ createMissing = $true; updateExisting = $true }
}

$importResult = Invoke-ZabbixApi -Method "configuration.import" -Params @{
    format = "yaml"
    source = $TemplateContent
    rules  = $importRules
}

if ($importResult) {
    Write-Host "[SUCCESS] Template successfully imported!" -ForegroundColor Green
}

# 6. Link to Host if specified (with automatic host.create and safe template merge)
if ($HostName) {
    Write-Host "[INFO] Checking host '$HostName'..." -ForegroundColor Cyan
    # Search by technical host name first, then by visible display name
    $hosts = Invoke-ZabbixApi -Method "host.get" -Params @{
        filter = @{ host = @($HostName) }
        selectParentTemplates = @("templateid")
    }
    if (-not $hosts -or $hosts.Count -eq 0) {
        $hosts = Invoke-ZabbixApi -Method "host.get" -Params @{
            filter = @{ name = @($HostName) }
            selectParentTemplates = @("templateid")
        }
    }
    
    # Retrieve template ID
    $tmplObj = Invoke-ZabbixApi -Method "template.get" -Params @{ filter = @{ host = @($TemplateTechName) } }
    if (-not $tmplObj -or $tmplObj.Count -eq 0) {
        throw "Could not find imported template with technical name '$TemplateTechName'"
    }
    $templateId = $tmplObj[0].templateid

    if (-not $hosts -or $hosts.Count -eq 0) {
        Write-Host "[INFO] Host '$HostName' does not exist. Creating new host (host.create)..." -ForegroundColor Yellow
        # Find default hostgroup Linux servers or Discovered hosts
        $groupObj = Invoke-ZabbixApi -Method "hostgroup.get" -Params @{ filter = @{ name = @("Linux servers", "Discovered hosts", "Templates/Applications") } }
        $groupId = if ($groupObj.Count -gt 0) { $groupObj[0].groupid } else { "2" }
        
        $newHost = Invoke-ZabbixApi -Method "host.create" -Params @{
            host = $HostName
            groups = @(@{ groupid = $groupId })
            templates = @(@{ templateid = $templateId })
            interfaces = @(@{
                type = 1
                main = 1
                useip = 1
                ip = "127.0.0.1"
                dns = ""
                port = "10050"
            })
        }
        Write-Host "[SUCCESS] Host '$HostName' created and linked to template!" -ForegroundColor Green
    } else {
        $targetHost = $hosts[0]
        $hostId = $targetHost.hostid
        $displayName = if ($targetHost.name) { $targetHost.name } else { $targetHost.host }
        Write-Host "[INFO] Linking template to existing host '$displayName' (hostid: $hostId)..." -ForegroundColor Cyan

        # Collect existing parent template IDs to avoid unlinking OS/database templates
        $existingTmplIds = [System.Collections.Generic.HashSet[string]]::new()
        if ($targetHost.parentTemplates) {
            foreach ($pt in $targetHost.parentTemplates) {
                [void]$existingTmplIds.Add($pt.templateid)
            }
        }

        if ($existingTmplIds.Contains($templateId)) {
            Write-Host "[INFO] Template '$TemplateTechName' is already linked to host '$displayName'." -ForegroundColor Yellow
        } else {
            [void]$existingTmplIds.Add($templateId)
            $mergedTemplates = @()
            foreach ($tid in $existingTmplIds) {
                $mergedTemplates += @{ templateid = $tid }
            }

            Invoke-ZabbixApi -Method "host.update" -Params @{
                hostid = $hostId
                templates = $mergedTemplates
            }
            $preservedCount = $existingTmplIds.Count - 1
            Write-Host "[SUCCESS] Safely linked template to existing host '$displayName' (preserved $preservedCount existing templates)!" -ForegroundColor Green
        }
    }
}

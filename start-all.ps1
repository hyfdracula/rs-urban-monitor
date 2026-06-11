[CmdletBinding()]
param(
    [switch]$NoBackend,
    [switch]$NoFrontend,
    [switch]$NoGeoServer,
    [switch]$WithNgrok,
    [switch]$NoPause,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSCommandPath
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$GeoServerHome = Join-Path $ProjectRoot "geoserver-2.25.5-bin"
$GeoServerBin = Join-Path $GeoServerHome "bin"
$LogDir = Join-Path $ProjectRoot "logs\startup"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Step {
    param([string]$Message)
    Write-Host "[start-all] $Message"
}

function ConvertTo-PSLiteral {
    param([string]$Value)
    return "'" + ($Value -replace "'", "''") + "'"
}

function Test-PathQuiet {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $false
    }

    try {
        return (Test-Path -LiteralPath $Path -ErrorAction Stop)
    }
    catch {
        return $false
    }
}

function Test-ListeningPort {
    param([int]$Port)

    foreach ($hostName in @("127.0.0.1", "localhost")) {
        $client = $null
        try {
            $client = [System.Net.Sockets.TcpClient]::new()
            $connectTask = $client.ConnectAsync($hostName, $Port)
            if ($connectTask.Wait(800) -and $client.Connected) {
                return $true
            }
        }
        catch {
            continue
        }
        finally {
            if ($client) {
                $client.Dispose()
            }
        }
    }

    return $false
}

function Get-PortOwnerSummary {
    param([int]$Port)
    $connections = @(Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Where-Object { "$($_.State)" -eq "Listen" })
    if ($connections.Count -eq 0) {
        return "owner unavailable"
    }

    $owners = foreach ($processId in ($connections.OwningProcess | Sort-Object -Unique)) {
        try {
            $process = Get-Process -Id $processId -ErrorAction Stop
            "$($process.ProcessName)($processId)"
        }
        catch {
            "pid:$processId"
        }
    }

    return ($owners -join ", ")
}

function Wait-ListeningPort {
    param(
        [int]$Port,
        [int]$TimeoutSeconds = 45
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-ListeningPort -Port $Port) {
            return $true
        }
        Start-Sleep -Seconds 1
    }

    return (Test-ListeningPort -Port $Port)
}

function Test-HttpEndpoint {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        return [pscustomobject]@{
            Ok = $true
            StatusCode = $response.StatusCode
            Error = $null
        }
    }
    catch {
        $statusCode = $null
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }
        return [pscustomobject]@{
            Ok = $false
            StatusCode = $statusCode
            Error = $_.Exception.Message
        }
    }
}

function Resolve-PythonCommand {
    $candidates = @()

    if ($env:RS_URBAN_PYTHON) {
        $candidates += [pscustomobject]@{ File = $env:RS_URBAN_PYTHON; Args = @(); Label = $env:RS_URBAN_PYTHON }
    }

    $candidates += [pscustomobject]@{ File = "py"; Args = @("-3"); Label = "py -3" }
    $candidates += [pscustomobject]@{ File = "python"; Args = @(); Label = "python" }

    $embeddedPython = Join-Path $BackendDir "python311-embed\python.exe"
    $candidates += [pscustomobject]@{ File = $embeddedPython; Args = @(); Label = $embeddedPython }

    if ($env:LOCALAPPDATA) {
        $localPython = Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"
        $candidates += [pscustomobject]@{ File = $localPython; Args = @(); Label = $localPython }
    }

    if ($env:USERPROFILE) {
        foreach ($minor in @("312", "311", "310")) {
            $profilePython = Join-Path $env:USERPROFILE "AppData\Local\Programs\Python\Python$minor\python.exe"
            $candidates += [pscustomobject]@{ File = $profilePython; Args = @(); Label = $profilePython }
        }
    }

    foreach ($candidate in ($candidates | Sort-Object File, Label -Unique)) {
        try {
            $versionArgs = @($candidate.Args) + @("-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'); raise SystemExit(0 if sys.version_info >= (3, 10) else 1)")
            $version = & $candidate.File @versionArgs 2>$null
            if ($LASTEXITCODE -eq 0) {
                return [pscustomobject]@{
                    File = $candidate.File
                    Args = [string[]]$candidate.Args
                    Label = "$($candidate.Label) ($version)"
                }
            }
        }
        catch {
            continue
        }
    }

    return $null
}

function Resolve-NpmCommand {
    $command = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $command) {
        $command = Get-Command npm -ErrorAction SilentlyContinue
    }
    if ($command) {
        return [pscustomobject]@{ File = $command.Source; PathPrefix = $null; Label = $command.Source }
    }

    $fallbacks = @()
    $fallbacks += "D:\software\node\npm.cmd"
    if ($env:ProgramFiles) {
        $fallbacks += (Join-Path $env:ProgramFiles "nodejs\npm.cmd")
    }
    if (${env:ProgramFiles(x86)}) {
        $fallbacks += (Join-Path ${env:ProgramFiles(x86)} "nodejs\npm.cmd")
    }

    foreach ($fallback in $fallbacks) {
        if (Test-PathQuiet -Path $fallback) {
            return [pscustomobject]@{
                File = $fallback
                PathPrefix = (Split-Path -Parent $fallback)
                Label = $fallback
            }
        }
    }

    return $null
}

function Resolve-JavaRuntime {
    if ($env:JAVA_HOME) {
        $javaExe = Join-Path $env:JAVA_HOME "bin\java.exe"
        if (Test-PathQuiet -Path $javaExe) {
            return [pscustomobject]@{ JavaHome = $env:JAVA_HOME; Label = "JAVA_HOME=$env:JAVA_HOME" }
        }
    }

    $knownHome = "C:\Program Files\Microsoft\jdk-17.0.19.10-hotspot"
    if (Test-PathQuiet -Path (Join-Path $knownHome "bin\java.exe")) {
        return [pscustomobject]@{ JavaHome = $knownHome; Label = $knownHome }
    }

    $roots = @(
        (Join-Path $env:ProgramFiles "Microsoft"),
        (Join-Path $env:ProgramFiles "Eclipse Adoptium"),
        (Join-Path $env:ProgramFiles "Java")
    )

    foreach ($root in $roots) {
        if (-not (Test-PathQuiet -Path $root)) {
            continue
        }

        $homes = @(Get-ChildItem -LiteralPath $root -Directory -Filter "jdk*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending)
        foreach ($home in $homes) {
            if (Test-PathQuiet -Path (Join-Path $home.FullName "bin\java.exe")) {
                return [pscustomobject]@{ JavaHome = $home.FullName; Label = $home.FullName }
            }
        }
    }

    $javaCommand = Get-Command java -ErrorAction SilentlyContinue
    if ($javaCommand) {
        return [pscustomobject]@{ JavaHome = $null; Label = "java on PATH" }
    }

    return $null
}

function Start-PowerShellWindow {
    param(
        [string]$Title,
        [string]$ScriptText
    )

    if ($DryRun) {
        Write-Step "Dry run: would start $Title"
        return
    }

    $encoded = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($ScriptText))
    Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-EncodedCommand", $encoded) | Out-Null
}

function Start-Backend {
    param([pscustomobject]$Python)

    $backendLog = Join-Path $LogDir "backend.log"
    $pythonArgs = ""
    if ($Python.Args.Count -gt 0) {
        $pythonArgs = ($Python.Args | ForEach-Object { ConvertTo-PSLiteral $_ }) -join " "
    }

    $script = @"
`$Host.UI.RawUI.WindowTitle = 'RS Urban Monitor Backend'
`$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $(ConvertTo-PSLiteral $BackendDir)
`$env:PYTHONPATH = (Get-Location).Path + ';' + `$env:PYTHONPATH
Write-Host 'Backend: http://127.0.0.1:8001'
Write-Host ('Log: ' + $(ConvertTo-PSLiteral $backendLog))
& $(ConvertTo-PSLiteral $Python.File) $pythonArgs -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload 2>&1 | Tee-Object -FilePath $(ConvertTo-PSLiteral $backendLog) -Append
Read-Host 'Backend stopped. Press Enter to close'
"@

    Start-PowerShellWindow -Title "Backend" -ScriptText $script
}

function Start-BackendBatch {
    $backendStart = Join-Path $BackendDir "start.bat"
    if (-not (Test-PathQuiet -Path $backendStart)) {
        Write-Step "backend\start.bat not found, cannot use backend fallback."
        return
    }

    $backendLog = Join-Path $LogDir "backend.log"
    $script = @"
`$Host.UI.RawUI.WindowTitle = 'RS Urban Monitor Backend'
Set-Location -LiteralPath $(ConvertTo-PSLiteral $BackendDir)
Write-Host 'Python 3.10+ was not detected by start-all.ps1.'
Write-Host 'Trying backend\start.bat fallback. If it still fails, install Python 3.10+ or set RS_URBAN_PYTHON.'
Write-Host ('Log: ' + $(ConvertTo-PSLiteral $backendLog))
& $(ConvertTo-PSLiteral $backendStart) 2>&1 | Tee-Object -FilePath $(ConvertTo-PSLiteral $backendLog) -Append
Read-Host 'Backend fallback stopped. Press Enter to close'
"@

    Start-PowerShellWindow -Title "Backend" -ScriptText $script
}

function Start-Frontend {
    param([pscustomobject]$Npm)

    $frontendLog = Join-Path $LogDir "frontend.log"
    $pathSetup = ""
    if ($Npm.PathPrefix) {
        $pathSetup = "`$env:PATH = $(ConvertTo-PSLiteral $Npm.PathPrefix) + ';' + `$env:PATH"
    }

    $script = @"
`$Host.UI.RawUI.WindowTitle = 'RS Urban Monitor Frontend'
`$ErrorActionPreference = 'Stop'
$pathSetup
Set-Location -LiteralPath $(ConvertTo-PSLiteral $ProjectRoot)
Write-Host 'Frontend: http://127.0.0.1:5173'
Write-Host ('Log: ' + $(ConvertTo-PSLiteral $frontendLog))
& $(ConvertTo-PSLiteral $Npm.File) run dev -- --host 0.0.0.0 2>&1 | Tee-Object -FilePath $(ConvertTo-PSLiteral $frontendLog) -Append
Read-Host 'Frontend stopped. Press Enter to close'
"@

    Start-PowerShellWindow -Title "Frontend" -ScriptText $script
}

function Start-GeoServer {
    param([pscustomobject]$Java)

    $geoServerLog = Join-Path $LogDir "geoserver.log"
    $javaSetup = ""
    if ($Java.JavaHome) {
        $javaSetup = @"
`$env:JAVA_HOME = $(ConvertTo-PSLiteral $Java.JavaHome)
`$env:PATH = (Join-Path `$env:JAVA_HOME 'bin') + ';' + `$env:PATH
"@
    }

    $script = @"
`$Host.UI.RawUI.WindowTitle = 'RS Urban Monitor GeoServer'
`$ErrorActionPreference = 'Stop'
$javaSetup
`$env:GEOSERVER_HOME = $(ConvertTo-PSLiteral $GeoServerHome)
Set-Location -LiteralPath $(ConvertTo-PSLiteral $GeoServerBin)
Write-Host 'GeoServer: http://127.0.0.1:8080/geoserver'
Write-Host ('Log: ' + $(ConvertTo-PSLiteral $geoServerLog))
& .\startup.bat 2>&1 | Tee-Object -FilePath $(ConvertTo-PSLiteral $geoServerLog) -Append
Read-Host 'GeoServer stopped. Press Enter to close'
"@

    Start-PowerShellWindow -Title "GeoServer" -ScriptText $script
}

function Start-Ngrok {
    $ngrokExe = Join-Path $FrontendDir "ngrok.exe"
    if (-not (Test-Path -LiteralPath $ngrokExe)) {
        Write-Step "ngrok.exe not found, skip ngrok."
        return
    }

    $ngrokLog = Join-Path $LogDir "ngrok.log"
    $script = @"
`$Host.UI.RawUI.WindowTitle = 'RS Urban Monitor ngrok'
`$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $(ConvertTo-PSLiteral $FrontendDir)
Write-Host 'ngrok: http 5173'
Write-Host 'Local inspector: http://127.0.0.1:4040'
Write-Host ('Log: ' + $(ConvertTo-PSLiteral $ngrokLog))
& $(ConvertTo-PSLiteral $ngrokExe) http 5173 2>&1 | Tee-Object -FilePath $(ConvertTo-PSLiteral $ngrokLog) -Append
Read-Host 'ngrok stopped. Press Enter to close'
"@

    Start-PowerShellWindow -Title "ngrok" -ScriptText $script
}

Write-Host "========================================"
Write-Host "  RS Urban Monitor - Start All"
Write-Host "========================================"
Write-Host ""
Write-Step "Project root: $ProjectRoot"
Write-Step "Logs: $LogDir"
Write-Host ""

$python = Resolve-PythonCommand
$npm = Resolve-NpmCommand
$java = Resolve-JavaRuntime

if ($python) { Write-Step "Python: $($python.Label)" } else { Write-Step "Python: not found" }
if ($npm) { Write-Step "npm: $($npm.Label)" } else { Write-Step "npm: not found" }
if ($java) { Write-Step "Java: $($java.Label)" } else { Write-Step "Java: not found" }
Write-Host ""

$backendExpected = $false
$frontendExpected = $false
$geoServerExpected = $false
$backendAvailable = (Test-HttpEndpoint -Url "http://127.0.0.1:8001/api/system/status").Ok -or (Test-ListeningPort -Port 8001)
$frontendAvailable = (Test-HttpEndpoint -Url "http://127.0.0.1:5173/").Ok -or (Test-ListeningPort -Port 5173)
$geoServerAvailable = (Test-HttpEndpoint -Url "http://127.0.0.1:8080/geoserver").Ok -or (Test-ListeningPort -Port 8080)

if ($NoGeoServer) {
    Write-Step "GeoServer disabled by -NoGeoServer."
}
elseif ($geoServerAvailable) {
    Write-Step "GeoServer already listening on port 8080 ($(Get-PortOwnerSummary -Port 8080)), skip start."
    $geoServerExpected = $true
}
elseif (-not (Test-PathQuiet -Path (Join-Path $GeoServerBin "startup.bat"))) {
    Write-Step "GeoServer startup.bat not found, skip GeoServer."
}
elseif (-not $java) {
    Write-Step "Java runtime not found, skip GeoServer."
}
else {
    Write-Step "Starting GeoServer..."
    Start-GeoServer -Java $java
    $geoServerExpected = -not $DryRun
}

if ($NoBackend) {
    Write-Step "Backend disabled by -NoBackend."
}
elseif ($backendAvailable) {
    Write-Step "Backend already listening on port 8001 ($(Get-PortOwnerSummary -Port 8001)), skip start."
    $backendExpected = $true
}
elseif (-not $python) {
    Write-Step "Python 3.10+ not found, trying backend\start.bat fallback."
    Start-BackendBatch
    $backendExpected = -not $DryRun
}
else {
    Write-Step "Starting backend..."
    Start-Backend -Python $python
    $backendExpected = -not $DryRun
}

if ($NoFrontend) {
    Write-Step "Frontend disabled by -NoFrontend."
}
elseif ($frontendAvailable) {
    Write-Step "Frontend already listening on port 5173 ($(Get-PortOwnerSummary -Port 5173)), skip start."
    $frontendExpected = $true
}
elseif (-not $npm) {
    Write-Step "npm not found, skip frontend."
}
else {
    Write-Step "Starting frontend..."
    Start-Frontend -Npm $npm
    $frontendExpected = -not $DryRun
}

$ngrokRequested = $WithNgrok -or ($env:RS_URBAN_WITH_NGROK -match "^(1|true|yes)$")
if ($ngrokRequested) {
    $existingNgrok = @(Get-Process -Name ngrok -ErrorAction SilentlyContinue)
    if ($existingNgrok.Count -gt 0) {
        Write-Step "ngrok already running, skip start."
    }
    else {
        Write-Step "Starting ngrok..."
        Start-Ngrok
    }
}
else {
    Write-Step "ngrok disabled by default. Use -WithNgrok if public tunnel is needed."
}

Write-Host ""
Write-Step "Readiness check..."

if ($geoServerExpected) {
    $geoReady = Wait-ListeningPort -Port 8080 -TimeoutSeconds 90
    if ($geoReady) {
        Write-Step "GeoServer port 8080 is listening."
    }
    else {
        Write-Step "GeoServer port 8080 did not become ready within 90s. Check logs/startup/geoserver.log."
    }
}

if ($backendExpected) {
    $backendReady = Wait-ListeningPort -Port 8001 -TimeoutSeconds 45
    if ($backendReady) {
        $backendHttp = Test-HttpEndpoint -Url "http://127.0.0.1:8001/api/system/status"
        if ($backendHttp.Ok) {
            Write-Step "Backend health endpoint OK: http://127.0.0.1:8001/api/system/status"
        }
        else {
            Write-Step "Backend port is open, but health request failed: $($backendHttp.Error)"
        }
    }
    else {
        Write-Step "Backend port 8001 did not become ready within 45s. Check logs/startup/backend.log."
    }
}

if ($frontendExpected) {
    $frontendReady = Wait-ListeningPort -Port 5173 -TimeoutSeconds 45
    if ($frontendReady) {
        $frontendHttp = Test-HttpEndpoint -Url "http://127.0.0.1:5173/"
        if ($frontendHttp.Ok) {
            Write-Step "Frontend OK: http://127.0.0.1:5173/"
        }
        else {
            Write-Step "Frontend port is open, but page request failed: $($frontendHttp.Error)"
        }
    }
    else {
        Write-Step "Frontend port 5173 did not become ready within 45s. Check logs/startup/frontend.log."
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host "  URLs"
Write-Host "========================================"
Write-Host "  Frontend  : http://127.0.0.1:5173/"
Write-Host "  Backend   : http://127.0.0.1:8001"
Write-Host "  API Docs  : http://127.0.0.1:8001/docs"
Write-Host "  Health    : http://127.0.0.1:8001/api/system/status"
Write-Host "  GeoServer : http://127.0.0.1:8080/geoserver"
Write-Host ""
Write-Host "Options:"
Write-Host "  .\start-all.bat -WithNgrok"
Write-Host "  .\start-all.bat -NoGeoServer"
Write-Host "  .\start-all.bat -NoBackend -NoFrontend"
Write-Host ""

if (-not $NoPause) {
    Read-Host "Press Enter to close this launcher window"
}

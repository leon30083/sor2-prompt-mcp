param(
    [string]$TargetDir = "$env:USERPROFILE\Documents\sor2-prompt-mcp",
    [string]$RepoUrl = "https://github.com/leon30083/sor2-prompt-mcp.git",
    [string]$Branch = "feat/composition-policy",
    [switch]$UseVenv,
    [string]$Proxy = "",
    [string]$MCPName = "sora2",
    [ValidateSet("trae","cherry","both")]
    [string]$GenerateConfig = "both"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

function Write-Info($msg){ Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg){ Write-Host "[WARN] $msg" -ForegroundColor DarkYellow }
function Write-ErrorMsg($msg){ Write-Host "[ERROR] $msg" -ForegroundColor Red }

# Check Python availability
try { $pythonVer = & python --version 2>$null } catch { $pythonVer = $null }
if(-not $pythonVer){
    Write-ErrorMsg "Python not found. Please install Python 3.11+ and retry."
    exit 1
}
Write-Info "Detected $pythonVer"

# Optional: set proxy for git and env (for cloning)
if($Proxy){
    Write-Info "Using proxy: $Proxy"
    git config --global http.proxy $Proxy | Out-Null
    git config --global https.proxy $Proxy | Out-Null
    $env:HTTP_PROXY = $Proxy
    $env:HTTPS_PROXY = $Proxy
}

# Ensure target directory exists
if(!(Test-Path $TargetDir)){
    Write-Info "Create target directory: $TargetDir"
    New-Item -ItemType Directory -Path $TargetDir | Out-Null
}

Write-Info "Clone repo: $RepoUrl -> $TargetDir (branch=$Branch)"
git clone --branch $Branch $RepoUrl $TargetDir
if($LASTEXITCODE -ne 0){
    Write-ErrorMsg "git clone failed. Check network or proxy settings."
    exit 1
}

# Optional: create and activate venv
if($UseVenv){
    Write-Info "Create virtual environment .venv and try activating"
    Push-Location $TargetDir
    python -m venv .venv
    if(Test-Path ".\.venv\Scripts\Activate.ps1"){
        & ".\.venv\Scripts\Activate.ps1"
        Write-Info "Virtual environment activated"
    } else {
        Write-Warn "Activate script not found. Continue without venv activation."
    }
    Pop-Location
}

# Generate MCP client config snippets (Trae / Cherry Studio)
$scriptDir = Join-Path $TargetDir "scripts"
if(!(Test-Path $scriptDir)){
    New-Item -ItemType Directory -Path $scriptDir | Out-Null
}

$traeConfig = @{
    mcpServers = @{
        $MCPName = @{
            command = "python"
            args = @("-m","src.mcp_server")
            env = @{
                PYTHONIOENCODING = "utf-8"
                PYTHONPATH = $TargetDir
            }
        }
    }
} | ConvertTo-Json -Depth 6

$cherryConfig = @{
    name = $MCPName
    command = "python"
    args = @("-m","src.mcp_server")
    cwd = $TargetDir
    env = @{
        PYTHONIOENCODING = "utf-8"
        PYTHONPATH = $TargetDir
    }
} | ConvertTo-Json -Depth 6

if($GenerateConfig -in @("trae","both")){
    $traeFile = Join-Path $scriptDir "trae_mcp_sora2.json"
    Set-Content -Path $traeFile -Value $traeConfig -Encoding UTF8
    Write-Info "Generated Trae config snippet: $traeFile"
}
if($GenerateConfig -in @("cherry","both")){
    $cherryFile = Join-Path $scriptDir "cherry_mcp_sora2.json"
    Set-Content -Path $cherryFile -Value $cherryConfig -Encoding UTF8
    Write-Info "Generated Cherry Studio config snippet: $cherryFile"
}

Write-Host ""
Write-Info "Quick verification:"
Write-Host "  1) Start server: cd `"$TargetDir`"; python -m src.mcp_server" -ForegroundColor Yellow
Write-Host "  2) Send JSON-RPC: initialize / tools/list / tools/call" -ForegroundColor Yellow
Write-Host "  3) Copy generated JSON into Trae/Cherry MCP settings" -ForegroundColor Yellow

Write-Host ""
Write-Info "Done."
exit 0
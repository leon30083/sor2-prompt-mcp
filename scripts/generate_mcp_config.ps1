param(
    [string]$MCPName = "sora2",
    [ValidateSet("trae","cherry","both")]
    [string]$GenerateConfig = "both",
    [string]$OutputFile = "mcp_config_sora2.txt"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

function Write-Info($msg){ Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-ErrorMsg($msg){ Write-Host "[ERROR] $msg" -ForegroundColor Red }

$RepoRoot = Split-Path -Parent $PSScriptRoot
if(-not (Test-Path (Join-Path $RepoRoot "src\mcp_server.py"))){
    Write-ErrorMsg "Run this script inside the cloned repository (src/mcp_server.py not found)."
    exit 1
}

$traeConfigObj = @{
    mcpServers = @{
        $MCPName = @{
            command = "python"
            args = @("-m","src.mcp_server")
            env = @{
                PYTHONIOENCODING = "utf-8"
                PYTHONPATH = $RepoRoot
            }
        }
    }
}

$cherryConfigObj = @{
    name = $MCPName
    command = "python"
    args = @("-m","src.mcp_server")
    cwd = $RepoRoot
    env = @{
        PYTHONIOENCODING = "utf-8"
        PYTHONPATH = $RepoRoot
    }
}

$lines = @()
$lines += "# MCP config snippets (copy-paste into your IDE settings)"
$lines += "# Repository path: $RepoRoot"
$lines += ""

if($GenerateConfig -in @("trae","both")){
    $lines += "[Trae mcpServers JSON]"
    $lines += ($traeConfigObj | ConvertTo-Json -Depth 6)
    $lines += ""
}

if($GenerateConfig -in @("cherry","both")){
    $lines += "[Cherry Studio MCP JSON]"
    $lines += ($cherryConfigObj | ConvertTo-Json -Depth 6)
    $lines += ""
}

$outPath = Join-Path $PSScriptRoot $OutputFile
Set-Content -Path $outPath -Value ($lines -join [Environment]::NewLine) -Encoding UTF8
Write-Info "Generated config file: $outPath"
Write-Info "Done."
exit 0
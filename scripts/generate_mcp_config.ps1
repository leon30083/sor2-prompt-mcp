param(
    [string]$MCPName = "sora2",
    [ValidateSet("trae","cherry","both")]
    [string]$GenerateConfig = "both",
    [ValidateSet("txt","json")]
    [string]$Format = "json",
    [string]$OutputFile = "mcp_config_sora2.txt",
    [string]$LogPath
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
try { $OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

function Write-Info($msg){ Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-ErrorMsg($msg){ Write-Host "[ERROR] $msg" -ForegroundColor Red }

$ScriptDir = $PSScriptRoot
if(-not $ScriptDir -or $ScriptDir -eq ""){
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$RepoRoot = Split-Path -Parent $ScriptDir
if(-not $LogPath -or $LogPath -eq ""){
    $LogPath = Join-Path $ScriptDir "generate_mcp_config.log"
}

try { [System.IO.File]::AppendAllText($LogPath, ("[BEGIN] " + (Get-Date).ToString() + [Environment]::NewLine)) } catch {}

try { Stop-Transcript | Out-Null } catch {}
try { Start-Transcript -Path $LogPath -Append -ErrorAction SilentlyContinue } catch {}
if(-not (Test-Path (Join-Path $RepoRoot "src\mcp_server.py"))){
    Write-ErrorMsg "Run this script inside the cloned repository (src/mcp_server.py not found)."
    try { Stop-Transcript | Out-Null } catch {}
    return
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

$writeNoBom = {
    param($path, $content)
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($path, $content, $utf8NoBom)
}

try {
    if($Format -eq "json"){
        if($GenerateConfig -in @("trae","both")){
            $traeJson = ($traeConfigObj | ConvertTo-Json -Depth 6)
            $traePath = Join-Path $ScriptDir ("trae_mcp_{0}.json" -f $MCPName)
            & $writeNoBom $traePath $traeJson
            Write-Info "Generated Trae JSON: $traePath"
        }
        if($GenerateConfig -in @("cherry","both")){
            $cherryJson = ($cherryConfigObj | ConvertTo-Json -Depth 6)
            $cherryPath = Join-Path $ScriptDir ("cherry_mcp_{0}.json" -f $MCPName)
            & $writeNoBom $cherryPath $cherryJson
            Write-Info "Generated Cherry JSON: $cherryPath"
        }
    }
    else {
        $lines = @()
        if($GenerateConfig -in @("trae","both")){
            $lines += "```json"
            $lines += ($traeConfigObj | ConvertTo-Json -Depth 6)
            $lines += "```"
            $lines += ""
        }
        if($GenerateConfig -in @("cherry","both")){
            $lines += "```json"
            $lines += ($cherryConfigObj | ConvertTo-Json -Depth 6)
            $lines += "```"
            $lines += ""
        }
        $outPath = Join-Path $ScriptDir $OutputFile
        & $writeNoBom $outPath ($lines -join [Environment]::NewLine)
        Write-Info "Generated TXT with JSON blocks: $outPath"
    }
    Write-Info "Done."
}
catch {
    Write-ErrorMsg ("Exception: " + $_.Exception.Message)
    try { [System.IO.File]::AppendAllText($LogPath, ("[ERROR] " + $_.Exception.Message + [Environment]::NewLine)) } catch {}
}
finally {
    try { Stop-Transcript | Out-Null } catch {}
    try { [System.IO.File]::AppendAllText($LogPath, ("[END] " + (Get-Date).ToString() + [Environment]::NewLine)) } catch {}
}
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

function Write-Info($msg){ Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg){ Write-Host "[WARN] $msg" -ForegroundColor DarkYellow }
function Write-ErrorMsg($msg){ Write-Host "[ERROR] $msg" -ForegroundColor Red }

# 检查 Python 是否可用
try {
    $pythonVer = & python --version 2>$null
} catch { $pythonVer = $null }
if(-not $pythonVer){
    Write-ErrorMsg "未检测到 Python。请安装 Python 3.11+ 后重试。"
    exit 1
}
Write-Info "检测到 $pythonVer"

# 可选：设置代理（用于 git clone 加速与临时环境变量）
if($Proxy){
    Write-Info "设置代理为 $Proxy"
    git config --global http.proxy $Proxy | Out-Null
    git config --global https.proxy $Proxy | Out-Null
    $env:HTTP_PROXY = $Proxy
    $env:HTTPS_PROXY = $Proxy
}

# 创建目标目录并克隆仓库
if(!(Test-Path $TargetDir)){
    Write-Info "创建目标目录: $TargetDir"
    New-Item -ItemType Directory -Path $TargetDir | Out-Null
}

Write-Info "克隆仓库: $RepoUrl -> $TargetDir (branch=$Branch)"
git clone --branch $Branch $RepoUrl $TargetDir
if($LASTEXITCODE -ne 0){
    Write-ErrorMsg "git clone 失败，请检查网络或代理设置。"
    exit 1
}

# 可选：创建并激活虚拟环境
if($UseVenv){
    Write-Info "创建虚拟环境 .venv 并尝试激活"
    Push-Location $TargetDir
    python -m venv .venv
    if(Test-Path ".\.venv\Scripts\Activate.ps1"){
        & ".\.venv\Scripts\Activate.ps1"
        Write-Info "已激活虚拟环境"
    } else {
        Write-Warn "未找到虚拟环境激活脚本，继续后续步骤"
    }
    Pop-Location
}

# 生成 MCP 客户端配置片段（Trae / Cherry Studio）
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
    Write-Info "已生成 Trae 配置片段: $traeFile"
}
if($GenerateConfig -in @("cherry","both")){
    $cherryFile = Join-Path $scriptDir "cherry_mcp_sora2.json"
    Set-Content -Path $cherryFile -Value $cherryConfig -Encoding UTF8
    Write-Info "已生成 Cherry Studio 配置片段: $cherryFile"
}

Write-Host "" 
Write-Info "快速验证："
Write-Host "  1) 在目标目录启动：cd `"$TargetDir`"; python -m src.mcp_server" -ForegroundColor Yellow
Write-Host "  2) 在客户端发送 JSON-RPC：initialize / tools/list / tools/call" -ForegroundColor Yellow
Write-Host "  3) Cherry/Trae 中将生成的 JSON 片段复制到设置中的 MCP 服务器配置处" -ForegroundColor Yellow

Write-Host "" 
Write-Info "完成。"
exit 0
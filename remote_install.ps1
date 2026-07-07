# ============================================================
# google-prospect-finder — Windows 一键安装脚本 (PowerShell)
# 用法:
#   irm https://raw.githubusercontent.com/adongtt/google-prospect-finder/main/remote_install.ps1 | iex
# ============================================================

$ErrorActionPreference = "Stop"

$SkillName = "google-prospect-finder"
$SkillDir = "$env:USERPROFILE\.workbuddy\skills\$SkillName"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  google-prospect-finder 安装程序 (Windows)       " -ForegroundColor Cyan
Write-Host "  B2B 客户搜索工具                               " -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ----------------------------------------------------------
# 1. 检查 Python 3.8+
# ----------------------------------------------------------
$Python = ""
foreach ($cmd in @("python", "python3")) {
    try {
        $ver = & $cmd -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>$null
        if ($ver) {
            $parts = $ver.Split('.')
            if ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 8) {
                $Python = $cmd
                break
            }
        }
    } catch { }
}

if (-not $Python) {
    Write-Host "[X] 未找到 Python 3.8+" -ForegroundColor Red
    Write-Host "    请先安装: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}
$PyVersion = & $Python --version
Write-Host "[OK] Python: $PyVersion" -ForegroundColor Green

# ----------------------------------------------------------
# 2. 下载 Skill
# ----------------------------------------------------------
Write-Host ""
Write-Host "--- 下载 Skill ---" -ForegroundColor Yellow

$ParentDir = Split-Path $SkillDir -Parent
if (-not (Test-Path $ParentDir)) {
    New-Item -ItemType Directory -Path $ParentDir -Force | Out-Null
}

if (Test-Path $SkillDir) {
    Write-Host "[!] 已存在 $SkillDir，正在更新..." -ForegroundColor Yellow
    Remove-Item $SkillDir -Recurse -Force
}

# GitHub 仓库地址（用户可修改为自己的仓库）
$RepoUrl = if ($env:REPO_URL) { $env:REPO_URL } else { "https://github.com/adongtt/google-prospect-finder" }
$ZipUrl = "$RepoUrl/archive/refs/heads/main.zip"

try {
    $TempZip = "$env:TEMP\$SkillName.zip"
    $TempDir = "$env:TEMP\${SkillName}_extract"

    Write-Host "[i] 从 $RepoUrl 下载..."
    Invoke-WebRequest -Uri $ZipUrl -OutFile $TempZip -UseBasicParsing

    if (Test-Path $TempDir) { Remove-Item $TempDir -Recurse -Force }
    Expand-Archive -Path $TempZip -DestinationPath $TempDir -Force

    # GitHub ZIP 会多一层目录 (repo-name-main)
    $Extracted = Get-ChildItem $TempDir -Directory | Select-Object -First 1
    Copy-Item $Extracted.FullName $SkillDir -Recurse -Force

    Remove-Item $TempZip -Force
    Remove-Item $TempDir -Recurse -Force

    Write-Host "[OK] 下载解压完成" -ForegroundColor Green
} catch {
    Write-Host "[X] 下载失败: $_" -ForegroundColor Red
    Write-Host "    请检查网络或仓库地址: $RepoUrl" -ForegroundColor Yellow
    exit 1
}

# ----------------------------------------------------------
# 3. 配置 API Key
# ----------------------------------------------------------
Write-Host ""
Write-Host "--- 配置 API Key ---" -ForegroundColor Yellow

if ($env:SERPER_API_KEY) {
    Write-Host "[OK] 已检测到环境变量 SERPER_API_KEY" -ForegroundColor Green
} elseif (Test-Path "$SkillDir\.env") {
    Write-Host "[OK] 已存在 .env 文件" -ForegroundColor Green
} else {
    Write-Host "[i] 请前往 https://serper.dev 注册获取 API Key（免费 2,500 次）" -ForegroundColor Cyan
    $ApiKey = Read-Host "请输入你的 Serper.dev API Key (直接回车跳过，稍后配置)"

    if ($ApiKey) {
        "SERPER_API_KEY=$ApiKey" | Out-File -FilePath "$SkillDir\.env" -Encoding UTF8
        Write-Host "[OK] API Key 已保存到 $SkillDir\.env" -ForegroundColor Green
    } else {
        Copy-Item "$SkillDir\.env.example" "$SkillDir\.env"
        Write-Host "[i] 已创建 .env 模板，请稍后编辑填入 API Key" -ForegroundColor Yellow
        Write-Host "    notepad $SkillDir\.env" -ForegroundColor Gray
    }
}

# ----------------------------------------------------------
# 4. 可选：安装 Playwright
# ----------------------------------------------------------
Write-Host ""
Write-Host "--- Playwright 浏览器模式（可选）---" -ForegroundColor Yellow
Write-Host "浏览器模式可处理 JavaScript 动态网站，提取率更高（55% vs 30%）"
$InstallPw = Read-Host "是否安装 Playwright + Chromium? [y/N]"

if ($InstallPw -match '^[Yy]') {
    Write-Host "安装 Playwright..." -ForegroundColor Cyan
    & $Python -m pip install playwright
    & $Python -m playwright install chromium

    try {
        & $Python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=['--no-sandbox'])
    b.close()
print('OK')
" 2>$null
        Write-Host "[OK] Playwright 验证通过" -ForegroundColor Green
    } catch {
        Write-Host "[!] Playwright 安装可能未成功，不影响基本功能" -ForegroundColor Yellow
    }
} else {
    Write-Host "[i] 跳过 Playwright 安装。基本搜索功能不需要它。" -ForegroundColor Gray
}

# ----------------------------------------------------------
# 5. 验证安装
# ----------------------------------------------------------
Write-Host ""
Write-Host "--- 验证安装 ---" -ForegroundColor Yellow

if ((Test-Path "$SkillDir\SKILL.md") -and (Test-Path "$SkillDir\scripts\prospect_search.py")) {
    Write-Host "[OK] Skill 文件完整" -ForegroundColor Green
    & $Python "$SkillDir\scripts\prospect_search.py" --help 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] 脚本运行正常" -ForegroundColor Green
    } else {
        Write-Host "[!] 脚本可能有依赖问题" -ForegroundColor Yellow
    }
} else {
    Write-Host "[X] Skill 文件不完整" -ForegroundColor Red
    exit 1
}

# ----------------------------------------------------------
# 完成
# ----------------------------------------------------------
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "           ✅ 安装完成！" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Skill 位置: $SkillDir" -ForegroundColor White
Write-Host ""
Write-Host "  使用方法:" -ForegroundColor White
Write-Host "  在 WorkBuddy 中直接说:" -ForegroundColor White
Write-Host "  '帮我找美国手套买家'" -ForegroundColor Cyan
Write-Host ""
Write-Host "  或命令行:" -ForegroundColor White
Write-Host "  $Python `"$SkillDir\scripts\prospect_search.py`" `"gloves importer USA`" -o leads.csv" -ForegroundColor Gray
Write-Host ""

# 检查 API Key 是否配置
$NeedKey = $false
if (-not (Test-Path "$SkillDir\.env")) {
    $NeedKey = $true
} else {
    $content = Get-Content "$SkillDir\.env" -Raw
    if ($content -match "your_api_key_here") { $NeedKey = $true }
}
if ($NeedKey) {
    Write-Host "[!] 还未配置 API Key!" -ForegroundColor Yellow
    Write-Host "     1. 访问 https://serper.dev 注册" -ForegroundColor Yellow
    Write-Host "     2. 编辑 $SkillDir\.env 填入 Key" -ForegroundColor Yellow
    Write-Host ""
}

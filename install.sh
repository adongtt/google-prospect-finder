#!/usr/bin/env bash
# ============================================================
# google-prospect-finder 安装脚本
# 安装 Playwright + Chromium（用于 --use-browser 模式）
# ============================================================
set -e

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "=== google-prospect-finder 安装 ==="
echo "Skill 目录: $SKILL_DIR"
echo ""

# ----------------------------------------------------------
# 1. 检查 Python 版本 (需要 3.8+)
# ----------------------------------------------------------
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$($cmd -c 'import sys; print(sys.version_info[:2])' 2>/dev/null)
        if [ -n "$ver" ]; then
            major=$(echo "$ver" | tr -d '() ' | cut -d',' -f1)
            minor=$(echo "$ver" | tr -d '() ' | cut -d',' -f2)
            if [ "$major" -ge 3 ] && [ "$minor" -ge 8 ] 2>/dev/null; then
                PYTHON="$cmd"
                break
            fi
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "[错误] 未找到 Python 3.8+，请先安装 Python。"
    echo "  下载: https://www.python.org/downloads/"
    exit 1
fi

echo "Python: $($PYTHON --version)"

# ----------------------------------------------------------
# 2. 检查是否已有 Serper.dev API Key
# ----------------------------------------------------------
if [ -z "$SERPER_API_KEY" ]; then
    # 检查 .env 文件
    ENV_FILE="$SKILL_DIR/.env"
    if [ ! -f "$ENV_FILE" ]; then
        echo ""
        echo "[提示] 未检测到 Serper.dev API Key。"
        echo "  1. 访问 https://serper.dev 注册（免费 2,500 次搜索额度）"
        echo "  2. 复制 .env.example 为 .env 并填入 API Key："
        echo "     cp \"$SKILL_DIR/.env.example\" \"$SKILL_DIR/.env\""
        echo "  3. 或设置环境变量：export SERPER_API_KEY=\"your_key\""
        echo ""
        echo "（不配置 API Key 也可以安装 Playwright，只是暂时无法搜索）"
    fi
fi

# ----------------------------------------------------------
# 3. 安装 Playwright
# ----------------------------------------------------------
echo ""
echo "--- 安装 Playwright ---"
$PYTHON -m pip install playwright

# ----------------------------------------------------------
# 4. 安装 Chromium 浏览器
# ----------------------------------------------------------
echo ""
echo "--- 安装 Chromium 浏览器 ---"
$PYTHON -m playwright install chromium

# ----------------------------------------------------------
# 5. 验证安装
# ----------------------------------------------------------
echo ""
echo "--- 验证安装 ---"
$PYTHON -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
    page = browser.new_page()
    page.goto('https://example.com', timeout=15000)
    print(f'Playwright OK! Page title: {page.title()}')
    browser.close()
"

echo ""
echo "=== 安装完成! ==="
echo ""
echo "使用方法："
echo "  基本搜索:  $PYTHON \"$SKILL_DIR/scripts/prospect_search.py\" \"gloves importer USA\" -o leads.csv"
echo "  浏览器模式: $PYTHON \"$SKILL_DIR/scripts/prospect_search.py\" \"gloves importer USA\" --use-browser -o leads.csv"
echo "  仅域名:    $PYTHON \"$SKILL_DIR/scripts/prospect_search.py\" \"gloves importer USA\" --no-visit -o domains.csv"

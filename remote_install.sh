#!/usr/bin/env bash
# ============================================================
# google-prospect-finder — 远程一键安装脚本
# 用法（Mac/Linux）:
#   curl -fsSL https://raw.githubusercontent.com/adongtt/google-prospect-finder/main/remote_install.sh | bash
#
# 用法（Windows Git Bash）:
#   curl -fsSL https://raw.githubusercontent.com/adongtt/google-prospect-finder/main/remote_install.sh | bash
# ============================================================
set -e

SKILL_NAME="google-prospect-finder"
SKILL_DIR="${HOME}/.workbuddy/skills/${SKILL_NAME}"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   google-prospect-finder 安装程序       ║"
echo "║   B2B 客户搜索工具                       ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ----------------------------------------------------------
# 1. 检查 Python 3.8+
# ----------------------------------------------------------
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$($cmd -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")' 2>/dev/null)
        if [ -n "$ver" ]; then
            major=$(echo "$ver" | cut -d'.' -f1)
            minor=$(echo "$ver" | cut -d'.' -f2)
            if [ "$major" -eq 3 ] && [ "$minor" -ge 8 ] 2>/dev/null; then
                PYTHON="$cmd"
                break
            fi
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "[✗] 未找到 Python 3.8+，请先安装：https://www.python.org/downloads/"
    exit 1
fi
echo "[✓] Python: $($PYTHON --version)"

# ----------------------------------------------------------
# 2. 创建 skill 目录
# ----------------------------------------------------------
echo ""
echo "--- 安装 Skill ---"
mkdir -p "$(dirname "$SKILL_DIR")"

if [ -d "$SKILL_DIR" ]; then
    echo "[!] 已存在 $SKILL_DIR，正在更新..."
    rm -rf "$SKILL_DIR"
fi

# 获取脚本所在目录（如果本地运行）或从远程下载
SCRIPT_DIR="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"
if [ -f "$SCRIPT_DIR/SKILL.md" ]; then
    # 本地安装
    cp -r "$SCRIPT_DIR" "$SKILL_DIR"
    echo "[✓] 从本地复制完成"
else
    # 远程下载
    REPO_URL="${REPO_URL:-https://github.com/adongtt/google-prospect-finder}"
    echo "[i] 从 $REPO_URL 下载..."
    
    # 尝试 git clone
    if command -v git &>/dev/null; then
        git clone --depth 1 "$REPO_URL" "$SKILL_DIR" 2>/dev/null || {
            echo "[✗] git clone 失败"
            exit 1
        }
        rm -rf "$SKILL_DIR/.git"
        echo "[✓] git clone 完成"
    else
        # 下载 ZIP
        ZIP_URL="${REPO_URL}/archive/refs/heads/main.zip"
        TMP_ZIP="/tmp/${SKILL_NAME}.zip"
        if command -v curl &>/dev/null; then
            curl -fsSL "$ZIP_URL" -o "$TMP_ZIP"
        elif command -v wget &>/dev/null; then
            wget -q "$ZIP_URL" -O "$TMP_ZIP"
        else
            echo "[✗] 需要 curl 或 wget 来下载"
            exit 1
        fi
        
        TMP_DIR="/tmp/${SKILL_NAME}_extract"
        mkdir -p "$TMP_DIR"
        # 解压（unzip 或 tar）
        if command -v unzip &>/dev/null; then
            unzip -q "$TMP_ZIP" -d "$TMP_DIR"
        else
            tar -xf "$TMP_ZIP" -C "$TMP_DIR"
        fi
        
        # GitHub ZIP 会多一层目录
        EXTRACTED=$(find "$TMP_DIR" -name "SKILL.md" -exec dirname {} \; | head -1)
        cp -r "$EXTRACTED" "$SKILL_DIR"
        rm -rf "$TMP_DIR" "$TMP_ZIP"
        echo "[✓] 下载解压完成"
    fi
fi

# ----------------------------------------------------------
# 3. 配置 API Key
# ----------------------------------------------------------
echo ""
echo "--- 配置 API Key ---"
if [ -n "$SERPER_API_KEY" ]; then
    echo "[✓] 已检测到环境变量 SERPER_API_KEY"
elif [ -f "$SKILL_DIR/.env" ]; then
    echo "[✓] 已存在 .env 文件"
else
    echo "[i] 请前往 https://serper.dev 注册获取 API Key（免费 2,500 次）"
    echo ""
    read -p "请输入你的 Serper.dev API Key (直接回车跳过，稍后配置): " API_KEY
    
    if [ -n "$API_KEY" ]; then
        echo "SERPER_API_KEY=${API_KEY}" > "$SKILL_DIR/.env"
        echo "[✓] API Key 已保存到 $SKILL_DIR/.env"
    else
        cp "$SKILL_DIR/.env.example" "$SKILL_DIR/.env"
        echo "[i] 已创建 .env 模板，请稍后编辑填入 API Key"
        echo "    vim $SKILL_DIR/.env"
    fi
fi

# ----------------------------------------------------------
# 4. 可选：安装 Playwright
# ----------------------------------------------------------
echo ""
echo "--- Playwright 浏览器模式（可选）---"
echo "浏览器模式可以处理 JavaScript 动态网站，提取率更高（55% vs 30%）"
read -p "是否安装 Playwright + Chromium? [y/N]: " INSTALL_PW

if [[ "$INSTALL_PW" =~ ^[Yy]$ ]]; then
    echo "安装 Playwright..."
    $PYTHON -m pip install playwright
    $PYTHON -m playwright install chromium
    
    # 验证
    $PYTHON -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=['--no-sandbox'])
    b.close()
print('[✓] Playwright 安装成功')
" 2>/dev/null && echo "[✓] Playwright 验证通过" || echo "[!] Playwright 安装可能未成功，不影响基本功能"
else
    echo "[i] 跳过 Playwright 安装。基本搜索功能不需要它。"
    echo "    稍后安装可运行: bash $SKILL_DIR/install.sh"
fi

# ----------------------------------------------------------
# 5. 验证安装
# ----------------------------------------------------------
echo ""
echo "--- 验证安装 ---"
if [ -f "$SKILL_DIR/SKILL.md" ] && [ -f "$SKILL_DIR/scripts/prospect_search.py" ]; then
    echo "[✓] Skill 文件完整"
    $PYTHON "$SKILL_DIR/scripts/prospect_search.py" --help > /dev/null 2>&1 && echo "[✓] 脚本运行正常" || echo "[!] 脚本可能有依赖问题"
else
    echo "[✗] Skill 文件不完整"
    exit 1
fi

# ----------------------------------------------------------
# 完成
# ----------------------------------------------------------
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║           ✅ 安装完成！                   ║"
echo "╠══════════════════════════════════════════╣"
echo "║                                          ║"
echo "║  Skill 位置: $SKILL_DIR"
echo "║                                          ║"
echo "║  使用方法:                                ║"
echo "║  在 WorkBuddy 中直接说:                   ║"
echo "║  '帮我找美国手套买家'                      ║"
echo "║                                          ║"
echo "║  或命令行:                                ║"
echo "║  $PYTHON \"$SKILL_DIR/scripts/prospect_search.py\" \\"
echo "║    \"gloves importer USA\" -o leads.csv      ║"
echo "║                                          ║"
echo "╚══════════════════════════════════════════╝"
echo ""

if [ ! -f "$SKILL_DIR/.env" ] || grep -q "your_api_key_here" "$SKILL_DIR/.env" 2>/dev/null; then
    echo "⚠️  还未配置 API Key!"
    echo "   1. 访问 https://serper.dev 注册"
    echo "   2. 编辑 $SKILL_DIR/.env 填入 Key"
    echo ""
fi

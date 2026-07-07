# Google Prospect Finder — B2B 客户开发工具

通过 Google 搜索自动发现 B2B 潜在客户网站，过滤大型平台，提取联系方式，输出 CSV 文件。

## 一键安装

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/adongtt/google-prospect-finder/main/remote_install.ps1 | iex
```

### Mac / Linux / Windows Git Bash

```bash
curl -fsSL https://raw.githubusercontent.com/adongtt/google-prospect-finder/main/remote_install.sh | bash
```

> 安装脚本会自动下载、配置 API Key、可选安装 Playwright。如果你 fork 了本仓库，请将脚本中的 `adongtt` 替换为你的 GitHub 用户名。

---

## 这是什么？

一个自动化 B2B 线索挖掘工具，帮你：

1. **Google 搜索** — 用 Serper.dev API 搜索目标关键词（如 "work gloves distributor USA"）
2. **智能过滤** — 自动屏蔽阿里巴巴、亚马逊、LinkedIn 等 100+ 大型平台
3. **提取联系方式** — 访问每个潜在客户网站，提取邮箱、电话、公司名
4. **浏览器渲染** — 用 Playwright 处理 JavaScript 动态加载的网站
5. **输出 CSV** — 结构化数据，可直接导入 CRM

## 手动安装

### 第一步：获取 API Key

1. 访问 [serper.dev](https://serper.dev) 注册（免费 2,500 次搜索额度）
2. 在 Dashboard 复制你的 API Key

### 第二步：配置 API Key

任选一种方式：

**方式 A — 环境变量（推荐）**
```bash
# Windows CMD（永久生效）
setx SERPER_API_KEY "你的API_Key"

# macOS / Linux
echo 'export SERPER_API_KEY="你的API_Key"' >> ~/.bashrc
source ~/.bashrc
```

**方式 B — .env 文件**
```bash
# 复制模板并编辑
cp .env.example .env
# 用文本编辑器打开 .env，替换 your_api_key_here
```

**方式 C — 命令行参数**
```bash
python scripts/prospect_search.py "gloves importer" --apikey "你的API_Key"
```

### 第三步：运行搜索

```bash
# 最简单的用法（纯 HTTP，无需安装额外依赖）
python scripts/prospect_search.py "work gloves distributor USA" -o leads.csv

# 多关键词搜索
python scripts/prospect_search.py "work gloves distributor USA,safety gloves importer USA" -o leads.csv

# 浏览器模式（提取率更高，但较慢）
python scripts/prospect_search.py "work gloves distributor USA" --use-browser -o leads.csv

# 仅搜索不访问网站（最快）
python scripts/prospect_search.py "work gloves distributor USA" --no-visit -o domains.csv
```

## 完整安装（可选 — 浏览器模式）

如果要用 `--use-browser` 功能（处理 JavaScript 动态网站），需要安装 Playwright：

```bash
# 一键安装
bash install.sh
```

或手动安装：
```bash
pip install playwright
playwright install chromium
```

> **不安装 Playwright 也能用** — 基本搜索 + HTTP 提取功能不需要任何额外依赖，纯 Python 标准库即可运行。

## 命令行参数

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `keywords` | — | （必填） | 搜索关键词，逗号分隔多个 |
| `--output` | `-o` | prospects.csv | 输出 CSV 文件路径 |
| `--apikey` | `-k` | 环境变量 | Serper.dev API Key |
| `--num-results` | `-n` | 20 | 每条查询返回结果数 |
| `--max-sites` | `-m` | 30 | 最多访问网站数 |
| `--countries` | `-c` | — | 目标国家代码，逗号分隔（如 US,DE,FR） |
| `--delay` | `-d` | 1.5 | 访问网站间隔秒数 |
| `--no-visit` | — | false | 跳过网站访问，仅输出搜索结果 |
| `--use-browser` | — | false | 用 Playwright 渲染 JS 网站 |
| `--product` | `-p` | — | 产品名，自动扩展搜索词 |
| `--keyword-file` | `-f` | — | 从文件读取关键词（每行一个） |

## 输出格式

CSV 文件包含以下字段：

| 字段 | 说明 |
|------|------|
| Domain | 网站域名 |
| Title | 搜索结果标题 |
| URL | 搜索结果链接 |
| Snippet | 搜索结果摘要 |
| Country | 国家（从域名 TLD 推断） |
| Company Name | 公司名（从网站提取） |
| Email | 主要邮箱 |
| Phone | 电话号码 |
| Secondary Email | 次要邮箱 |
| Contact Page | 联系页面 URL |
| Search Query | 匹配的搜索词 |

## 搜索策略

### 推荐关键词组合

```
# 按角色搜索
"{product}" importer {country}     # 进口商
"{product}" distributor {country}  # 分销商
"{product}" wholesaler {country}   # 批发商
"{product}" buyer {country}        # 买家
"{product}" supplier {country}      # 供应商

# 按产品类型搜索
"work gloves" buyer USA
"leather gloves" importer Germany
"safety gloves" distributor UK
"PPE gloves" wholesaler Canada
"nitrile gloves" importer France
"cut resistant gloves" buyer Australia
```

### 多关键词搜索

用逗号分隔多个关键词，脚本会自动去重：

```bash
python scripts/prospect_search.py \
  "work gloves distributor USA,work gloves wholesaler USA,safety gloves importer USA" \
  -o leads.csv
```

### 从文件读取关键词

创建 `keywords.txt`：
```
work gloves distributor USA
work gloves wholesaler USA
safety gloves importer USA
PPE gloves supplier USA
```

```bash
python scripts/prospect_search.py -f keywords.txt -o leads.csv
```

## 两种模式对比

| | 基本模式（默认） | 浏览器模式（--use-browser） |
|---|---|---|
| **依赖** | Python 标准库，无需安装 | 需安装 Playwright + Chromium |
| **速度** | 快（每个网站 ~2秒） | 慢（每个网站 ~5-10秒） |
| **提取率** | ~30-40% | ~50-60% |
| **原理** | 用 urllib 获取 HTML，正则提取 | 先用 HTTP 提取，无结果时用 Playwright 渲染 JS 重试 |
| **适用场景** | 快速筛选，批量搜索 | 精准提取联系方式 |

## 域名过滤

脚本自动过滤以下类型的网站（共 100+ 域名）：

- **B2B 平台**：alibaba.com, made-in-china.com, globalsources.com, indiamart.com...
- **电商**：amazon.com, ebay.com, etsy.com, walmart.com...
- **社交媒体**：facebook.com, linkedin.com, instagram.com...
- **搜索引擎**：google.com, bing.com, yahoo.com...
- **参考/百科**：wikipedia.org, youtube.com...
- **目录/数据**：thomasnet.com, europages.com, volza.com...
- **招聘**：indeed.com, glassdoor.com, ziprecruiter.com...

如需调整，编辑 `scripts/prospect_search.py` 中的 `BLOCKLIST` 集合。

## 常见问题

### Q: 搜索结果为空？

- 检查 API Key 是否正确（免费额度是否用完）
- 尝试更简单的关键词（如 `"gloves" importer` 而非 `"leather work gloves" importer Germany`）
- 确认网络能访问 google.serper.dev

### Q: 提取不到邮箱/电话？

- 用 `--use-browser` 模式重试（处理 JS 动态网站）
- 部分网站的联系方式在图片或 PDF 中，无法自动提取
- 有些网站需要填表单才能看到联系方式

### Q: 提示 "Playwright not available"？

- 运行 `bash install.sh` 安装 Playwright
- 或不使用 `--use-browser`，基本模式不需要 Playwright

### Q: CSV 在 Excel 中中文乱码？

CSV 已使用 UTF-8 BOM 编码。如仍乱码：
- Excel → 数据 → 从文本导入 → 选择 UTF-8 编码

### Q: 如何节省 API 额度？

- 用 `--no-visit` 先搜索看域名列表，再选择性访问
- 用 `--num-results 10` 减少每页结果数
- 多个关键词合并搜索（逗号分隔），比分别搜索更省

## 文件结构

```
google-prospect-finder/
├── SKILL.md              # Skill 元数据（WorkBuddy 自动识别）
├── README.md             # 本文档
├── install.sh            # 本地安装 Playwright + Chromium
├── remote_install.sh     # 远程一键安装（Mac/Linux）
├── remote_install.ps1    # 远程一键安装（Windows PowerShell）
├── .env.example          # API Key 配置模板
├── .gitignore            # Git 忽略规则
├── scripts/
│   └── prospect_search.py    # 主脚本（纯 Python 标准库）
├── references/
│   ├── search_strategies.md  # 搜索关键词模板
│   └── blocklist.md          # 域名黑名单说明
└── assets/
    └── results_template.csv  # CSV 输出格式示例
```

## 技术细节

- **搜索 API**：Serper.dev（Google 搜索结果接口）
- **脚本语言**：Python 3.8+（标准库 + 可选 Playwright）
- **联系方式提取**：正则表达式（邮箱、国际电话号码）
- **浏览器渲染**：Playwright + Chromium（headless 模式）
- **输出格式**：CSV（UTF-8 BOM，兼容 Excel）
- **无外部依赖**：基本模式仅用 Python 标准库（urllib, json, re, csv, argparse）

## 许可证

自由使用，无限制。

---
name: google-prospect-finder
description: |
  B2B潜在客户搜索工具。通过Google搜索（Serper.dev API）发现潜在B2B客户网站，
  自动过滤大型平台（阿里巴巴、亚马逊、LinkedIn等），访问目标网站提取邮箱、电话和公司名称，
  输出CSV文件便于导入CRM。当用户需要找客户、开发潜在客户、B2B线索挖掘、搜邮箱、
  找进口商/批发商/分销商、外贸客户开发时使用此skill。
agent_created: true
---

# B2B Prospect Finder - Google Search Lead Generation

通过 Google 搜索自动发现 B2B 潜在客户，过滤已知大型平台，提取联系方式，输出结构化 CSV。

## 触发场景

- 用户说"帮我找客户"、"找进口商"、"开发海外客户"
- 用户说"搜索手套买家"、"找XX产品的分销商"
- 用户说"Google搜索XX"、"找XX的邮箱"
- 用户需要 B2B 线索挖掘、外贸客户开发

## 重要：Serper.dev API Key

本 skill 使用 Serper.dev API（Google 搜索结果接口）。**使用前需获取 API Key**：

1. 访问 https://serper.dev 注册（免费 2,500 次搜索额度）
2. 获取 API Key 后，设置环境变量：
   ```bash
   # Windows CMD
   set SERPER_API_KEY=your_key_here
   # 或永久设置
   setx SERPER_API_KEY "your_key_here"
   ```
3. 或在命令中通过 `--apikey` 参数传入

## 工作流程

### Step 1: 理解用户需求

从用户输入中提取：
- **产品关键词**：如"手套"、"皮手套"、"劳保手套"
- **目标市场**：如"欧洲"、"德国"、"美国"（若无则搜索全球）
- **角色**：默认为进口商，也可能是批发商/分销商/买家

### Step 2: 生成搜索查询

参考 `references/search_strategies.md` 中的关键词模板，生成 3-10 条搜索查询。

示例（用户说"找欧洲手套进口商"）：
```
"leather gloves" importer Germany
"work gloves" importer Europe
"safety gloves" distributor Europe
"gloves" buyer Germany
"protective gloves" import company Europe
```

### Step 3: 执行搜索脚本

```bash
# 基本用法
python "{SKILL_ROOT}/scripts/prospect_search.py" \
  "leather gloves importer Germany" \
  -o "./prospects.csv"


# 多国家搜索
python "{SKILL_ROOT}/scripts/prospect_search.py" \
  "safety gloves buyer" \
  --countries "DE,FR,UK,IT" \
  -o "./prospects.csv"

# 不访问网站（仅搜索结果）
python "{SKILL_ROOT}/scripts/prospect_search.py" \
  "gloves importer" \
  --no-visit \
  -o "./domains_only.csv"
```

**Python 运行时**：使用系统 Python 3.8+ 或 WorkBuddy 托管 Python。
- 基本模式（纯 HTTP）：`python` 即可，无需额外依赖
- 浏览器模式（`--use-browser`）：需安装 Playwright，运行 `bash {SKILL_ROOT}/install.sh`

### Step 4: 展示结果

脚本运行完成后：
1. 向用户展示 CSV 文件路径
2. 展示找到的潜在客户数量（特别是有邮箱的）
3. 展示前 5-10 条有联系方式的客户摘要
4. 使用 `present_files` 打开 CSV 文件供用户查看

## 命令行参数速查

| 参数 | 说明 |
|------|------|
| `keywords` | 搜索关键词（逗号分隔多个） |
| `--apikey`, `-k` | Serper.dev API Key |
| `--output`, `-o` | 输出 CSV 路径（默认 prospects.csv） |
| `--max-sites`, `-m` | 最多访问网站数（默认 30） |
| `--countries`, `-c` | 目标国家代码，逗号分隔 |
| `--delay`, `-d` | 访问网站间隔秒数（默认 1.5） |
| `--num-results`, `-n` | 每条查询返回结果数（默认 20） |
| `--no-visit` | 跳过网站访问，仅输出搜索结果 |
| `--use-browser` | 使用 Playwright 浏览器渲染 JS 动态网站（更彻底但较慢） |
| `--product`, `-p` | 产品名，自动扩展搜索词 |
| `--keyword-file`, `-f` | 从文件读取关键词（每行一个） |

## 域名过滤

脚本自动过滤以下类型网站（详见 `references/blocklist.md`）：
- B2B 贸易平台（阿里巴巴、中国制造、Global Sources 等）
- 电商平台（亚马逊、eBay、Etsy 等）
- 社交媒体（Facebook、LinkedIn、Instagram 等）
- 搜索引擎、新闻网站、政府网站、招聘网站、商业目录

如需调整过滤范围，编辑 `scripts/prospect_search.py` 中的 `BLOCKLIST` 集合。

## 搜索策略参考

详细关键词模板见 `references/search_strategies.md`，包括：
- 角色关键词模板（进口商/买家/分销商等）
- 手套行业特定关键词
- 国家特定搜索模式（欧洲/亚洲/美洲等）
- 高级 Google 搜索技巧

## 故障排查

### API Key 错误
```
Error: Serper.dev API key required.
```
→ 前往 https://serper.dev 注册获取 Key，设置 `SERPER_API_KEY` 环境变量。

### 无搜索结果
→ 尝试更通用的关键词，或减少 `--num-results` 参数值。
→ 检查 API Key 是否有效（免费额度是否已用完）。

### 网站访问失败（大量错误）
→ 增加 `--delay` 参数值（如 `--delay 3`）。
→ 使用 `--no-visit` 跳过网站访问，先查看搜索结果。

### CSV 在 Excel 中中文乱码
→ CSV 已使用 UTF-8 BOM 编码，Excel 应能正确打开。如仍乱码，用"数据→从文本导入"并选择 UTF-8。

## 注意事项

- 脚本默认使用 Python 标准库（urllib），无需 pip install
- 使用 `--use-browser` 需安装 Playwright（已安装在 venv 中）
- `--use-browser` 模式：先用 urllib 快速提取，无联系方式时自动回退到 Playwright 渲染 JS
- 网站访问有 1.5 秒间隔，访问 30 个网站约需 1-3 分钟
- `--use-browser` 模式可能需要 3-6 分钟（Playwright 渲染较慢但更全面）
- Serper.dev 免费额度 2,500 次/月，每次搜索消耗 1 次额度
- 联系信息提取依赖于目标网站是否有公开的联系方式

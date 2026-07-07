# B2B 搜索关键词策略参考

本文件提供手套类产品的 B2B 搜索关键词模板。AI 根据用户需求选择合适的模板组合，生成高质量搜索查询。

## 一、角色关键词模板

将 `{product}` 替换为具体产品名，`{country}` 替换为目标国家/地区。

```
"{product}" importer {country}
"{product}" buyer {country}
"{product}" distributor {country}
"{product}" wholesaler {country}
"{product}" import company {country}
"{product}" procurement {country}
"{product}" sourcing agent {country}
"{product}" trading company {country}
"buy" "{product}" wholesale {country}
"import" "{product}" {country}
```

## 二、手套行业特定关键词

```
glove manufacturer supplier {country}
glove import export {country}
industrial glove suppliers {country}
safety glove distributor {country}
leather glove importer {country}
work glove wholesale {country}
sports glove buyer {country}
protective gloves procurement {country}
PPE glove distributor {country}
medical glove importer {country}
cut resistant glove buyer {country}
winter glove importer {country}
motorcycle glove distributor {country}
cycling glove buyer {country}
ski glove importer {country}
```

## 三、产品变体关键词

根据用户需求选择合适的产品变体：

| 英文产品名 | 适用场景 |
|-----------|---------|
| leather gloves | 皮手套 |
| work gloves | 劳保手套/工作手套 |
| safety gloves | 安全手套 |
| sports gloves | 运动手套 |
| cycling gloves | 骑行手套 |
| ski gloves | 滑雪手套 |
| motorcycle gloves | 摩托车手套 |
| winter gloves | 冬季手套 |
| cut resistant gloves | 防切割手套 |
| medical gloves | 医用手套 |
| nitrile gloves | 丁腈手套 |
| heat resistant gloves | 耐热手套 |
| welding gloves | 焊接手套 |
| gardening gloves | 园艺手套 |
| touchscreen gloves | 触屏手套 |

## 四、国家特定搜索模式

### 欧洲市场
```
site:.de "gloves" "import" -alibaba -amazon
site:.fr "gants" importateur
site:.it "guanti" importazione
site:.es "guantes" importador
site:.nl "handschoenen" importeur
site:.co.uk "gloves" importer
site:.pl "rekawice" import
site:.se "handskar" import
```

### 亚洲市场
```
site:.jp "手袋" 輸入
site:.kr "장갑" 수입
site:.in "gloves" importer
```

### 美洲市场
```
site:.us "gloves" importer
site:.ca "gloves" distributor
site:.com.au "gloves" importer
site:.com.br "luvas" importador
site:.com.mx "guantes" importador
```

### 中东/非洲市场
```
site:.ae "gloves" importer
site:.sa "gloves" supplier
site:.za "gloves" distributor
```

## 五、市场调研类搜索

用于发现行业信息、展会和协会，辅助客户开发：

```
"{product}" trade shows {country}
"{product}" industry associations {country}
"{product}" chamber of commerce {country}
"top" "{product}" importers in {country}
"{product}" import statistics {country}
"{product}" market report {country}
```

## 六、高级 Google 搜索技巧

### 排除特定平台
在查询中直接排除主要 B2B 平台和电商：
```
"gloves importer" Europe -site:alibaba.com -site:amazon.com -site:ebay.com -site:linkedin.com
```

### 精确匹配
使用引号进行精确短语匹配：
```
"glove importer" "contact" Germany
"safety glove distributor" "email"
```

### 文件类型搜索
搜索含联系方式的文档：
```
"gloves" importer filetype:pdf "contact"
"gloves" distributor filetype:xlsx
```

### intitle 搜索
```
intitle:"glove importer" Europe
intitle:"contact us" "gloves" distributor
```

## 七、组合查询策略

当用户说"帮我找欧洲的手套进口商"时，AI 应生成以下组合查询：

1. `"leather gloves" importer Europe`
2. `"work gloves" buyer Germany`
3. `"safety gloves" distributor France`
4. `"gloves" import company UK`
5. `"gloves" wholesale Italy`

每条查询单独调用 Serper.dev API，结果合并后去重。

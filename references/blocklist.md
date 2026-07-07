# 域名黑名单参考

本文件记录所有需要过滤的域名。脚本中 `BLOCKLIST` 集合与此文档保持同步。

## 过滤原则

- 过滤掉大型 B2B 平台、电商平台、社交媒体、搜索引擎等非目标网站
- 保留有可能是真实进口商/买家/分销商的公司网站
- 政府域名（.gov）和军事域名（.mil）整体排除
- 如需调整过滤范围，修改脚本中的 `BLOCKLIST` 集合并同步更新本文件

## 一、B2B 贸易平台

alibaba.com, made-in-china.com, globalsources.com, tradekey.com,
dhgate.com, ec21.com, ecplaza.net, exportersindia.com, indiamart.com,
tradeindia.com, go4worldbusiness.com, fibre2fashion.com, busytrade.com,
chinabrands.com, eworldtrade.com, hktdc.com, 1688.com

## 二、电商平台

amazon.com, amazon.co.uk, amazon.de, amazon.fr, amazon.it, amazon.es,
amazon.co.jp, amazon.in, amazon.ca, amazon.com.au, amazon.com.mx,
ebay.com, ebay.co.uk, ebay.de, etsy.com, walmart.com, target.com,
bestbuy.com, homedepot.com, lowes.com, wayfair.com, shopify.com,
aliexpress.com, wish.com, shopee.com, lazada.com, flipkart.com,
temu.com, shein.com, overstock.com, costco.com, newegg.com

## 三、社交媒体

facebook.com, instagram.com, twitter.com, x.com, linkedin.com,
tiktok.com, reddit.com, pinterest.com, youtube.com, tumblr.com,
snapchat.com, whatsapp.com, telegram.org, discord.com, medium.com,
quora.com, vk.com, weibo.com, weixin.qq.com, threads.net

## 四、搜索引擎/聚合器

google.com, bing.com, yahoo.com, duckduckgo.com, baidu.com,
yandex.com, yandex.ru, ask.com, aol.com

## 五、新闻/媒体/参考

wikipedia.org, wikimedia.org, britannica.com, nytimes.com, bbc.com,
cnn.com, reuters.com, bloomberg.com, forbes.com, businessinsider.com,
wsj.com, ft.com, economist.com, theguardian.com, usatoday.com,
huffpost.com, buzzfeed.com, techcrunch.com, theverge.com, wired.com

## 六、政府/监管

.gov, .gov.uk, .gov.au, .gov.in, .gov.cn, .gov.sg, .gov.hk,
europa.eu, ec.europa.eu, who.int, un.org, wto.org

## 七、招聘网站

indeed.com, monster.com, glassdoor.com, ziprecruiter.com,
careerbuilder.com, simplyhired.com, naukri.com, seek.com.au, stepstone.de

## 八、商业目录

yellowpages.com, yelp.com, manta.com, kompass.com, hotfrog.com,
cylex.us.com, brownbook.net, infobel.com, europages.com

## 九、论坛/社区/问答

stackexchange.com, stackoverflow.com, github.com, gitlab.com,
bitbucket.org, sourceforge.net, wordpress.org, wordpress.com,
blogspot.com, blogger.com, substack.com, ghost.org

## 十、域名/建站/技术

godaddy.com, namecheap.com, bluehost.com, hostgator.com,
wix.com, weebly.com, squarespace.com, webflow.com

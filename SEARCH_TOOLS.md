# 小宇搜索工具配置 ⛰️

**版本**: v1.0  
**更新日期**: 2026-02-17  
**用途**: 学习资料搜索、技术调研

---

## 🔍 搜索工具优先级

### 第一优先级：Multi-Search-Engine（多搜索引擎）
**使用场景**: 绝大多数搜索需求  
**优势**: 无需API Key、无需Chrome扩展、17个引擎可用

| 引擎类型 | 推荐引擎 | 适用场景 |
|---------|---------|---------|
| **国内技术资料** | 百度、必应中国 | 中文技术文档、博客 |
| **国际技术资料** | Google、Brave | 英文文档、GitHub、StackOverflow |
| **隐私/无跟踪** | DuckDuckGo、Startpage | 敏感搜索、隐私保护 |
| **知识计算** | WolframAlpha | 数学、换算、数据查询 |
| **微信生态** | 搜狗微信 | 公众号文章、小程序资料 |

### 第二优先级：Brave Search API
**使用场景**: 需要快速摘要、时效性筛选  
**优势**: 返回结构化摘要、支持时间过滤

### 第三优先级：Browser自动化
**使用场景**: 复杂页面、需要登录的网站  
**限制**: 需要Chrome扩展（备用方案）

---

## 🚀 搜索执行流程

```
用户提出技术问题
      ↓
选择合适搜索引擎
      ↓
构建搜索URL（带高级语法）
      ↓
web_fetch获取结果页面
      ↓
提取关键信息
      ↓
如需深入 → 抓取详情页
      ↓
整理输出技术报告
```

---

## 🛠️ 常用搜索模板

### 技术文档搜索
```
引擎: Google/Brave
查询: "{技术名}" tutorial documentation best practices
示例: "Kubernetes" tutorial documentation best practices
```

### 错误排查搜索
```
引擎: Google/百度
查询: {错误信息} solution fix
示例: "Connection refused" docker solution fix
```

### 最新资讯搜索
```
引擎: Google
查询: {关键词}&tbs=qdr:w (过去一周)
示例: AI news&tbs=qdr:w
```

### GitHub项目搜索
```
引擎: Google
查询: site:github.com {关键词} stars:>1000
示例: site:github.com react state management stars:>1000
```

### PDF文档搜索
```
引擎: Google
查询: {主题} filetype:pdf
示例: microservices architecture filetype:pdf
```

### 站内搜索
```
引擎: 任意
查询: site:{域名} {关键词}
示例: site:stackoverflow.com python async
```

---

## 📋 搜索引擎URL模板

```javascript
// 国内引擎
const BAIDU = `https://www.baidu.com/s?wd=${encodeURIComponent(keyword)}`;
const BING_CN = `https://cn.bing.com/search?q=${encodeURIComponent(keyword)}&ensearch=0`;
const SO_360 = `https://www.so.com/s?q=${encodeURIComponent(keyword)}`;
const SOGOU = `https://sogou.com/web?query=${encodeURIComponent(keyword)}`;

// 国际引擎
const GOOGLE = `https://www.google.com/search?q=${encodeURIComponent(keyword)}`;
const DUCKDUCKGO = `https://duckduckgo.com/html/?q=${encodeURIComponent(keyword)}`;
const BRAVE = `https://search.brave.com/search?q=${encodeURIComponent(keyword)}`;
const STARTPAGE = `https://www.startpage.com/sp/search?query=${encodeURIComponent(keyword)}`;

// 知识计算
const WOLFRAM = `https://www.wolframalpha.com/input?i=${encodeURIComponent(keyword)}`;
```

---

## 🎯 学习场景匹配

| 学习场景 | 推荐引擎 | 搜索策略 |
|---------|---------|---------|
| **新技术入门** | Google + 百度 | 找教程+中文解读 |
| **深度原理** | Google | 官方文档+论文 |
| **实战案例** | 百度 + 微信 | CSDN+公众号 |
| **错误解决** | Google + StackOverflow | 精确错误信息 |
| **最新趋势** | Google (tbs=qdr:w) | 时间筛选 |
| **工具对比** | Google + Brave | 多源交叉验证 |
| **数学/数据** | WolframAlpha | 精确计算 |

---

## ⚡ 高级搜索语法

| 语法 | 作用 | 示例 |
|------|------|------|
| `""` | 精确匹配 | `"machine learning"` |
| `site:` | 站内搜索 | `site:github.com react` |
| `filetype:` | 文件类型 | `filetype:pdf kubernetes` |
| `-` | 排除关键词 | `python -snake` |
| `OR` | 或运算 | `docker OR kubernetes` |
| `*` | 通配符 | `python * tutorial` |
| `..` | 数字范围 | `cpu 2020..2024` |

### 时间筛选参数
| 参数 | 含义 |
|------|------|
| `tbs=qdr:h` | 过去1小时 |
| `tbs=qdr:d` | 过去1天 |
| `tbs=qdr:w` | 过去1周 |
| `tbs=qdr:m` | 过去1月 |
| `tbs=qdr:y` | 过去1年 |

---

## 🔧 使用示例

### 示例1：搜索Kubernetes最新特性
```javascript
// 方式1：Google + 时间筛选
web_fetch({
  url: "https://www.google.com/search?q=Kubernetes+new+features+2024&tbs=qdr:m"
})

// 方式2：Brave搜索
web_fetch({
  url: "https://search.brave.com/search?q=Kubernetes+latest+features"
})
```

### 示例2：搜索Python最佳实践PDF
```javascript
web_fetch({
  url: "https://www.google.com/search?q=python+best+practices+filetype:pdf"
})
```

### 示例3：搜索微信公众号文章
```javascript
web_fetch({
  url: "https://wx.sogou.com/weixin?type=2&query=微服务架构"
})
```

### 示例4：货币换算
```javascript
web_fetch({
  url: "https://www.wolframalpha.com/input?i=100+USD+to+CNY"
})
```

---

## 📊 工具对比

| 工具 | 依赖 | 速度 | 适用场景 | 优先级 |
|------|------|------|---------|--------|
| **Multi-Search** | 无 | 快 | 通用搜索 | ⭐⭐⭐ 第一 |
| **Brave API** | API Key | 很快 | 摘要+时效 | ⭐⭐ 第二 |
| **Browser** | Chrome扩展 | 慢 | 复杂页面 | ⭐ 第三 |

---

## ✅ 检查清单

搜索前：
- [ ] 判断搜索类型（技术/错误/趋势/计算）
- [ ] 选择合适搜索引擎
- [ ] 构建带高级语法的查询URL

搜索中：
- [ ] 使用web_fetch获取结果
- [ ] 提取关键信息
- [ ] 如需深入，抓取详情页

搜索后：
- [ ] 整理结构化输出
- [ ] 标注信息来源
- [ ] 保存重要发现到MEMORY.md

---

**配置人**: 小宇 ⛰️  
**生效日期**: 2026-02-17  
**关联技能**: multi-search-engine

---

*多引擎在手，搜索无忧！* 🔍💪
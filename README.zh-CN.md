# 个人投资与财富管理插件
**卡拉米跟着喝汤版**
这是从 Anthropic 官方 financial plugins 拆出来重做的个人版本。  
原版偏企业/机构协作，模块多且繁杂，很多能力对个人投资者基本用不到。 
所以只保留两个最核心插件：
- `financial-analysis` 负责研究估值
- `wealth-management` 负责组合与规划
以及增加了数个穷鬼友好数据源替代原版死贵死贵的订阅

<p align="right"><a href="./README.md">English</a> | <a href="./README.zh-CN.md">简体中文</a></p>

一个面向个人投资者与理财顾问的 Claude 插件套件。

当前仓库仅包含两个插件：
- `financial-analysis`
- `wealth-management`

该套件默认采用“免费数据源优先”的研究策略，并强制输出来源溯源字段。

## 插件市场

| 插件 | 类型 | 作用 |
|------|------|------|
| **[financial-analysis](./financial-analysis)** | 核心 | 面向美股个股的可比分析（Comps）、DCF 与三表建模，支持来源元数据与回退策略。 |
| **[wealth-management](./wealth-management)** | 增强 | 客户回顾/报告、财务规划、组合再平衡与税损收割工作流。 |

## 数据源策略

回退层级写在各核心分析技能里（沿用 upstream 风格），不再使用统一中心策略文件：
- `financial-analysis/skills/comps-analysis/SKILL.md`
- `financial-analysis/skills/dcf-model/SKILL.md`
- `financial-analysis/skills/3-statements/SKILL.md`（按模板需要触发 SEC 提取）

当前基本面默认优先级：
1. SEC MCP / SEC EDGAR
2. 结构化二级来源（Twelve Data / Alpha Vantage / 可选 premium MCP）
3. Web/文档回退（必须显式标注来源）

### SEC MCP（本地）启动
```bash
cd financial-analysis/mcp/sec-edgar
npm install
npm run build
```

`financial-analysis/.mcp.json` 已配置为运行：
`node mcp/sec-edgar/dist/index.js`

`financial-analysis/.mcp.json` 中保留了 Premium MCP 连接器，作为可选的二级数据源。

所有外部结论都必须包含：
- `source`
- `as_of`
- `freshness`
- `confidence`
- `fallback_used`

### 免费数据源常见坑（务必看）
- SEC 请求需要真实 `SEC_USER_AGENT`，不要高频突发抓取。
- FRED 的鉴权/版本口径要统一，跨源对比前先做时间戳归一化。
- NY Fed / Treasury 的 endpoint 对路径非常敏感，别在运行时盲猜。
- Twelve Data / Alpha Vantage 返回 200 也可能是业务错误或限流。
- Google News RSS 常见单行 XML，解析别依赖行号。
- Massive 仅建议回退使用（免费档限频明显）。
- 重试后仍过旧/缺失的数据要标记 `data unavailable`，并下调置信度。

## 快速开始

### Cowork
在 [claude.com/plugins](https://claude.com/plugins/) 安装插件。

### Claude Code
```bash
# 添加插件市场
claude plugin marketplace add flora535/financial-services-plugins

# 先安装核心插件
claude plugin install financial-analysis@financial-services-plugins

# 再安装财富管理插件
claude plugin install wealth-management@financial-services-plugins
```

## 仓库结构

```text
financial-services-plugins/
├── .claude-plugin/marketplace.json
├── financial-analysis/
│   ├── .claude-plugin/plugin.json
│   ├── .mcp.json
│   ├── mcp/sec-edgar/
│   ├── commands/
│   └── skills/
└── wealth-management/
    ├── .claude-plugin/plugin.json
    ├── commands/
    └── skills/
```

## 破坏性变更

- 已移除插件：
  - `investment-banking`
  - `equity-research`
  - `private-equity`
  - `partner-built/lseg`
  - `partner-built/spglobal`
- 市场清单目前仅发布 `financial-analysis` 与 `wealth-management`。
- 默认数据路由已改为“免费优先 + 强制溯源字段”。

## 许可证

[Apache License 2.0](./LICENSE)

## 免责声明

本插件用于辅助金融工作流，不构成投资建议。请在实际决策前由具备资质的专业人士复核。

# 个人投资与财富管理插件
**卡拉米跟着喝汤版**

<p align="center"><a href="./README.md">English</a> | <a href="./README.zh-CN.md">简体中文</a></p>

这是从 Anthropic 官方 financial plugins 拆出来重做的个人版本。  
原版偏企业/机构协作，模块多且繁杂，很多能力对个人投资者基本用不到。 
所以只保留两个最核心插件：
- `financial-analysis` 负责研究估值
- `wealth-management` 负责组合与规划
以及增加了数个穷鬼友好数据源替代原版死贵死贵的订阅

一个面向个人投资者与理财顾问的 Claude 插件套件。

当前仓库仅包含两个插件：
- `financial-analysis`
- `wealth-management`

该套件默认采用”免费数据源优先”的研究策略。

## 插件市场

| 插件 | 类型 | 作用 |
|------|------|------|
| **[financial-analysis](./financial-analysis)** | 核心 | 面向美股个股的可比分析（Comps）、DCF 与三表建模。 |
| **[wealth-management](./wealth-management)** | 增强 | 客户回顾/报告、财务规划、组合再平衡与税损收割工作流。 |

## 新增免费数据源

详见 [docs/FREE_DATA_SOURCES.md](./docs/FREE_DATA_SOURCES.md)。

| 数据源 | 免费额度 | 已集成 | MCP | 备注 |
|--------|----------|--------|-----|------|
| SEC EDGAR | 无限制（限流） | ✅ | [edgartools](https://github.com/dgunning/edgartools) 内置 MCP | 10-K/10-Q/8-K 公告、XBRL 财报、内部人交易、13-F 持仓 |
| FRED | 无限制（限流） | ✅ | [fred-mcp-server](https://github.com/stefanoamorelli/fred-mcp-server) | 80万+序列：利率、通胀、GDP、就业、信用利差 |
| Alpha Vantage | 25次/天 | ✅ | [官方远程 MCP](https://mcp.alphavantage.co) | 行情、技术指标、基本面 |
| NY Fed + U.S. Treasury | 无限制 | ❌ | — | SOFR、ON RRP、TGA |
| CoinGecko | 50次/分钟 | ❌ | — | BTC/ETH 现货价格 |
| Twelve Data | 800次/天，8只标的 | ✅ | [官方 MCP](https://github.com/twelvedata/mcp) | 股票/加密行情 |
| Google News | 无限制 | ❌ | [server-google-news](https://github.com/chanmeng666/server-google-news) | 新闻搜索；网页搜索已覆盖大部分功能 |
| Massive API | 5次/分钟，2年历史 | ✅ | [官方 MCP](https://github.com/massive-com/mcp_massive) | 股票、基本面、分析师评级、期权、加密货币 |

## 快速开始

安装后，日常投资最常用的命令：

```
/financial-analysis:evaluate AAPL at 150
```

对持仓做多因子快速评估（估值、基本面、技术面、催化剂、盈亏），输出 **加仓 / 持有 / 减仓 / 卖出** 信号及置信度。自动从 SEC EDGAR、Massive API、FRED、Twelve Data 拉取实时数据，并在需要时建议深入分析：

- 信号为加仓？→ 建议跑 `/financial-analysis:dcf` 算内在价值
- 持仓浮亏？→ 提示 `/wealth-management:tlh` 做税损收割
- 建议减仓？→ 指向 `/wealth-management:rebalance` 评估组合影响

### 全部命令

| 命令 | 功能 |
|------|------|
| `/financial-analysis:evaluate` | 持仓快速买卖信号 |
| `/financial-analysis:dcf` | DCF 估值（含可比公司终值倍数） |
| `/financial-analysis:comps` | 可比公司交易倍数分析 |
| `/financial-analysis:3-statements` | 填充利润表/资产负债表/现金流量表模板 |
| `/financial-analysis:lbo` | PE 收购 LBO 模型 |
| `/financial-analysis:competitive-analysis` | 竞争格局分析 |
| `/financial-analysis:check-deck` | 演示文稿质检 |
| `/financial-analysis:debug-model` | 财务模型审计纠错 |
| `/wealth-management:client-review` | 客户回顾会议准备 |
| `/wealth-management:rebalance` | 偏离分析与再平衡交易 |
| `/wealth-management:tlh` | 税损收割机会识别 |
| `/wealth-management:client-report` | 业绩报告 |
| `/wealth-management:proposal` | 投资建议书 |
| `/wealth-management:financial-plan` | 财务规划 |

### 安装

**Cowork：** 在 [claude.com/plugins](https://claude.com/plugins/) 安装。

**Claude Code：**
```bash
claude plugin marketplace add flora535/financial-services-plugins
claude plugin install financial-analysis@financial-services-plugins
claude plugin install wealth-management@financial-services-plugins
```

## 说明
- `financial-analysis` 所有免费数据源优先使用上游官方 MCP。

## 贡献
欢迎贡献，尤其是新增 **免费** 数据源 MCP 集成，以提升个人投资工作流覆盖。

重点方向：
- 面向可信免费来源的新 MCP 连接器
- 已有数据源稳定性改进（清晰错误处理、限流友好、结果可复现）

## 许可证

[Apache License 2.0](./LICENSE)

## 免责声明

本插件用于辅助金融工作流，不构成投资建议。请在实际决策前由具备资质的专业人士复核。

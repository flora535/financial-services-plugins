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

## 说明
- `financial-analysis` 内置本地 `free-sec-edgar` MCP 支持。
- 数据源回退规则写在各技能的 `SKILL.md` 中。

## 许可证

[Apache License 2.0](./LICENSE)

## 免责声明

本插件用于辅助金融工作流，不构成投资建议。请在实际决策前由具备资质的专业人士复核。

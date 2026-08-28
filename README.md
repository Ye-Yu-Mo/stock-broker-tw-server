# stock-broker-tw-server

> 台湾元大证券 Spark API 的本地 Broker Server
> 单账户、本土股票，HTTP + WebSocket，生产化风控与恢复能力。

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![uv](https://img.shields.io/badge/uv-0.12%2B-4F46E5?logo=python&logoColor=white)](https://docs.astral.sh/uv/)
[![CI](https://github.com/Ye-Yu-Mo/stock-broker-tw-server/actions/workflows/ci.yml/badge.svg)](https://github.com/Ye-Yu-Mo/stock-broker-tw-server/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 简介

`stock-broker-tw-server` 是一个基于**元大 SPARK API** 的本地 Broker Server，使用 **Python + FastAPI + SQLite** 构建。

它把元大 SPARK API 封装成统一的 HTTP JSON API 和 WebSocket 推送，适合：

- 个人量化策略调用
- 本地自动化交易研究
- 行情订阅与订单状态管理

> ⚠️ 本项目仅用于个人自动化交易研究与合法合规场景。正式环境交易具有法律效力，请自行确认券商合规要求。

## 功能特性

- 会话管理：登录 / 登出 / 状态
- 本土股票交易：新单 / 撤单 / 改价 / 改量
- 订单状态机：`PENDING → SUBMITTED → ACCEPTED → FILLED/CANCELLED/REJECTED`
- 幂等控制：`client_order_id` 防止重复下单
- 行情订阅：watchlist / 五档 / 分时 / 个股资讯
- 行情查询：报价快照 / 分时 / 分价量 / K 线 / 个股资讯
- 只读查询：库存 / 银行余额 / 交割款 / 损益 / 回报
- WebSocket：实时回报与行情推送
- 风控：panic、黑名单、数量/金额/价格偏离限制
- 限流：按 FunctionID + 账户统一限流
- 熔断：连续失败自动保护写接口
- 恢复：启动对账 + 人工确认未知订单
- 通知：Webhook 告警（飞书/钉钉/企微/通用），报警事件与消息模板可配置
- 审计：结构化日志 + JSON Lines

## 快速开始

### 环境要求

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- macOS / Linux
- 元大 Spark API SDK（需自行向营业部申请）

### 1. 准备 Spark API

1. 向元大营业部申请 Spark API 权限。
2. 下载对应平台的 Spark API 压缩包。
3. 解压到项目目录：

```text
vendor/yuanta/sparkapi/
```

> 第三方 SDK 不随仓库分发，请自行获取并遵守元大授权协议。

### 2. 安装依赖

```bash
uv sync
```

### 3. 配置

复制默认配置：

```bash
cp config/default.toml config/syz.toml
```

然后编辑 `config/syz.toml`，填入账号、密码、凭据路径。

### 4. 启动服务

```bash
uv run stock-broker-tw
# 或
uv run python -m stock_broker_tw
```

默认监听 `http://127.0.0.1:8000`。

### 5. 验证

```bash
curl http://127.0.0.1:8000/health
```

## 文档

| 文档 | 说明 |
|---|---|
| [客户端 API 文档](docs/client-api.md) | HTTP / WebSocket 接口说明 |
| [部署文档](docs/deploy.md) | 安装、配置、启动、升级 |
| [UAT 联调清单](docs/uat-checklist.md) | 获取 UAT 权限后的验证清单 |
| [元大 API 整理](docs/api.md) | 元大 SPARK API 功能整理 |
| [设计文档](DESIGN.md) | 系统设计 |
| [开发计划](PLAN.md) | 里程碑计划 |
| [TODO-M1](TODO-M1.md) ~ [TODO-M6](TODO-M6.md) | 各里程碑任务清单 |

## 测试

```bash
uv run pytest
```

代码检查：

```bash
uv run ruff check .
```

## 项目结构

```text
stock-broker-tw-server/
├── src/stock_broker_tw/
│   ├── api/          # HTTP / WebSocket
│   ├── broker/       # 交易与行情业务
│   ├── engine/       # 订单状态机、队列、回报处理
│   ├── risk/         # 风控、限流、熔断
│   ├── service/      # 会话、查询、行情订阅
│   ├── state/        # SQLite 存储与恢复
│   └── yuanta/       # 元大 Spark API Adapter
├── docs/             # 文档
├── config/           # 本地配置（不入库）
└── tests/            # 测试
```

## 开源协议

[MIT](LICENSE)

## 免责声明

本项目与元大证券无官方合作关系，不构成投资建议。使用本项目进行真实交易前，请确保：

- 已获得券商 API 使用权限
- 已理解自动化交易风险
- 已遵守当地法律法规与券商规定

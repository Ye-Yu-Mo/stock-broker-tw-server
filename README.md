# stock-broker-tw-server

台湾元大证券 API 的本地 broker server，使用 Python + FastAPI + SQLite。

## 快速开始

```bash
uv sync
uv run stock-broker-tw
```

详细部署步骤见 [docs/deploy.md](docs/deploy.md)，UAT 联调清单见 [docs/uat-checklist.md](docs/uat-checklist.md)。

## 主要能力

- 会话管理：登录/登出/状态
- 只读查询：库存、余额、交割、损益、回报、行情
- 交易：新单/撤单/改价/改量，本地幂等与状态机
- 行情订阅：watchlist、tick、五档、个股资讯等
- 风控：panic 开关、黑名单、数量/金额/偏离限制
- 限流：按 FunctionID + 账户统一限流
- 熔断：连续失败自动保护写接口
- 恢复：启动对账 M3/M4 订单，人工确认未知订单
- 通知：webhook 告警（飞书/钉钉/企微/通用）
- WebSocket：实时回报与行情推送

## 测试

```bash
uv run pytest
```

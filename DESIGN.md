# stock_broker_tw_server 设计文档

> 基于元大 SPARK API（YuantaSparkAPI）的 Broker Server。
> 已确认范围：**单账户、本土股票、Python + uv 管理环境**。
> 参考了 `stock_broker_a_server` 的服务化、状态机、风控、审计、恢复等设计思路。
> API 整理见 [docs/api.md](docs/api.md)，官方原始文档见 [docs/API](docs/API)。

## 1. 背景与目标

### 1.1 背景

元大 SPARK API 是一套跨平台的 .NET 8 元件，提供行情、证券/期货/条件单交易、帐务查询、即时期货/证券回报等能力。官方范例使用 Python + `pythonnet` 呼叫 `YuantaSparkAPI.dll`。

本项目最初考虑用 Rust 实现，但元大 API 是 .NET 元件且为事件驱动异步模型，Rust 直接调用成本高、收益低。因此改为：

- 使用 **Python** 实现整个 broker server。
- 使用 **uv** 管理 Python 环境和依赖。
- 直接使用 `pythonnet` 加载 `YuantaSparkAPI.dll`，不需要额外 bridge 子进程。
- 首期只支持**单账户**与**本土股票**（上市/上柜/零股），暂不覆盖期货、海外、条件单等复杂品种。

### 1.2 目标

- 提供 HTTP JSON API 与 WebSocket 实时推送，供策略/客户端调用。
- 覆盖本土股票核心闭环：
  - 登录/登出
  - 行情订阅与查询
  - 证券下单、撤单、改量、改价
  - 库存/资金/银行余额/交割款/损益查询
  - 委托/成交/即时回报查询与推送
- 内置订单状态机、幂等、串行化、限流、风控、审计、持久化、崩溃恢复。
- 通过 uv 管理依赖，方便本地开发与部署。

### 1.3 非目标

- 不替代券商官方合规/风控系统；用户需自行确认自动化交易合规性。
- 不做低延迟高频交易；元大 API 本身有调用频率限制。
- 本期不实现期货、期权、海外股票/期货、复式单。
- 条件单/演算法单可后续扩展，本期不承诺。
- 不实现多账户并发管理。

## 2. 需求分析

### 2.1 用户/调用方

| 调用方 | 使用方式 | 关注点 |
|---|---|---|
| 策略系统 | HTTP 下单/撤单、WebSocket 收回报 | 低延迟、可靠、幂等 |
| 行情服务 | 订阅报价、K 线、五档 | 实时推送、订阅管理 |
| 账户管理 | 查询资金/持仓/委托/成交 | 数据一致、可审计 |
| 运维 | 健康检查、指标、熔断、日志 | 可观测、可恢复 |

### 2.2 核心功能需求

1. **连接与会话**
   - Open / Login / LogOut / Close / Dispose
   - 支持 Windows 式（帐号+密码）与 macOS/Linux 式（PfxPath + PfxPass + 帐号 + 密码）
   - 单账户单 session

2. **行情**
   - 订阅/取消订阅：报价表、完整报价表、五档、分时明细、盘前资讯、个股其他资讯
   - 查询：已订阅列表、报价表、标的资讯、分时明细、分价量、K 线
   - 通过 WebSocket 推送订阅事件

3. **本土股票交易**
   - 证券新单：现股/融资/融券/零股/盘后等（取决于权限）
   - 撤单：`SendStockOrder` + `TradeKind=04`
   - 改量：`TradeKind=03`
   - 改价：`TradeKind=07`
   - 幂等：`client_order_id` 可放入 `BasketNo`

4. **帐务**
   - 股票库存总表
   - 银行余额、交割款
   - 未实现/已实现损益、冲销明细

5. **回報**
   - 查询即时回报、汇总即时回报、委託成交综合回报
   - 登录后自动接收 `RR_RealReport` / `RR_RealReportMerge` 并推送到 WebSocket

6. **生产化**
   - 幂等、状态机、限流、风控、审计、持久化、恢复、通知、指标

### 2.3 技术约束

- 元大 API 是 .NET 元件，Python 通过 `pythonnet` 调用。
- API 调用全部异步，必须维护 `strIndex` / `Identify` / `BasketNo` 与 `OnResponse` 的关联。
- 必须遵守元大 API 使用限制（见 `docs/api.md` 第 8 节）。
- `pythonnet` 的 .NET 事件回调可能运行在非主线程，需要线程安全地桥接到 asyncio 事件循环。

## 3. 总体架构

```text
┌──────────────────────────────────────────────────────────────┐
│                    外部策略 / 客户端                           │
│              HTTP JSON + WebSocket / REST                     │
└───────────────────────────────┬──────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────┐
│               stock_broker_tw_server (Python)                 │
│                                                              │
│  ┌───────────┐  ┌──────────┐  ┌────────────┐  ┌───────────┐  │
│  │ FastAPI   │  │ Engine   │  │ Risk/限流   │  │ State/恢复 │  │
│  └─────┬─────┘  └────┬─────┘  └─────┬──────┘  └─────┬─────┘  │
│        │             │              │               │        │
│  ┌─────▼─────────────▼──────────────▼───────────────▼─────┐  │
│  │               BrokerService                              │  │
│  │        下单/撤单/查询/行情订阅/回报分发                    │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                             │ 直接调用（同进程）                 │
└─────────────────────────────┼─────────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│               YuantaAdapter (Python + pythonnet)               │
│       持有 YuantaSparkAPITrader 实例，翻译 .NET 对象 <-> dict    │
└─────────────────────────────┬─────────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│              YuantaSparkAPI.dll / 元大伺服器                    │
└────────────────────────────────────────────────────────────────┘
```

说明：当前采用同进程直接调用，部署最简单。如果未来需要隔离崩溃影响，可以再把 `YuantaAdapter` 拆成独立子进程；当前单账户/本土股票场景不需要。

## 4. 核心模块设计

### 4.1 `api` — FastAPI 路由与 WebSocket

主要端点：

- `GET /health`、`GET /metrics`
- `POST /api/v1/session/login`、`POST /api/v1/session/logout`、`GET /api/v1/session/status`
- `GET /api/v1/account/balance`、`/account/settlement`
- `GET /api/v1/positions`
- `GET /api/v1/orders`、`/trades`、`/reports/real`、`/reports/order-trade`
- `POST /api/v1/orders/stock`（new / replace / cancel）
- `POST /api/v1/quotes/subscribe`、`/unsubscribe`、`/quotes/subscribed`、`/quotes/snapshot`、`/quotes/ticks`、`/quotes/classify-price`、`/quotes/kline`、`/stocks/info`
- `GET /ws` 实时事件推送
- `POST /api/v1/yuanta/{FunctionName}` 通用透传（保留给高级功能）

统一响应格式：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

### 4.2 `yuanta` — 元大 Adapter

职责：

- 加载 `YuantaSparkAPI.dll`（`clr.AddReference`）。
- 创建 `YuantaSparkAPITrader`，注册 `OnResponse`。
- 封装 Open / Login / LogOut / Close / Dispose。
- 将 .NET 对象序列化为 Python dict/list。
- 维护请求关联：`Identify` / `BasketNo` / `request_id`。
- 把 `OnResponse` 事件放入线程安全队列，由 asyncio 任务消费并分发。

建议文件：

```text
src/stock_broker_tw/yuanta/
├── loader.py       # 加载 pythonnet / DLL
├── adapter.py      # YuantaAdapter 封装
├── models.py       # dataclass/pydantic 领域模型
├── serializer.py   # .NET 对象 -> dict
└── events.py       # OnResponse 队列与事件分发
```

### 4.3 `broker` — 领域模型与交易服务

```python
class Side(str, Enum):
    BUY = "B"
    SELL = "S"

class TimeInForce(str, Enum):
    ROD = "0"
    IOC = "3"
    FOK = "4"

class OrderStatus(str, Enum):
    PENDING = "Pending"
    SUBMITTED = "Submitted"
    ACCEPTED = "Accepted"
    PARTIALLY_FILLED = "PartiallyFilled"
    FILLED = "Filled"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"
    FAILED = "Failed"
    NEED_MANUAL_REVIEW = "NeedManualReview"

@dataclass
class StockOrderRequest:
    client_order_id: str
    account: str
    symbol: str
    side: Side
    price: float | None
    price_flag: str       # " "=限价, M=市价, H=涨停, L=跌停, "-"=平盘
    quantity: int
    time_in_force: TimeInForce
    ap_code: int          # 0=一般, 2=零股, 4=盘零, 7=盘后
    action: str           # new / replace / cancel
    order_no: str | None  # 撤单/改价/改量时必填
```

核心逻辑：

- 新单：`BasketNo = client_order_id`，便于幂等与追溯。
- 撤单：`TradeKind=04`，带 `OrderNo` / `TradeDate`。
- 改量/改价：`TradeKind=03/07`。
- 回报更新：根据 `RR_RealReport` / `RR_RealReportMerge` 更新订单状态。

### 4.4 `engine` — 状态机与调度

订单状态机：

```text
                 +--------+
                 | Pending| 收到 HTTP 请求
                 +--------+
                     |
                     v
                 +---------+
                 | Submitted| 已调用元大 API
                 +---------+
                     |
                     v
              +------------+
              |  Accepted  | SendStockOrder OnResponse 成功
              +------------+
                 |        \
                 v         v
        +----------+   +----------+
        | Filled   |   | Cancelled| 由回报/查询确认
        +----------+   +----------+
                 \
                  v
             +----------+
             | Rejected | 回报/查询显示失败或风控拒绝
             +----------+
```

引擎职责：

- 幂等：`client_order_id` 去重，重复请求返回已有状态。
- 串行化：同一账户交易请求排队，避免并发操作同一连接。
- 超时：请求发出后如果在 N 秒内未收到 `OnResponse`，标记超时并调用 `GetRealReport` / `GetOrderTradeReport` 对账。
- 恢复：启动时从未完成订单 + 委托成交回报重建状态。

### 4.5 `risk` — 风控与限流

风控（下单前）：

- 价格范围：相对昨收/最新价偏离比例限制
- 数量限制：单笔最大数量、单日累计数量
- 金额限制：单笔/单日最大金额
- 标的黑名单/白名单
- 卖出不超过可卖数量（可先查询库存）
- 手动 panic / 自动熔断

限流（遵守元大 API 限制）：

- 同一 FunctionID 每秒行情/帐务 3 次、K 线 1 次、交易 10 次、订阅 10 次
- 单次交易最多 30 笔、单次订阅最多 200 档
- 每账户每分钟行情 1200、帐务 600、交易 3000
- 登录失败至少间隔 4 秒
- 提供指标和告警，防止触发元大暂停服务

### 4.6 `state` — 持久化与恢复

使用 SQLite（Python 标准库 `sqlite3` 即可，必要时换 SQLAlchemy）保存：

- 账户配置与 session 状态
- 本地订单表（client_order_id ↔ 委托书号、状态、原始请求）
- 订阅清单
- 审计事件
- 风控计数（每日累计下单/金额）

启动恢复流程：

1. 启动元大 Adapter 并 Open/Login。
2. 加载本地未完成订单。
3. 调用 `GetRealReportMerge` / `GetOrderTradeReport` 拉取当日委托/成交。
4. 对账并更新本地状态。
5. 无法自动判定的标记为 `NEED_MANUAL_REVIEW`。

### 4.7 `audit` / `notify` / `metrics`

- `audit`：每次请求记录时间、client_order_id、操作类型、参数（脱敏）、风控结果、元大响应、最终状态。
- `notify`：订单成功/失败、风控触发、熔断、Adapter 异常、每日对账摘要；支持 webhook（飞书/钉钉/企业微信/Telegram）。
- `metrics`：Prometheus 格式，包括请求量、成功率、延迟、限流拒绝数、风控拒绝数、队列深度、Adapter 状态。

## 5. 对外 API 设计

### 5.1 认证

默认只监听 `127.0.0.1`，使用 `Authorization: Bearer <token>` 或 `X-Auth-Token`。

### 5.2 会话

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/session/login` | 登录元大 API |
| POST | `/api/v1/session/logout` | 登出 |
| GET | `/api/v1/session/status` | 查看连接/登录状态 |

### 5.3 行情

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/quotes/subscribe` | 订阅行情，type 指定 watchlist/watchlist_all/five_tick/stock_tick/market_info/stock_info |
| POST | `/api/v1/quotes/unsubscribe` | 取消订阅 |
| GET | `/api/v1/quotes/subscribed` | 已订阅列表（GetQuoteList） |
| GET | `/api/v1/quotes/snapshot` | 报价表（GetWatchListAll） |
| GET | `/api/v1/quotes/ticks` | 分时明细（GetStkTickDetail） |
| GET | `/api/v1/quotes/classify-price` | 分价量（GetStkClassifyPrice） |
| GET | `/api/v1/quotes/kline` | K 线（GetKLine） |
| GET | `/api/v1/stocks/info` | 标的资讯（GetStockInformation） |

### 5.4 本土股票交易

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/orders/stock` | 新单/撤单/改量/改价，由 `action` 区分 |
| GET | `/api/v1/orders` | 委托列表（GetOrderTradeReport / 本地状态） |
| GET | `/api/v1/trades` | 成交列表 |

`POST /api/v1/orders/stock` 请求体：

```json
{
  "client_order_id": "20260827-0001",
  "account": "S98875005091",
  "action": "new",
  "symbol": "2885",
  "side": "buy",
  "price": 35.0,
  "price_flag": " ",
  "quantity": 1000,
  "time_in_force": "ROD",
  "ap_code": 0,
  "dry_run": false
}
```

### 5.5 帐务

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/account/balance` | 银行余额（GetBankBalance） |
| GET | `/api/v1/account/settlement` | 交割款（GetStkTransactionOutlay） |
| GET | `/api/v1/positions` | 股票库存总表（GetStoreSummary） |
| GET | `/api/v1/pnl/unrealized` | 未实现损益 |
| GET | `/api/v1/pnl/realized` | 已实现损益 |
| GET | `/api/v1/pnl/reversal` | 冲销明细 |

### 5.6 回報

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/reports/real` | 即时回报查询 |
| GET | `/api/v1/reports/real-merge` | 即时回报汇总查询 |
| GET | `/api/v1/reports/order-trade` | 委託成交综合回报 |
| WS | `/ws` | 实时推送 `RR_RealReport` / `RR_RealReportMerge` / 行情订阅 / 订单状态变更 |

### 5.7 通用透传

为了保留扩展能力，提供：

```http
POST /api/v1/yuanta/{FunctionName}
```

body 直接传入该 Function 的 params，服务做通用限流/审计后转发元大 Adapter。当前范围外的期货、条件单等可先通过该接口手工调用，后续再固化为专用端点。

### 5.8 WebSocket 事件

```json
{
  "type": "real_report",
  "timestamp_ms": 1730000000000,
  "account": "S98875005091",
  "data": {}
}
```

事件类型至少包括：

- `real_report` / `real_report_merge`
- `quote.updated`
- `order.updated`
- `position.changed`
- `account.changed`
- `risk.panic`
- `health.changed`

### 5.9 元大 API 覆盖矩阵（首期）

| 元大 API | 本期状态 | 建议 REST / 处理方式 |
|---|---|---|
| Open / Close / Dispose | ✅ 实现 | session 生命周期，由服务启动/停止时自动处理 |
| SetLogType / SetPMMServerCheck | ✅ 实现 | 配置文件驱动，Adapter 启动时执行 |
| Login / LogOut | ✅ 实现 | `POST /api/v1/session/login`、`POST /api/v1/session/logout` |
| SubscribeWatchlist / UnSubscribeWatchlist | ✅ 实现 | `POST /api/v1/quotes/subscribe`、`/unsubscribe` |
| SubscribeWatchlistAll / UnSubscribeWatchlistAll | ✅ 实现 | 同上，type=`watchlist_all` |
| SubscribeFiveTickA / UnSubscribeFiveTickA | ✅ 实现 | 同上，type=`five_tick` |
| SubscribeStockTick / UnSubscribeStockTick | ✅ 实现 | 同上，type=`stock_tick` |
| SubscribeMarketInformation / UnSubscribeMarketInformation | ✅ 实现 | 同上，type=`market_info` |
| SubscribeStockInformation / UnSubscribeStockInformation | ✅ 实现 | 同上，type=`stock_info` |
| GetQuoteList | ✅ 实现 | `GET /api/v1/quotes/subscribed` |
| GetWatchListAll | ✅ 实现 | `GET /api/v1/quotes/snapshot` |
| GetStockInformation | ✅ 实现 | `GET /api/v1/stocks/info` |
| GetStkTickDetail | ✅ 实现 | `GET /api/v1/quotes/ticks` |
| GetStkClassifyPrice | ✅ 实现 | `GET /api/v1/quotes/classify-price` |
| GetKLine | ✅ 实现 | `GET /api/v1/quotes/kline` |
| SendStockOrder | ✅ 实现 | `POST /api/v1/orders/stock`（new/replace/cancel） |
| GetStoreSummary | ✅ 实现 | `GET /api/v1/positions` |
| GetUnrealizedGainLossDetail | ✅ 实现 | `GET /api/v1/pnl/unrealized` |
| GetHisRealizedGainLoss | ✅ 实现 | `GET /api/v1/pnl/realized` |
| GetStkHistoryReportReversal | ✅ 实现 | `GET /api/v1/pnl/reversal` |
| GetBankBalance | ✅ 实现 | `GET /api/v1/account/balance` |
| GetStkTransactionOutlay | ✅ 实现 | `GET /api/v1/account/settlement` |
| GetRealReport | ✅ 实现 | `GET /api/v1/reports/real` |
| GetRealReportMerge | ✅ 实现 | `GET /api/v1/reports/real-merge` |
| GetOrderTradeReport | ✅ 实现 | `GET /api/v1/reports/order-trade` |
| RR_RealReport / RR_RealReportMerge | ✅ 实现 | 登录后自动接收，WebSocket 推送 |
| SendStockEarmark | 🟡 可选 | `POST /api/v1/orders/stock-earmark` |
| SendPrefundedMargin | 🟡 可选 | `POST /api/v1/orders/prefunded-margin` |
| SendFutureOrder / SendFutureCombined / SendFutureApart | ⛔ 本期不做 | 保留通用透传 |
| GetFutStoreSummary / GetOVFutStoreSummary / GetFutSprStore / GetFutInterestStore / GetFutDepositOptimum | ⛔ 本期不做 | 保留通用透传 |
| SendAlgoCOOdrStrategy / DeleteAlgoCOOdrStrategy / GetConditionStrategy / GetHisConditionStrategy | ⛔ 本期不做 | 保留通用透传 |

## 6. Python 技术栈与工程结构

### 6.1 技术栈

| 组件 | 选择 | 说明 |
|---|---|---|
| 语言 | Python 3.11+ | 建议 3.11/3.12 |
| 依赖管理 | uv | `uv sync` / `uv add` |
| Web 框架 | FastAPI | HTTP + WebSocket 都方便 |
| ASGI 服务器 | uvicorn | 本地服务 |
| 数据校验 | pydantic | 请求/响应模型 |
| 元大 API 调用 | pythonnet | 加载 .NET 8 元件 |
| 持久化 | sqlite3 | 标准库，后续可换 SQLAlchemy |
| 配置 | pydantic-settings | 支持 TOML / env |
| 指标 | prometheus-client | `/metrics` |
| 测试 | pytest | 单元/集成测试 |

### 6.2 项目结构

```text
stock_broker_tw_server/
├── pyproject.toml          # uv 项目定义
├── uv.lock
├── README.md
├── DESIGN.md
├── docs/
│   ├── api.md
│   └── API/                # 元大官方文档快照
├── config/
│   └── default.toml        # 服务、账户、风控配置
├── vendor/
│   └── yuanta/sparkapi/    # 官方 DLL / 范例
├── src/
│   └── stock_broker_tw/
│       ├── __init__.py
│       ├── main.py         # uvicorn 入口
│       ├── config.py       # pydantic-settings
│       ├── api/
│       │   ├── __init__.py
│       │   ├── http.py
│       │   └── ws.py
│       ├── broker/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   └── service.py
│       ├── yuanta/
│       │   ├── __init__.py
│       │   ├── loader.py
│       │   ├── adapter.py
│       │   ├── serializer.py
│       │   └── events.py
│       ├── engine/
│       │   ├── __init__.py
│       │   ├── state.py
│       │   ├── queue.py
│       │   └── recovery.py
│       ├── risk/
│       │   ├── __init__.py
│       │   └── rules.py
│       ├── state/
│       │   ├── __init__.py
│       │   └── store.py
│       ├── audit.py
│       ├── notify.py
│       └── metrics.py
└── tests/
    ├── test_models.py
    ├── test_engine.py
    └── test_api.py
```

### 6.3 pyproject.toml 草案

```toml
[project]
name = "stock-broker-tw-server"
version = "0.1.0"
description = "Yuanta Spark API broker server (domestic stock, single account)"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "pydantic>=2.7",
    "pydantic-settings>=2.3",
    "pythonnet>=3.0",
    "prometheus-client>=0.20",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "httpx>=0.27",
    "ruff>=0.5",
]

[tool.uv]
package = false
```

## 7. 配置设计

```toml
[server]
host = "127.0.0.1"
port = 8787
auth_token = "change-me"

[yuanta]
environment = "UAT"              # PROD / UAT
spark_api_dir = "vendor/yuanta/sparkapi"
log_type = "COMMON"
pmm_server_check = false

[account]
account = "S98875005091"
password = "1234"
# pfx_path = "/path/to/cert.pfx"   # macOS/Linux 登入需要
# pfx_pass = "yuanta"

[risk]
panic_file = "/tmp/yuanta_panic"
max_order_amount = 500000
max_order_quantity = 100000
max_daily_orders = 100
price_deviation_pct = 3.0
symbol_blacklist = []

[notify]
type = "feishu"
webhook = "https://..."

[state]
db_path = "state/yuanta.db"
```

## 8. 生产化要点

### 8.1 串行化

同一账户的交易类请求必须排队，避免并发导致 `OnResponse` 错乱或触发限流。

### 8.2 幂等

- 每个 HTTP 下单请求必须带 `client_order_id`。
- 证券单写入 `BasketNo`，已存在的 `client_order_id` 直接返回旧状态，绝不重复下到券商。

### 8.3 验证闭环

- 不能只依赖 `SendStockOrder` 返回“已送出”。
- 必须等待 `OnResponse`、`RR_RealReport` / `RR_RealReportMerge`，必要时再调用 `GetOrderTradeReport` 确认最终状态。

### 8.4 限流与熔断

- 在 Python 侧做令牌桶/滑动窗口限流，按 FunctionID 维度。
- 连续失败或 Adapter 异常自动熔断。
- 熔断后只读/行情接口仍可用，写接口拒绝并返回明确错误。

### 8.5 安全

- 默认只监听本机。
- token 鉴权。
- 密码/凭据不写日志。
- 审计日志脱敏。

### 8.6 可观测性

- 结构化 JSON 日志。
- Prometheus metrics：请求量、成功率、延迟、限流/风控拒绝数、队列深度、Adapter 存活。
- 健康检查包含：Adapter 进程状态、登录状态、最近心跳、最近回报、审计可写性、panic 状态。

## 9. 实施里程碑

### M0：环境与 Adapter 可行性

- [ ] 用 uv 初始化项目：`uv init`、`uv add fastapi uvicorn pythonnet ...`
- [ ] 编写 `YuantaAdapter`：Open / Login / LogOut / Close
- [ ] 跑通测试环境：`S98875005091 / 1234`
- [ ] 确认 `OnResponse` 能收到 Login 结果

### M1：基础服务

- [ ] FastAPI + uvicorn
- [ ] `/health`、`/metrics`
- [ ] session login/logout/status
- [ ] 配置加载、日志、审计基础

### M2：只读能力

- [ ] 股票库存 `GetStoreSummary`
- [ ] 银行余额/交割款
- [ ] 即时回报/委託成交查询
- [ ] REST：positions/orders/trades/reports

### M3：交易闭环

- [ ] 证券新单 `SendStockOrder`
- [ ] 撤单 `TradeKind=04`
- [ ] 改量/改价
- [ ] 订单状态机 + 幂等 + 串行队列
- [ ] 风控基础规则
- [ ] WebSocket 回报推送

### M4：行情订阅

- [ ] 订阅/取消订阅本土股票行情
- [ ] 行情查询：报价表、五档、K 线、分时
- [ ] WebSocket 行情推送
- [ ] 订阅数限制与去重

### M5：生产加固

- [ ] 限流（按 FunctionID）
- [ ] 崩溃恢复对账
- [ ] 熔断与手动 panic
- [ ] 通知
- [ ] 端到端测试与部署文档

## 10. 风险与注意事项

- 元大 API 有严格使用限制，超限会被暂停服务；限流模块是必须项。
- `OnResponse` 是异步事件，必须做请求关联和超时对账，否则会出现“已下单但服务不知道结果”。
- `pythonnet` 与 .NET 8 的版本兼容性需要提前验证。
- macOS/Linux 登入需要 Pfx 凭据路径与密码，配置文件不能提交到 git。
- 正式环境下单具有法律效力，必须先测试环境验证。
- 本期只覆盖本土股票，期货/海外/条件单等通过通用透传保留扩展能力。

## 11. 待确认问题

1. 部署目标是 macOS（本机）还是 Linux 服务器？影响凭据登录方式。
2. 是否需要启动时自动登录，还是由客户端调用 `/session/login` 手动登录？
3. 是否需要支持 `dry_run`（只填单不送券商）？
4. 是否需要行情订阅多客户端共享同一份订阅？
5. 通知渠道使用哪种？
6. 是否要把 `Cargo.toml`/`src/main.rs` 的 Rust 骨架移除，改为纯 Python 项目？

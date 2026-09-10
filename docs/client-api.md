# Client API 文档

本文档面向接入 stock-broker-tw-server 的客户端开发者，覆盖 HTTP API 与 WebSocket 推送。

- 服务默认地址：`http://127.0.0.1:8000`
- 默认认证：`Authorization: Bearer <api_token>`
- 如果服务端未配置 `api_token`，则不需要认证头。

## 1. 通用说明

### 1.1 请求头

| Header | 必填 | 说明 |
|---|---|---|
| `Authorization` | 视配置 | `Bearer <api_token>` |
| `Content-Type` | POST 必填 | `application/json` |
| `X-Request-ID` | 可选 | 请求追踪 ID，会写入审计日志 |

### 1.2 响应格式

成功响应统一为：

```json
{
  "code": 0,
  "message": "ok",
  "data": { }
}
```

失败响应使用 FastAPI/HTTPException 格式：

```json
{
  "detail": {
    "code": "ERROR_CODE",
    "message": "错误说明",
    "detail": { }
  }
}
```

### 1.3 常见错误码

| HTTP | code | 含义 |
|---|---|---|
| 401 | `UNAUTHORIZED` | 缺少或错误的 token |
| 400 | `INVALID_REQUEST` / `INVALID_DATE` / `MAX_PER_REQUEST_EXCEEDED` 等 | 请求参数错误 |
| 404 | `ORDER_NOT_FOUND` / `MOCK_ACCOUNT_NOT_FOUND` | 订单或 Mock 账户不存在 |
| 409 | `IDEMPOTENCY_CONFLICT` / `MOCK_ACCOUNT_INACTIVE` / `MOCK_ORDER_FINAL` / `MOCK_OPERATION_UNSUPPORTED` | 幂等冲突、账户停用或 Mock 操作不支持 |
| 429 | `RATE_LIMITED` | 触发限流；Mock provider 的限流错误保留此状态码 |
| 502 | `QUERY_ERROR` / `MOCK_QUOTE_UNAVAILABLE` / `SUBSCRIBE_FAILED` / `ORDER_REJECTED` 等 | 元大接口、外部行情或订单调用失败 |
| 503 | `CIRCUIT_OPEN` / `MOCK_QUOTE_PROVIDER_REQUIRED` | 熔断开启或未配置 Mock 行情 provider |
| 504 | `QUERY_TIMEOUT` | 查询或显式注入的行情 provider 超时 |

## 2. 健康与监控

### 2.1 健康检查

```
GET /health
```

无需认证。示例响应：

```json
{
  "status": "ok",
  "adapter_ready": true,
  "login_status": true,
  "event_queue_size": 0,
  "audit_enabled": true,
  "audit_file": null,
  "version": "0.1.7",
  "environment": "UAT",
  "panic": false,
  "circuit_breaker_open": false,
  "circuit_breaker": {
    "name": "yuanta",
    "state": "closed",
    "is_open": false,
    "consecutive_failures": 0,
    "failure_threshold": 5,
    "cooldown_seconds": 30.0,
    "last_error": null,
    "last_failure_at": null,
    "rejections": 0
  },
  "last_failure": null,
  "last_recovery": {
    "status": "ok",
    "unfinished_before": 0,
    "unfinished_after": 0,
    "reconciled": true,
    "unresolved_orders": 0,
    "unresolved_stock_orders": 0
  }
}
```

### 2.2 Prometheus 指标

```
GET /metrics
```

无需认证。客户端一般不需要调用，运维可通过该端点观察：

- `http_requests_total`
- `rate_limited_total`
- `circuit_breaker_state`
- `circuit_breaker_opens_total`
- `circuit_breaker_rejections_total`

## 3. 会话管理

### 3.1 登录

```
POST /api/v1/session/login
```

请求体可选；缺省使用服务端配置的账号。

```json
{
  "account": "S98875005091",
  "password": "your-password",
  "pfx_path": "/path/to/cert.pfx",
  "pfx_pass": "your-pfx-password"
}
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "login": {
      "login_list": [
        {
          "account": "S98875005091",
          "name": "測試用戶",
          "investor_id": "A123456789"
        }
      ]
    },
    "account": "S98875005091",
    "name": "測試用戶",
    "investor_id": "A123456789"
  }
}
```

### 3.2 登出

```
POST /api/v1/session/logout
```

### 3.3 查询会话状态

```
GET /api/v1/session/status
```

## 4. 账户与查询

所有查询接口均可选传 `account`；缺省使用服务端默认账户。当前服务为单账户模式，显式传入的真实账户必须与服务端配置账户一致，否则返回 `ACCOUNT_NOT_ALLOWED`。

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/positions` | 库存/持仓 |
| GET | `/api/v1/account/balance` | 银行余额 |
| GET | `/api/v1/account/settlement` | 交割金额 |
| GET | `/api/v1/pnl/unrealized?market_type=TWSE&stk_code=2330` | 未实现损益 |
| GET | `/api/v1/pnl/realized?start_date=2026/01/01&end_date=2026/01/31` | 已实现损益 |
| GET | `/api/v1/pnl/reversal` | 反向损益，`re_gain_loss` 可传 JSON 字符串 |
| GET | `/api/v1/reports/real` | 实时回报 |
| GET | `/api/v1/reports/real-merge` | 合并回报 |
| GET | `/api/v1/reports/order-trade?notshow_cancel=false` | 委托/成交回报 |

示例：

```bash
curl -H "Authorization: Bearer test-token" \
  "http://127.0.0.1:8000/api/v1/positions?account=S98875005091"
```

## 5. 行情

### 5.1 订阅行情

```
POST /api/v1/quotes/subscribe
```

请求体：

```json
{
  "type": "five_tick",
  "symbols": ["2330", "2885"],
  "account": "S98875005091",
  "market_type": "TWSE",
  "index_flag": 7
}
```

`type` 支持：

| type | 对应元大订阅 |
|---|---|
| `watchlist` | SubscribeWatchlist |
| `watchlist_all` | SubscribeWatchlistAll |
| `five_tick` | SubscribeFiveTickA |
| `stock_tick` | SubscribeStockTick |
| `market_info` | SubscribeMarketInformation |
| `stock_info` | SubscribeStockInformation |

`index_flag` 主要用于 `watchlist`，相同股票不同 `index_flag` 会作为不同订阅保存。

### 5.2 取消订阅

```
POST /api/v1/quotes/unsubscribe
```

请求体与订阅相同。

### 5.3 查看已订阅

```
GET /api/v1/quotes/subscribed?source=local
GET /api/v1/quotes/subscribed?source=broker
GET /api/v1/quotes/subscribed?source=both
```

- `source=local`：默认，返回本地 SQLite 订阅清单。
- `source=broker`：调用元大 `GetQuoteList` 返回券商端实际已订阅清单。
- `source=both`：同时返回本地与券商端清单。

### 5.4 行情查询

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/quotes/snapshot?stk_code=2330&market_type=TWSE` | 报价快照 |
| GET | `/api/v1/quotes/ticks?stk_code=2330&market_type=TWSE&last_count=20` | 分时明细 |
| GET | `/api/v1/quotes/classify-price?stk_code=2330&market_type=TWSE` | 分价量 |
| GET | `/api/v1/quotes/kline?stk_code=2330&start_date=2026/01/01&end_date=2026/01/31` | K 线 |
| GET | `/api/v1/stocks/info?stk_code=2330&market_type=TWSE` | 个股资讯 |

## 6. 交易

### 6.1 委托下单 / 撤单 / 改价 / 改量

```
POST /api/v1/orders/stock
```

统一入口，通过 `action` 区分操作。

#### 新单

```json
{
  "client_order_id": "C001",
  "action": "new",
  "account": "S98875005091",
  "stk_code": "2330",
  "side": "B",
  "price": 500.0,
  "quantity": 10,
  "time_in_force": "ROD",
  "price_flag": "LIMIT"
}
```

`client_order_id` 是本地幂等键，允许 1–64 位 Unicode 字符；发送至元大时，服务端会生成稳定的 `BasketNo`（最多 32 位 ASCII 英数字），不会截断客户端 ID。新单未传 `trade_date` 时服务端使用当天的 `YYYY/MM/DD`。

#### 撤单

```json
{
  "client_order_id": "C002",
  "action": "cancel",
  "account": "S98875005091",
  "order_no": "H00001",
  "trade_date": "2026/08/28",
  "stk_code": "2330",
  "side": "B"
}
```

#### 改价

```json
{
  "client_order_id": "C003",
  "action": "replace",
  "account": "S98875005091",
  "order_no": "H00001",
  "stk_code": "2330",
  "side": "B",
  "new_price": 510.0
}
```

#### 改量

```json
{
  "client_order_id": "C003",
  "action": "replace",
  "account": "S98875005091",
  "order_no": "H00001",
  "stk_code": "2330",
  "side": "B",
  "new_quantity": 20
}
```

> 注意：`replace` 不允许同时传 `new_price` 和 `new_quantity`，否则返回 `REPLACE_BOTH_FIELDS_UNSUPPORTED`。

字段约束：`side` 只能为 `B`/`S`；`time_in_force` 只能为 `ROD`/`IOC`/`FOK`；`price_flag` 只能为 `LIMIT`/`M`/`H`/`L`/`-`；`ap_code` 推荐使用语义值 `REGULAR`（整股）、`ODD_LOT`（零股）、`INTRADAY_ODD_LOT`（盘中零股）或 `AFTER_HOURS`（盘后），同时兼容旧数字 `0`、`2`、`4`、`7`。改量时 `new_quantity` 必须为正整数。限价单价格必须为正，市价等非限价订单价格可省略或为 `0`。

### 6.2 幂等性

`client_order_id` 是幂等键：

- 同一 `client_order_id`、同一账户、相同 `action` 重复提交不会重复送单或重复撮合。
- 同一 `client_order_id` 被不同账户、不同模式（Mock/真实）或不同 `action` 使用时，返回 `IDEMPOTENCY_CONFLICT`。
- 首次请求原子 claim 成功后才拥有执行权；并发竞争请求只返回已有订单状态。看到 `PENDING` 表示订单已被接收但仍在执行，不应再次并发提交同一 ID。
- Mock 报价失败且订单尚未结算时，订单为 `FAILED` 且 `data.retryable=true`。之后的同 ID Mock 请求可重新 claim 一次执行权，并递增 `data.execution.attempt`。
- `REJECTED`、`FILLED`、`CANCELLED` 不自动重试；真实券商失败也不自动重试，因为请求可能已经到达券商。

### 6.3 Mock 账户与离线撮合

Mock 账户必须使用独立的 `MOCK-` 命名空间，例如 `MOCK-TEST`。初始化接口：

```
POST /api/v1/mock/accounts/init
```

```json
{
  "account": "MOCK-TEST",
  "cash": 100000.0,
  "positions": []
}
```

默认 Mock 行情来自服务端配置的离线固定盘口（默认 bid1=99.0、ask1=101.0），不需要登录元大、不需要 UAT，也不会调用 Spark API。若要使用外部/实时盘口，必须由应用显式注入 `mock_quote_provider`，不能由 Mock 路径自动复用真实行情。

- Mock 买单按 ask1 成交，Mock 卖单按 bid1 成交，默认全部成交。
- `mock=true` 的订单只能使用 `MOCK-*` 账户；`mock=false` 不能使用 Mock 账户。
- Mock 撤单/改单当前不会发送 Spark API。已成交订单返回 `MOCK_ORDER_FINAL`（409）；未决但不支持的操作返回 `MOCK_OPERATION_UNSUPPORTED`（409）。
- 停用账户但保留历史账本：

```
DELETE /api/v1/mock/accounts/{account}
```

停用后新订单返回 `MOCK_ACCOUNT_INACTIVE`（409）。

### 6.4 订单状态

| 状态 | 含义 |
|---|---|
| `PENDING` | 已接收，等待发送 |
| `SUBMITTED` | 已发送券商 |
| `ACCEPTED` | 已接受 |
| `PARTIALLY_FILLED` | 部分成交 |
| `FILLED` | 全部成交 |
| `CANCELLED` | 已取消 |
| `REJECTED` | 被拒绝 |
| `FAILED` | 本地失败 |
| `NEED_MANUAL_REVIEW` | 需要人工确认 |

### 6.5 查询订单

```
GET /api/v1/orders?account=S98875005091&status=ACCEPTED
GET /api/v1/orders/{client_order_id}
```

## 7. 风控与运维控制

### 7.1 手动 Panic

```
POST /api/v1/control/panic
```

开启后所有下单/撤单/改单会被风控拒绝。

### 7.2 恢复

```
POST /api/v1/control/resume
```

关闭 Panic 并手动复位熔断器。

## 8. 恢复与人工确认

### 8.1 查看未解决订单

```
GET /api/v1/recovery/unresolved
```

响应 `data` 为数组，每项包含 `source`，取值 `orders`（M3 旧表）或 `stock_orders`（M4 新表）。

### 8.2 人工确认订单

```
POST /api/v1/recovery/{client_order_id}/resolve
```

请求体：

```json
{
  "status": "FILLED",
  "order_no": "H00001",
  "trade_date": "2026/08/28",
  "source": "stock_orders",
  "note": "人工确认"
}
```

- `source` 为 `orders` 时，必须提供 `order_no`。
- `source` 省略时优先按 M4 `stock_orders` 处理；若找不到，会尝试按 `order_no` 或路径参数作为 M3 旧订单号处理。

## 9. WebSocket

### 9.1 连接

```
WS /ws?token=<api_token>
```

也可以使用请求头 `Authorization: Bearer <api_token>`。

连接成功后先收到：

```json
{
  "type": "welcome",
  "message": "connected"
}
```

### 9.2 接收事件

服务端会推送以下事件：

| type | 说明 |
|---|---|
| `Login` | 登录事件 |
| `RR_RealReport` | 实时回报原始事件 |
| `RR_RealReportMerge` | 合并回报原始事件 |
| `real_report` / `real_report_merge` | 处理后的回报事件 |
| `order.updated` | 订单状态更新 |
| `SubscribeWatchlist` / `SubscribeFiveTickA` 等 | 订阅原始行情事件 |
| `quote.updated` | 统一行情推送 |
| `heartbeat` | 每 30 秒心跳 |

示例回报推送：

```json
{
  "type": "order.updated",
  "data": {
    "client_order_id": "C001",
    "status": "FILLED",
    "order_no": "H00001",
    "trade_date": "2026/08/28",
    "request": { },
    "data": { },
    "last_error": null
  }
}
```

## 10. 快速示例

### 10.1 登录后查库存

```bash
TOKEN=test-token
BASE=http://127.0.0.1:8000

curl -X POST "$BASE/api/v1/session/login" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

curl "$BASE/api/v1/positions?account=S98875005091" \
  -H "Authorization: Bearer $TOKEN"
```

### 10.2 下一笔限价买单

```bash
curl -X POST "$BASE/api/v1/orders/stock" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_order_id": "C001",
    "action": "new",
    "account": "S98875005091",
    "stk_code": "2330",
    "side": "B",
    "price": 500.0,
    "quantity": 10
  }'
```

### 10.3 订阅五档行情并监听 WebSocket

```bash
curl -X POST "$BASE/api/v1/quotes/subscribe" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "five_tick",
    "symbols": ["2330"]
  }'
```

```bash
# 使用 wscat 或其他 WebSocket 客户端
wscat -c "ws://127.0.0.1:8000/ws?token=test-token"
```

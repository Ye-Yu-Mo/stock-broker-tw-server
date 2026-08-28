# TODO-M5: 行情订阅与 WebSocket

---

## 目标
- 实现本土股票行情订阅/取消订阅。
- 实现行情查询 API。
- WebSocket 统一推送行情与回报事件。
- 所属 Milestone: M5

## 功能1: 行情订阅领域模型

### 修改1:
- 改什么：新增行情订阅模型，例如 `QuoteType`、`SubscribeRequest`、`SubscribedQuote`，统一表示 watchlist / watchlist_all / five_tick / stock_tick / market_info / stock_info。
- 为什么改：避免 API 层和 broker 层各自维护不一致的行情类型字符串。
- 预期结果：业务层可以用统一模型表达订阅请求和已订阅列表。

### 修改2:
- 改什么：定义订阅类型的枚举映射到元大 API：
  - `watchlist` → `SubscribeWatchlist`
  - `watchlist_all` → `SubscribeWatchlistAll`
  - `five_tick` → `SubscribeFiveTickA`
  - `stock_tick` → `SubscribeStockTick`
  - `market_info` → `SubscribeMarketInformation`
  - `stock_info` → `SubscribeStockInformation`
- 为什么改：让订阅 API 对客户端友好，同时内部能准确映射到元大函数。
- 预期结果：外部传 `type=five_tick` 即可订阅最佳五档。

### 影响文件
- `src/stock_broker_tw/broker/quote.py`（新增）
- `src/stock_broker_tw/broker/__init__.py`
- `src/stock_broker_tw/engine/state.py`（如复用枚举风格）

---

## 功能2: 订阅/取消订阅服务

### 修改1:
- 改什么：新增 `QuoteService`，封装 `subscribe()`、`unsubscribe()`、`list_subscribed()`。
- 为什么改：将 HTTP API 与元大 Adapter 隔离。
- 预期结果：调用 `subscribe(request)` 能完成订阅并返回已订阅列表。

### 修改2:
- 改什么：订阅时维护本地订阅清单，并做去重。
- 为什么改：避免同一客户端重复订阅同一标的导致元大 API 超限。
- 预期结果：重复订阅同一商品不会重复调用元大 API。

### 修改3:
- 改什么：取消订阅时从本地清单移除，并调用对应 `UnSubscribe*` 函数。
- 为什么改：确保取消后不再收到推送。
- 预期结果：取消后本地清单和元大端都移除。

### 影响文件
- `src/stock_broker_tw/broker/quote.py`
- `src/stock_broker_tw/service/quote.py`（新增）
- `src/stock_broker_tw/state/store.py`
- `src/stock_broker_tw/yuanta/adapter.py`

---

## 功能3: 订阅数量上限与限流

### 修改1:
- 改什么：在订阅服务中检查单次订阅数量上限和总订阅数量上限。
- 为什么改：元大 API 单次最多 200 档、总订阅最多 2000/3000 档，超过会被暂停。
- 预期结果：超过上限返回 429 或 400 明确错误。

### 修改2:
- 改什么：复用或扩展 `RateLimiter`，对订阅类 FunctionID 做每秒限制。
- 为什么改：元大 API 同 FunctionID 每秒订阅次数上限 10。
- 预期结果：超限请求被拒绝。

### 影响文件
- `src/stock_broker_tw/risk/rate_limit.py`
- `src/stock_broker_tw/broker/quote.py`
- `src/stock_broker_tw/service/quote.py`
- `src/stock_broker_tw/config.py`

---

## 功能4: 行情订阅 API

### 修改1:
- 改什么：新增 `POST /api/v1/quotes/subscribe`。
- 为什么改：外部客户端需要通过 HTTP 订阅行情。
- 预期结果：请求体包含 `type`、`symbols`、`account`，成功后返回已订阅列表。

### 修改2:
- 改什么：新增 `POST /api/v1/quotes/unsubscribe`。
- 为什么改：客户端需要取消订阅。
- 预期结果：取消后返回剩余已订阅列表。

### 修改3:
- 改什么：新增 `GET /api/v1/quotes/subscribed`。
- 为什么改：客户端需要查看当前已订阅内容。
- 预期结果：返回结构化订阅列表。

### 影响文件
- `src/stock_broker_tw/api/http.py`
- `src/stock_broker_tw/service/quote.py`
- `src/stock_broker_tw/broker/quote.py`

---

## 功能5: 行情查询 API

### 修改1:
- 改什么：新增 `GET /api/v1/quotes/snapshot` → `GetWatchListAll`。
- 为什么改：客户端需要查询整包报价表。
- 预期结果：返回结构化报价数据。

### 修改2:
- 改什么：新增 `GET /api/v1/quotes/ticks` → `GetStkTickDetail`。
- 为什么改：客户端需要查询当日分时明细。
- 预期结果：返回分时明细列表。

### 修改3:
- 改什么：新增 `GET /api/v1/quotes/classify-price` → `GetStkClassifyPrice`。
- 为什么改：客户端需要查询分价量。
- 预期结果：返回分价量数据。

### 修改4:
- 改什么：新增 `GET /api/v1/quotes/kline` → `GetKLine`。
- 为什么改：客户端需要查询 K 线。
- 预期结果：返回 K 线列表。

### 修改5:
- 改什么：新增 `GET /api/v1/stocks/info` → `GetStockInformation`。
- 为什么改：客户端需要查询标的资讯。
- 预期结果：返回标的基本信息、涨跌停、信用交易等数据。

### 影响文件
- `src/stock_broker_tw/api/http.py`
- `src/stock_broker_tw/service/query.py`
- `src/stock_broker_tw/yuanta/serializer.py`
- `src/stock_broker_tw/state/store.py`

---

## 功能6: WebSocket 行情事件推送

### 修改1:
- 改什么：扩展 WebSocket 事件，新增 `quote.updated`。
- 为什么改：让客户端能实时收到行情订阅推送。
- 预期结果：收到 `SubscribeWatchlist`、`SubscribeFiveTickA`、`SubscribeStockTick` 等事件时，以 `quote.updated` 统一推送给客户端。

### 修改2:
- 改什么：将原始订阅事件同时保留为 raw 事件，并增加 processed `quote.updated`。
- 为什么改：兼容 M2 的 raw 事件行为，同时提供统一行情事件。
- 预期结果：客户端可选择消费 raw 或 `quote.updated`。

### 修改3:
- 改什么：行情事件序列化使用统一的 `to_dict`，避免 .NET 对象泄漏到 WebSocket。
- 为什么改：保证 JSON 输出稳定。
- 预期结果：WebSocket 消息始终为 JSON 可序列化结构。

### 影响文件
- `src/stock_broker_tw/api/ws.py`
- `src/stock_broker_tw/yuanta/serializer.py`
- `src/stock_broker_tw/engine/report_handler.py`（如复用事件分发模式）

---

## 功能7: 行情序列化映射

### 修改1:
- 改什么：扩展 `serializer.py`，支持：
  - `WatchListResult` / `WatchListAllResult`
  - `FiveTickAResult`
  - `StockTickResult`
  - `MarketInfoResult`
  - `StockOtherInfoResult`
  - `StkInformationResult`
  - `StickDetailResult`
  - `StkClassifyPriceResult`
  - `KLineResult`
- 为什么改：行情订阅和查询返回对象字段多，需要集中映射。
- 预期结果：所有行情数据都能转成 JSON-friendly dict/list。

### 影响文件
- `src/stock_broker_tw/yuanta/serializer.py`
- `tests/test_serializer_m5.py`

---

## 测试计划
- 单元测试：
  - 订阅模型与类型映射。
  - 订阅去重、上限、限流。
  - 行情序列化：watchlist、five_tick、stock_tick、kline 等。
  - QuoteService subscribe/unsubscribe/list。
- 集成测试：
  - 使用 FakeAdapter 通过 HTTP 完成订阅、取消订阅、已订阅列表。
  - 验证 WebSocket 能收到 `quote.updated`。
  - 验证 WebSocket 能同时收到行情与交易回报。
  - 验证超限订阅返回 429/400。
- 回归测试：
  - M1、M2、M3、M4 全部测试继续通过。
  - 交易回报推送不受影响。
- 边界条件测试：
  - 空订阅列表。
  - 重复订阅同一标的。
  - 取消不存在的订阅。
  - 单次超过 200 档。
  - 总订阅超过上限。
  - 非法 `type`。
  - K 线日期格式错误。

## 验收标准
- [x] 能订阅并收到 `SubscribeWatchlist` / `SubscribeWatchlistAll` / `SubscribeFiveTickA` / `SubscribeStockTick` 等事件。
- [x] 能取消订阅，取消后不再收到对应推送。
- [x] 订阅数量超过上限时被拒绝并提示。
- [x] 行情查询接口能返回结构化数据。
- [x] WebSocket 客户端能同时收到行情与交易回报。
- [x] M1、M2、M3、M4 的单元测试全部通过。

## 兼容性检查
- 是否影响现有行为：不影响 M1 CLI、M2 会话、M3 只读、M4 交易接口。
- 是否需要兼容旧接口/旧数据：M5 新增订阅清单存储，旧数据不存在；SQLite 新增表无需迁移已有数据。
- 是否存在 break userspace 风险：`POST /api/v1/quotes/subscribe` 等为新增接口；WebSocket 新增 `quote.updated` 事件类型为追加，不影响已有 `real_report` / `order.updated`。

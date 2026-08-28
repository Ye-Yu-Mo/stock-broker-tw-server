# TODO-M4: 交易闭环

---

## 目标
- 实现本土股票下单、撤单、改量、改价。
- 实现订单状态机、幂等、串行队列和基础风控。
- 通过 WebSocket 推送订单状态与即时回报。
- 所属 Milestone: M4

## 功能1: 订单领域模型与状态机

### 修改1:
- 改什么：新增 `src/stock_broker_tw/engine/state.py`，定义 `OrderStatus`、`OrderSide`、`TimeInForce`、`PriceFlag`、`StockOrderRequest`、`StockOrderState` 等模型。
- 为什么改：统一订单相关概念，避免 API 层和 broker 层各自维护不一致的状态。
- 预期结果：业务层能使用统一的 Python dataclass/enum 描述订单。

### 修改2:
- 改什么：实现订单状态机 `OrderStateMachine`，支持 `Pending -> Submitted -> Accepted -> PartiallyFilled/Filled/Cancelled/Rejected/Failed` 等转换。
- 为什么改：防止非法状态跳转，保证订单生命周期可追踪。
- 预期结果：非法转换抛错或忽略，合法转换记录时间戳和原因。

### 影响文件
- `src/stock_broker_tw/engine/state.py`
- `src/stock_broker_tw/engine/__init__.py`
- `tests/test_engine_state.py`

---

## 功能2: 幂等与交易串行队列

### 修改1:
- 改什么：新增 `src/stock_broker_tw/engine/queue.py`，实现单账户交易串行队列。
- 为什么改：元大 API 是事件驱动且单连接，必须避免并发下单导致响应错乱。
- 预期结果：同一时间只有一个交易操作在执行，其他请求排队。

### 修改2:
- 改什么：实现幂等存储：以 `client_order_id` 为唯一键，保存订单请求和当前状态。
- 为什么改：网络重试或客户端重复提交不能重复下单。
- 预期结果：相同 `client_order_id` 的重复请求直接返回已有状态。

### 修改3:
- 改什么：在队列执行前做“是否已存在”检查，执行中持久化中间状态。
- 为什么改：崩溃恢复需要知道哪些订单已提交、哪些尚未提交。
- 预期结果：SQLite 中能看到每个 `client_order_id` 的状态。

### 影响文件
- `src/stock_broker_tw/engine/queue.py`
- `src/stock_broker_tw/state/store.py`
- `src/stock_broker_tw/engine/__init__.py`
- `tests/test_engine_queue.py`

---

## 功能3: 券商交易服务层

### 修改1:
- 改什么：新增 `src/stock_broker_tw/broker/service.py`，封装证券新单、撤单、改量、改价。
- 为什么改：将 HTTP API 与元大 API 细节隔离。
- 预期结果：调用 `place_stock_order`、`cancel_stock_order`、`replace_stock_order` 即可完成对应操作。

### 修改2:
- 改什么：新单时把 `client_order_id` 写入 `BasketNo`，并保存 `OrderNo` / `TradeDate` 映射。
- 为什么改：后续撤单/改价需要 `OrderNo`，幂等也需要能追溯。
- 预期结果：订单提交成功后，本地能记录券商委托书号。

### 修改3:
- 改什么：撤单/改量/改价时复用 `SendStockOrder`，分别使用 `TradeKind=04/03/07`，并带上 `OrderNo`、`TradeDate`。
- 为什么改：元大 API 没有独立撤单函数，必须走证券下单通道。
- 预期结果：撤单/改价请求能正确映射到元大参数。

### 影响文件
- `src/stock_broker_tw/broker/service.py`
- `src/stock_broker_tw/broker/__init__.py`
- `src/stock_broker_tw/yuanta/adapter.py`
- `src/stock_broker_tw/yuanta/serializer.py`

---

## 功能4: HTTP 下单/撤单/改量/改价 API

### 修改1:
- 改什么：新增 `POST /api/v1/orders/stock`，请求体支持 `action=new/replace/cancel`。
- 为什么改：对外提供统一交易入口。
- 预期结果：`action=new` 下单，`action=cancel` 撤单，`action=replace` 改量/改价。

### 修改2:
- 改什么：新增查询当前订单/状态的接口，例如 `GET /api/v1/orders`、`GET /api/v1/orders/{client_order_id}`。
- 为什么改：客户端需要查询自己提交的订单状态。
- 预期结果：能按 `client_order_id` 查询本地订单状态。

### 修改3:
- 改什么：所有写接口都需要 token 鉴权，并记录审计。
- 为什么改：交易接口必须受保护且可追溯。
- 预期结果：未带 token 返回 401，审计中能看到下单/撤单/改价记录。

### 影响文件
- `src/stock_broker_tw/api/http.py`
- `src/stock_broker_tw/api/ws.py`
- `src/stock_broker_tw/broker/service.py`
- `src/stock_broker_tw/service/order.py`（如需要）

---

## 功能5: 基础风控规则

### 修改1:
- 改什么：新增 `src/stock_broker_tw/risk/rules.py`，实现价格偏离、数量上限、金额上限、黑名单等规则。
- 为什么改：在真实下单前拦截明显异常或高风险请求。
- 预期结果：风控拒绝时返回明确错误码并写入审计。

### 修改2:
- 改什么：在 broker service 下单前执行风控检查，风控失败不进入串行队列。
- 为什么改：避免无效请求占用队列和触发元大 API 调用。
- 预期结果：风控拒绝的请求不会调用 `SendStockOrder`。

### 修改3:
- 改什么：增加手动 panic / 熔断检查。
- 为什么改：紧急情况下需要一键停止所有交易。
- 预期结果：panic 状态下所有写交易接口被拒绝。

### 影响文件
- `src/stock_broker_tw/risk/rules.py`
- `src/stock_broker_tw/risk/__init__.py`
- `src/stock_broker_tw/broker/service.py`
- `src/stock_broker_tw/config.py`
- `tests/test_risk_rules.py`

---

## 功能6: WebSocket 订单状态与回报推送

### 修改1:
- 改什么：扩展 WebSocket 事件类型，新增 `order.updated`、`real_report`、`real_report_merge`。
- 为什么改：客户端需要实时感知订单状态变化和券商回报。
- 预期结果：订单状态变化时推送 `order.updated`，收到 `RR_RealReport` / `RR_RealReportMerge` 时推送对应事件。

### 修改2:
- 改什么：在 `_on_response` 或回报处理中，根据 `OrderNo` / `BasketNo` 更新本地订单状态。
- 为什么改：让本地状态机与券商回报保持一致。
- 预期结果：成交回报到达后，订单状态自动变为 `PartiallyFilled` / `Filled`。

### 修改3:
- 改什么：将状态更新写入 SQLite，并通过 WebSocket 广播。
- 为什么改：崩溃恢复和实时通知都需要持久化 + 推送。
- 预期结果：服务重启后能从 SQLite 恢复订单状态。

### 影响文件
- `src/stock_broker_tw/api/ws.py`
- `src/stock_broker_tw/engine/state.py`
- `src/stock_broker_tw/broker/service.py`
- `src/stock_broker_tw/state/store.py`
- `src/stock_broker_tw/yuanta/adapter.py`

---

## 功能7: 回报驱动的订单状态更新

### 修改1:
- 改什么：新增回报处理模块，订阅 `RR_RealReport` / `RR_RealReportMerge` 事件并更新订单状态。
- 为什么改：`SendStockOrder` 只代表“已送出”，真正状态要由回报决定。
- 预期结果：委托成功、成交、撤单成功、失败等回报都能映射到状态机。

### 修改2:
- 改什么：处理 `OnResponse` 中 `SendStockOrder` 的返回结果，区分受理成功/失败。
- 为什么改：避免把“请求被接受”误判为“订单已成功”。
- 预期结果：`SendStockOrder` 响应失败时订单进入 `Rejected`。

### 修改3:
- 改什么：对无法自动判定的回报标记 `NEED_MANUAL_REVIEW`。
- 为什么改：防止错误状态误导客户端。
- 预期结果：异常/未知回报不会静默丢失。

### 影响文件
- `src/stock_broker_tw/engine/report_handler.py`（新增）
- `src/stock_broker_tw/engine/state.py`
- `src/stock_broker_tw/state/store.py`
- `src/stock_broker_tw/api/ws.py`

---

## 测试计划
- 单元测试：
  - 状态机：合法/非法状态转换。
  - 队列：串行执行、重复 client_order_id 幂等。
  - 风控：价格/数量/金额/黑名单/panic。
  - broker service：下单/撤单/改量/改价参数映射。
  - 回报处理：`RR_RealReport` / `RR_RealReportMerge` 更新状态。
- 集成测试：
  - 使用 FakeAdapter 通过 HTTP 完成下单 → 回报 → 状态更新 → WebSocket 推送。
  - 验证重复 `client_order_id` 不会重复调用券商。
  - 验证风控拒绝不调用券商。
- 回归测试：
  - M1、M2、M3 全部测试继续通过。
  - 只读查询接口不受影响。
- 边界条件测试：
  - 撤单时找不到本地 `OrderNo`。
  - 改价时价格非法。
  - 重复撤单/重复改价。
  - 回报先于 `SendStockOrder` 响应到达。
  - 队列等待超时。
  - panic 状态下所有写接口拒绝。

## 验收标准
- [ ] 测试环境能成功下一笔股票买单。
- [ ] 使用 `client_order_id` 重复提交同一请求不会重复下单。
- [ ] 能对未成交委托执行撤单，状态变为已撤。
- [ ] 风控拒绝时返回明确错误，并写入审计。
- [ ] 回报到达后订单状态能自动更新并通过 WebSocket 推送。
- [ ] M1、M2、M3 的单元测试全部通过。

## 兼容性检查
- 是否影响现有行为：不影响 M1 CLI、M2 会话接口、M3 只读查询接口。
- 是否需要兼容旧接口/旧数据：M3 已有 `orders` 表，M4 需要在其上扩展字段或新增 `client_order_id` 映射表，需做兼容迁移。
- 是否存在 break userspace 风险：`POST /api/v1/orders/stock` 为新增接口；如果后续调整请求字段或状态枚举，需保持向后兼容或提供迁移文档。

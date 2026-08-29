# TODO-M1: 并发请求关联与状态一致性技术债修复

---

## 目标
- 修复 `_query_responses` 并发同名查询响应错配问题。
- 修复 `save_stock_order` 全行覆盖导致状态机约束失效的问题。
- 清理 serializer / report_handler / `_trade_kind` 中容易出错或来源不明确的实现。
- 消除三处重复的配置归一化逻辑。
- 所属 Milestone: M1（技术债修复批次）

## 功能1: `_query_responses` 增加请求关联

### 修改1:
- 改什么：将 `YuantaAdapter._query_responses` 从“按 Function 名称存响应列表”升级为“按 Function 名称 + request_id/Identify 关联存响应”。
- 为什么改：当前并发调用同一个查询 Function 时，响应只按 `str_index` 分发，可能出现 A 请求拿到 B 请求的响应，导致数据错配。
- 预期结果：每个查询请求携带唯一 request_id，响应按 request_id 匹配；无法匹配的响应进入待处理队列或丢弃并记录日志。

### 修改2:
- 改什么：在 `adapter.query()` 和 `send_stock_order()` 中传入并透传 request_id，等待时只消费属于当前 request_id 的响应。
- 为什么改：让交易/查询调用在并发场景下也能准确拿到自己的 `OnResponse`。
- 预期结果：并发同名查询/下单不会互相串响应，超时行为保持正确。

### 影响文件
- `src/stock_broker_tw/yuanta/adapter.py`
- `src/stock_broker_tw/yuanta/events.py`
- `tests/test_adapter.py`
- `tests/test_query.py`

---

## 功能2: `save_stock_order` 按状态机约束更新

### 修改1:
- 改什么：调整 `StateStore.save_stock_order` / `update_stock_order`，避免无条件全行覆盖。
- 为什么改：当前直接覆盖整行可能绕过订单状态机，例如已 FILLED 的订单还能被旧响应覆盖回 PENDING/ACCEPTED。
- 预期结果：只有状态机允许的转换才允许更新；非法转换写入错误日志或保持原状态。

### 修改2:
- 改什么：在 store 层增加状态转换校验入口，或要求调用方先通过 `OrderStateMachine` 再写入。
- 为什么改：把状态一致性约束下沉到持久化层，避免上层遗漏。
- 预期结果：非法状态更新被拒绝，审计中能看到拒绝原因。

### 影响文件
- `src/stock_broker_tw/state/store.py`
- `src/stock_broker_tw/engine/state.py`
- `src/stock_broker_tw/broker/service.py`
- `tests/test_store_m4.py`
- `tests/test_engine_state.py`

---

## 功能3: serializer 反射兜底与魔法数字清理

### 修改1:
- 改什么：修复 `serializer.to_dict` 反射兜底静默丢字段的问题。
- 为什么改：当前反射获取属性失败时直接 `continue`，可能静默丢失重要字段，且没有日志/错误提示。
- 预期结果：反射失败时记录 warning 或返回缺失字段占位，关键字段不静默丢失。

### 修改2:
- 改什么：为 `report_handler._map_report_status` 中的魔法数字增加来源注释或改为表驱动。
- 为什么改：`2/23/30`、`1/3/5/7/10/21`、`24/25` 等状态码直接散落代码中，后续维护容易出错。
- 预期结果：状态码映射集中为常量/表，并注明对应元大回报文档来源。

### 修改3:
- 改什么：确认并注释 `broker/service.py::_trade_kind` 中 `4/7/3` 的来源。
- 为什么改：`4=取消`、`7=改价`、`3=改量` 是元大 `SendStockOrder.TradeKind` 的字段约定，需要明确来源。
- 预期结果：常量命名清晰，并链接到 `docs/API` 或 `docs/api.md` 对应说明。

### 影响文件
- `src/stock_broker_tw/yuanta/serializer.py`
- `src/stock_broker_tw/engine/report_handler.py`
- `src/stock_broker_tw/broker/service.py`
- `tests/test_serializer_m3.py`
- `tests/test_report_handler.py`
- `tests/test_broker_service.py`

---

## 功能4: 配置归一化抽成函数

### 修改1:
- 改什么：将 `main.py:59`、`query.py:51`、`quote.py:57` 三处重复的查询/行情限流配置归一化逻辑抽成公共函数。
- 为什么改：三处代码重复，后续调整限流参数容易漏改。
- 预期结果：新增统一配置解析函数，三处都调用同一实现。

### 修改2:
- 改什么：为归一化函数补充单元测试，覆盖旧配置字段与新配置字段的优先级。
- 为什么改：保证重构后行为不变。
- 预期结果：测试覆盖 `query` / `quote` / `rate_limit` 配置的兼容读取。

### 影响文件
- `src/stock_broker_tw/config.py`
- `src/stock_broker_tw/main.py`
- `src/stock_broker_tw/service/query.py`
- `src/stock_broker_tw/service/quote.py`
- `tests/test_config.py`

---

## 测试计划
- 单元测试：
  - 并发同名查询响应按 request_id 正确匹配。
  - 超时请求不会消费其他请求的响应。
  - `save_stock_order` 非法状态转换被拒绝。
  - serializer 反射兜底不静默丢字段。
  - report_handler 状态码映射表驱动。
  - `_trade_kind` 常量映射正确。
  - 配置归一化函数兼容新旧配置。
- 集成测试：
  - 使用 FakeAdapter 并发发起多个相同 Function 查询，验证结果不串。
  - 模拟旧响应覆盖已 FILLED 订单，验证状态不被回退。
- 回归测试：
  - M1–M6 现有测试全部继续通过。
  - 现有 HTTP / WebSocket 行为不变化。
- 边界条件测试：
  - request_id 缺失时行为。
  - 响应到达时请求已超时。
  - 未知状态码映射到 `NEED_MANUAL_REVIEW`。
  - 配置同时存在新旧字段时优先级。

## 验收标准
- [ ] 并发同名查询响应不再错配，相关测试通过。
- [ ] `save_stock_order` 不再绕过状态机，非法更新被拒绝。
- [ ] serializer 反射兜底不再静默丢关键字段。
- [ ] report_handler 魔法数字改为表驱动或带来源注释。
- [ ] `_trade_kind` 的 4/7/3 来源已确认并注释。
- [ ] 三处配置归一化逻辑抽成公共函数并有测试覆盖。
- [ ] M1–M6 全部现有测试继续通过。

## 兼容性检查
- 是否影响现有行为：不影响对外 HTTP/WebSocket API；主要是内部并发正确性与状态一致性修复。
- 是否需要兼容旧接口/旧数据：`save_stock_order` 行为变化可能影响已存在订单数据，需要确认旧数据仍可正常读取；不改变表结构。
- 是否存在 break userspace 风险：无；客户端接口路径与响应格式保持不变。

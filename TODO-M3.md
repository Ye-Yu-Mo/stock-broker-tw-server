# TODO-M3: 只读能力

---

## 目标
- 实现本土股票相关的只读查询 API。
- 打通元大查询类 API 的请求/响应闭环。
- 建立本地 SQLite 状态存储与首次启动恢复逻辑。
- 所属 Milestone: M3

## 功能1: 查询基座与通用序列化扩展

### 修改1:
- 改什么：在 `yuanta/adapter.py` 增加通用查询方法，例如 `query(function_name, **params)`，统一走元大 API 并等待 `OnResponse` 对应 `strIndex`。
- 为什么改：M3 有大量查询类 API，若每个都手写等待逻辑会重复且容易出错。
- 预期结果：调用方传入 Function 名称和参数，能拿到序列化后的 dict/list 结果或超时错误。

### 修改2:
- 改什么：扩展 `serializer.py`，补充 `GetStoreSummary`、`GetBankBalance`、`GetStkTransactionOutlay`、损益、回报、委託成交等对象的字段映射。
- 为什么改：元大返回对象字段多，需要集中映射为 JSON-friendly 结构，避免业务层直接依赖 .NET 类型。
- 预期结果：所有 M3 查询结果都能转换为结构化 dict/list，字段命名统一 snake_case。

### 修改3:
- 改什么：为查询类 API 增加请求关联与超时处理，支持 `request_id` 和超时异常。
- 为什么改：查询类 API 同样是异步 `OnResponse`，必须有超时和错误映射。
- 预期结果：查询超时返回明确错误，不阻塞后续请求。

### 影响文件
- `src/stock_broker_tw/yuanta/adapter.py`
- `src/stock_broker_tw/yuanta/serializer.py`
- `src/stock_broker_tw/service/query.py`（新增）
- `src/stock_broker_tw/config.py`

---

## 功能2: 股票库存查询 API

### 修改1:
- 改什么：新增 `GET /api/v1/positions`，调用 `GetStoreSummary` 并返回国内/国外股票库存。
- 为什么改：策略和客户端需要查询当前持仓。
- 预期结果：能返回股票代码、名称、可交易数量、成本、市值、未实现损益等结构化数据。

### 修改2:
- 改什么：对 `GetStoreSummary` 响应做本地快照持久化。
- 为什么改：即使元大查询失败，也能提供最近一次成功快照。
- 预期结果：SQLite 中保存最近一次持仓快照，查询 API 可优先返回缓存或附带时间戳。

### 影响文件
- `src/stock_broker_tw/api/http.py`
- `src/stock_broker_tw/service/query.py`
- `src/stock_broker_tw/state/store.py`
- `src/stock_broker_tw/yuanta/serializer.py`

---

## 功能3: 银行余额与交割款查询 API

### 修改1:
- 改什么：新增 `GET /api/v1/account/balance`，调用 `GetBankBalance`。
- 为什么改：客户端需要查询银行可用余额。
- 预期结果：返回银行余额相关字段；若账号无权限则返回明确错误。

### 修改2:
- 改什么：新增 `GET /api/v1/account/settlement`，调用 `GetStkTransactionOutlay`。
- 为什么改：客户端需要查询交割款信息。
- 预期结果：返回交割日期、应收/应付等结构化数据。

### 影响文件
- `src/stock_broker_tw/api/http.py`
- `src/stock_broker_tw/service/query.py`
- `src/stock_broker_tw/yuanta/serializer.py`
- `src/stock_broker_tw/state/store.py`

---

## 功能4: 损益与冲销明细查询 API

### 修改1:
- 改什么：新增损益相关 API：
  - `GET /api/v1/pnl/unrealized` → `GetUnrealizedGainLossDetail`
  - `GET /api/v1/pnl/realized` → `GetHisRealizedGainLoss`
  - `GET /api/v1/pnl/reversal` → `GetStkHistoryReportReversal`
- 为什么改：覆盖 M3 要求的未实现/已实现损益和冲销明细。
- 预期结果：能按股票或日期范围查询损益数据。

### 修改2:
- 改什么：为这些查询补充参数校验和日期格式校验。
- 为什么改：元大要求 `yyyy/MM/dd` 格式，错误格式会直接失败。
- 预期结果：非法参数返回 400，合法参数正常查询。

### 影响文件
- `src/stock_broker_tw/api/http.py`
- `src/stock_broker_tw/service/query.py`
- `src/stock_broker_tw/yuanta/serializer.py`

---

## 功能5: 即时回报查询 API

### 修改1:
- 改什么：新增：
  - `GET /api/v1/reports/real` → `GetRealReport`
  - `GET /api/v1/reports/real-merge` → `GetRealReportMerge`
- 为什么改：客户端需要查询当日即时回报和汇总回报。
- 预期结果：返回委托/成交明细或汇总数据。

### 修改2:
- 改什么：将回报查询结果写入本地 SQLite，作为订单/回报对账的数据源。
- 为什么改：为 M4 订单状态机和崩溃恢复打基础。
- 预期结果：SQLite 中保存最近一次回报数据，可按 `OrderNo` 查询。

### 影响文件
- `src/stock_broker_tw/api/http.py`
- `src/stock_broker_tw/service/query.py`
- `src/stock_broker_tw/state/store.py`
- `src/stock_broker_tw/yuanta/serializer.py`

---

## 功能6: 委託成交综合回报 API

### 修改1:
- 改什么：新增 `GET /api/v1/reports/order-trade`，调用 `GetOrderTradeReport(NotshowCancel, Account)`。
- 为什么改：这是委托和成交列表的核心数据源。
- 预期结果：返回现货委托、现货成交、期货委托、期货成交等列表；本期重点处理现货部分。

### 修改2:
- 改什么：对委托/成交回报做本地持久化，建立 `orders`、`trades` 表。
- 为什么改：M4 需要基于这些数据做订单状态恢复和幂等。
- 预期结果：SQLite 中能按 `OrderNo`、`TradeDate` 等字段保存委托和成交。

### 影响文件
- `src/stock_broker_tw/api/http.py`
- `src/stock_broker_tw/service/query.py`
- `src/stock_broker_tw/state/store.py`
- `src/stock_broker_tw/yuanta/serializer.py`

---

## 功能7: SQLite 状态存储与启动恢复

### 修改1:
- 改什么：新增 `src/stock_broker_tw/state/store.py`，使用标准库 `sqlite3` 建立数据库连接和表结构。
- 为什么改：为快照、委托、成交、回报数据提供本地持久化。
- 预期结果：启动时自动建表，写入/读取接口可用。

### 修改2:
- 改什么：新增表：
  - `snapshots`：最近一次持仓/资金/余额快照
  - `orders`：委托数据
  - `trades`：成交数据
  - `reports`：即时回报/汇总回报
- 为什么改：M3 查询结果和 M4 订单状态机需要这些基础表。
- 预期结果：各查询 API 能写入快照，恢复逻辑能读取。

### 修改3:
- 改什么：在应用启动时执行首次恢复逻辑：读取本地未完成/最近委托，尝试调用 `GetRealReportMerge` 或 `GetOrderTradeReport` 对账。
- 为什么改：保证服务重启后仍能恢复最近状态，为 M4 崩溃恢复打基础。
- 预期结果：启动日志能看到恢复结果；无法判定的数据标记为待人工确认。

### 影响文件
- `src/stock_broker_tw/state/store.py`
- `src/stock_broker_tw/state/recovery.py`（新增）
- `src/stock_broker_tw/main.py`
- `config/default.toml`

---

## 功能8: 查询限流与错误处理

### 修改1:
- 改什么：为查询类 API 增加按 FunctionID 的简单限流器。
- 为什么改：元大 API 对查询/帐务类有每秒 3 次、每分钟 600 次等限制。
- 预期结果：超限请求返回 429，避免触发元大暂停服务。

### 修改2:
- 改什么：统一查询错误响应格式。
- 为什么改：客户端需要稳定识别超时、无权限、限流、元大错误码等。
- 预期结果：错误响应包含 `code`、`message`、`detail`。

### 影响文件
- `src/stock_broker_tw/risk/rate_limit.py`（新增）
- `src/stock_broker_tw/api/http.py`
- `src/stock_broker_tw/service/query.py`
- `src/stock_broker_tw/config.py`

---

## 测试计划
- 单元测试：
  - `serializer`：覆盖库存、余额、交割款、损益、回报、委托/成交对象映射。
  - `store`：SQLite 建表、写入快照、读取订单/成交。
  - `query`：FakeAdapter 下各查询方法返回正确结果。
  - `rate_limit`：限流计数与拒绝逻辑。
- 集成测试：
  - 使用 FakeAdapter 通过 `TestClient` 调用 `/positions`、`/account/balance`、`/account/settlement`、`/pnl/*`、`/reports/*`。
  - 验证 SQLite 中确实写入了快照和回报数据。
  - 验证未带 token 返回 401。
- 回归测试：
  - M1、M2 全部测试继续通过。
  - CLI 登录验证脚本仍可运行。
- 边界条件测试：
  - 元大返回空列表时 API 返回空数组而不是报错。
  - 查询超时返回 504。
  - 账号无银行余额权限时返回明确错误。
  - 非法日期格式返回 400。
  - 限流超限返回 429。
  - SQLite 文件不存在时自动创建。

## 验收标准
- [ ] 测试环境能查询到股票库存/银行余额/交割款（待 UAT 开通后验证）。
- [x] 委托与成交列表能通过 API 返回结构化 JSON（FakeAdapter + serializer 测试已覆盖）。
- [x] SQLite 中能持久化最近一次快照与订单/回报数据。
- [x] 查询类接口在限流范围内稳定运行（限流器单测 + API 429 测试已覆盖）。
- [x] M1、M2 的单元测试全部通过。
- [x] 启动时能执行首次恢复并对账（recovery 单测已覆盖）。

## 兼容性检查
- 是否影响现有行为：不影响 M1 CLI 和 M2 会话接口；M2 的 HTTP API 保持兼容。
- 是否需要兼容旧接口/旧数据：M3 新增 SQLite 表，旧数据不存在；若后续调整表结构需提供迁移。
- 是否存在 break userspace 风险：新增只读 API 不会破坏现有接口；但 `/api/v1/positions`、`/api/v1/reports/*` 一旦发布，后续字段变更需向后兼容。

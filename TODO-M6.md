# TODO-M6: 生产加固与遗留补齐

---

## 目标
- 补齐 M1–M5 遗留的缺口，确保在取得 UAT 权限后可以进入真实联调。
- 完成限流、熔断、恢复、通知、部署与测试。
- 让 broker server 达到可长期运行的本地生产状态。
- 所属 Milestone: M6

## 功能1: M1–M5 遗留功能补齐

### 修改1:
- 改什么：修复 `StateStore.trades` 表对同一委托多笔成交会互相覆盖的问题。
- 为什么改：M3 review 时已指出 `UNIQUE(order_no, trade_date)` 会把同一委托同日多笔成交压缩成一条，M4 订单闭环需要完整成交记录。
- 预期结果：同一委托同日多笔成交都能独立保存，不丢失成交明细。

### 修改2:
- 改什么：为 `quote_subscriptions` 表增加 `index_flag` 字段，并让 `QuoteService` 保存/删除时使用它。
- 为什么改：M5 review 时已指出同一支股票用不同 `index_flag` 订阅 watchlist 时无法区分。
- 预期结果：watchlist 订阅能精确按 `type + symbol + market_type + index_flag` 管理。

### 修改3:
- 改什么：补上 `GET /api/v1/quotes/subscribed` 对元大 `GetQuoteList` 的查询支持，或明确区分“本地订阅清单”和“券商端已订阅清单”。
- 为什么改：当前 `/subscribed` 只返回本地 SQLite 清单，可能与券商端不一致。
- 预期结果：客户端可以同时查看本地清单和券商端实际已订阅清单。

### 修改4:
- 改什么：完善 `replace` 订单对“同时改价+改量”的处理。
- 为什么改：M4 review 已指出同时传 `new_price` 和 `new_quantity` 时只发改价 `TradeKind=07`。
- 预期结果：如果同时改价改量，明确拒绝或拆成两次操作，避免静默丢失其中一个变更。

### 修改5:
- 改什么：整理 M1–M5 中所有“待 UAT 验证”的验收点，形成真实联调清单。
- 为什么改：拿到 UAT 权限后需要按清单逐项验证登录、查询、交易、行情、回报。
- 预期结果：新增 `docs/uat-checklist.md`，包含账号、环境、IP、凭据、验证步骤和预期结果。

### 影响文件
- `src/stock_broker_tw/state/store.py`
- `src/stock_broker_tw/service/quote.py`
- `src/stock_broker_tw/broker/quote.py`
- `src/stock_broker_tw/api/http.py`
- `src/stock_broker_tw/broker/service.py`
- `docs/uat-checklist.md`
- `tests/`

---

## 功能2: 按 FunctionID 的统一限流器

### 修改1:
- 改什么：把 M3 查询限流、M4 交易限流、M5 订阅限流统一到一个按 FunctionID 的限流服务。
- 为什么改：目前 `QueryService`、`QuoteService`、`BrokerService` 各自创建 `RateLimiter`，规则分散且可能遗漏。
- 预期结果：所有元大 API 调用都经过统一限流，按 FunctionID 和账户维度计数。

### 修改2:
- 改什么：补充交易类限流：同 FunctionID 每秒 10 次、单次最多 30 笔。
- 为什么改：元大 API 对交易类有明确限制，超限会被暂停服务。
- 预期结果：下单/撤单/改价超过限制时返回 429。

### 修改3:
- 改什么：为限流器增加指标和审计，记录被拒绝的 FunctionID。
- 为什么改：便于观察是否接近元大限制。
- 预期结果：`/metrics` 能看到限流拒绝次数，审计中有记录。

### 影响文件
- `src/stock_broker_tw/risk/rate_limit.py`
- `src/stock_broker_tw/service/query.py`
- `src/stock_broker_tw/service/quote.py`
- `src/stock_broker_tw/broker/service.py`
- `src/stock_broker_tw/config.py`
- `tests/`

---

## 功能3: 自动熔断与手动 panic

### 修改1:
- 改什么：新增自动熔断器，连续 N 次 adapter 调用失败或超时后自动进入熔断状态。
- 为什么改：避免在券商端异常时继续发送交易请求，保护账户和系统。
- 预期结果：熔断后写接口返回 503，只读/行情接口仍可用。

### 修改2:
- 改什么：将手动 panic 从 `RiskConfig.panic` 提升为运行时开关，支持 API 动态开启/关闭。
- 为什么改：目前 panic 只能改配置重启，紧急情况下不够快。
- 预期结果：新增 `POST /api/v1/control/panic` 和 `POST /api/v1/control/resume`。

### 修改3:
- 改什么：熔断状态写入 SQLite 或内存状态，并在 `/health` 和 `/metrics` 中暴露。
- 为什么改：运维需要快速看到当前是否熔断。
- 预期结果：健康检查包含 `panic`、`circuit_breaker_open`、最近失败原因。

### 影响文件
- `src/stock_broker_tw/risk/circuit_breaker.py`（新增）
- `src/stock_broker_tw/risk/__init__.py`
- `src/stock_broker_tw/api/http.py`
- `src/stock_broker_tw/main.py`
- `src/stock_broker_tw/config.py`
- `tests/`

---

## 功能4: 崩溃恢复与对账增强

### 修改1:
- 改什么：增强启动恢复流程，支持对本地 `stock_orders` 与 `orders` 表统一对账。
- 为什么改：当前恢复主要依赖 M3 的 `orders` 表，M4 新增 `stock_orders` 后需要统一。
- 预期结果：启动时能同时恢复 M3/M4 的订单数据，状态一致。

### 修改2:
- 改什么：增加“恢复失败/未知订单”的人工确认接口。
- 为什么改：无法自动判定的订单不应静默丢失。
- 预期结果：新增 `GET /api/v1/recovery/unresolved` 和 `POST /api/v1/recovery/{client_order_id}/resolve`。

### 修改3:
- 改什么：把恢复结果写入审计，并在 `/health` 中返回最近恢复摘要。
- 为什么改：运维需要知道服务重启后是否对账成功。
- 预期结果：健康检查包含 `last_recovery` 信息。

### 影响文件
- `src/stock_broker_tw/state/recovery.py`
- `src/stock_broker_tw/state/store.py`
- `src/stock_broker_tw/api/http.py`
- `src/stock_broker_tw/main.py`
- `tests/`

---

## 功能5: 通知模块

### 修改1:
- 改什么：新增 `src/stock_broker_tw/notify.py`，支持至少一种 webhook 通知（飞书/钉钉/企业微信/Telegram）。
- 为什么改：订单成功/失败、风控拒绝、熔断、恢复异常需要主动告警。
- 预期结果：配置 webhook 后，关键事件能发送通知。

### 修改2:
- 改什么：定义通知事件与消息模板：
  - 订单状态变化
  - 风控拒绝
  - 熔断/恢复
  - 启动恢复异常
  - 每日对账摘要
- 为什么改：避免通知内容随意，便于阅读和告警。
- 预期结果：每个事件有固定标题和关键字段。

### 修改3:
- 改什么：将通知模块接入 `BrokerService`、`RiskEngine`、`CircuitBreaker`、`Recovery`。
- 为什么改：关键事件发生时自动通知。
- 预期结果：不需要手动查看日志也能知道异常。

### 影响文件
- `src/stock_broker_tw/notify.py`
- `src/stock_broker_tw/config.py`
- `src/stock_broker_tw/broker/service.py`
- `src/stock_broker_tw/risk/circuit_breaker.py`
- `src/stock_broker_tw/state/recovery.py`
- `tests/`

---

## 功能6: 端到端测试与部署文档

### 修改1:
- 改什么：新增端到端测试，使用 FakeAdapter 覆盖“登录 → 下单 → 回报 → 状态更新 → WebSocket 推送”完整链路。
- 为什么改：确保核心链路在真实 UAT 前已通过模拟验证。
- 预期结果：`pytest` 能跑通完整交易闭环。

### 修改2:
- 改什么：编写部署文档 `docs/deploy.md`，说明：
  - 环境要求
  - `uv sync` 安装
  - 配置 `config/syz.toml` 或 `.env`
  - 启动命令
  - 升级步骤
  - 常见问题
- 为什么改：方便自己和团队后续部署。
- 预期结果：按文档可以从零启动服务。

### 修改3:
- 改什么：确认并保持纯 Python 项目结构，移除或忽略 Rust 残留。
- 为什么改：项目已确定为 Python + uv，避免混淆。
- 预期结果：`Cargo.toml` / `Cargo.lock` / Rust `src` 残留不再存在或被明确忽略。

### 影响文件
- `tests/test_e2e.py`
- `docs/deploy.md`
- `README.md`
- `pyproject.toml`
- `.gitignore`

---

## 测试计划
- 单元测试：
  - trades 多笔成交不覆盖。
  - quote_subscriptions 支持 index_flag。
  - replace 同时改价改量的处理。
  - 统一限流器按 FunctionID/账户计数。
  - 自动熔断开启/恢复。
  - 通知消息格式化与发送。
- 集成测试：
  - FakeAdapter 端到端：登录 → 下单 → 回报 → WebSocket。
  - panic/resume API。
  - recovery unresolved/resolve API。
  - 限流 429、熔断 503。
- 回归测试：
  - M1–M5 全部测试继续通过。
  - 现有 HTTP/WebSocket 接口行为不破坏。
- 边界条件测试：
  - 同一委托多笔成交。
  - 同一 watchlist 不同 index_flag。
  - replace 同时改价改量。
  - 熔断后恢复。
  - 恢复时遇到未知订单。
  - 通知 webhook 不可达时不影响主流程。

## 验收标准
- [ ] M1–M5 遗留缺口已补齐，且对应测试通过。
- [ ] 所有元大 API 调用都经过统一限流，超限返回 429。
- [ ] 连续失败或 adapter 异常时自动熔断，写接口被拒绝。
- [ ] 服务重启后能从未完成订单与当日回报恢复状态。
- [ ] 关键事件能通过通知模块发送到 webhook。
- [ ] 端到端测试覆盖核心交易闭环。
- [ ] 文档说明如何用 uv 安装、配置、启动和升级。
- [ ] M1–M5 全部单元测试继续通过。

## 兼容性检查
- 是否影响现有行为：不影响 M1 CLI、M2 会话、M3 只读、M4 交易、M5 行情接口；新增接口均为追加。
- 是否需要兼容旧接口/旧数据：`trades` 表结构变更和 `quote_subscriptions` 增加字段需要做 SQLite 迁移；`stock_orders` 表保持兼容。
- 是否存在 break userspace 风险：如果调整 `/api/v1/quotes/subscribed` 返回结构或 replace 行为，需要提供迁移说明；其余新增接口不破坏现有调用。

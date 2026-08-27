# PLAN

## 背景

- 当前问题：元大 SPARK API 是 .NET 元件且事件驱动异步，直接给策略/客户端使用很困难；没有统一 HTTP/WebSocket 接口，没有订单状态机、幂等、限流、风控、审计、持久化和恢复机制。
- 为什么这是个真实问题：策略系统需要稳定调用券商 API，若每次交易都直接操作 `YuantaSparkAPI.dll`，会面临重复下单、回报丢失、超限暂停、无法追溯等问题；单账户场景虽然简单，但生产化所需的服务封装、状态管理和安全控制仍然必不可少。
- 为什么现在要做：已获得元大 API 元件与官方范例，测试环境账号可用；当前项目处于早期，正好以“单账户、本土股票、Python + uv”的最小闭环落地，后续再扩展其他品种和功能。

## 目标

- 本次要解决什么：
  - 用 Python + uv 搭建 broker server，直接通过 `pythonnet` 调用元大 SPARK API。
  - 提供 HTTP JSON API 与 WebSocket 实时推送。
  - 覆盖单账户本土股票核心闭环：登录、行情、下单/撤单/改量/改价、库存/资金/损益查询、委托/成交/即时回报。
  - 内置订单状态机、幂等、串行化、限流、风控、审计、持久化、崩溃恢复。
- 不解决什么：
  - 不实现期货、期权、海外股票/期货、复式单。
  - 不实现条件单/演算法单。
  - 不实现多账户并发管理。
  - 不替代券商合规与风控系统。
  - 不做低延迟高频交易优化。

## 约束

- 相容性要求：
  - Python 版本 >= 3.11，建议 3.12。
  - 依赖 `pythonnet`，需能加载 .NET 8 的 `YuantaSparkAPI.dll`。
  - 需要兼容 Windows 式登录（帐号+密码）与 macOS/Linux 式登录（Pfx 凭据+帐号+密码）。
  - 对外 API 响应格式统一为 `{ "code": 0, "message": "ok", "data": ... }`。
- 性能要求：
  - 单账户场景下请求应串行化，避免并发操作同一连接。
  - 必须遵守元大 API 限制：行情/帐务每秒 3 次、K 线每秒 1 次、交易每秒 10 次、订阅每秒 10 次。
  - 下单接口应在合理时间内返回受理结果，异步回报通过 WebSocket 推送。
- 可维护性要求：
  - 使用 uv 管理依赖与锁文件。
  - 模块按 `api / broker / yuanta / engine / risk / state / audit / notify / metrics` 划分。
  - 元大 .NET 对象转换集中在 `yuanta/serializer.py`，业务层不直接依赖 .NET 类型。
  - 关键流程要有日志、审计和测试。
- 明确不能 break userspace 的点：
  - 已定义的 HTTP API 路径与响应结构不能随意变更；如必须调整，需要提供迁移路径。
  - `client_order_id` 幂等语义不能破坏：同一 ID 重复请求必须返回已有状态，不能重复下单。
  - `BasketNo` 作为证券单 `client_order_id` 载体的约定不能随意改变。
  - WebSocket 事件类型不能随意改名；新增事件只能追加。

## 里程碑

### Milestone 1: 环境与 Yuanta Adapter

#### 目标
- 建立 Python + uv 项目骨架。
- 跑通元大 API 的 Open / Login / LogOut / Close。
- 验证 `OnResponse` 事件能够被 Python 接收并解析。

#### 交付物
- `pyproject.toml`、`uv.lock`、`.python-version`。
- `src/stock_broker_tw/yuanta/loader.py`：加载 pythonnet 与 DLL。
- `src/stock_broker_tw/yuanta/adapter.py`：封装 Open/Login/LogOut/Close。
- `src/stock_broker_tw/yuanta/serializer.py`：.NET 对象转 dict。
- `src/stock_broker_tw/yuanta/events.py`：OnResponse 事件队列。
- 一个可运行的 CLI/脚本，用于在测试环境验证登录。

#### 验收标准
- `uv sync` 能成功安装依赖。
- 测试环境账号 `S98875005091 / 1234` 能成功 Open 并 Login。
- 能收到 `Login` 的 `OnResponse` 并解析出账号/姓名。
- LogOut / Close 后进程能正常退出，无残留线程。

#### 风险
- `pythonnet` 与 .NET 8 的版本兼容性问题。
- macOS/Linux 需要 Pfx 凭据路径，环境差异可能导致登录失败。
- `OnResponse` 回调线程与 Python 主线程的交互需要正确处理。

---

### Milestone 2: 基础服务与会话

#### 目标
- 提供 FastAPI HTTP 服务。
- 实现健康检查、指标、会话登录/登出/状态接口。
- 建立配置加载、结构化日志、审计基础。

#### 交付物
- `src/stock_broker_tw/main.py`：uvicorn 入口。
- `src/stock_broker_tw/config.py`：pydantic-settings 配置。
- `src/stock_broker_tw/api/http.py`：FastAPI 路由。
- `src/stock_broker_tw/api/ws.py`：WebSocket 基础连接。
- `src/stock_broker_tw/audit.py`、`src/stock_broker_tw/metrics.py`。
- `GET /health`、`GET /metrics`、`POST /api/v1/session/login`、`POST /api/v1/session/logout`、`GET /api/v1/session/status`。

#### 验收标准
- 服务启动后 `/health` 返回正常状态。
- 通过 API 可以登录/登出，状态接口能反映当前连接状态。
- 日志与审计中能看到登录请求和结果，密码不落明文。
- `/metrics` 能输出 Prometheus 文本格式。

#### 风险
- FastAPI 异步事件循环与 .NET 事件线程的桥接复杂度。
- token 鉴权若实现不当会影响后续所有接口。
- 配置中凭据泄露风险。

---

### Milestone 3: 只读能力

#### 目标
- 实现本土股票相关的只读查询 API。
- 打通元大查询类 API 的请求/响应闭环。

#### 交付物
- 股票库存：`GetStoreSummary` → `GET /api/v1/positions`
- 银行余额：`GetBankBalance` → `GET /api/v1/account/balance`
- 交割款：`GetStkTransactionOutlay` → `GET /api/v1/account/settlement`
- 未实现/已实现损益、冲销明细
- 即时回报查询：`GetRealReport`、`GetRealReportMerge`
- 委託成交综合回报：`GetOrderTradeReport` → `GET /api/v1/reports/order-trade`
- 本地 SQLite 状态表与首次启动恢复逻辑

#### 验收标准
- 测试环境能查询到股票库存/银行余额/交割款。
- 委托与成交列表能通过 API 返回结构化 JSON。
- SQLite 中能持久化最近一次快照与订单/回报数据。
- 查询类接口在限流范围内稳定运行。

#### 风险
- 元大测试环境部分账号可能没有银行余额权限。
- 查询返回字段多，序列化映射容易遗漏。
- 启动恢复对账依赖回报数据完整性。

---

### Milestone 4: 交易闭环

#### 目标
- 实现本土股票下单、撤单、改量、改价。
- 实现订单状态机、幂等、串行队列和基础风控。
- WebSocket 推送订单状态与即时回报。

#### 交付物
- `POST /api/v1/orders/stock`：支持 `action=new/replace/cancel`。
- `src/stock_broker_tw/engine/state.py`：订单状态机。
- `src/stock_broker_tw/engine/queue.py`：交易串行队列。
- `src/stock_broker_tw/risk/rules.py`：价格/数量/金额/黑名单风控。
- `src/stock_broker_tw/broker/service.py`：下单/撤单/改量/改价业务逻辑。
- WebSocket 事件：`order.updated`、`real_report`、`real_report_merge`。

#### 验收标准
- 测试环境能成功下一笔股票买单。
- 使用 `client_order_id` 重复提交同一请求不会重复下单。
- 能对未成交委托执行撤单，状态变为已撤。
- 风控拒绝时返回明确错误，并写入审计。
- 回报到达后订单状态能自动更新并通过 WebSocket 推送。

#### 风险
- `OnResponse` 与后续 `RR_RealReport` 的时序不一致可能导致状态误判。
- 撤单/改价需要正确的 `OrderNo`、`TradeDate` 等字段，映射错误会导致失败。
- 测试环境成交规则复杂，需要仔细核对状态。

---

### Milestone 5: 行情订阅与 WebSocket

#### 目标
- 实现本土股票行情订阅/取消订阅。
- 实现行情查询 API。
- WebSocket 统一推送行情与回报事件。

#### 交付物
- `POST /api/v1/quotes/subscribe`、`POST /api/v1/quotes/unsubscribe`
- `GET /api/v1/quotes/subscribed`
- `GET /api/v1/quotes/snapshot`
- `GET /api/v1/quotes/ticks`
- `GET /api/v1/quotes/classify-price`
- `GET /api/v1/quotes/kline`
- `GET /api/v1/stocks/info`
- WebSocket 事件：`quote.updated`

#### 验收标准
- 能订阅并收到 `SubscribeWatchlist` / `SubscribeWatchlistAll` / `SubscribeFiveTickA` / `SubscribeStockTick` 等事件。
- 能取消订阅，取消后不再收到对应推送。
- 订阅数量超过上限时被拒绝并提示。
- 行情查询接口能返回结构化数据。
- WebSocket 客户端能同时收到行情与交易回报。

#### 风险
- 订阅事件量大，Python 序列化可能成为瓶颈。
- 不同订阅类型的事件字段差异大，映射工作量大。
- 重复订阅/泄漏订阅会导致元大 API 超限。

---

### Milestone 6: 生产加固

#### 目标
- 完成限流、熔断、恢复、通知、部署与测试。
- 达到可长期运行的本地 broker server 状态。

#### 交付物
- 按 FunctionID 的限流器。
- 自动熔断与手动 panic。
- 崩溃恢复对账流程。
- 通知模块（飞书/钉钉/企业微信/Telegram 至少一种）。
- 端到端测试与部署文档。
- 确认并保持纯 Python 项目结构。

#### 验收标准
- 连续失败或 adapter 异常时自动熔断，写接口被拒绝。
- 服务重启后能从未完成订单与当日回报恢复状态。
- 所有关键操作有审计日志与指标。
- 测试覆盖：幂等、撤单、限流、风控、恢复。
- 文档说明如何用 uv 安装、配置、启动和升级。

#### 风险
- 崩溃恢复依赖元大回报数据，可能遇到无法自动判定的订单。
- 限流参数需要根据元大官方限制仔细配置。
- 通知渠道配置与运维成本。

---

## 兼容性检查

- 对外 HTTP API 路径、请求/响应字段一旦发布，应保持向后兼容。
- 统一响应格式 `{ code, message, data }` 必须保持不变。
- `client_order_id` 幂等语义不能破坏：重复请求返回已有状态。
- `BasketNo = client_order_id` 的映射约定不能随意改变。
- WebSocket 事件类型只能追加，不能删除或改名。
- 如果必须调整接口，先提供新端点并保留旧端点至少一个版本，或提供明确的迁移文档。

## 退出条件

- 什么算完成：
  - 单账户本土股票核心闭环全部跑通：登录、行情、下单/撤单/改量/改价、库存/资金/损益查询、回报推送。
  - 通过测试环境验证，且具备风控、限流、审计、持久化、恢复能力。
  - 文档齐全，可以用 `uv sync` 一键安装并启动。
- 什么情况下应停止继续扩展：
  - 核心闭环未稳定前，不扩展到期货、海外、条件单等多品种。
  - 元大 API 限制频繁触发或测试环境无法稳定验证时，先暂停功能扩展，优先解决稳定性。
  - 如果券商政策或合规风险不允许继续，应立即停止并移除相关自动化能力。

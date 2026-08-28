# Changelog

变更记录

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)

版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)

---

## 版本号说明

- **主版本号（Major）**：不兼容的 API 变更或架构重构
- **次版本号（Minor）**：向后兼容的功能新增（新模块、新页面、新接口）
- **修订号（Patch）**：向后兼容的问题修正、小优化、文档更新

---

## [0.1.0] - 2026-08-28

### Added

#### M1: 环境与 Yuanta Adapter

- 新增 Python + uv 项目骨架：`pyproject.toml`、`uv.lock`、`.python-version`
- 新增 `src/stock_broker_tw/yuanta/loader.py`：加载 pythonnet 与 `YuantaSparkAPI.dll`
- 新增 `src/stock_broker_tw/yuanta/adapter.py`：封装 Open / Login / LogOut / Close / Dispose
- 新增 `src/stock_broker_tw/yuanta/serializer.py`：.NET 对象转 dict
- 新增 `src/stock_broker_tw/yuanta/events.py`：OnResponse 事件队列与 asyncio 桥接
- 新增 `scripts/yuanta_check.py`：测试环境登录验证 CLI
- 自动探测 `DOTNET_ROOT`，解决 macOS Homebrew .NET 无法启动 coreclr 的问题

#### M2: 基础服务与会话

- 新增 FastAPI 服务入口：`src/stock_broker_tw/main.py`
- 新增 `src/stock_broker_tw/config.py`：pydantic-settings 配置加载
- 新增 `src/stock_broker_tw/api/http.py`：HTTP 路由
- 新增 `src/stock_broker_tw/api/ws.py`：WebSocket 基础连接
- 新增 `src/stock_broker_tw/audit.py`：结构化日志与审计
- 新增 `src/stock_broker_tw/metrics.py`：Prometheus 指标
- 新增会话 API：
  - `POST /api/v1/session/login`
  - `POST /api/v1/session/logout`
  - `GET /api/v1/session/status`
- 新增健康检查 `GET /health`
- 新增指标接口 `GET /metrics`
- 新增 Bearer Token 鉴权

#### M3: 只读能力

- 新增 `src/stock_broker_tw/service/query.py`：只读查询编排
- 新增 `src/stock_broker_tw/state/store.py`：SQLite 状态存储
- 新增 `src/stock_broker_tw/state/recovery.py`：启动恢复对账
- 新增 `src/stock_broker_tw/risk/rate_limit.py`：按 FunctionID 限流
- 新增只读 HTTP API：
  - `GET /api/v1/positions`
  - `GET /api/v1/account/balance`
  - `GET /api/v1/account/settlement`
  - `GET /api/v1/pnl/unrealized`
  - `GET /api/v1/pnl/realized`
  - `GET /api/v1/pnl/reversal`
  - `GET /api/v1/reports/real`
  - `GET /api/v1/reports/real-merge`
  - `GET /api/v1/reports/order-trade`
- SQLite 支持快照、委托、成交、回报持久化

#### M4: 交易闭环

- 新增 `src/stock_broker_tw/engine/state.py`：订单领域模型与状态机
- 新增 `src/stock_broker_tw/engine/queue.py`：单账户交易串行队列
- 新增 `src/stock_broker_tw/engine/report_handler.py`：回报驱动状态更新
- 新增 `src/stock_broker_tw/broker/service.py`：下单 / 撤单 / 改量 / 改价业务
- 新增 `src/stock_broker_tw/risk/rules.py`：风控规则
- 新增 `POST /api/v1/orders/stock`
- 新增 `GET /api/v1/orders`
- 新增 `GET /api/v1/orders/{client_order_id}`
- `client_order_id` 幂等控制，避免重复下单
- WebSocket 支持 `order.updated`、`real_report`、`real_report_merge`

#### M5: 行情订阅与 WebSocket

- 新增 `src/stock_broker_tw/broker/quote.py`：行情订阅模型
- 新增 `src/stock_broker_tw/service/quote.py`：订阅 / 取消订阅服务
- 新增行情 API：
  - `POST /api/v1/quotes/subscribe`
  - `POST /api/v1/quotes/unsubscribe`
  - `GET /api/v1/quotes/subscribed`
  - `GET /api/v1/quotes/snapshot`
  - `GET /api/v1/quotes/ticks`
  - `GET /api/v1/quotes/classify-price`
  - `GET /api/v1/quotes/kline`
  - `GET /api/v1/stocks/info`
- WebSocket 新增 `quote.updated`
- 新增行情序列化：watchlist、五档、分时、K 线、个股资讯等

#### M6: 生产加固与遗留补齐

- 新增 `src/stock_broker_tw/risk/circuit_breaker.py`：自动熔断器
- 新增手动 Panic / Resume：
  - `POST /api/v1/control/panic`
  - `POST /api/v1/control/resume`
- 新增恢复与人工确认 API：
  - `GET /api/v1/recovery/unresolved`
  - `POST /api/v1/recovery/{client_order_id}/resolve`
- 新增 `src/stock_broker_tw/notify.py`：Webhook 通知模块
- 支持通用 JSON / 飞书 / 钉钉 / 企业微信 Webhook
- 支持按事件配置报警标题与消息模板
- 修复同一委托多笔成交被覆盖的问题
- 修复 watchlist 订阅 `index_flag` 无法区分的问题
- 补充 `GET /api/v1/quotes/subscribed?source=broker` 券商端订阅查询
- 新增 GitHub Actions CI：pytest + ruff
- 新增 MIT License
- 新增 README、客户端 API 文档、部署文档、UAT 联调清单、CHANGELOG
- 移除随仓库分发的第三方 Spark API SDK，改为用户自行下载放置到 `vendor/yuanta/sparkapi`

### Changed

- 项目从 Rust 骨架切换为 Python + FastAPI + SQLite
- 元大 API 调用统一通过 `YuantaAdapter`，业务层不直接依赖 .NET 类型
- 查询类 API 自动将 `QuoteList` / `StkList` 转为 .NET 对象，并转换 enum 参数
- 同一 `client_order_id` 不允许被不同 action 复用，避免覆盖原订单
- `replace` 同时传 `new_price` 与 `new_quantity` 时明确拒绝，避免静默丢失变更
- 通知模块支持 `[notify.events]` 配置，报警消息不再硬编码
- 默认配置移除本机绝对路径，敏感配置统一放入 `config/` 且不入库

### Fixed

- 修复 macOS Homebrew .NET 未导出 `DOTNET_ROOT` 导致 coreclr 启动失败
- 修复 `adapter.query()` 会消费不相关事件导致 WebSocket 丢事件
- 修复同步 `send_stock_order` 阻塞事件循环的问题
- 修复 `RR_RealReport` 撤单成功状态被误判为 `NEED_MANUAL_REVIEW`
- 修复 `trades` 表同一委托多笔成交互相覆盖
- 修复 `quote_subscriptions` 无法区分同一标的的不同 `index_flag`
- 修复 ruff 误扫 vendor 官方范例的问题

### Security

- HTTP API 默认只监听 `127.0.0.1`
- 支持 Bearer Token 鉴权
- 密码 / 凭据不写入审计日志
- 真实凭据与本地配置不提交到 Git
- 第三方 Spark API SDK 不再随开源仓库分发
- 支持手动 panic 与自动熔断，异常时保护写接口

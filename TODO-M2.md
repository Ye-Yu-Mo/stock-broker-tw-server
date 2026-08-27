# TODO-M2: 基础服务与会话

---

## 目标
- 在 M1 的 Yuanta Adapter 之上，提供 FastAPI HTTP 服务。
- 实现健康检查、指标、会话登录/登出/状态接口。
- 建立配置加载、结构化日志、审计基础。
- 所属 Milestone: M2

## 功能1: FastAPI 服务入口与配置加载

### 修改1:
- 改什么：新增 `src/stock_broker_tw/config.py`，使用 `pydantic-settings` 加载服务配置、元大配置、账户配置、风控/审计等配置。
- 为什么改：统一配置入口，支持 TOML、环境变量和 `.env` 覆盖，避免硬编码。
- 预期结果：启动时能读取 `config/default.toml`，并支持 `YUANTA_*` 环境变量覆盖。

### 修改2:
- 改什么：新增 `src/stock_broker_tw/main.py`，创建 FastAPI app 并启动 uvicorn。
- 为什么改：提供可执行的 ASGI 服务入口。
- 预期结果：执行 `uv run uvicorn stock_broker_tw.main:app` 或 `uv run python -m stock_broker_tw` 可启动服务。

### 修改3:
- 改什么：在 `pyproject.toml` 中补充 `[project.scripts]` 或 uvicorn 启动说明。
- 为什么改：让本地启动命令统一、可复现。
- 预期结果：文档和命令一致，团队可以用同一方式启动服务。

### 影响文件
- `src/stock_broker_tw/config.py`
- `src/stock_broker_tw/main.py`
- `pyproject.toml`
- `config/default.toml`

---

## 功能2: 健康检查与 Prometheus 指标

### 修改1:
- 改什么：新增 `src/stock_broker_tw/metrics.py`，提供 Prometheus 指标对象和采集辅助。
- 为什么改：为后续可观测性打基础，便于监控请求量、成功率、延迟、限流/风控拒绝等。
- 预期结果：`/metrics` 能输出 Prometheus 文本格式。

### 修改2:
- 改什么：新增 `GET /health`，返回服务、Yuanta Adapter、事件队列、审计等健康状态。
- 为什么改：运维和部署检查需要知道服务是否可用。
- 预期结果：服务启动后 `GET /health` 返回结构化 JSON，包含 `status`、`adapter_ready`、`login_status`、`event_queue_size` 等字段。

### 影响文件
- `src/stock_broker_tw/metrics.py`
- `src/stock_broker_tw/api/http.py`
- `src/stock_broker_tw/main.py`

---

## 功能3: 会话登录/登出/状态 API

### 修改1:
- 改什么：在 `src/stock_broker_tw/api/http.py` 新增路由：
  - `POST /api/v1/session/login`
  - `POST /api/v1/session/logout`
  - `GET /api/v1/session/status`
- 为什么改：让外部客户端可以通过 HTTP 控制 Yuanta 登录生命周期，而不是只能使用 CLI。
- 预期结果：可以通过 API 登录、登出，并查询当前连接/登录状态。

### 修改2:
- 改什么：登录接口接收账号密码或 Pfx 凭据，并调用 `YuantaAdapter.login`，异步等待 `Login` 的 `OnResponse`。
- 为什么改：保持 M1 的异步事件模型，让 API 返回真实的登录结果而不是只返回“请求已送出”。
- 预期结果：登录成功后返回账号、姓名等结构化信息；失败时返回明确错误码和消息。

### 修改3:
- 改什么：登出接口调用 `YuantaAdapter.logout`，并清理本地会话状态。
- 为什么改：让客户端可以主动结束会话。
- 预期结果：登出后 `/session/status` 显示未登录。

### 修改4:
- 改什么：状态接口返回 adapter 的 `opened`、`logged_in`、`last_login_result`、`event_queue_size` 等信息。
- 为什么改：方便客户端和运维确认当前会话状态。
- 预期结果：状态信息准确反映当前生命周期。

### 影响文件
- `src/stock_broker_tw/api/http.py`
- `src/stock_broker_tw/api/ws.py`
- `src/stock_broker_tw/main.py`
- `src/stock_broker_tw/cli.py`（如复用登录等待逻辑）

---

## 功能4: 结构化日志与审计基础

### 修改1:
- 改什么：新增 `src/stock_broker_tw/audit.py`，提供审计日志写入能力。
- 为什么改：所有关键操作需要可追溯，尤其是登录请求和结果。
- 预期结果：每次登录/登出都会记录时间、操作类型、结果、请求 ID；密码不落明文。

### 修改2:
- 改什么：配置结构化日志格式，使用 JSON lines 或 key-value 格式输出到 stdout/日志文件。
- 为什么改：便于日志采集、搜索和告警。
- 预期结果：日志中能看到请求、耗时、结果等结构化字段。

### 修改3:
- 改什么：在登录/登出 API 中接入审计，并在返回错误时也记录。
- 为什么改：即使失败也需要留痕。
- 预期结果：审计文件/表中有完整的会话操作记录。

### 影响文件
- `src/stock_broker_tw/audit.py`
- `src/stock_broker_tw/api/http.py`
- `src/stock_broker_tw/config.py`
- `src/stock_broker_tw/main.py`

---

## 功能5: WebSocket 基础连接

### 修改1:
- 改什么：新增 `src/stock_broker_tw/api/ws.py`，提供 `GET /ws` WebSocket 端点。
- 为什么改：为后续实时回报、行情推送打基础。
- 预期结果：客户端能建立 WebSocket 连接，并收到欢迎/心跳消息。

### 修改2:
- 改什么：在 WebSocket 中接入事件队列的异步消费，后续 `RR_RealReport` 等事件可广播给客户端。
- 为什么改：M2 先建立通道，M3/M4 再接入实际交易回报和行情。
- 预期结果：事件队列有事件时，已连接的 WebSocket 客户端能收到事件。

### 影响文件
- `src/stock_broker_tw/api/ws.py`
- `src/stock_broker_tw/main.py`
- `src/stock_broker_tw/yuanta/events.py`

---

## 功能6: Token 鉴权

### 修改1:
- 改什么：在 FastAPI 中增加简单 Bearer Token 鉴权依赖。
- 为什么改：服务默认只监听本机，但仍需要防止本机其他进程随意调用交易接口。
- 预期结果：未带 token 的请求返回 401；带正确 token 的请求正常通过。

### 修改2:
- 改什么：`/health` 和 `/metrics` 可匿名访问或单独配置。
- 为什么改：监控探活通常不带 token，避免运维复杂度。
- 预期结果：健康检查和指标无需鉴权，业务 API 需要鉴权。

### 影响文件
- `src/stock_broker_tw/api/http.py`
- `src/stock_broker_tw/config.py`
- `src/stock_broker_tw/main.py`

---

## 测试计划
- 单元测试：
  - `config`：默认值、环境变量覆盖、TOML 加载。
  - `audit`：审计记录写入、密码脱敏。
  - `metrics`：指标注册与文本输出。
  - 登录/登出 service 层的状态转换。
- 集成测试：
  - 使用 `TestClient` 启动 FastAPI app，调用 `/health`、`/metrics`。
  - 使用 FakeAdapter 验证 `/session/login`、`/session/logout`、`/session/status` 的完整流程。
  - 验证未带 token 的请求返回 401。
- 回归测试：
  - M1 的 `pytest` 全部继续通过。
  - CLI 登录验证脚本仍可运行。
- 边界条件测试：
  - 重复登录返回明确错误。
  - 未 Open 就 Login。
  - 未 Login 就 Logout。
  - token 错误/缺失。
  - `/health` 在 adapter 未初始化时仍能返回降级状态。

## 验收标准
- [ ] 服务启动后 `GET /health` 返回正常状态。
- [ ] 通过 API 可以登录/登出，状态接口能反映当前连接状态。
- [ ] 日志与审计中能看到登录请求和结果，密码不落明文。
- [ ] `GET /metrics` 能输出 Prometheus 文本格式。
- [ ] 未带 token 的 API 请求返回 401。
- [ ] M1 的单元测试全部通过。

## 兼容性检查
- 是否影响现有行为：不影响 M1 CLI；CLI 仍可直接运行。
- 是否需要兼容旧接口/旧数据：暂无旧 HTTP API；SQLite 状态库尚未引入，无需迁移。
- 是否存在 break userspace 风险：新增 HTTP API 不会破坏现有 CLI；但一旦对外发布，后续接口变更需保持向后兼容。

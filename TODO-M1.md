# TODO-M1: 环境与 Yuanta Adapter

---

## 目标
- 建立 Python + uv 项目骨架，并锁定依赖。
- 跑通元大 API 的 Open / Login / LogOut / Close。
- 验证 `OnResponse` 事件能够被 Python 接收并解析。
- 所属 Milestone: M1

## 功能1: uv 项目骨架与依赖锁定

### 修改1:
- 改什么：完善 `pyproject.toml`，声明项目元数据、Python 版本、运行依赖和开发依赖。
- 为什么改：让项目可以通过 `uv sync` 一键安装环境，统一团队/部署环境。
- 预期结果：`uv sync` 能根据 `pyproject.toml` 成功创建虚拟环境并安装依赖。

### 修改2:
- 改什么：生成 `uv.lock`，锁定所有传递依赖版本。
- 为什么改：保证不同机器安装的依赖版本一致，避免“本地能跑、部署不能跑”。
- 预期结果：仓库中存在 `uv.lock`，`uv sync --frozen` 可复现安装。

### 修改3:
- 改什么：添加 `.python-version` 指定 Python 版本。
- 为什么改：`uv` 会根据该文件自动选择 Python 版本。
- 预期结果：`uv sync` 使用 Python 3.12 创建环境。

### 影响文件
- `pyproject.toml`
- `uv.lock`
- `.python-version`
- `.gitignore`

---

## 功能2: YuantaAdapter 基础封装

### 修改1:
- 改什么：新增 `src/stock_broker_tw/yuanta/loader.py`，负责加载 pythonnet、添加 DLL 路径并 `clr.AddReference("YuantaSparkAPI")`。
- 为什么改：将 .NET 加载细节隔离在单独模块，避免业务代码直接依赖 pythonnet 环境。
- 预期结果：能成功 import `YuantaSparkAPITrader` 及相关枚举/对象。

### 修改2:
- 改什么：新增 `src/stock_broker_tw/yuanta/adapter.py`，封装 `YuantaSparkAPITrader` 的 Open / Login / LogOut / Close / Dispose。
- 为什么改：提供稳定的 Python 接口，隐藏 .NET 对象和异步事件细节。
- 预期结果：可以通过 Python 调用 Open、Login、LogOut、Close，并在测试环境跑通。

### 修改3:
- 改什么：新增 `src/stock_broker_tw/yuanta/serializer.py`，将 `OnResponse` 中的 .NET 对象转换为 dict/list。
- 为什么改：业务层只处理普通 Python 数据，不直接操作 .NET 类型。
- 预期结果：`LoginResult`、`Status`、`LoginData` 等对象能转换为结构化 JSON 友好的 dict。

### 影响文件
- `src/stock_broker_tw/yuanta/loader.py`
- `src/stock_broker_tw/yuanta/adapter.py`
- `src/stock_broker_tw/yuanta/serializer.py`

---

## 功能3: OnResponse 事件队列与异步桥接

### 修改1:
- 改什么：新增 `src/stock_broker_tw/yuanta/events.py`，提供线程安全的 `OnResponse` 事件队列。
- 为什么改：.NET 回调可能运行在非主线程，需要把事件安全地传给 asyncio 主循环。
- 预期结果：事件能进入队列，并由 asyncio 任务消费和分发。

### 修改2:
- 改什么：在 `adapter.py` 中注册 `OnResponseEventHandler`，将原始事件写入队列。
- 为什么改：让 Adapter 成为唯一的事件入口，后续 API 层和 Engine 统一订阅。
- 预期结果：`Login` 的响应到达后能通过事件队列被 Python 侧获取。

### 影响文件
- `src/stock_broker_tw/yuanta/events.py`
- `src/stock_broker_tw/yuanta/adapter.py`

---

## 功能4: 可运行 CLI 登录验证脚本

### 修改1:
- 改什么：新增 `scripts/yuanta_check.py` 或 `python -m stock_broker_tw.cli`，用于加载配置并执行 Open → Login → 等待 Login 响应 → LogOut → Close。
- 为什么改：Milestone 1 需要一个不依赖 Web 服务的最小验证入口。
- 预期结果：在测试环境执行脚本后，能看到登录成功、账号/姓名等解析结果，进程能干净退出。

### 修改2:
- 改什么：提供示例配置或环境变量读取方式，支持账号密码登录和 macOS/Linux 凭据登录。
- 为什么改：不同平台登录方式不同，CLI 需要兼容两种模式。
- 预期结果：Windows/macOS 两种模式都能通过配置切换。

### 影响文件
- `scripts/yuanta_check.py`
- `src/stock_broker_tw/__main__.py`（可选）
- `config/default.toml` 或 `.env.example`

---

## 测试计划
- 单元测试：
  - `serializer`：用构造的 .NET 对象或等价 dict 验证 Login 结果序列化。
  - `events`：验证事件队列线程安全、顺序消费、超时获取。
- 集成测试：
  - 使用测试环境账号执行 Open → Login → LogOut → Close，验证完整生命周期。
  - 验证能收到 `Login` 的 `OnResponse` 并解析出账号/姓名。
- 回归测试：
  - 重复运行 CLI 不应残留 .NET 线程或导致进程无法退出。
  - 重复 Login 应被 Adapter 拒绝或明确报错。
- 边界条件测试：
  - 错误账号/密码返回明确错误。
  - 未 Open 就 Login 的行为。
  - 未 Login 就 LogOut / Close 的行为。
  - macOS/Linux 凭据路径不存在时的错误处理。

## 验收标准
- [ ] `uv sync` 能成功安装依赖并生成 `.venv`。
- [ ] 测试环境账号 `S98875005091 / 1234` 能成功 Open 并 Login。
- [ ] 能收到 `Login` 的 `OnResponse` 并解析出账号/姓名。
- [ ] LogOut / Close 后进程能正常退出，无残留线程。
- [ ] 单元测试通过：serializer、events。
- [ ] CLI 支持账号密码登录，并预留 Pfx 凭据登录参数。

## 兼容性检查
- 是否影响现有行为：当前只有项目骨架，暂无线上行为，不影响存量用户。
- 是否需要兼容旧接口/旧数据：无旧接口；SQLite 状态库尚未引入，无需数据迁移。
- 是否存在 break userspace 风险：不涉及对外 HTTP API；但后续若调整 `YuantaAdapter` 的方法签名，需要同步更新 CLI 和测试。

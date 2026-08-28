# 部署文档

## 环境要求

- Python 3.11+（项目使用 3.12 开发）
- [uv](https://docs.astral.sh/uv/) 包管理器
- macOS / Linux（元大 Spark API 通常提供 macOS/Linux .NET 绑定）
- 元大 Spark API 目录：`vendor/yuanta/sparkapi`

> 第三方 Spark API SDK **不随仓库分发**。请向元大营业部申请后，将解压内容放到 `vendor/yuanta/sparkapi/`。

## 1. 安装依赖

```bash
uv sync
```

如需更新锁定文件：

```bash
uv lock
```

## 2. 配置

复制或编辑配置文件。推荐使用 `config/syz.toml` 作为本地真实配置：

```bash
cp config/default.toml config/syz.toml
# 然后编辑 config/syz.toml
```

关键配置项：

```toml
[server]
host = "127.0.0.1"
port = 8000
api_token = "your-token"

[yuanta]
environment = "UAT"          # UAT 或 PROD
spark_api_dir = "vendor/yuanta/sparkapi"
login_timeout = 15.0

[account]
account = "S98875005091"
password = "your-password"
pfx_path = "/absolute/path/to/your.pfx"
pfx_pass = "your-pfx-password"

[state]
db_path = "state/yuanta.db"

[query]
timeout = 10.0
rate_limit_per_second = 3
rate_limit_per_minute = 600

[quote]
timeout = 10.0
max_per_request = 200
max_total_subscriptions = 2000
rate_limit_per_second = 10

[risk]
panic = false
max_order_qty = 100000
max_order_amount = 100000000.0
max_price_deviation_pct = 10.0
order_timeout = 10.0
circuit_failure_threshold = 5
circuit_cooldown_seconds = 30.0

[rate_limit]
query_per_second = 3
query_per_minute = 600
quote_per_second = 10
trade_per_second = 10
trade_max_batch = 30

[notify]
enabled = false
webhook_url = ""
webhook_type = "feishu"   # generic / feishu / dingtalk / wecom
timeout = 3.0
```

也可以通过环境变量覆盖：

```bash
export YUANTA_SERVER__API_TOKEN=your-token
export YUANTA_ACCOUNT__ACCOUNT=S98875005091
export YUANTA_NOTIFY__WEBHOOK_URL=https://example.com/hook
```

## 3. 启动

```bash
uv run stock-broker-tw
# 或
uv run python -m stock_broker_tw
```

默认监听 `127.0.0.1:8000`。使用 `config/syz.toml` 时，通过 `YUANTA_CONFIG` 指定：

```bash
YUANTA_CONFIG=config/syz.toml uv run stock-broker-tw
```

## 4. 验证

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/metrics
```

带 token 访问接口示例：

```bash
curl -H "Authorization: Bearer your-token" http://127.0.0.1:8000/api/v1/session/status
```

## 5. 升级步骤

1. 备份状态库与审计日志：`cp state/yuanta.db state/yuanta.db.bak`
2. 拉取新代码，执行 `uv sync`
3. 查看 `docs/uat-checklist.md`，确认兼容性
4. 启动新版本，观察 `/health` 的 `last_recovery`
5. 如遇到数据库结构变更，`StateStore` 启动时会自动迁移 `trades` 与 `quote_subscriptions`

## 6. 常见问题

### 登录失败 / 找不到 Spark API

- 确认 `vendor/yuanta/sparkapi` 存在且版本匹配。
- 确认 `pfx_path` 为绝对路径且文件权限可读。

### 429 限流

- 查看 `/metrics` 中 `rate_limited_total` 的 FunctionID。
- 调整 `[rate_limit]` 或 `[query]`、`[quote]`、`[risk]` 对应值。

### 下单 503

- 查看 `/health` 的 `circuit_breaker_open` 和 `last_failure`。
- 连续失败后自动熔断；确认券商端恢复后调用 `POST /api/v1/control/resume` 或等待冷却。

### WebSocket 收不到推送

- 确认使用 `token` 查询参数或 `Authorization: Bearer`。
- 确认登录成功且事件队列正常消费。

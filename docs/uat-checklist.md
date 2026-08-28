# UAT 真实联调清单

> 本文档汇总 M1–M5 中所有“待 UAT 验证”的验收点，以及 M6 生产加固后的联调项目。
> 拿到元大 UAT 权限后，按以下顺序逐项验证。

## 0. 环境与凭据

| 项目 | 值 |
|---|---|
| 环境 | UAT |
| 元大 Spark API 目录 | `vendor/yuanta/sparkapi` |
| 服务地址 | `127.0.0.1:8000` |
| API Token | 由 `config/syz.toml` 或环境变量 `YUANTA_SERVER__API_TOKEN` 配置 |
| 账号 | `config/syz.toml` 中的 `[account]` |
| 凭据 | 密码 / PFX 路径 / PFX 密码，见 `config/syz.toml`（不入库） |

## 1. 启动与登录

- [ ] `uv sync` 后能成功启动服务。
- [ ] `/health` 返回 `adapter_ready=true`、`login_status=false`。
- [ ] `POST /api/v1/session/login` 使用正确账号密码登录成功。
- [ ] 登录后 `GET /api/v1/session/status` 显示 `logged_in=true`。
- [ ] 错误密码登录返回明确错误，不影响后续正确登录。
- [ ] `POST /api/v1/session/logout` 能正常登出。

## 2. 只读查询（M3）

- [ ] `GET /api/v1/positions` 返回库存/持仓。
- [ ] `GET /api/v1/account/balance` 返回银行余额。
- [ ] `GET /api/v1/account/settlement` 返回交割金额。
- [ ] `GET /api/v1/pnl/unrealized` 返回未实现损益。
- [ ] `GET /api/v1/pnl/realized?start_date=YYYY/MM/DD&end_date=YYYY/MM/DD` 返回已实现损益。
- [ ] `GET /api/v1/pnl/reversal` 返回反向损益。
- [ ] `GET /api/v1/reports/real`、`/reports/real-merge`、`/reports/order-trade` 返回回报。
- [ ] 行情快照、分时、分价、K 线、个股资讯接口均返回真实数据。

## 3. 交易（M4）

- [ ] `POST /api/v1/orders/stock` 新单成功，返回 `order_no`。
- [ ] 重复 `client_order_id` 幂等，不重复送单。
- [ ] 撤单成功：`action=cancel` + `order_no`。
- [ ] 改价成功：`action=replace` + `new_price`（不同时传 `new_quantity`）。
- [ ] 改量成功：`action=replace` + `new_quantity`（不同时传 `new_price`）。
- [ ] 同时传 `new_price` 与 `new_quantity` 返回 `REPLACE_BOTH_FIELDS_UNSUPPORTED`。
- [ ] 风控拒绝（黑名单/超量/超金额/panic）不会送单。
- [ ] 自动熔断开启后写接口返回 503，读接口仍可用。

## 4. 行情订阅（M5）

- [ ] `POST /api/v1/quotes/subscribe` 各 `type` 均能订阅。
- [ ] watchlist 使用不同 `index_flag` 能分别订阅/取消。
- [ ] `GET /api/v1/quotes/subscribed` 默认返回本地清单。
- [ ] `GET /api/v1/quotes/subscribed?source=broker` 返回券商端 `GetQuoteList` 实际清单。
- [ ] 同一 symbol 不同 `index_flag` 不互相覆盖。
- [ ] WebSocket 能收到 `quote.updated` 推送。

## 5. 回报与状态闭环（M4/M6）

- [ ] 下单后 WebSocket 收到 `RR_RealReport` 原始事件。
- [ ] 收到 `real_report` / `order.updated` 处理后事件。
- [ ] 部分成交状态为 `PARTIALLY_FILLED`，全部成交为 `FILLED`。
- [ ] 同一委托多笔成交在本地 `trades` 表中全部保留。
- [ ] 重启后 `GET /health` 的 `last_recovery` 显示对账摘要。
- [ ] 无法自动判定的订单出现在 `GET /api/v1/recovery/unresolved`。
- [ ] 通过 `POST /api/v1/recovery/{client_order_id}/resolve` 人工确认后状态更新。

## 6. 运维与告警

- [ ] `/metrics` 包含 `rate_limited_total`、`circuit_breaker_*`。
- [ ] 超过限流时接口返回 429。
- [ ] `POST /api/v1/control/panic` 后下单被拒；`/resume` 后恢复。
- [ ] 配置 webhook 后，订单状态变化/风控拒绝/熔断/恢复异常会收到通知。
- [ ] 按 `docs/deploy.md` 可以从零部署。

## 7. 预期结果记录

联调时建议为每个勾选项记录：
- 请求参数（脱敏）
- 返回/推送内容
- 是否与预期一致
- 备注/问题

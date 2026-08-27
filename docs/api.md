# 元大 SPARK API 整理

> 本文整理自 `docs/API/` 下官方文件與 `vendor/yuanta/sparkapi/YSendOrder.py` 範例。
> 目的是作為 `stock_broker_tw_server` 設計與開發時的 API 對照表。
> 完整欄位、錯誤碼、情境仍以 `docs/API/*.md` 及 `FunctionList.xls` 為準。

## 1. 總覽

| 分類 | 功能 |
|---|---|
| 基礎 | Open / Close / Dispose / SetLogType / SetPMMServerCheck |
| 登入 | Login / LogOut |
| 回應 | OnResponse 事件（查詢、訂閱、系統） |
| 行情訂閱 | SubscribeWatchlist / SubscribeWatchlistAll / SubscribeFiveTickA / SubscribeStockTick / SubscribeMarketInformation / SubscribeStockInformation |
| 行情查詢 | GetQuoteList / GetWatchListAll / GetStockInformation / GetStkTickDetail / GetStkClassifyPrice / GetKLine |
| 證券交易 | SendStockOrder（含下單、改量、取消、改價） |
| 期貨交易 | SendFutureOrder / SendFutureCombined / SendFutureApart |
| 條件/演算法單 | SendAlgoCOOdrStrategy / DeleteAlgoCOOdrStrategy / GetConditionStrategy / GetHisConditionStrategy |
| 帳務庫存 | GetStoreSummary / GetFutStoreSummary / GetOVFutStoreSummary / GetFutSprStore / GetFutInterestStore / GetFutDepositOptimum |
| 損益/資金 | GetUnrealizedGainLossDetail / GetHisRealizedGainLoss / GetStkHistoryReportReversal / GetBankBalance / GetStkTransactionOutlay |
| 回報 | GetRealReport / GetRealReportMerge / GetOrderTradeReport / RR_RealReport / RR_RealReportMerge |
| 其他 | SendPrefundedMargin / SendStockEarmark |

## 2. 環境與連線

- API 為 .NET 8 元件 `YuantaSparkAPI.dll`，官方支援 Windows / Linux / macOS。
- Python 透過 `pythonnet` 載入 .NET Core 後使用；C# 直接參考 `YuantaOneAPI` namespace。
- 測試環境：UAT；正式環境：PROD。
- macOS/Linux 登入需帶憑證路徑與憑證密碼。
- 使用前需向營業員申請 API 權限並開通固定 IP。

### 常用基礎函數

| 函數 | 簽名 | 說明 |
|---|---|---|
| Open | `void Open(enumEnvironmentMode Mode)` | 開啟 API 連線 |
| Close | `void Close()` | 關閉 API 連線 |
| Dispose | `void Dispose()` | 釋放 API 連線 |
| SetLogType | `void SetLogType(enumLogType logType)` | 設定 Log 等級 |
| SetPMMServerCheck | `void SetPMMServerCheck(bool flag)` | 是否檢查 PMM Server |
| Login | `bool Login(Account, Pass)` | 登入（Windows） |
| Login | `bool Login(PfxPath, PfxPass, Account, Pass)` | 登入（macOS/Linux，需憑證） |
| LogOut | `bool LogOut()` | 登出所有 API 登入帳號 |

### 帳號格式

| 種類 | 格式 | 範例 |
|---|---|---|
| 證券 | `S` + 分公司(4) + 帳號(7)，共 11 碼 | `S98875005091` |
| 期貨 | `F` + 分公司(7+3) + 帳號(7)，共 17 碼 | `FF021000P001234567` |

### 測試環境帳號

- 帳號：`S98875005091`，密碼：`1234`
- 測試憑證可從官方下載，密碼為 `yuanta`
- 測試環境有模擬成交/失敗規則，詳見 `docs/API/元大API說明文件 1.md`

## 3. 事件模型 OnResponse

所有 API 呼叫都是**非同步**：函數只回傳 `bool` 表示呼叫是否成功送出，真正的結果由 `OnResponse` 事件回傳。

```text
OnResponseEventHandler(intMark, dwIndex, strIndex, objHandle, objValue)
```

| 參數 | 說明 |
|---|---|
| intMark | 0=系統資訊、1=查詢資訊、2=訂閱資訊 |
| dwIndex | 回應狀態（連線狀態 / 功能錯誤 / 訂閱失敗等） |
| strIndex | 功能名稱字串，例如 `Login`、`SendStockOrder` |
| objHandle | 訂閱時傳入的 Handle |
| objValue | 回傳資料物件，依功能轉型 |

> 重要：`Login` 成功後，系統通常會自動訂閱 `RR_RealReport` / `RR_RealReportMerge`，因此下單後的即時委託/成交回報會以事件方式持續推送。

## 4. 行情 API

### 4.1 行情訂閱

| 函數 | 簽名 | 說明 |
|---|---|---|
| SubscribeWatchlist | `bool SubscribeWatchlist(LoginAcno, List<Watchlist>, Lng)` | 訂閱行情報價表（指定欄位） |
| UnSubscribeWatchlist | `bool UnSubscribeWatchlist(...)` | 取消訂閱 |
| SubscribeWatchlistAll | `bool SubscribeWatchlistAll(LoginAcno, List<WatchlistAll>, Lng)` | 訂閱完整行情報價表 |
| UnSubscribeWatchlistAll | `bool UnSubscribeWatchlistAll(...)` | 取消訂閱 |
| SubscribeFiveTickA | `bool SubscribeFiveTickA(LoginAcno, List<FiveTickA>, Lng)` | 訂閱最佳五檔 |
| UnSubscribeFiveTickA | `bool UnSubscribeFiveTickA(...)` | 取消訂閱 |
| SubscribeStockTick | `bool SubscribeStockTick(LoginAcno, List<StockTick>, Lng)` | 訂閱分時明細 |
| UnSubscribeStockTick | `bool UnSubscribeStockTick(...)` | 取消訂閱 |
| SubscribeMarketInformation | `bool SubscribeMarketInformation(LoginAcno, List<MarketInformation>, Lng)` | 訂閱個股盤前資訊 |
| UnSubscribeMarketInformation | `bool UnSubscribeMarketInformation(...)` | 取消訂閱 |
| SubscribeStockInformation | `bool SubscribeStockInformation(LoginAcno, List<StockOtherInformation>, Lng)` | 訂閱個股其他資訊 |
| UnSubscribeStockInformation | `bool UnSubscribeStockInformation(...)` | 取消訂閱 |

訂閱事件以 `strIndex` 區分，例如 `SubscribeWatchlist`、`SubscribeWatchlistAll`、`SubscribeStockTick`、`SubscribeFiveTickA`、`SubscribeMarketInformation`、`SubscribeStockInformation`。

### 4.2 行情查詢

| 函數 | 簽名 | 說明 |
|---|---|---|
| GetQuoteList | `bool GetQuoteList(Account)` | 查詢目前已訂閱商品清單 |
| GetWatchListAll | `bool GetWatchListAll(Account, List<Quote>, Lng)` | 查詢報價表（整包） |
| GetStockInformation | `bool GetStockInformation(Account, List<StkInfo>, lng)` | 查詢標的資訊 |
| GetStkTickDetail | `bool GetStkTickDetail(Account, MarketType, StkCode, SelectType, STime, ETime, LastCount, lng)` | 查詢當日分時明細 |
| GetStkClassifyPrice | `bool GetStkClassifyPrice(Account, MarketType, StkCode, lng)` | 查詢分價量 |
| GetKLine | `bool GetKLine(Account, KLineType, MarketType, StkCode, SDate, EDate, lng)` | 查詢 K 線 |

主要市場類別：

| 列舉 | 值 | 說明 |
|---|---|---|
| TWSE | 1 | 上市 |
| TWOTC | 2 | 上櫃 |
| TAIFEX | 3 | 期貨 |
| TWEMERGING | 4 | 興櫃 |
| TWSEODD | 5 | 盤中零股-上市 |
| TWOTCODD | 6 | 盤中零股-上櫃 |
| SGX / CME / OSE / HKFE ... | 202+ | 海外交易所 |

## 5. 交易 API

### 5.1 國內證券下單 / 改量 / 取消 / 改價

```text
bool SendStockOrder(LoginAcno, List<StockOrder>, lng)
```

`StockOrder` 關鍵欄位：

| 欄位 | 說明 |
|---|---|
| Identify | 自訂識別碼，回應時對應 |
| Account | 下單帳號 |
| OrderNo | 委託書編號；**新單不需填，取消/改量/改價必填** |
| TradeDate | yyyy/MM/dd |
| APCode | 0=一般、2=零股、4=盤中零股、7=盤後 |
| TradeKind | 00=委託單、03=改量、04=取消、07=改價 |
| OrderType | "0"=現貨、"3"=融資、"4"=融券、"5"=策略借券、"6"=避險借券、"9"=現股當沖 |
| StkCode | 股票代號 |
| BuySell | B=買、S=賣 |
| PriceFlag | H=漲停、L=跌停、-=平盤、空白=限價、M=市價 |
| Price | 委託價格，非限價填 0 |
| BasketNo | 使用者自訂欄位，最多 32 英數字（可作為 `client_order_id` 載體） |
| OrderQty | 委託數量 |
| Time_in_force | 0=ROD、3=IOC、4=FOK |

回應物件：`StkOrderResult`
- `ResultCount`：`MsgCode` / `MsgContent` / `Count`
- `ResultList`：`Identify` / `ReplyCode` / `OrderNO` / `TradeDate` / `ErrType` / `ErrNO` / `Advisory`

### 5.2 國內期貨下單 / 取消 / 改量 / 改價

```text
bool SendFutureOrder(LoginAcno, List<FutureOrder>, lng)
```

`FutureOrder` 關鍵欄位：

| 欄位 | 說明 |
|---|---|
| FunctionCode | 00=委託單、04=取消、05=改量、07=改價 |
| CommodityID1 / SettlementMonth1 / StrikePrice1 | 第一腳商品 |
| CommodityID2 / SettlementMonth2 / StrikePrice2 | 第二腳商品（複式單用） |
| OrderQty1 / BuySell1 | 第一腳數量/買賣別 |
| Price | 委託價格 |
| OpenOffsetKind | 0=新倉、1=平倉、2=自動 |
| OrderType | 1=市價、2=限價、3=範圍市價 |
| OrderCond | 空白=ROD、I=FOK、2=IOC |
| Session | 1=預約、其他=盤中單 |

回應物件：`FutOrderResult`。

### 5.3 期貨複式單

| 函數 | 說明 |
|---|---|
| SendFutureCombined | 期貨複式單組合下單 |
| SendFutureApart | 期貨複式單拆解 |
| GetFutSprStore | 查詢期貨複式單庫存明細 |

### 5.4 條件/演算法單

| 函數 | 簽名 | 說明 |
|---|---|---|
| SendAlgoCOOdrStrategy | `bool SendAlgoCOOdrStrategy(Account, List<STOStrategy/MLPStrategy/OCOStrategy/SpiderStrategy/MS_SpiderStrategy/MS_DayTradeSpiderStrategy>, lng)` | 新增條件單 |
| DeleteAlgoCOOdrStrategy | `bool DeleteAlgoCOOdrStrategy(Account, List<DeleteStrategy>, lng)` | 刪除條件單 |
| GetConditionStrategy | `bool GetConditionStrategy(Account, StrategyType, StkCode, lng)` | 查詢有效策略 |
| GetHisConditionStrategy | `bool GetHisConditionStrategy(Account, StrategyType, StkCode, SDate, EDate, lng)` | 查詢歷史策略 |

策略類型：

| 類型 | 值 | 說明 |
|---|---|---|
| STO | 1 | 停損利 |
| MLP | 2 | 移動鎖利 |
| OCO | 3 | 二擇一 |
| MS_Spider | 4 | 母子單 |
| Spider | 5 | 多條件 |
| 查詢用 6 | 6 | 全部 |

### 5.5 其他交易功能

| 函數 | 簽名（參考 YSendOrder.py） | 說明 |
|---|---|---|
| SendPrefundedMargin | `SendPrefundedMargin(Account, amount, currency, type)` | 預收保證金 |
| SendStockEarmark | `SendStockEarmark(Account, StkCode, qty)` | 股票圈存 |

## 6. 帳務/庫存/損益 API

| 函數 | 簽名 | 說明 |
|---|---|---|
| GetStoreSummary | `bool GetStoreSummary(Account, lng)` | 股票庫存綜合總表（含國內/國外股票） |
| GetFutStoreSummary | `bool GetFutStoreSummary(Account, lng)` | 期貨庫存總表 |
| GetOVFutStoreSummary | `bool GetOVFutStoreSummary(Account, lng)` | 國際期貨庫存總表 |
| GetFutInterestStore | `bool GetFutInterestStore(Account, Type, Currency, lng)` | 期貨權益數 |
| GetFutDepositOptimum | `bool GetFutDepositOptimum(Account, lng)` | 期貨保證金最佳化查詢 |
| GetUnrealizedGainLossDetail | `bool GetUnrealizedGainLossDetail(Account, MarketType, StkCode, lng)` | 未實現損益明細 |
| GetHisRealizedGainLoss | `bool GetHisRealizedGainLoss(Account, SDate, EDate, lng)` | 已實現損益查詢 |
| GetStkHistoryReportReversal | `bool GetStkHistoryReportReversal(Account, ReGainLoss, lng)` | 沖銷明細查詢 |
| GetBankBalance | `bool GetBankBalance(Account, lng)` | 銀行餘額查詢 |
| GetStkTransactionOutlay | `bool GetStkTransactionOutlay(Account, lng)` | 交割款查詢 |

## 7. 回報 API

### 7.1 查詢

| 函數 | 簽名 | 說明 |
|---|---|---|
| GetRealReport | `bool GetRealReport(Account, lng)` | 即時回報查詢（委託/成交明細） |
| GetRealReportMerge | `bool GetRealReportMerge(Account, lng)` | 即時回報彙總查詢 |
| GetOrderTradeReport | `bool GetOrderTradeReport(NotshowCancel, Account, lng)` | 委託成交綜合回報 |

`GetOrderTradeReport` 回傳包含：

- `StkOrderList` / `StkTradeList`：現貨委託 / 成交
- `FutOrderList` / `FutTradeList`：期貨委託 / 成交
- `OVStkOrderList` / `OVStkTradeList`：國外股票委託 / 成交
- `OVFutOrderList` / `OVFutTradeList`：國外期貨委託 / 成交

### 7.2 即時訂閱（登入即訂閱）

| 事件 | 說明 |
|---|---|
| RR_RealReport | 即時回報：委託/成交事件 |
| RR_RealReportMerge | 彙總的即時回報：含最新成交價、成交均價、委託狀態等 |

## 8. 使用限制（必須在 broker server 內實作）

單一連線：

| 限制 | 數值 |
|---|---|
| 已登入帳號不允許重複登入 | 1 |
| 登入失敗重試間隔 | 至少 4 秒 |
| 所有訂閱報價商品總數上限 | 2000 |
| 同 FunctionID 每秒訂閱次數 | 10 |
| 單次訂閱商品數上限 | 200 |
| 報價/帳務類每秒發送次數（不含 K 線） | 3 |
| K 線每秒發送次數 | 1 |
| 交易類每秒發送次數 | 10 |
| 單次交易最多筆數 | 30 |

單一帳號：

| 限制 | 數值 |
|---|---|
| 同時最高連線數 | 10 |
| 登入次數 | 1000 次/日 |
| 總訂閱商品數 | 3000 |
| 行情類呼叫 | 1200 次/分鐘 |
| 帳務類呼叫 | 600 次/分鐘 |
| 交易類呼叫 | 3000 次/分鐘 |

超過限制會被暫停服務 1 分鐘；1 小時內暫停 10 次可能停止當日 API 服務。

## 9. 與 broker server 的整合建議

- Broker server 使用 **Python + uv** 實現，直接在同程序內透過 `pythonnet` 呼叫 `YuantaSparkAPI.dll`。
- 已確認首期範圍：**單帳戶、本土股票**；期貨、海外、條件單等先不做，但保留通用透傳能力。
- Python 端職責：
  1. `Open` / `Login` / `LogOut` / `Close`
  2. 將所有 Yuanta API 呼叫包裝成服務方法
  3. 將 `OnResponse` 事件轉成內部事件，並透過 WebSocket 推送給客戶端
- 依賴管理使用 `uv`：`pyproject.toml` + `uv.lock`，主要依賴包含 `fastapi`、`uvicorn`、`pydantic`、`pythonnet`、`prometheus-client`。
- 所有 Yuanta 欄位在 Adapter 邊界做 camelCase/snake_case 轉換，Python domain model 使用自己的命名。

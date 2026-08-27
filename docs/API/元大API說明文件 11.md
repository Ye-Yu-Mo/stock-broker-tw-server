---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## 列舉物件

### enumEnvironmentMode 連線環境類別

```
• PROD：正式環境 (1)
• UAT：測試環境 (2)
```

### enumLangType 語系

```
• Normal：Big5 (0)
• UTF8：UTF8 (1)
• SC：簡體中文 (2)
```

### enumLogType Log類別

```sql
• NONE：不記錄任何的LOG (0)
• System：紀錄一般Log & 排除訂閱即時回報/彙總 (1)
• COMMON：紀錄一般Log (2)
• COMMON_WITH_QUOTE：紀錄一般Log & 特定行情Log (3)
• ALL：全部訊息都強制記錄 (4)
```

### enumMarketType 市場類別

```
• TWSE：上市 (1)
• TWOTC：上櫃 (2)
• TAIFEX：期貨 (3)
• TWEMERGING：興櫃 (4)
• TWSEODD：盤中零股-上市 (5)
• TWOTCODD：盤中零股-上櫃 (6)
• SGX：新加坡交易所 (202)
• CME：芝商所CME Group (203)
• CBOT：芝商所原CBOT (204)
• TCE：東京商品 TOCOM (205)
• OSE：日本交易所JPX (207)
• HKFE：香港交易所 (208)
• NYBOT：洲際-美國ICE-US交易所 (209)
• LIFFE：洲際-英國ICE-UK交易所 (210)
• XEUREX：歐洲交易所 (211)
• ASX：澳洲交易所 (212)
• CBOE： CBOE期貨交易所 (215)
```

### enumQuoteType 訂閱報價類別

```
• Watchlist：行情報價表(指定欄位) (0)
• WatchlistAll：行情報價表 (1)
• FiveTickA：最佳五檔行情 (2)
• FiveTickB：五檔報價(合併最佳五檔) (3)
• StockTick：分時明細 (4)
• MarketInformation：個股盤前資訊 (5)
• StockInformation：個股其他資訊 (6)
```

### enumQuoteIndexType 訂閱索引值類別

```
• 開盤：0
• 最高：1
• 最低：2
• 買價：3
• 累計外盤量：4
• 賣價：5
• 累計內盤量：6
• 成交價：7
• 總成交金額：8
• 單量：9
• 總成交量：10
• 定價量：11
• 未平倉量：12
• 結算價：13
• 合約高價：14
• 合約低價：15
• 委託買進總筆數：16
• 委託買進總口數：17
• 委託賣出總筆數：18
• 委託賣出總口數：19
• 累計買進成交筆數：20
• 累計賣出成交筆數：21
• IndexFlag22：22
• 波動率：23
• 虛擬最佳一檔買進價：24
• 虛擬最佳一檔買進量：25
• 虛擬最佳一檔賣出價：26
• 虛擬最佳一檔賣出量：27
• IndexFlag28：28
• IndexFlag29：29
• 第一買量：42
• 第一賣量：43
• delay一秒的成交價：45
• 瞬間價格趨勢：48
• 昨收價：201
• 漲停價：202
• 跌停價：203
• 交易狀態：240
• 試撮價：241
• 試撮量：242
• 開盤參考價：254
• 開盤參考價清盤用：255
```

### enumQuoteFiveTickIndexType 訂閱五檔索引值類別

```
• 第一買量：0
• 第二買量：1
• 第三買量：2
• 第四買量：3
• 第五買量：4
• 第一買價：5
• 第二買價：6
• 第三買價：7
• 第四買價：8
• 第五買價：9
• 第一賣量：10
• 第二賣量：11
• 第三賣量：12
• 第四賣量：13
• 第五賣量：14
• 第一賣價：15
• 第二賣價：16
• 第三賣價：17
• 第四賣價：18
• 第五賣價：19
• IndexFlag20：20
• IndexFlag21：21
• 第六買量：22
• 第七買量：23
• 第八買量：24
• 第九買量：25
• 第十買量：26
• 第六買價：27
• 第七買價：28
• 第八買價：29
• 第九買價：30
• 第十買價：31
• 第六賣量：32
• 第七賣量：33
• 第八賣量：34
• 第九賣量：35
• 第十賣量：36
• 第六賣價：37
• 第七賣價：38
• 第八賣價：39
• 第九賣價：40
• 第十賣價：41
• IndexFlag42：42
• IndexFlag43：43
• IndexFlag50：50
• IndexFlag51：51
```

### enumQuoteStkInfoIndexType 訂閱個股其他資訊索引值類別

```
• 試搓成交時間：53
```

### enumStkWarningType 股票警示類別

```
• 處置股票：0
• 理財節目異常推介個股：1
• 特殊異常股票：2
```

### enumStkTickSelectType 分時明細查詢類別

```
• 區間查詢：0
• 最後筆數：1
```

### StrategyType 條件單類別

```cpp
• STO：1 //停損利
• MLP：2 //移動鎖利
• OCO：3 //二擇一
• MS_Spider：4 //母子單
• Spider：5 //多條件
```

### StrategyOrder1 條件單下單方式1

```
• 成交就停：1
• 觸發就停：2
• 下單到滿：3
• 每次同量：4
```

### StrategyOrder2 條件單下單方式2

```
• 交易到設定單位全部成交：5
• 母單成交子單就立即下單：6
```

### StrategyCondition1 條件單條件1

```
• 成交價：1
• 總量：2
• 當日漲幅：3
• 當日跌幅：4
```

### StrategyCondition2 條件單條件2

```
• 成交價：1
• 總量：2
• 當日漲幅：3
• 當日跌幅：4
• 總漲幅：5
• 總跌幅：6
• 當日漲停：7
• 當日跌停：8
• 當日上漲：9
• 當日下跌：10
```

### OrderPriceType1 委託價格種類1

```
• 限價：0
• 市價：1
• 成交價：2
• 漲停：3
• 平盤：4
• 跌停：5
```

### OrderPriceType2 委託價格種類2

```
• 市價：1
• 成交價：2
• 漲停：3
• 平盤：4
• 跌停：5
```

### OrderType1 委託種類1

```
• 現股賣出：2
• 融資賣出：4
• 融劵買進：5
• 借劵賣出：7
```

### OrderType2 委託種類2

```
• 現股買進：1
• 現股賣出：2
• 融資買進：3
• 融資賣出：4
• 融劵買進：5
• 融劵賣出：6
• 借劵賣出：7
```

### OrderType3 委託種類3

```
• 現股買進：1
• 現股賣出：2
• 融資買進：3
• 融劵賣出：6
```

### SStatus 策略狀態

```cpp
• SstBuilt：0 //建立策略
• SstWorking：1 //策略執行中
• SstSuspended：2 //策略暫停
• SstCanceled：3 //刪除策略(客戶刪除)
• SstUnsolCxl：4 //刪除策略(系統判定刪除)
• SstExpired：5 //策略失效
• SstDfd：6 //策略今日執行完成
• SstCompleted：7 //策略完成
• SstAbort：8 //失敗;對應客戶刪除or暫停策略失敗
• SstAbortClear：9 //無法建立策略
• SstTrig：99 //觸發子單
• SstTrigBuilt：100 //建立策略
• SstTrigWorking：101 //策略執行中
• SstTrigSuspended：102 //策略暫停
• SstTrigCanceled：103 //刪除策略(客戶刪除)
• SstTrigUnsolCxl：104 //刪除策略(系統判定刪除)
• SstTrigExpired：105 //策略失效
• SstTrigDfd：106 //子單今日執行完成
• SstTrigCompleted：107 //策略完成
• SstTrigAbort：108 //對應客戶刪除or暫停策略失敗
• SstTrigAbortClear：109 //無法建立策略
• SstError：911 //建立失敗
```

### KLineType K線周期

```
• 一分線：0
• 五分線：1
• 十五分線：2
• 三十分線：3
• 六十分線：4
• 日線：11
• 周線：12
• 月線：13
```
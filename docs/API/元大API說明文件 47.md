---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9B%9E%E5%A0%B1/%E5%A7%94%E8%A8%97%E6%88%90%E4%BA%A4%E7%B6%9C%E5%90%88%E5%9B%9E%E5%A0%B1/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## GetOrderTradeReport

委託成交綜合回報

```
GetOrderTradeReport(NotshowCancel, Account, lng)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| NotshowCancel | bool | 是否不列出取消單 |  |
| Account | string | 帳號 | 證券: S + 分公司代號(4) + 帳號(7)   例如 S98875005091   期貨: F + 分公司代號(7+3) + 帳號(7)   例如 FF021000P001234567 |
| lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   \- Normal：Big5   \- UTF8：UTF8   \- SC：簡體中文 |

---

### Output Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| StkOrderList | List\<StkOrder> | 現貨委託回報清單 |  |
| StkTradeList | List\<StkTrade> | 現貨成交回報清單 |  |
| FutOrderList | List\<FutOrder> | 期貨委託回報清單 |  |
| FutTradeList | List\<FutTrade> | 期貨成交回報清單 |  |
| OVStkOrderList | List\<OVStkOrder> | 國外股票委託回報清單 |  |
| OVStkTradeList | List\<OVStkTrade> | 國外股票成交回報清單 |  |
| OVFutOrderList | List\<OVFutOrder> | 國外期貨委託回報清單 |  |
| OVFutTradeList | List\<OVFutTrade> | 國外期貨成交回報清單 |  |

#### StkOrder 現貨委託回報物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 |  |
| TradeDate | TYuantaDate | 交易日 | [參考物件-日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadate) |
| MarketNo | enumMarketType | 市場代碼 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| MarketName | string | 市場名稱 | 上市/上櫃 |
| CompanyNo | string | 股票代碼 |  |
| StkName | string | 股票名稱 |  |
| OrderType | Short | 委託種類 | 0:現貨      3:融資      4:融券      5:策略借券      6:避險借券      7:資沖      8:券沖 |
| BS | string | 買賣別 | S:賣      B:買 |
| Price | double | 價位 | 現貨小數4位,興櫃小數4位 |
| PriceFlag | string | 價格種類 | H:漲停      L:跌停   "-":平盤      1-市價      2-限價 |
| BeforeQty | Int | 前一次委託量 | For 委託狀態=取消成功 |
| AfterQty | Int | 目前委託量 | 委託狀態=取消成功時,委託口數為0, 前端要改讀前一次委託量      委託狀態=10or24，COM改給OR\_QTY原委託量 |
| OkQty | Int | 成交量 |  |
| OrderStatus | Short | 委託狀態 | 0:傳輸中      5:預約單      10:委託失敗      20:委託成功      24:委託失效      25:價穩失效　      30:取消成功 |
| AcceptDate | TYuantaDate | 委託日期 | [參考物件-日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadate) |
| AcceptTime | TYuantaTime | 委託時間 | [參考物件-時間物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantatime) |
| OrderNo | string | 委託單號 | "H00001" |
| ErrorNo | string | 錯誤碼 |  |
| ErrorMessage | string | 錯誤訊息 |  |
| Seller | Short | 營業員代碼 |  |
| Channel | string | Channel |  |
| APCode | Short | APCode | 0:現貨      2:盤後零股      7:盤後      4:盤中零股      99:盤中零股 |
| OTax | Int | 證交稅 |  |
| OCharge | Int | 手續費 |  |
| ODueAmt | Int | 應收付 |  |
| CancelFlag | string | 可取消Flag | 'Y'/'N'      盤中or 預約單才可取消 |
| ReduceFlag | string | 可減量Flag | 'Y'/'N'      盤中or 預約單才可減量 |
| TraditionFlag | string | 傳統單Flag | 'Y":傳統單 |
| BasketNo | string | BasketNo | 無值 |
| TradeCurrency | string | 報價幣別 | TWD      CNY      HKD      USD |
| Time\_in\_Force | string | 委託效期 | 0:當日有效      3:IOC      4:FOK |
| Order\_Success | string | 委託成功旗標 |  |
| Reduce\_Flag | string | 本委託下單是否被減量 |  |
| Chg\_Prz\_Flag | string | 本委託下單是否進行改價 |  |
| TSE\_Cancel | string | 本委託下單是否      被交易所主動刪單 |  |
| CancelQty | Int | 取消數量 |  |
| OR\_QTY | Int | 原委託量 |  |
| UpdateDate | TYuantaDate | 更新日期 | [參考物件-日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadate) |
| UpdateTime | TYuantaTime | 更新時間 | [參考物件-時間物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantatime) |

#### StkTrade 現貨成交回報物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 |  |
| MarketNo | enumMarketType | 市場代碼 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| MarketName | string | 市場名稱 |  |
| CompanyNo | string | 股票代碼 |  |
| StkName | string | 股票名稱 |  |
| OrderType | Short | 委託種類 | 0:現貨      3:融資      4:融券      5:策略借券      6:避險借券      7:資沖      8:券沖 |
| BS | string | 買賣別 | S:賣      B:買 |
| OkQty | Int | 成交量 |  |
| OPrice | double | 委託價 | 現貨小數4位,興櫃小數4位 |
| SPrice | double | 成交價 | 現貨小數4位,興櫃小數4位 |
| DateTime | TYuantaDateTime | 交易日 | [參考物件-時間日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadatetime)   年月日時分秒毫秒 |
| OrderNo | string | 委託單號 | "H0001" |
| TradeCurrency | string | 報價幣別 | TWD      CNY      HKD      USD |
| Price\_Flag | string | 價位Flag | 1-市價      2-限價 |
| Exchange\_Code | Short | 委託別 | 0-一般委託      1-鉅額      2-零股      4-盤後定價      5 盤中零股 |

#### FutOrder 期貨委託回報物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 |  |
| TradeDate | TYuantaDate | 交易日期 | [參考物件-日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadate) |
| MarketNo | enumMarketType | 市場代碼 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| MarketName | string | 市場名稱 |  |
| Commodity1 | string | 商品代碼1 | 選擇權第7碼是C或P |
| SettlementMonth1 | Int | 商品月份1 |  |
| StrikePrice1 | double | 履約價1 |  |
| BuySellKind1 | string | 買賣別1 |  |
| Commodity2 | string | 商品代碼2 | 選擇權第7碼是C或P |
| SettlementMonth2 | Int | 商品月份2 |  |
| StrikePrice2 | double | 履約價2 |  |
| BuySellKind2 | string | 買賣別2 |  |
| OpenOffsetKind | string | 新/平倉 | 0:新倉      1:平倉      2系統 |
| OrderCondition | string | 委託條件 | " ":ROD      "1":FOK      "2":IOC |
| OrderPrice | string | 委託價 | M:市價      P:範圍市價 |
| BeforeQty | Int | 前一次委託量 | For 委託狀態=取消成功 |
| AferQty | Int | 目前委託量 | 委託狀態=取消成功時,委託口數為0, 前端要改讀前一次委託量 |
| OKQty | Int | 成交口數 |  |
| OrderStatus | short | 委託狀態 | 0:傳輸中      5:預約單      10:委託失敗      20:委託成功      30:取消成功 |
| AcceptDate | TYuantaDate | 委託日期 | [參考物件-日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadate) |
| AcceptTime | TYuantaTime | 委託時間 | [參考物件-時間物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantatime) |
| ErrorNo | string | 錯誤碼 |  |
| ErrorMessage | string | 錯誤訊息 |  |
| OrderNO | string | 委託單號 |  |
| ProductType | string | 商品種類 | O:選擇權      F:期貨 |
| Seller | short | 營業員代碼 |  |
| TotalMatFee | double | 手續費總和 |  |
| TotalMatExchTax | double | 交易稅總和 |  |
| TotalMatPremium | double | 應收付 |  |
| DayTradeID | string | 當沖註記 | Y:當沖 |
| CancelFlag | string | 可取消Flag | 'Y'/'N'      盤中or 預約單才可取消 |
| ReduceFlag | string | 可減量Flag | 'Y'/'N'      盤中or 預約單才可減量 |
| StkName1 | string | 商品名稱1 | Ex:'中鋼實 06 0030 C', '台指01',' 櫃指選 03 00400 C' |
| StkName2 | string | 商品名稱2 | Ex:'中鋼實 06 0030 C', '台指01',' 櫃指選 03 00400 C' |
| TraditionFlag | string | 傳統單Flag | 'Y":傳統單 |
| TRID | string | 商品代碼 | FITX 200709,   URO200709,      FIGTL7/C8,   TXO09000T7,   TXO08000/08100U7 |
| CurrencyType | string | 交易幣別 | NTD:台幣      USD:美元 |
| CurrencyType2 | string | 交割幣別 | NTD:台幣      USD:美元 |
| BasketNo | string | BasketNo |  |
| MarketNo1 | enumMarketType | 市場代碼1 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype)      <第1支腳> |
| StkCode1 | string | 行情股票代碼1 | <第1支腳> |
| MarketNo2 | enumMarketType | 市場代碼2 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype)      <第2支腳> |
| StkCode2 | string | 行情股票代碼2 | <第2支腳> |

#### FutTrade 期貨成交回報物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 |  |
| MarketNo | enumMarketType | 市場代碼 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| MarketName | string | 市場名稱 |  |
| Commodity1 | string | 商品代號1 | 選擇權第7碼是C或P |
| SettlementMonth1 | Int | 商品月份1 |  |
| BuySellKind1 | string | 買賣別1 |  |
| OkQty | Int | 成交口數 |  |
| MatchPrice1 | double | 成交價1 |  |
| MatchPrice2 | double | 成交價2 |  |
| MatchTime | TYuantaTime | 成交時間 | [參考物件-時間物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantatime) |
| MatchDate | TYuantaDate | 成交日期 | [參考物件-日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadate) |
| OrderNO | string | 委託單號 |  |
| StrikePrice1 | double | 履約價1 |  |
| Commodity2 | string | 商品代碼2 | 選擇權第7碼是C或P |
| SettlementMonth2 | Int | 商品月份2 |  |
| BuySellKind2 | string | 買賣別2 |  |
| StrikePrice2 | double | 履約價2 |  |
| RecType | string | 單式單/複式單 | "1":單式      "2":複式 |
| ProductType | string | 商品種類 |  |
| OrderPrice | double | 委託價 |  |
| StkName1 | string | 商品名稱1 | Ex:'中鋼實 06 0030 C', '台指01',' 櫃指選 03 00400 C' |
| StkName2 | string | 商品名稱2 | Ex:'中鋼實 06 0030 C', '台指01',' 櫃指選 03 00400 C' |
| DayTradeID | string | 當沖註記 |  |
| SprMatchPrice | double | 複式單成交價 |  |
| TRID | string | 商品代碼 | 2854, 05311   FITX 200709,   URO200709,      FIGTL7/C8,   TXO09000T7,   TXO08000/08100U7 |
| CurrencyType | string | 交易幣別 | NTD:台幣      USD:美元 |
| CurrencyType2 | string | 交割幣別 | NTD:台幣      USD:美元 |
| SubNo | string | 子成交序號 | 0(單式)      1(複式腳1)      2(複式腳2) |

**OVStkOrder 國外股票委託回報物件**

| **Name** | **Type** | **Description** | **Memo** |
| --- | --- | --- | --- |
| Account | string | 證券帳號 |  |
| TradeDate | TYuantaDate | 交易日 | [參考物件-日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadate) |
| MarketNo | enumMarketType | 市場代碼 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| MarketName | string | 市場名稱 |  |
| CompanyNo | string | 商品代碼 |  |
| StkName | string | 商品名稱 |  |
| BS | string | 買賣別 | S:賣      B:買 |
| CurrencyType | string | 交易幣別 | USD:美元      HDK:港幣 |
| Price | double | 委託價 | 港股小數3位,美股小數4位 |
| PriceType | string | 價格型態 | 'LMT':限價單 |
| OrderQty | Int | 委託量 | 股數 |
| OkQty | Int | 成交量 |  |
| OrderStatus | short | 狀態碼 | 0:傳輸中      5:預約單      10:委託失敗      20:委託成功      30:取消成功 |
| OrderTime | TYuantaDateTime | 委託時間 | [參考物件-時間日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadatetime) |
| OrderType | string | 委託單型態 | DAY:當日有效單   GTD:指定日期單 |
| OrderNo | string | 委託單號 |  |
| Fee | double | 手續費 |  |
| PolarisAMT | double | 應收付金額 |  |
| ErrorNo | string | 錯誤碼 |  |
| ErrorMessage | string | 錯誤訊息 |  |
| CurrencyType2 | string | 交割幣別 | USD:美元      HDK:港幣 |
| CancelFlag | string | 可取消Flag | 'Y'/'N'      盤中or 預約單才可取消 |
| ReduceFlag | string | 可減量Flag | 'Y'/'N'   ＊美股不提供改量改價功能,由元件固定回N |
| TraditionFlag | string | 傳統單Flag | 'Y":傳統單 |
| SettleType | string | 交割方式 | 0:外幣      1:台幣 |
| BasketNo | string | BasketNo | smart-04:長效單 |

#### OVStkTrade 國外股票成交回報物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 |  |
| MarketNo | enumMarketType | 市場代碼 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| MarketName | string | 市場名稱 |  |
| CompanyNo | string | 商品代碼 |  |
| StkName | string | 商品名稱 |  |
| BS | string | 買賣別 | S:賣      B:買 |
| CurrencyType | string | 交易幣別 | USD:美元      HDK:港幣 |
| OkQty | Int | 成交量 |  |
| OrderPrice | double | 委託價 | 港股小數3位,美股小數4位 |
| MatchPrice | double | 成交價 | 港股小數3位,美股小數4位 |
| DateTime | TYuantaDateTime | 成交時間 | [參考物件-時間日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadatetime) |
| Fee | double | 手續費 |  |
| OrderNo | string | 委託單號 |  |
| SettlementAMT | double | 成交金額 | 含手續費 |
| CurrencyType2 | string | 交割幣別 | USD:美元      HDK:港幣 |

#### OVFutOrder 國外期貨委託回報物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 |  |
| TradeDate | TYuantaDate | 交易日 | [參考物件-日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadate)      西元年 |
| MarketNo | enumMarketType | 市場代碼 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| MarketName | string | 市場名稱 |  |
| CompanyNo | string | 商品代碼 | URO,JGL |
| SettlementMonth | Int | 商品年月 | 200909 |
| StkName | string | 商品名稱 |  |
| BS | string | 買賣別 | "B":買      "S":賣 |
| OrderType | string | 委託方式 | LMT:限價單      MKT:市價單      STP:停損市價單      SWL:停損限價單 |
| Price | double | 委託價 | 000116'21.75 |
| TouchPrice | double | 停損執行價 | 000116'21.75 |
| OrderQty | int | 委託口數 |  |
| OkQty | int | 成交口數 |  |
| OrderStatus | short | 狀態碼 | 0:傳輸中      5:預約單      10:委託失敗      20:委託成功      30:取消成功 |
| AcceptDate | TYuantaDate | 委託日期 | [參考物件-日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadate) |
| AcceptTime | TYuantaTime | 委託時間 | [參考物件-時間物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantatime) |
| ErrorNo | string | 錯誤代碼 |  |
| ErrorMessage | string | 錯誤訊息 |  |
| OrderNo | string | 委託單號 | AA0484 |
| DayTradeID | string | 當沖註記 | Y:當沖 |
| CancelFlag | string | 可取消Flag | 'Y'/'N'      盤中or 預約單才可取消 |
| ReduceFlag | string | 可減量Flag | 國際期貨目前無提供減量      'P':可改價 |
| UtPrice | double | 委託價格整數位 | 市價或市價停損單= 0      \<For 取消下單時使用> |
| UtPrice2 | double | 委託價格分子 | \<For 取消下單時使用> |
| MinPrice2 | Int | 委託價格分母 | \<For 取消下單時使用> |
| UtPrice4 | double | 停損執行價整數位 | 非停損單=0      \<For 取消下單時使用> |
| UtPrice5 | double | 停損執行價格分子 | \<For 取消下單時使用> |
| UtPrice6 | Int | 停損執行價格分母 | \<For 取消下單時使用> |
| TraditionFlag | string | 傳統單Flag | 'Y":傳統單 |
| BasketNo | string | BasketNo |  |
| MarketNo1 | enumMarketType | 市場代碼1 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| StkCode1 | string | 行情股票代碼1 |  |
| CurrencyType | string | 交易幣別 |  |
| CurrencyType2 | string | 交割幣別 |  |

##### OVFutTrade 國外期貨成交回報物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 |  |
| MarketNo | enumMarketType | 市場代碼 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| MarketName | string | 市場名稱 |  |
| CompanyNo | string | 商品代碼 | URO,JGL |
| SettlementMonth | Int | 商品年月 | 200909 |
| StkName | string | 商品名稱 |  |
| BS | string | 買賣別 | "B":買      "S":賣 |
| OkQty | int | 成交口數 |  |
| OrderPrice | double | 委託價 | 000116'21.75 |
| MatchPrice | double | 成交價 | 000116'21.75 |
| MatchDate | TYuantaDate | 成交日期 | [參考物件-日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadate) |
| MatchTime | TYuantaTime | 成交時間 | [參考物件-時間物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantatime) |
| OrderNo | string | 委託單號 | AA0484 |
| CurrencyType | string | 交易幣別 | NTD:台幣      USD:美元 |
| CurrencyType2 | string | 交割幣別 | NTD:台幣      USD:美元 |

---

### 範例

#### 引用元件

```python
import os, time, datetime, struct, pathlib, sys
from datetime import datetime
from pathlib import Path
from pythonnet import load

load("coreclr")
import clr, System

##透過Clr引用系統標準函式
clr.AddReference('System.Collections')
from System.Collections.Generic import List

##宣告增加模組、DLL的路徑(windows可抓取當前路徑 Linux跟MAC需指定路徑)
sys.path.append(Path(pathlib.Path(__file__).parent.resolve()))
if sys.platform == "win32":
    os.add_dll_directory(Path(pathlib.Path(__file__).parent.resolve()))

##透過Clr引用YuantaSparkAPI.dll
##pythonnet引用元件不用加附檔名
try:
    clr.AddReference("YuantaSparkAPI")
except Exception as e:
    print(f"Error loading YuantaSparkAPI: {e}")
from YuantaOneAPI import YuantaSparkAPITrader, enumLogType, enumEnvironmentMode

# 建立 API 物件
objYuantaSparkAPI = YuantaSparkAPITrader()
objYuantaSparkAPI.SetLogType(enumLogType.COMMON)
```

```
using System;
using System.Collections.Generic;
using System.Text;
using System.Threading;
using YuantaOneAPI;

YuantaSparkAPITrader objYuantaSparkAPI = new YuantaSparkAPITrader();
string Account = "S98875005091";
string Password = "1234";
enumEnvironmentMode enumEvenMode =enumEnvironmentMode.UAT;

objYuantaSparkAPI.OnResponse += objApi_OnResponse;
objYuantaSparkAPI.SetLogType(enumLogType.ALL);

objYuantaSparkAPI.Open(enumEvenMode);
Thread.Sleep(1000);

objYuantaSparkAPI.Login(Account, Password);
Thread.Sleep(1000);

objYuantaSparkAPI.GetOrderTradeReport(false, Account);
Thread.Sleep(2000);
```

#### Onresponse

```
def on_response(intMark, dwIndex, strIndex, objHandle, objValue):
    try:
        result = ''
        match intMark:
            case 0:  # 系統回應資訊
                result = str(objValue)

            case 1:  # 查詢回應資訊
                match strIndex:
                    case 'Login':
                        loginResult = objValue
                        status = loginResult.LoginStatus
                        strMsgCode = status.MsgCode # 訊息代碼
                        strMsgContent = status.MsgContent # 訊息內容
                        intCount = status.Count # 筆數
                        result = '{0},{1},帳號筆數:{2}\r\n'.format(strMsgCode,strMsgContent, str(intCount))
                        if strMsgCode == '0001' or strMsgCode == '00001' or intCount > 0 :
                            for i in objValue.LoginList:
                                result += f"{i.Account},{i.Name},{i.InvestorID},{i.SellerNo}\n"

                    case 'GetOrderTradeReport':
                        orderTradeReport = objValue
                        SOList = orderTradeReport.StkOrderList
                        STList = orderTradeReport.StkTradeList
                        FOList = orderTradeReport.FutOrderList
                        FTList = orderTradeReport.FutTradeList
                        OVSOList = orderTradeReport.OVStkOrderList
                        OVSTList = orderTradeReport.OVStkTradeList
                        OVFOList = orderTradeReport.OVFutOrderList
                        OVFTList = orderTradeReport.OVFutTradeList

                        result += '委託成交綜合回報:\r\n'
                        for i in range(SOList.Count):
                            #tradeDate = TYuantaDate()
                            tradeDate = SOList[i].TradeDate
                            Tdate= '{0}/{1}/{2}'.format(tradeDate.ushtYear, tradeDate.bytMon, tradeDate.bytDay)
                            #acceptDate = TYuantaDate()
                            acceptDate = SOList[i].AcceptDate
                            Adate= '{0}/{1}/{2}'.format(acceptDate.ushtYear, acceptDate.bytMon, acceptDate.bytDay)        
                            #acceptTime = TYuantaTime()
                            acceptTime = SOList[i].AcceptTime
                            Atime= '{0}:{1}:{2}.{3}'.format(str(acceptTime.bytHour), str(acceptTime.bytMin), str(acceptTime.bytSec), str(acceptTime.ushtMSec))
                            #updateDate = TYuantaDate()
                            updateDate = SOList[i].UpdateDate
                            Udate= '{0}/{1}/{2}'.format(updateDate.ushtYear, updateDate.bytMon, updateDate.bytDay)
                            #updateTime = TYuantaTime()
                            updateTime = SOList[i].UpdateTime
                            Utime= '{0}:{1}:{2}.{3}'.format(str(updateTime.bytHour), str(updateTime.bytMin), str(updateTime.bytSec), str(updateTime.ushtMSec))

                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14} {15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29},{30},{31},{32},{33},{34},{35},{36},{37} {38}\r\n'.format(
                                SOList[i].Account,Tdate,str(SOList[i].MarketNo),SOList[i].MarketName,SOList[i].CompanyNo,SOList[i].StkName,str(SOList[i].OrderType),SOList[i].BS,str(SOList[i].Price),SOList[i].PriceFlag,
                                str(SOList[i].BeforeQty),str(SOList[i].AfterQty),str(SOList[i].OkQty),str(SOList[i].OrderStatus),Adate,Atime,SOList[i].OrderNo,SOList[i].ErrorNo,SOList[i].ErrorMessage,str(SOList[i].Seller),
                                SOList[i].Channel,str(SOList[i].APCode),str(SOList[i].OTax),str(SOList[i].OCharge),str(SOList[i].ODueAmt),SOList[i].CancelFlag,SOList[i].ReduceFlag,SOList[i].TraditionFlag,SOList[i].BasketNo,
                                SOList[i].TradeCurrency,SOList[i].Time_in_Force,SOList[i].Order_Success,SOList[i].Reduce_Flag,SOList[i].Chg_Prz_Flag,SOList[i].TSE_Cancel,str(SOList[i].CancelQty),str(SOList[i].OR_QTY),Udate,Utime)

                        result += '現貨成交筆數:{0}\r\n'.format(STList.Count)
                        for i in range(STList.Count):
                            #dateTime=TYuantaDateTime()
                            dateTime=STList[i].DateTime

                            Date= '{0}/{1}/{2}'.format(dateTime.Year, dateTime.Month, dateTime.Day)
                            Time= '{0}:{1}:{2}.{3}'.format(str(dateTime.Hour), str(dateTime.Minute), str(dateTime.Second), str(dateTime.Millisecond))

                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10} {11},{12},{13},{14},{15}\r\n'.format(
                                STList[i].Account,str(STList[i].MarketNo),STList[i].MarketName,STList[i].CompanyNo,STList[i].StkName,str(STList[i].OrderType),STList[i].BS,str(STList[i].OkQty),str(STList[i].OPrice),
                                str(STList[i].SPrice),Date,Time,STList[i].OrderNo,STList[i].TradeCurrency,STList[i].Price_Flag,str(STList[i].Exchange_Code))

                        result += '期貨委託筆數:{0}\r\n'.format(FOList.Count)
                        for i in range(FOList.Count):
                            #tradeDate = TYuantaDate()
                            tradeDate = FOList[i].TradeDate
                            Tdate= '{0}/{1}/{2}'.format(tradeDate.Year, tradeDate.Month, tradeDate.Day)
                            #acceptDate = TYuantaDate()
                            acceptDate = FOList[i].AcceptDate
                            Adate= '{0}/{1}/{2}'.format(acceptDate.Year, acceptDate.Month, acceptDate.Day)        
                            #acceptTime = TYuantaTime()
                            acceptTime = FOList[i].AcceptTime
                            Atime= '{0}:{1}:{2}.{3}'.format(str(acceptTime.Hour), str(acceptTime.Minute), str(acceptTime.Second), str(acceptTime.Millisecond))

                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19} {20},{21},{22},{23},{24},{25},{26},{27},{28},{29},{30},{31},{32},{33},{34},{35},{36},{37} {38},{39},{40},{41},{42}\r\n'.format(
                                FOList[i].Account,Tdate,str(FOList[i].MarketNo),FOList[i].MarketName,FOList[i].Commodity1,str(FOList[i].SettlementMonth1),str(FOList[i].StrikePrice1),FOList[i].BuySellKind1,FOList[i].Commodity2,
                                str(FOList[i].SettlementMonth2),str(FOList[i].StrikePrice2),FOList[i].BuySellKind2,FOList[i].OpenOffsetKind,FOList[i].OrderCondition,FOList[i].OrderPrice,str(FOList[i].BeforeQty),str(FOList[i].AfterQty),
                                str(FOList[i].OkQty),str(FOList[i].OrderStatus),Adate,Atime,FOList[i].ErrorNo,FOList[i].ErrorMessage,FOList[i].OrderNo,FOList[i].ProductType,str(FOList[i].Seller),str(FOList[i].TotalMatFee),
                                str(FOList[i].TotalMatExchTax),str(FOList[i].TotalMatPremium),FOList[i].DayTradeID,FOList[i].CancelFlag,FOList[i].ReduceFlag,FOList[i].StkName1,FOList[i].StkName2,FOList[i].TraditionFlag,
                                FOList[i].TRID,FOList[i].CurrencyType,FOList[i].CurrencyType2,FOList[i].BasketNo,str(FOList[i].MarketNo1),FOList[i].StkCode1,str(FOList[i].MarketNo2),FOList[i].StkCode2)

                        result += '期貨成交筆數:{0}\r\n'.format(FTList.Count)
                        for i in range(FTList.Count):
                            #date = TYuantaDate()
                            date = FTList[i].MatchDate
                            Mdate= '{0}/{1}/{2}'.format(date.ushtYear, date.bytMon, date.bytDay)        
                            #time = TYuantaTime()
                            time = FTList[i].MatchTime
                            Mtime= '{0}:{1}:{2}.{3}'.format(str(time.bytHour), str(time.bytMin), str(time.bytSec), str(time.ushtMSec))

                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9} {10} {11},{12},{13},{14},{15},{16},{17},{18},{19} {20},{21},{22},{23},{24},{25},{26},{27}\r\n'.format(
                                FTList[i].Account,str(FTList[i].MarketNo),FTList[i].MarketName,FTList[i].Commodity1,str(FTList[i].SettlementMonth1),FTList[i].BuySellKind1,str(FTList[i].OkQty),str(FTList[i].MatchPrice1),
                                str(FTList[i].MatchPrice2),Mdate,Mtime,FTList[i].OrderNo,str(FTList[i].StrikePrice1),FTList[i].Commodity2,str(FTList[i].SettlementMonth2),FTList[i].BuySellKind2,str(FTList[i].StrikePrice2),
                                FTList[i].RecType,FTList[i].ProductType,str(FTList[i].OrderPrice),FTList[i].StkName1,FTList[i].StkName2,FTList[i].DayTradeID,str(FTList[i].SprMatchPrice),FTList[i].TRID,FTList[i].CurrencyType,
                                FTList[i].CurrencyType2,FTList[i].SubNo)

                        result += '國外現貨委託筆數:{0}\r\n'.format(OVSOList.Count)
                        for i in range(OVSOList.Count):
                            #tradeDate = TYuantaDate()
                            tradeDate = OVSOList[i].TradeDate
                            Tdate= '{0}/{1}/{2}'.format(tradeDate.ushtYear, tradeDate.bytMon, tradeDate.bytDay)
                            #dt=TYuantaDateTime()
                            dateTime=OVSOList[i].OrderTime

                            #date = TYuantaDate()
                            Date= '{0}/{1}/{2}'.format(dateTime.Year, dateTime.Month, dateTime.Day)
                            #time = TYuantaTime()
                            Time = '{0}:{1}:{2}.{3}'.format(dateTime.Hour, dateTime.Minute, dateTime.Second, dateTime.Millisecond)

                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13} {14},{15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26}\r\n'.format(
                                OVSOList[i].Account,Tdate,str(OVSOList[i].MarketNo),OVSOList[i].MarketName,OVSOList[i].CompanyNo,OVSOList[i].StkName,OVSOList[i].BS,OVSOList[i].CurrencyType,str(OVSOList[i].Price),
                                OVSOList[i].PriceType,str(OVSOList[i].OrderQty),str(OVSOList[i].OkQty),str(OVSOList[i].OrderStatus),Date,Time,OVSOList[i].OrderType,OVSOList[i].OrderNo,str(OVSOList[i].Fee),str(OVSOList[i].PolarisAMT),
                                OVSOList[i].ErrorNo,OVSOList[i].ErrorMessage,OVSOList[i].CurrencyType2,OVSOList[i].CancelFlag,OVSOList[i].ReduceFlag,OVSOList[i].TraditionFlag,OVSOList[i].SettleType,OVSOList[i].BasketNo)

                        result += '國外現貨成交筆數:{0}\r\n'.format(OVSTList.Count)
                        for i in range(OVSTList.Count):
                            #dateTime=TYuantaDateTime()

                            dateTime=OVSTList[i].DateTime

                            Date= '{0}/{1}/{2}'.format(dateTime.Year, dateTime.Month, dateTime.Day)
                            Time= '{0}:{1}:{2}.{3}'.format(str(dateTime.tHour), str(dateTime.Minute), str(dateTime.Second), str(dateTime.Millisecond))

                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9} {10} {11},{12},{13},{14},{15}\r\n'.format(
                                OVSTList[i].Account,str(OVSTList[i].MarketNo),OVSTList[i].MarketName,OVSTList[i].CompanyNo,OVSTList[i].StkName,OVSTList[i].BS,OVSTList[i].CurrencyType,str(OVSTList[i].OkQty),
                                str(OVSTList[i].OrderPrice),str(OVSTList[i].MatchPrice),Date,Time,str(OVSTList[i].Fee),OVSTList[i].OrderNo,str(OVSTList[i].SettlementAMT),OVSTList[i].CurrencyType2)

                        result += '國外期貨委託筆數:{0}\r\n'.format(OVFOList.Count)
                        for i in range(OVFOList.Count):
                            #tradeDate = TYuantaDate()
                            tradeDate = OVFOList[i].TradeDate
                            Tdate= '{0}/{1}/{2}'.format(tradeDate.ushtYear, tradeDate.bytMon, tradeDate.bytDay)
                            #acceptDate = TYuantaDate()
                            acceptDate = OVFOList[i].AcceptDate
                            Adate= '{0}/{1}/{2}'.format(acceptDate.ushtYear, acceptDate.bytMon, acceptDate.bytDay)        
                            #acceptTime = TYuantaTime()
                            acceptTime = OVFOList[i].AcceptTime
                            Atime= '{0}:{1}:{2}.{3}'.format(str(acceptTime.bytHour), str(acceptTime.bytMin), str(acceptTime.bytSec), str(acceptTime.ushtMSec))

                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14} {15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29},{30},{31},{32},{33}\r\n'.format(
                                OVFOList[i].Account,Tdate,str(OVFOList[i].MarketNo),OVFOList[i].MarketName,OVFOList[i].CompanyNo,str(OVFOList[i].SettlementMonth),OVFOList[i].StkName,OVFOList[i].BS,OVFOList[i].OrderType,
                                str(OVFOList[i].Price),OVFOList[i].TouchPrice,str(OVFOList[i].OrderQty),str(OVFOList[i].OkQty),str(OVFOList[i].OrderStatus),Adate,Atime,OVFOList[i].ErrorNo,OVFOList[i].ErrorMessage,
                                OVFOList[i].OrderNo,OVFOList[i].DayTradeID,OVFOList[i].CancelFlag,OVFOList[i].ReduceFlag,str(OVFOList[i].UtPrice),str(OVFOList[i].UtPrice2),str(OVFOList[i].MinPrice2),str(OVFOList[i].UtPrice4),
                                str(OVFOList[i].UtPrice5),str(OVFOList[i].UtPrice6),OVFOList[i].TraditionFlag,OVFOList[i].BasketNo,str(OVFOList[i].MarketNo1),OVFOList[i].StkCode1,OVFOList[i].CurrencyType,OVFOList[i].CurrencyType2)

                        result += '國外期貨成交筆數:{0}\r\n'.format(OVFTList.Count)
                        for i in range(OVFTList.Count):
                            #date = TYuantaDate()
                            date = OVFTList[i].MatchDate
                            Date= '{0}/{1}/{2}'.format(date.ushtYear, date.bytMon, date.bytDay)        
                            #time = TYuantaTime()
                            time = OVFTList[i].MatchTime
                            Time= '{0}:{1}:{2}.{3}'.format(str(time.bytHour), str(time.bytMin), str(time.bytSec), str(time.ushtMSec))

                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10} {11},{12},{13},{14}\r\n'.format(
                                OVFTList[i].Account,str(OVFTList[i].MarketNo),OVFTList[i].MarketName,OVFTList[i].CompanyNo,str(OVFTList[i].SettlementMonth),OVFTList[i].StkName,OVFTList[i].BS,str(OVFTList[i].OkQty),
                                str(OVFTList[i].OrderPrice),str(OVFTList[i].MatchPrice),Date,Time,OVFTList[i].OrderNo,OVFTList[i].CurrencyType,OVFTList[i].CurrencyType2)

        if result:
            print('##================================================##\n')
            print(result)

    except Exception as error:
        print(f"處理回應時發生錯誤: {error}")

objYuantaSparkAPI.OnResponse += on_response
#測試環境帳號:UAT 正式環境:PROD
objYuantaSparkAPI.Open(enumEnvironmentMode.UAT)
time.sleep(2)
objYuantaSparkAPI.Login('S98875005091', '1234')
time.sleep(2)

#委託成交綜合回報
objYuantaSparkAPI.GetOrderTradeReport(False,'S98875005091')

# 保持程式運行
while True:
    time.sleep(1)
```

```csharp
void objApi_OnResponse(int intMark, uint dwIndex, string strIndex, object objHandle, object objValue)
{
    string strResult = "";
    try
    {
        if (intMark == 0)
        {
            Console.WriteLine(Convert.ToString(objValue));
            return;
        }

        if (intMark == 1)
        {
            if (strIndex == "Login")
            {
                var result = (LoginResult)objValue;

                string strMsgCode = result.LoginStatus.MsgCode;
                string strMsgContent = result.LoginStatus.MsgContent;
                int intCount = result.LoginStatus.Count;

                strResult += $"{strMsgCode}, {strMsgContent}{Environment.NewLine}";
                if (strMsgCode == "0001" || strMsgCode == "00001")
                {
                    strResult += $"帳號筆數: {intCount.ToString()}{Environment.NewLine}";
                    result.LoginList.ForEach(r => strResult += $"{r.Account},{r.Name},{r.InvestorID},{r.SellerNo}\r\n");

                }
                else
                {
                    Account = "";
                }

                Console.WriteLine("\n======================");
                Console.WriteLine(strResult.ToString());
                Console.WriteLine("======================\n");
                return;
            }

            if (strIndex == "GetOrderTradeReport")
            {
                var result = (OrderTradeReportResult)objValue;
                try
                {
                    TYuantaDate yuantaDate;
                    TYuantaTime yuantaTime;

                    strResult += "委託成交回報查詢結果 : \r\n";

                    strResult += "現貨委託筆數: " + result.StkOrderList.Count + "\r\n";
                    result.StkOrderList.ForEach(x =>
                    {
                        strResult += $"{x.Account},";
                        yuantaDate = x.TradeDate;
                        strResult += $"{yuantaDate.ushtYear}/{yuantaDate.bytMon}/{yuantaDate.bytDay},";
                        strResult += $"{x.MarketNo},{x.MarketName},{x.CompanyNo},{x.StkName},{x.OrderType},{x.BS},{x.Price},{x.PriceFlag},{x.BeforeQty},{x.AfterQty},{x.OkQty},{x.OrderStatus},";
                        yuantaDate = x.AcceptDate;
                        yuantaTime = x.AcceptTime;
                        strResult += $"{yuantaDate.ushtYear}/{yuantaDate.bytMon}/{yuantaDate.bytDay} {yuantaTime.bytHour}:{yuantaTime.bytMin}:{yuantaTime.bytSec}.{yuantaTime.ushtMSec},";
                        strResult += $"{x.OrderNo},{x.ErrorNo},{x.ErrorMessage},{x.Seller},{x.Channel},{x.APCode},{x.OTax},{x.OCharge},{x.ODueAmt},{x.CancelFlag},{x.ReduceFlag},{x.TraditionFlag}," +
                        $"{x.BasketNo},{x.TradeCurrency},{x.Time_in_Force},{x.Order_Success},{x.Reduce_Flag},{x.Chg_Prz_Flag},{x.TSE_Cancel},{x.CancelQty}";
                        yuantaDate = x.UpdateDate;
                        yuantaTime = x.UpdateTime;
                        strResult += $"{yuantaDate.ushtYear}/{yuantaDate.bytMon}/{yuantaDate.bytDay} {yuantaTime.bytHour}:{yuantaTime.bytMin}:{yuantaTime.bytSec}.{yuantaTime.ushtMSec}\r\n";
                    });

                    strResult += "現貨成交筆數: " + result.StkTradeList.Count + "\r\n";
                    result.StkTradeList.ForEach(x =>
                    {
                        strResult += $"{x.Account},{x.MarketNo},{x.MarketName},{x.CompanyNo},{x.StkName},{x.OrderType},{x.BS},{x.OkQty},{x.OPrice},{x.SPrice},";
                        strResult += $"{x.DateTime.ToString()},{x.OrderNo},{x.TradeCurrency},{x.Price_Flag},{x.Exchange_Code}\r\n";
                    });

                    strResult += "期貨委託筆數: " + result.FutOrderList.Count + "\r\n";
                    result.FutOrderList.ForEach(x =>
                    {
                        strResult += $"{x.Account},";
                        yuantaDate = x.TradeDate;
                        strResult += $"{yuantaDate.ushtYear}/{yuantaDate.bytMon}/{yuantaDate.bytDay},";
                        strResult += $"{x.MarketNo},{x.MarketName},{x.Commodity1},{x.SettlementMonth1},{x.StrikePrice1},{x.BuySellKind1},{x.Commodity2},{x.SettlementMonth2},{x.StrikePrice2}," +
                        $"{x.BuySellKind2},{x.OpenOffsetKind},{x.OrderCondition},{x.OrderPrice},{x.BeforeQty},{x.AfterQty},{x.OkQty},{x.OrderStatus},";
                        yuantaDate = x.AcceptDate;
                        yuantaTime = x.AcceptTime;
                        strResult += $"{yuantaDate.ushtYear}/{yuantaDate.bytMon}/{yuantaDate.bytDay} {yuantaTime.bytHour}:{yuantaTime.bytMin}:{yuantaTime.bytSec}.{yuantaTime.ushtMSec},";
                        strResult += $"{x.ErrorNo},{x.ErrorMessage},{x.OrderNo},{x.ProductType},{x.Seller},{x.TotalMatFee},{x.TotalMatExchTax},{x.TotalMatPremium},{x.DayTradeID},{x.CancelFlag}," +
                        $"{x.ReduceFlag},{x.StkName1},{x.StkName2},{x.TraditionFlag},{x.TRID},{x.CurrencyType},{x.CurrencyType2},{x.BasketNo},{x.MarketNo1},{x.StkCode1},{x.MarketNo2},{x.StkCode2}\r\n";
                    });

                    strResult += "期貨成交筆數: " + result.FutTradeList.Count + "\r\n";

                    result.FutTradeList.ForEach(x =>
                    {
                        strResult += $"{x.Account},{x.MarketNo},{x.MarketName},{x.Commodity1},{x.SettlementMonth1},{x.BuySellKind1},{x.OkQty},{x.MatchPrice1},{x.MatchPrice2},";
                        yuantaTime = x.MatchTime;
                        yuantaDate = x.MatchDate;
                        strResult += $"{yuantaDate.ushtYear}/{yuantaDate.bytMon}/{yuantaDate.bytDay} {yuantaTime.bytHour}:{yuantaTime.bytMin}:{yuantaTime.bytSec}.{yuantaTime.ushtMSec},";
                        strResult += $"{x.OrderNo},{x.StrikePrice1},{x.Commodity2},{x.SettlementMonth2},{x.BuySellKind2},{x.StrikePrice2},{x.RecType},{x.ProductType},{x.OrderPrice},{x.StkName1}," +
                        $"{x.StkName2},{x.DayTradeID},{x.SprMatchPrice},{x.TRID},{x.CurrencyType},{x.CurrencyType2},{x.SubNo}\r\n";
                    });

                    strResult += "國外股票委託筆數:" + result.OVStkOrderList.Count + "\r\n";
                    result.OVStkOrderList.ForEach(x =>
                    {
                        strResult += $"{x.Account},";
                        yuantaDate = x.TradeDate;
                        strResult += $"{yuantaDate.ushtYear}/{yuantaDate.bytMon}/{yuantaDate.bytDay},";
                        strResult += $"{x.MarketNo},{x.MarketName},{x.CompanyNo},{x.StkName},{x.BS},{x.CurrencyType},{x.Price},{x.PriceType},{x.OrderQty},{x.OkQty},{x.OrderStatus},";
                        strResult += $"{x.OrderTime.ToString()},{x.OrderType},{x.OrderNo},{x.Fee},{x.PolarisAMT},{x.ErrorNo},{x.ErrorMessage},{x.CurrencyType2},{x.CancelFlag},{x.ReduceFlag},{x.TraditionFlag},{x.SettleType},{x.BasketNo}\r\n";
                    });

                    strResult += "國外股票成交筆數:" + result.OVStkTradeList.Count + "\r\n";
                    result.OVStkTradeList.ForEach(x =>
                    {
                        strResult += $"{x.Account},{x.MarketNo},{x.MarketName},{x.CompanyNo},{x.StkName},{x.BS},{x.CurrencyType},{x.OkQty},{x.OrderPrice},{x.MatchPrice},";
                        strResult += $"{x.DateTime.ToString()},{x.Fee},{x.OrderNo},{x.SettlementAMT},{x.CurrencyType2}\r\n";
                    });
                    strResult += "國外期貨委託筆數:" + result.OVFutOrderList.Count + "\r\n";
                    result.OVFutOrderList.ForEach(x =>
                    {
                        strResult += $"{x.Account},";
                        yuantaDate = x.TradeDate;
                        strResult += $"{yuantaDate.ushtYear}/{yuantaDate.bytMon}/{yuantaDate.bytDay},";
                        strResult += $"{x.MarketNo},{x.MarketName},{x.CompanyNo},{x.SettlementMonth},{x.StkName},{x.BS},{x.OrderType},{x.Price},{x.TouchPrice},{x.OrderQty},{x.OkQty},{x.OrderStatus},";
                        yuantaDate = x.AcceptDate;
                        yuantaTime = x.AcceptTime;
                        strResult += $"{yuantaDate.ushtYear}/{yuantaDate.bytMon}/{yuantaDate.bytDay} {yuantaTime.bytHour}:{yuantaTime.bytMin}:{yuantaTime.bytSec}.{yuantaTime.ushtMSec},";
                        strResult += $"{x.ErrorNo},{x.ErrorMessage},{x.OrderNo},{x.DayTradeID},{x.CancelFlag},{x.ReduceFlag},{x.UtPrice},{x.UtPrice2},{x.MinPrice2},{x.UtPrice4},{x.UtPrice5},{x.UtPrice6}," +
                        $"{x.TraditionFlag},{x.BasketNo},{x.MarketNo1},{x.StkCode1},{x.CurrencyType},{x.CurrencyType2}\r\n";
                    });

                    strResult += "國外期貨成交筆數:" + result.OVFutTradeList.Count + "\r\n";
                    result.OVFutTradeList.ForEach(x =>
                    {
                        strResult += $"{x.Account},{x.MarketNo},{x.MarketName},{x.CompanyNo},{x.SettlementMonth},{x.StkName},{x.BS},{x.OkQty},{x.OrderPrice},{x.MatchPrice},";
                        yuantaDate = x.MatchDate;
                        yuantaTime = x.MatchTime;
                        strResult += $"{yuantaDate.ushtYear}/{yuantaDate.bytMon}/{yuantaDate.bytDay} {yuantaTime.bytHour}:{yuantaTime.bytMin}:{yuantaTime.bytSec}.{yuantaTime.ushtMSec},";
                        strResult += $"{x.OrderNo},{x.CurrencyType},{x.CurrencyType2}\r\n";
                    });
                }
                catch (Exception ex)
                {
                    strResult = "";
                }

                Console.WriteLine("\n======================");
                Console.WriteLine(strResult);
                Console.WriteLine("======================\n");
                return;
            }

            Console.WriteLine($"[{strIndex}] {Convert.ToString(objValue)}");
        }
    }
    catch (Exception exc)
    {
        Console.WriteLine("OnResponse Error: " + exc.Message);
    }
}
```

#### Response Body

```json
{
  "Result": {
    "StkOrderList": [
      {
        "Account": "S98875005091",
        "TradeDate": "2025/11/27",
        "MarketNo": "TWOTC",
        "MarketName": "上櫃",
        "CompanyNo": "4991",
        "StkName": "環宇-KY",
        "OrderType": "0",
        "BS": "S",
        "Price": "165.0",
        "PriceFlag": "L",
        "BeforeQty": "0",
        "AfterQty": "1000",
        "OkQty": "0",
        "OrderStatus": "10",
        "AcceptDate": "2025/11/26",
        "AcceptTime": "22:42:13.247",
        "OrderNo": "m0033",
        "ErrorNo": "00290",
        "ErrorMessage": "未簽署外國企業來台上市(櫃)有價證券風險預告書，請立即上網簽署",
        "Seller": "0",
        "Channel": "171",
        "APCode": "0",
        "OTax": "0",
        "OCharge": "0",
        "ODueAmt": "0",
        "CancelFlag": "N",
        "ReduceFlag": "N",
        "TraditionFlag": "N",
        "BasketNo": "",
        "TradeCurrency": "TWD",
        "Time_in_Force": "0",
        "Order_Success": "N",
        "Reduce_Flag": "Y",
        "Chg_Prz_Flag": "N",
        "TSE_Cancel": "N",
        "CancelQty": "1000",
        "OR_QTY": "1000",
        "UpdateDate": "2025/11/27",
        "UpdateTime": "8:30:3.880"
      }
    ],
    "StkTradeList": [
      {
        "Account": "S98875005091",
        "MarketNo": "TWSE",
        "MarketName": "上市",
        "CompanyNo": "3711",
        "StkName": "日月光投控",
        "OrderType": "0",
        "BS": "S",
        "OkQty": "1000",
        "OPrice": "196.0",
        "SPrice": "197.0",
        "TradeDate": "2025/11/27",
        "TradeTime": "8:30:4.547",
        "OrderNo": "m0171",
        "TradeCurrency": "TWD",
        "Price_Flag": "2",
        "Exchange_Code": "0"
      }
    ]
    .........
  }
}
```
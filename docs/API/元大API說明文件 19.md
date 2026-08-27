---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E8%A1%8C%E6%83%85/%E5%A0%B1%E5%83%B9%E8%A1%A8%E6%9F%A5%E8%A9%A2/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## GetWatchListAll

報價表查詢

```
bool GetWatchListAll(Account, QuoteList, Lng)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 訂閱帳號 | 證券：S + 分公司代號(4) + 帳號(7)   例如：S98875005091   期貨：F + 分公司代號(7+3) + 帳號(7)   例如：FF021000P001234567 |
| QuoteList | [List\<Quote>](#quote) | 查詢商品清單 |  |
| Lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   \- Normal：Big5   \- UTF8：UTF8   \- SC：簡體中文 |

#### Quote 訂閱商品明細

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MarketType | enumMarketType | 市場類別 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| StockCode | string | 商品代碼 |  |

---

### Output Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| QueryWatchList | [List\<QueryWatchList>](#querywatchlist) | 結果清單 |  |

#### QueryWatchList 報價表物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MarketNo | enumMarketType | 市場代碼 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| StkCode | string | 股票代碼 |  |
| StkName | string | 股票名稱 |  |
| YstPrice | double | 昨收價 |  |
| OpenRefPrice | double | 開盤參考價 |  |
| UpStopPrice | double | 漲停價 |  |
| DownStopPrice | double | 跌停價 |  |
| YstVol | int | 昨量 |  |
| ExtName | string | 擴充名 |  |
| Decimal | short | 小數位數 |  |
| CreditPercent | byte | 融資成數 | 未提供回傳 `0` |
| LenBondPercent | byte | 融券成數 | 未提供回傳 `0` |
| OpenPrice | double | 開盤價 |  |
| HighPrice | double | 最高價 |  |
| LowPrice | double | 最低價 |  |
| BuyPrice | double | 買價 | 市價買： `999999999` |
| TotalOutVol | int | 累計外盤量 |  |
| SellPrice | double | 賣價 | 市價賣： `-999999999` |
| TotalInVol | int | 累計內盤量 |  |
| DealPrice | double | 成交價 |  |
| TotalDealAmt | int | 總成交金額 |  |
| VolFlag | byte | 單量內外盤標記 | `0` ：內盤 / `1` ：外盤 |
| Vol | int | 單量 | 最高位元的Bit，   表示內/外盤的旗標，   0:內盤/1:外盤 |
| TotalVol | int | 總成交量 |  |
| FixedPriceVol | int | 定價量 |  |
| ReserveVol | int | 未平倉量 |  |
| SettlementPrice | double | 結算價 |  |
| HiContractPrice | double | 合約高價 |  |
| LoContractPrice | double | 合約低價 |  |
| OrderBuyCount | int | 委託買進總筆數 |  |
| OrderBuyQty | int | 委託買進總口數 |  |
| OrderSellCount | int | 委託賣出總筆數 |  |
| OrderSellQty | int | 委託賣出總口數 |  |
| DealBuyCount | int | 累計買進成交筆數 |  |
| DealSellCount | int | 累計賣出成交筆數 |  |
| Volatility | int | 波動率 |  |
| Time | TYuantaTime | 時間 | [參考物件-日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantatime) |
| TimeDiff | string | 時差 | 台股為0，（晚＝正值，早＝負值）。   日本比台灣早一小時，時差就是等於-1 |
| StkType2 | byte | 屬性2 | Bit 1: 可轉換公司債   Bit 2: 附認股權公司債   Bit 3: 警示股   Bit 4: 指數記號   Bit 5: 期貨   Bit 6: 個股選擇權   Bit 7: 指數選擇權   Bit 8: 保留 |
| ReserveVolDiff | int | 未平倉量增減 |  |
| BelongCode | string | 所屬產業分類碼 | 01: 水泥工業   02: 食品工業   03: 塑膠工業 |
| IndustryName | string | 產業類股名稱 |  |
| PrincipalPercent | double | 市值 (%) | 小數點兩位數(單位％) |
| UpDownDay | short | 連續漲跌(天) | +：連續漲天數   –：連續跌天數 |
| BidQty | int | 第一買量 |  |
| AskQty | int | 第一賣量 |  |
| PriceTrends | byte | 瞬間價格趨勢 | 10：一般揭示   11：暫緩撮合且瞬間趨跌   12：暫緩撮合且瞬間趨漲   13：試算後延後收盤   14：暫停交易   15：恢復交易 |
| EstDealPrice | double | 盤前揭露價 |  |
| EstDealVol | int | 盤前揭露量 |  |
| EstDealVolFlag | byte | 盤前揭露量內外盤標記 | `0` ：內盤 / `1` ：外盤 |

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
from YuantaOneAPI import YuantaSparkAPITrader, enumLogType, enumMarketType, enumEnvironmentMode, Quote
# 建立 API 物件
objYuantaSparkAPI = YuantaSparkAPITrader()
objYuantaSparkAPI.SetLogType(enumLogType.COMMON)
```

```csharp
using System;
using System.Collections.Generic;
using System.Text;
using System.Threading;
using YuantaOneAPI;

YuantaSparkAPITrader objYuantaSparkAPI = new YuantaSparkAPITrader();
string Account = "S98875005091";
string Password = "1234";
enumEnvironmentMode enumEvenMode = enumEnvironmentMode.UAT;

objYuantaSparkAPI.OnResponse += objApi_OnResponse;
objYuantaSparkAPI.SetLogType(enumLogType.ALL);

objYuantaSparkAPI.Open(enumEvenMode);
Thread.Sleep(1000);
objYuantaSparkAPI.Login(Account, Password);
Thread.Sleep(1000);

List<Quote> QuoteList = new List<Quote>();
Quote quote = new Quote
{
    MarketType = enumMarketType.TWSE,
    StockCode = "2885"
};
QuoteList.Add(quote);

objYuantaSparkAPI.GetWatchListAll(Account, QuoteList);

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

                    case 'GetWatchListAll':
                        WResult = objValue
                        QueryWatchList = WResult.QueryWatchList

                        result += '報價表:\r\n'
                        for i in range(QueryWatchList.Count):
                            #yuantaTime = TYuantaTime()
                            yuantaTime = QueryWatchList[i].Time
                            time= '{0}:{1}:{2}.{3}'.format(str(yuantaTime.Hour), str(yuantaTime.Minute), str(yuantaTime.Second), str(yuantaTime.Millisecond))
                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29},{30},{31},{32},{33},{34},{35},{36},{37},{38},{39},{40},{41},{42},{43},{44},{45},{46},{47},{48},{49}\r\n'.format(
                                QueryWatchList[i].MarketNo,QueryWatchList[i].StkCode,QueryWatchList[i].StkName,str(QueryWatchList[i].YstPrice),str(QueryWatchList[i].OpenRefPrice),str(QueryWatchList[i].UpStopPrice),
                            str(QueryWatchList[i].DownStopPrice),str(QueryWatchList[i].YstVol),QueryWatchList[i].ExtName,str(QueryWatchList[i].Decimal),int(QueryWatchList[i].CreditPercent),int(QueryWatchList[i].LenBondPercent),
                            str(QueryWatchList[i].OpenPrice),QueryWatchList[i].HighPrice,str(QueryWatchList[i].LowPrice),str(QueryWatchList[i].BuyPrice),str(QueryWatchList[i].TotalOutVol),str(QueryWatchList[i].SellPrice),
                            str(QueryWatchList[i].TotalInVol),str(QueryWatchList[i].DealPrice),str(QueryWatchList[i].TotalDealAmt),str(QueryWatchList[i].VolFlag),str(QueryWatchList[i].Vol),int(QueryWatchList[i].TotalVol),
                            str(QueryWatchList[i].FixedPriceVol),str(QueryWatchList[i].ReserveVol),str(QueryWatchList[i].SettlementPrice),str(QueryWatchList[i].HiContractPrice),QueryWatchList[i].LoContractPrice,
                            str(QueryWatchList[i].OrderBuyCount),str(QueryWatchList[i].OrderBuyQty),str(QueryWatchList[i].OrderSellCount),str(QueryWatchList[i].OrderSellQty),str(QueryWatchList[i].DealBuyCount),str(QueryWatchList[i].DealSellCount),
                            str(QueryWatchList[i].Volatility),time,QueryWatchList[i].TimeDiff,str(QueryWatchList[i].StkType2),str(QueryWatchList[i].ReserveVolDiff),QueryWatchList[i].BelongCode,QueryWatchList[i].IndustryName,
                            str(QueryWatchList[i].PrincipalPercent),str(QueryWatchList[i].UpDownDay),str(QueryWatchList[i].BidQty),str(QueryWatchList[i].AskQty),str(QueryWatchList[i].PriceTrends),str(QueryWatchList[i].EstDealPrice),
                            str(QueryWatchList[i].EstDealVol),str(QueryWatchList[i].EstDealVolFlag))

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

#報價表查詢
quoteList = List[Quote]()
quote = Quote()
quote.MarketType = enumMarketType.TWSE
quote.StockCode = '2885'
quoteList.Add(quote)
objYuantaSparkAPI.GetWatchListAll('S98875005091', quoteList)

# 保持程式運行
while True:
    time.sleep(1)
```

```swift
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
            if (strIndex == "GetWatchListAll")
            {
                var result = (QueryWatchListResult)objValue;

                try
                {
                    strResult = "===============\r\n50.0.0.16 報價表\r\n===============";
                    result.QueryWatchList.ForEach(data =>
                    {
                        strResult += String.Format("{0}\r\n市場代碼:{1} 股票代碼:{2} 股票名稱:{3}\r\n昨收價:{4}\r\n開盤參考價:{5}\r\n漲停價:{6}\r\n跌停價:{7}\r\n昨量:{8}" +
                            "\r\n擴充名:{9}\r\n小數位數:{10}\r\n融資成數:{11}\r\n融券成數:{12}\r\n開盤價:{13}\r\n最高價:{14}\r\n最低價:{15}\r\n買價:{16}\r\n累計外盤量:{17}" +
                            "\r\n賣價:{18}\r\n累計內盤量:{19}\r\n成交價:{20}\r\n總成交金額:{21}\r\n單量內外盤標記:{22}\r\n單量:{23}\r\n總成交量:{24}\r\n定價量:{25}" +
                            "\r\n未平倉量:{26}\r\n結算價:{27}\r\n合約高價:{28}\r\n合約低價:{29}\r\n委託買進總筆數:{30}\r\n委託買進總口數:{31}\r\n委託賣出總筆數:{32}" +
                            "\r\n委託賣出總口數:{33}\r\n累計買進成交筆數:{34}\r\n累計賣出成交筆數:{35}\r\n波動率:{36}\r\n時間:{37}\r\n時差:{38}\r\n屬性2:{39}\r\n未平倉量增減:{40}" +
                            "\r\n所屬產業分類碼:{41}\r\n產業類股名稱:{42}\r\n市值(%):{43}\r\n連續漲跌(天):{44}\r\n第一買量:{45}\r\n第一賣量:{46}\r\n瞬間價格趨勢:{47}" +
                            "\r\n盤前揭露價:{48}\r\n盤前揭露量:{49}\r\n盤前揭露量內外盤標記:{50}\r\n",
                            string.Empty, data.MarketNo, data.StkCode, data.StkName, data.YstPrice, data.OpenRefPrice, data.UpStopPrice, data.DownStopPrice, data.YstVol,
                            data.ExtName, data.Decimal, data.CreditPercent, data.LenBondPercent, data.OpenPrice, data.HighPrice, data.LowPrice, data.BuyPrice, data.TotalOutVol,
                            data.SellPrice, data.TotalInVol, data.DealPrice, data.TotalDealAmt, data.VolFlag, data.Vol, data.TotalVol, data.FixedPriceVol, data.ReserveVol,
                            data.SettlementPrice, data.HiContractPrice, data.LoContractPrice, data.OrderBuyCount, data.OrderBuyQty, data.OrderSellCount, data.OrderSellQty,
                            data.DealBuyCount, data.DealSellCount, data.Volatility, data.Time.ToLongTimeString(), data.TimeDiff, data.StkType2,
                            data.ReserveVolDiff, data.BelongCode, data.IndustryName, data.PrincipalPercent, data.UpDownDay, data.BidQty, data.AskQty, data.PriceTrends, data.EstDealPrice,
                            data.EstDealVol, data.EstDealVolFlag);
                    });
                }
                catch
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
    "QueryWatchList": [
      {
        "MarketNo": "TWSE",
        "StkCode": "2885",
        "StkName": "元大金",
        "YstPrice": "36.0",
        "OpenRefPrice": "36.0",
        "UpStopPrice": "39.6",
        "DownStopPrice": "32.4",
        "YstVol": "22442",
        "ExtName": "2885",
        "Decimal": "4",
        "CreditPercent": "0",
        "LenBondPercent": "0",
        "OpenPrice": "36.0",
        "HighPrice": "36.7",
        "LowPrice": "35.75",
        "BuyPrice": "36.5",
        "TotalOutVol": "15413",
        "SellPrice": "36.55",
        "TotalInVol": "9639",
        "DealPrice": "36.5",
        "TotalDealAmt": "90907",
        "VolFlag": "0",
        "Vol": "21",
        "TotalVol": "25052",
        "FixedPriceVol": "21",
        "ReserveVol": "0",
        "SettlementPrice": "0.0",
        "HiContractPrice": "0.0",
        "LoContractPrice": "0.0",
        "OrderBuyCount": "0",
        "OrderBuyQty": "0",
        "OrderSellCount": "0",
        "OrderSellQty": "0",
        "DealBuyCount": "0",
        "DealSellCount": "0",
        "Volatility": "0",
        "Time": "14:30:0.0",
        "TimeDiff": "0",
        "StkType2": "0",
        "ReserveVolDiff": "17",
        "BelongCode": "金融保險",
        "IndustryName": "0.54",
        "PrincipalPercent": "1",
        "UpDownDay": "14",
        "BidQty": "149",
        "AskQty": "0",
        "PriceTrends": "36.5",
        "EstDealPrice": "2826",
        "EstDealVol": "0",
        "EstDealVolFlag": "0"
      }
    ]
  }
}
```
---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%B8%B3%E5%8B%99/%E8%82%A1%E7%A5%A8%E5%BA%AB%E5%AD%98%E7%B6%9C%E5%90%88%E7%B8%BD%E8%A1%A8/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## GetStoreSummary

股票庫存綜合總表

```
bool GetStoreSummary(Account, lng)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 | 證券:S+分公司代號(4)+帳號(7)   例如 S98875005091      註1 |
| lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   \- Normal：Big5   \- UTF8：UTF8   \- SC：簡體中文 |

> [!tip] Tip
> 註1：限證券使用

---

### Output Parameters

#### StoreSummaryResult 查詢股票庫存總表結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| StkStoreList | List\<StkStore> | 現貨庫存清單 |  |
| OVStkStoreList | List\<OVStkStore> | 國外股票庫存清單 |  |

#### StkStore 現貨庫存物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 |  |
| TradeKind | Int | 交易種類 | 0:現股   3:資買   4:券賣   6:借券 |
| MarketNo | enumMarketType | 市場代碼 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| MarketName | string | 市場名稱 | 上市/上櫃 |
| StkCode | string | 股票代號 |  |
| StkName | string | 股票名稱 |  |
| StockQty | Long | 股數 |  |
| Price | double | 成交均價 |  |
| Cost | double | 持有成本 |  |
| Interest | Long | 預估利息 |  |
| BuyNotInNos | Int | 買進未入帳股數 |  |
| SellNotInNos | Int | 賣出未入帳股數 |  |
| TradingQty | Long | 可交易股數 |  |
| Loan | Long | 資保證金/券擔保價品 |  |
| TaxRate | double | 交易稅率 | 0:Reits 股票   1:基金,認股權證,債券,存託憑證   3:一般股票(單位千分之一) |
| LotSize | Int | 交易單位 | 每手股數 |
| MarketPrice | double | 市價 | 盤前市價若為0則給開盤參考價 |
| Decimal | Int | 小數位數 | +為小數位數   \-為分數分母   0為整數 |
| StkType1 | Int | 屬性1 | Bit 1: 管理商品   Bit 2: 交易記號   Bit 3: 受益憑證   Bit 4: ETF商品   Bit 5: 權證記號   Bit 6: 特別股   Bit 7: 存託憑證   Bit 8: 外國股票 |
| StkType2 | Int | 屬性2 | Bit 1: 可轉換公司債   Bit 2: 附認股權公司債   Bit 3: 警示股   Bit 4: 指數記號   Bit 5: 期貨   Bit 6: 個股選擇權   Bit 7: 指數選擇權   Bit 8: 保留 |
| BuyPrice | double | 買價 |  |
| SellPrice | double | 賣價 |  |
| UpStopPrice | double | 漲停價 |  |
| DownStopPrice | double | 跌停價 |  |
| PriceMultiplier | uint | 計價倍數 | 1，乘1倍   10，乘10倍 |
| CurrencyType | string | 幣別 | TWD   CNY   HKD   USD |
| CDQTY | Long | 借貸股數 |  |
| OddTradingQty | Long | 零股可下單股數 |  |
| ReturnAmt | double | 未實現損益 |  |
| MarketAmt | double | 股票市值 |  |

#### OVStkStore 國外股票庫存物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 現貨帳號 |  |
| CurrencyType | string | 幣別 | USD:美元   HKD:港幣 |
| MarketNo | enumMarketType | 市場代碼 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| MarketName | string | 市場名稱 |  |
| StkCode | string | 股票代號 |  |
| StkName | string | 股票名稱 |  |
| StkFullName | string | 股票全名 |  |
| StockQty | Long | 庫存股數 |  |
| TradingQty | Long | 可交易股數 |  |
| Price | double | 成交均價 |  |
| Cost | double | 持有成本 |  |
| CloseRate | double | 匯率 |  |
| RateKind | Int | 匯率運算模式 | 1:除以匯率   2:乘以匯率 |
| LotSize | int | 交易單位 | 每手股數 |
| MarketPrice | double | 市價 | 固定為0,前端自行根據登入權限查詢 |
| Decimal | Int | 小數位數 | +為小數位數   \-為分數分母   0為整數 |
| BuyPrice | int | 買價 |  |
| SellPrice | int | 賣價 |  |

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
enumEnvironmentMode enumEvenMode = enumEnvironmentMode.UAT;

objYuantaSparkAPI.OnResponse += objApi_OnResponse;
objYuantaSparkAPI.SetLogType(enumLogType.ALL);

objYuantaSparkAPI.Open(enumEvenMode);
Thread.Sleep(1000);

objYuantaSparkAPI.Login(Account, Password);
Thread.Sleep(1000);

objYuantaSparkAPI.GetStoreSummary(Account);
Thread.Sleep(2000);
```

#### Onresponse

```python
# 回應事件
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

                    case 'GetStoreSummary':
                        sResult = objValue
                        stkList = sResult.StkStoreList
                        OVstkList = sResult.OVStkStoreList

                        result += '股票庫存綜合總表:\n'
                        # 現貨庫存
                        result += f'現貨庫存筆數:{stkList.Count}\n'
                        for i in range(stkList.Count):
                            result +='{0},{1},{2},{3},{4},{5},{6},{7}\r\n'.format(int(stkList[i].TradeKind),str(stkList[i].MarketNo),stkList[i].StkCode,stkList[i].StkName,stkList[i].StockQty,stkList[i].Price,stkList[i].ReturnAmt,stkList[i].MarketAmt)
                            #所有欄位資料太多印不出來
                            """ result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14} {15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29}\r\n'.format(
                                stkList[i].Account,str(stkList[i].TradeKind),str(stkList[i].MarketNo),stkList[i].MarketName,stkList[i].StkCode,stkList[i].StkName,str(stkList[i].StockQty),str(stkList[i].Price),str(stkList[i].Cost),
                                str(stkList[i].Interest),str(stkList[i].BuyNotInNos),str(stkList[i].SellNotInNos),str(stkList[i].TradingQty),str(stkList[i].Loan),float(stkList[i].TaxRate),str(stkList[i].LotSize),float(stkList[i].MarketPrice),
                                int(stkList[i].Decimal),int(stkList[i].StkType1),int(stkList[i].StkType2),float(stkList[i].BuyPrice),float(stkList[i].SellPrice),float(stkList[i].UpStopPrice),float(stkList[i].DownStopPrice),
                                str(stkList[i].PriceMultiplier),stkList[i].CurrencyType,str(stkList[i].CDQTY),str(stkList[i].OddTradingQty),float(stkList[i].ReturnAmt),float(stkList[i].MarketAmt)) """

                        # 國外現貨庫存
                        result += f'國外現貨庫存筆數:{OVstkList.Count}\n'
                        for i in range(OVstkList.Count):
                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13} {14},{15},{16},{17}\r\n'.format(
                                OVstkList[i].Account,OVstkList[i].CurrencyType,str(OVstkList[i].MarketNo),OVstkList[i].MarketName,OVstkList[i].StkCode,OVstkList[i].StkName,OVstkList[i].StkFullName,str(OVstkList[i].StockQty),
                                str(OVstkList[i].TradingQty),str(OVstkList[i].Price),str(OVstkList[i].Cost),str(OVstkList[i].CloseRate),int(OVstkList[i].RateKind),str(OVstkList[i].LotSize),float(OVstkList[i].MarketPrice),
                                int(OVstkList[i].Decimal),str(OVstkList[i].BuyPrice),str(OVstkList[i].SellPrice))

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

#股票庫存綜合總表
objYuantaSparkAPI.GetStoreSummary('S98875005091')

# 保持程式運行
while True:
    time.sleep(2)
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
        }
        if (strIndex == "GetStoreSummary")
        {
            var result = (StoreSummaryResult)objValue;

            strResult += "庫存綜合總表筆數: " + result.StkStoreList.Count + "\r\n";
            result.StkStoreList.ForEach(x =>
            {
                strResult += $"{x.Account},{x.TradeKind},{x.MarketNo},{x.MarketName},{x.StkCode},{x.StkName},{x.StockQty},{x.Price},{x.Cost},{x.Interest},{x.BuyNotInNos},{x.SellNotInNos}," +
                            $"{x.TradingQty},{x.Loan},{x.TaxRate},{x.LotSize},{x.MarketPrice},{x.Decimal},{x.StkType1},{x.StkType2},{x.BuyPrice},{x.SellPrice},{x.UpStopPrice},{x.DownStopPrice}," +
                            $"{x.PriceMultiplier},{x.CurrencyType},{x.CDQTY},{x.OddTradingQty},{x.ReturnAmt},{x.MarketAmt}\r\n";
            });

            strResult += "國外股票庫存筆數: " + result.OVStkStoreList.Count + "\r\n";
            result.OVStkStoreList.ForEach(x =>
            {
                strResult += $"{x.Account},{x.CurrencyType},{x.MarketNo},{x.MarketName},{x.StkCode},{x.StkName},{x.StkFullName},{x.StockQty},{x.TradingQty},{x.Price},{x.Cost},{x.CloseRate}," +
                            $"{x.RateKind},{x.LotSize},{x.MarketPrice},{x.Decimal},{x.BuyPrice},{x.SellPrice}\r\n";
            });

            Console.WriteLine("\n======================");
            Console.WriteLine(strResult);
            Console.WriteLine("======================\n");
            return;
        }
        Console.WriteLine($"{Convert.ToString(objValue)}");
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
    "StkStoreList": [
      {
        "TradeKind": "0",
        "MarketNo": "TWSE",
        "StkCode": "0050",
        "StkName": "元大台灣50",
        "StockQty": "4901285512",
        "Price": "0.0077",
        "ReturnAmt": "0.0",
        "MarketAmt": "0.0"
      }
    ],
    "OVStkStoreList": []
  }
}
```
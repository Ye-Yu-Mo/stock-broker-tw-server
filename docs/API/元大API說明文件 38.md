---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%B8%B3%E5%8B%99/%E6%B2%96%E9%8A%B7%E6%98%8E%E7%B4%B0%E6%9F%A5%E8%A9%A2/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## GetStkHistoryReportReversal

沖銷明細查詢

```
bool GetStkHistoryReportReversal(Account, ReGainLoss, lng)
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
| ReGainLoss | RealizedGainLoss | 已實現損益 | 註2 |
| lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   \- Normal：Big5   \- UTF8：UTF8   \- SC：簡體中文 |

> [!tip] Tip
> 註1：限證券使用  
> 註2：資料由已實現損益查詢

---

### Output Parameters

#### ReversalReportResult 沖銷明細查詢結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| ReversalReportList | List\<ReversalReport> | 結果清單 |  |

#### ReversalReport 沖銷明細物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 |  |
| ReversalDate | string | 被沖抵成交日 | yyyy/MM/dd |
| ReversalPrice | double | 被沖抵成交價 |  |
| ReversalQty | long | 被沖抵股數 |  |
| GlAmt | double | 沖抵損益 |  |

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
from YuantaOneAPI import YuantaSparkAPITrader, enumLogType, enumMarketType, enumEnvironmentMode, enumStkTickSelectType

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
List<RealizedGainLoss> RealizedGainLossList = new List<RealizedGainLoss>();
objYuantaSparkAPI.OnResponse += objApi_OnResponse;
objYuantaSparkAPI.SetLogType(enumLogType.ALL);

objYuantaSparkAPI.Open(enumEvenMode);
Thread.Sleep(1000);

objYuantaSparkAPI.Login(Account, Password);
Thread.Sleep(2000);

//先呼叫已實現損益
objYuantaSparkAPI.GetHisRealizedGainLoss(Account, "2025/06/01", "2025/06/12");
Thread.Sleep(2000);

foreach (var item in RealizedGainLossList)
{
    if (item.StkCode == "2885") 
    {
        objYuantaSparkAPI.GetStkHistoryReportReversal(Account, item);
    }
}
```

#### Onresponse

```python
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

                    case 'GetHisRealizedGainLoss':
                        GResult = objValue
                        global RealizedGainLossList
                        RealizedGainLossList = GResult.RealizedGainLossList
                        gResult = RealizedGainLossList

                        result += '已實現損益查詢結果:\r\n'
                        for i in range(gResult.Count):  
                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14}\r\n'.format(gResult[i].Account,gResult[i].MarketNo,gResult[i].StkCode,gResult[i].TradeDate,gResult[i].TradeKind,gResult[i].Price,gResult[i].Qty,gResult[i].ProfitLoss,gResult[i].OrderNo,gResult[i].TermSplit,gResult[i].TermExt,gResult[i].Charge,gResult[i].Cost,gResult[i].Tax,gResult[i].TotalAMT)

                    case 'GetStkHistoryReportReversal':
                        GResult = objValue
                        gResult = GResult.ReversalReportList

                        result = ''
                        result += '沖銷明細查詢:\r\n'
                        for i in range(gResult.Count):  
                            result += '{0},{1},{2},{3},{4}\r\n'.format(gResult[i].Account,gResult[i].ReversalDate,gResult[i].ReversalPrice,gResult[i].ReversalQty,gResult[i].GlAmt)

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
#先呼叫已實現損益
objYuantaSparkAPI.GetHisRealizedGainLoss('S98875005091','2025/06/01','2025/06/12')  
time.sleep(2)
for item in RealizedGainLossList:
    if "2885" in str(item.StkCode):  # 只顯示 2885 的資料
        print(f"帳號={item.Account}, 股票代號={item.StkCode}")
        objYuantaSparkAPI.GetStkHistoryReportReversal('S98875005091', item)

# 保持程式運行
while True:
    time.sleep(2)
```

```csharp
void objApi_OnResponse(int intMark, uint dwIndex, string strIndex, object objHandle, object objValue)
{
    try
    {
        string strResult = "";
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

            if (strIndex == "GetHisRealizedGainLoss")
            {
                var result = (RealizedGainLossResult)objValue;
                try
                {
                    strResult += $"已實現損益查詢: {result.RealizedGainLossList.Count}筆\r\n";
                    result.RealizedGainLossList.ForEach(r =>
                    {
                        strResult += $"{r.Account} {r.MarketNo} {r.StkCode} {r.TradeDate} {r.TradeKind} {r.Price} {r.Qty} {r.ProfitLoss} {r.OrderNo} {r.TermSplit} {r.TermExt} {r.Charge} {r.Cost} {r.Tax} {r.TotalAMT}\r\n";
                    });
                    RealizedGainLossList = result.RealizedGainLossList;

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

            if (strIndex == "GetStkHistoryReportReversal")
            {
                var result = (ReversalReportResult)objValue;
                try
                {
                    strResult += $"沖銷明細查詢: {result.ReversalReportList.Count}筆\r\n";
                    result.ReversalReportList.ForEach(r =>
                    {
                        strResult += $"{r.Account} {r.ReversalDate} {r.ReversalPrice} {r.ReversalQty} {r.GlAmt}\r\n";
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

        }
            Console.WriteLine($"[{strIndex}] {Convert.ToString(objValue)}");
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
    "ReversalReportList": [
      {
        "Account": "S98875005091",
        "ReversalDate": "2020/12/10",
        "ReversalPrice": "17.9",
        "ReversalQty": "25",
        "GlAmt": "301"
      }
    ]
  }
}
```
---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E8%A1%8C%E6%83%85/K%E7%B7%9A%E6%9F%A5%E8%A9%A2/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## GetKLine

K線查詢

```
bool GetKLine(Account, KLineType, MarketType, StkCode , SDate, EDate, lng)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 | 證券:S+分公司代號(4)+帳號(7)   例如 S98875005091      期貨:F+分公司代號(7+3)+帳號(7)   例如 FF021000P001234567 |
| KLineType | KLineType | K線周期 | [參考列舉物件-K線周期](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#klinetype-k) |
| MarketType | enumMarketType | 市場類別 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype)   註1 |
| StkCode | string | 商品代號 |  |
| Sdate | string | 開始時間 | yyyy/MM/dd   註2 |
| Edate | string | 結束時間 | yyyy/MM/dd   註2 |
| lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   \- Normal：Big5   \- UTF8：UTF8   \- SC：簡體中文 |

> [!tip] Tip
> 註1：僅提供台股上市櫃商品查詢  
> 註2：查詢限制

---

### Output Parameters

#### KLineResult K線查詢結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MarketNo | enumMarketType | 市場代碼 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| StockCode | string | 商品代碼 |  |
| KLineList | List< KLine> | 結果清單 |  |

#### Kline K線物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| TimeStamp | DateTime | 時間戳記 |  |
| OpenPrice | double | 開盤價 |  |
| HighPrice | double | 最高價 |  |
| LowPrice | double | 最低價 |  |
| ClosePrice | double | 收盤價 |  |
| DealVol | int | 成交量 |  |

#### K線種類查詢限制

| K線種類 | 單次查詢限制 | 最大查詢區間限制 |
| --- | --- | --- |
| 1分k | 1天 | 20天 |
| 5,15,30,60分k | 5天 | 100天 |
| 日k | 1年 | 10年 |
| 周k | 5年 | 10年 |
| 月k | 10年 | 10年 |

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
from YuantaOneAPI import (YuantaSparkAPITrader, enumLogType, 
                        enumMarketType, enumEnvironmentMode, enumStkTickSelectType,
                        KLineType)

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

// K線查詢
KLineType klineType = (KLineType)11;            // 日K線
enumMarketType market = enumMarketType.TWSE;    // 市場代碼
string stk = "2885";                                      // 股票代號
string sDate = "2026/01/01";                    // 查詢起始日期
string eDate = "2026/03/31";                    // 查詢結束日期

objYuantaSparkAPI.GetKLine(Account, klineType, market, stk, sDate, eDate);
Thread.Sleep(2000);
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

                    case 'GetKLine':
                        KResult = objValue
                        kResult = KResult.KLineList

                        result = ''
                        result += 'K線查詢結果:\r\n'
                        result += '市場代碼:{0}, 商品代碼:{1}\r\n'.format(KResult.MarketNo, KResult.StockCode)
                        for i in range(kResult.Count):  
                            result += '{0},{1},{2},{3},{4},{5}\r\n'.format(kResult[i].TimeStamp,kResult[i].OpenPrice,kResult[i].HighPrice,kResult[i].LowPrice,kResult[i].ClosePrice,kResult[i].DealVol)

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

daily_kline_type = KLineType(11)    #日K
#weekly_kline_type = KLineType(12)   #週K
#monthly_kline_type = KLineType(13)  #月K
objYuantaSparkAPI.GetKLine('S98875005091', daily_kline_type, enumMarketType.TWSE, "2885", "2025/01/01", "2025/03/31")
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
                    strResult += $"帳號筆數: {intCount}{Environment.NewLine}";
                    result.LoginList.ForEach(r => strResult += $"{r.Account},{r.Name},{r.InvestorID},{r.SellerNo}\r\n");
                }
                else
                {
                    Account = "";
                }

                Console.WriteLine("\n======================");
                Console.WriteLine(strResult);
                Console.WriteLine("======================\n");
                return;
            }

            if (strIndex == "GetKLine")
            {
                var result = (KLineResult)objValue;
                try
                {
                    strResult += "K線查詢:\r\n";
                    strResult += $"{result.MarketNo} {result.StockCode}\r\n";
                    result.KLineList?.ForEach(k =>
                    {
                        strResult += $"{k.TimeStamp} {k.OpenPrice} {k.HighPrice} {k.LowPrice} {k.ClosePrice} {k.DealVol}\r\n";
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
    "MarketNo": "TWSE",
    "StockCode": "2885",
    "KLineList": [
      {
        "TimeStamp": "2026/01/27",
        "OpenPrice": "100.00",
        "HighPrice": "105.00",
        "LowPrice": "98.00",
        "ClosePrice": "103.00",
        "DealVol": "53855234"
      }
    ]
  }
}
```
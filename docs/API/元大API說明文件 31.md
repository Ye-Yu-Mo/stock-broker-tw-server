---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E6%A2%9D%E4%BB%B6%E5%96%AE/%E6%AD%B7%E5%8F%B2%E7%AD%96%E7%95%A5%E6%9F%A5%E8%A9%A2/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## GetHisConditionStrategy

歷史策略查詢

```
bool GetHisConditionStrategy(Account, StrategyType, StkCode, SDate, EDate, lng)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| **Name** | **Type** | **Description** | **Memo** |
| --- | --- | --- | --- |
| Account | string | 帳號 | 證券:S+分公司代號(4)+帳號(7)   例如 S98875005091 |
| StrategyType | int | 策略類型 | 1:停損利   2:移動鎖利   3:二擇一   4:母子單   5:多條件   6.全部 |
| StkCode | string | 商品代號 | **預設為空字串**   空字串則全查 |
| SDate | string | 起始日 | yyyy/MM/dd |
| EDate | string | 終止日 | yyyy/MM/dd |
| lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   \- Normal：Big5   \- UTF8：UTF8   \- SC：簡體中文 |

---

### Output Parameters

#### HisConditionStrategyResult 歷史策略查詢結果

| **Name** | **Type** | **Description** | **Memo** |
| --- | --- | --- | --- |
| HisConditionStrategyList | List\<HisConditionStrategy> | 結果清單 |  |

#### HisConditionStrategy 歷史策略結果物件

| **Name** | **Type** | **Description** | **Memo** |
| --- | --- | --- | --- |
| Account | string | 帳號 |  |
| StrategyType | StrategyType | 策略類型 | [參考列舉物件-條件單類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#strategytype) |
| StrategyNo | string | 策略編號 |  |
| OrdDateTime | DateTime | 設定日期 |  |
| TermiateDate | string | 結束日期 | yyyy/MM/dd |
| CancelDate | string | 刪除時間 | yyyy/MM/dd HH:mm |
| StrategyStatus | SStatus | 條件單狀態 | [參考列舉物件-策略狀態](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#sstatus) |
| OrdStatus | string | 委託狀態 |  |
| MarketType | string | 市場別 |  |
| StkCode | string | 委託商品代號 |  |
| Condition | string | 條件設定 | 母子單/多條件詳細條件，請至明細查詢 |
| OrderKind | string | 委託買賣種類 | 委託種類+買賣別+委託時效 |
| Price | string | 下單價格 |  |
| OrderQty | long | 設定股數 |  |
| DealQty | long | 成交股數 |  |
| RestQty | long | 剩餘股數 |  |
| SDate | string | 有效期限(起日) | yyyy/MM/dd |
| EDate | string | 有效期限(迄日) | yyyy/MM/dd |
| OrderTypeMsg | string | 下單方式 |  |
| HighPx | double | 區間高點 | 僅移動鎖利用，預設0 |
| TriggerPx | string | 觸發價格 | 僅停損利、移動鎖利、二擇一用   其他單別顯示-- |
| DetailList | List\<ConditionStrategyDetail> | 查詢明細清單 |  |

#### ConditionStrategyDetail 查詢明細物件

| **Name** | **Type** | **Description** | **Memo** |
| --- | --- | --- | --- |
| DealTime | string | 成交時間 | yyyy/MM/dd |
| OrderPrice | string | 委託價格 |  |
| AveragePrice | double | 成交均價 |  |
| DealQty | long | 成交股數 |  |
| Memo | string | 備註 |  |
| TrigTime | string | 觸發時間 | HH:mm   僅母子單、多條件用   其他單別顯示-- |
| TrigCondition | string | 觸發條件 | 僅母子單、多條件用   其他單別顯示-- |

> [!tip] Tip
> 註1：資料上限200筆  
> 註2：API不提供長效單的歷史策略查詢，長效單請透過其他電子平台查詢  
> 註3：限近兩年之查詢，一次查詢起訖日限一年內

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
                        enumMarketType, enumEnvironmentMode, enumStkTickSelectType)

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

// 策略類型：1:停損利 2:移動鎖利 3:二擇一 4:母子單 5:多條件
int strategyType = 4;
string stk = " ";                           // 空白表示查全部，填股票代號則查指定股票
string sDate = "2025/01/01";               // 查詢起始日期
string eDate = "2025/03/31";               // 查詢結束日期

objYuantaSparkAPI.GetHisConditionStrategy(Account, strategyType, stk, sDate, eDate);
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

                    case 'GetHisConditionStrategy':
                        GResult = objValue
                        gResult = GResult.HisConditionStrategyList

                        result = ''
                        result += "歷史策略查詢結果:\r\n"

                        for i in range(gResult.Count):
                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20}\r\n'.format(
                                gResult[i].Account,gResult[i].StrategyType,gResult[i].StrategyNo,gResult[i].OrdDateTime,gResult[i].TermiateDate,
                                gResult[i].CancelDate,gResult[i].StrategyStatus,gResult[i].OrdStatus,gResult[i].MarketType,gResult[i].StkCode,
                                gResult[i].Condition,gResult[i].OrderKind,gResult[i].Price,gResult[i].OrderQty,gResult[i].DealQty,
                                gResult[i].RestQty,gResult[i].SDate,gResult[i].EDate,gResult[i].OrderTypeMsg,gResult[i].HighPx,gResult[i].TriggerPx)
                            dList = gResult[i].DetailList
                            for j in range(dList.Count):
                                result += '  {0},{1},{2},{3},{4},{5},{6}\r\n'.format(
                                    dList[j].DealTime,dList[j].OrderPrice,dList[j].AveragePrice,dList[j].DealQty,
                                    dList[j].Memo,dList[j].TrigTime,dList[j].TrigCondition)

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
objYuantaSparkAPI.GetHisConditionStrategy('S98875005091', 1, " ", "2025/03/01", "2025/04/30") # 策略類型: 1:停損利 2:移動鎖利 3:二擇一 4:母子單 5:多條件 6:全部

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

            if (strIndex == "GetHisConditionStrategy")
            {
                var result = (HisConditionStrategyResult)objValue;
                try
                {
                    strResult += "歷史策略查詢:\r\n";
                    result.HisConditionStrategyList?.ForEach(c =>
                    {
                        strResult += $"{c.Account} {c.StrategyType.GetDescriptionName()} {c.StrategyNo} " +
                                    $"{c.OrdDateTime:yyyy/MM/dd HH:mm:ss} {c.TermiateDate} {c.CancelDate} " +
                                    $"{c.StrategyStatus.GetDescriptionName()} {c.OrdStatus} {c.MarketType} " +
                                    $"{c.StkCode} {c.Condition} {c.OrderKind} {c.Price} {c.OrderQty} " +
                                    $"{c.DealQty} {c.RestQty} {c.SDate} {c.EDate} " +
                                    $"{c.OrderTypeMsg} {c.HighPx} {c.TriggerPx}\r\n";

                        c.DetailList.ForEach(d =>
                        {
                            strResult += $"  [{d.DealTime} {d.OrderPrice} {d.AveragePrice} " +
                                        $"{d.DealQty} {d.Memo} {d.TrigTime} {d.TrigCondition}]\r\n";
                        });
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
    "HisConditionStrategyList": [
      {
        "Account": "S98875005091",
        "StrategyType": "3",
        "StrategyNo": "k263F000000050",
        "OrdDateTime": "2025/01/15 09:30:00",
        "TermiateDate": "2025/03/15",
        "CancelDate": "2025/03/15 14:30:00",
        "StrategyStatus": "2",
        "OrdStatus": "0",
        "MarketType": "TWSE",
        "StkCode": "2885",
        "Condition": "1",
        "OrderKind": "B",
        "Price": "46.2",
        "OrderQty": "10",
        "DealQty": "10",
        "RestQty": "0",
        "SDate": "2025/01/01",
        "EDate": "2025/03/31",
        "OrderTypeMsg": "限價",
        "HighPx": "47.0",
        "TriggerPx": "46.2",
        "DetailList": [
          {
            "DealTime": "2025/03/15 10:30:00",
            "OrderPrice": "46.2",
            "AveragePrice": "46.2",
            "DealQty": "10",
            "Memo": "條件觸發成交",
            "TrigTime": "2025/03/15 10:29:00",
            "TrigCondition": "價格>=46.2"
          }
        ]
      }
    ]
  }
}
```
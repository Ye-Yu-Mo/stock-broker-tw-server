---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%B8%B3%E5%8B%99/%E6%9C%9F%E8%B2%A8%E4%BF%9D%E8%AD%89%E9%87%91%E6%9C%80%E4%BD%B3%E5%8C%96%E6%9F%A5%E8%A9%A2/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## GetFutDepositOptimum

期貨保證金最佳化查詢

```
bool GetFutDepositOptimum(Account, lng)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 | 期貨:F+分公司代號(7+3)+帳號(7)   例如 FF021000P001234567 |
| Lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   \- Normal：Big5   \- UTF8：UTF8   \- SC：簡體中文 |

---

### Output Parameters

#### DepositOptimumResult 期貨保證金最佳化查詢結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| DepositOptimumList | [List\<DepositOptimum>](#depositoptimum) | 結果清單 |  |

#### DepositOptimum 期貨保證金最佳化物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| StrategyID | Byte | 策略ID | 6.買賣權混合部位(跨式,勒式)   7.多頭價差   8.Put空頭價差   9.溫跌作莊   10.溫漲作莊   11.Call時間價差   12.Put時間價差 |
| FutAccountInfo | string | 期貨帳號 |  |
| Qty | Short | 口數 |  |
| BuySell1 | string | 買賣別1 | B, S |
| BuySell2 | string | 買賣別2 | B, S |
| DealPrice1 | double | 成交價1 | 此值即為市價 |
| DealPrice2 | double | 成交價2 | 此值即為市價 |
| Decimal1 | Short | 小數位數1 | +為小數位數,-為分數分母,0為整數 |
| CurrentIM1 | Int | 商品一保證金 |  |
| CurrentIM2 | Int | 商品二保證金 |  |
| SaveIM | Int | 可節省保證金 |  |
| CommodityID1 | string | 商品ID1 | TXO |
| CallPut1 | string | 買賣權1 | C/P |
| SettlementMonth1 | Int | 商品年月1 | 202502 |
| StrikePrice1 | double | 履約價1 |  |
| StkName1 | string | 商品名稱1 | 台指選 02 22800 P |
| CommodityID2 | string | 商品ID2 | TXO |
| CallPut2 | string | 買賣權2 | C/P |
| SettlementMonth2 | Int | 商品年月2 | 202502 |
| StrikePrice2 | double | 履約價2 |  |
| StkName2 | string | 商品名稱2 | 台指選 02 23000 P |

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
from YuantaOneAPI import YuantaSparkAPITrader, enumLogType, enumQuoteIndexType, enumMarketType, enumEnvironmentMode, enumQuoteFiveTickIndexType, DepositOptimum

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
string Account = "FF0210132243219588";
string Password = "abcd123";
enumEnvironmentMode enumEvenMode = enumEnvironmentMode.UAT;

List<DepositOptimum> DepositOptimumList = new List<DepositOptimum>();

objYuantaSparkAPI.OnResponse += objApi_OnResponse;
objYuantaSparkAPI.SetLogType(enumLogType.ALL);

objYuantaSparkAPI.Open(enumEvenMode);
Thread.Sleep(1000);
objYuantaSparkAPI.Login(Account, Password);
Thread.Sleep(1000);

objYuantaSparkAPI.GetFutDepositOptimum(Account);
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

                    case 'GetFutDepositOptimum':
                        # 期貨保證金最佳化查詢
                        fResult = objValue

                        # 最佳化清單（保留到全域變數）
                        global DepositOptimumList
                        DepositOptimumList = fResult.DepositOptimumList

                        result += '期貨保證金最佳化查詢:\r\n'
                        result += '最佳化筆數:{0}\r\n'.format(DepositOptimumList.Count)

                        for i in range(DepositOptimumList.Count):
                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20}\r\n'.format(
                                str(DepositOptimumList[i].StrategyID),DepositOptimumList[i].FutAccountInfo,str(DepositOptimumList[i].Qty),DepositOptimumList[i].BuySell1,DepositOptimumList[i].BuySell2,str(DepositOptimumList[i].DealPrice1),
                                str(DepositOptimumList[i].DealPrice2),str(DepositOptimumList[i].Decimal1),str(DepositOptimumList[i].CurrentIM1),str(DepositOptimumList[i].CurrentIM2),str(DepositOptimumList[i].SaveIM),DepositOptimumList[i].CommodityID1,
                                DepositOptimumList[i].CallPut1,str(DepositOptimumList[i].SettlementMonth1),str(DepositOptimumList[i].StrikePrice1),DepositOptimumList[i].StkName1,DepositOptimumList[i].CommodityID2,DepositOptimumList[i].CallPut2,
                                str(DepositOptimumList[i].SettlementMonth2),str(DepositOptimumList[i].StrikePrice2),DepositOptimumList[i].StkName2)

        # 輸出結果
        if result:
            print('##================================================##\n')
            print(result)

    except Exception as error:
        print(f"處理回應時發生錯誤: {error}")

objYuantaSparkAPI.OnResponse += on_response
#測試環境帳號:UAT 正式環境:PROD
objYuantaSparkAPI.Open(enumEnvironmentMode.UAT)
time.sleep(2)
objYuantaSparkAPI.Login('FF0210132243219588', 'abcd123')
time.sleep(2)

DepositOptimumList = List[DepositOptimum]()
objYuantaSparkAPI.GetFutDepositOptimum('FF0210132243219588')
time.sleep(3)

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

            if (strIndex == "GetFutDepositOptimum")
            {
                var result = (DepositOptimumResult)objValue;
                try
                {
                    var list = result?.DepositOptimumList;
                    int intCount = list?.Count ?? 0;

                    strResult += $"保證金最佳化：{intCount}筆 \r\n";

                    if (list != null && list.Count > 0)
                    {
                        list.ForEach(x =>
                        {
                            strResult +=
                                $"{x.StrategyID},{x.FutAccountInfo},{x.Qty},{x.BuySell1},{x.BuySell2},{x.DealPrice1},{x.DealPrice2}," +
                                $"{x.Decimal1},{x.CurrentIM1},{x.CurrentIM2},{x.SaveIM}," +
                                $"{x.CommodityID1},{x.CallPut1},{x.SettlementMonth1},{x.StrikePrice1},{x.StkName1}," +
                                $"{x.CommodityID2},{x.CallPut2},{x.SettlementMonth2},{x.StrikePrice2},{x.StkName2}\r\n";
                        });

                        DepositOptimumList = list;
                    }
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
    "DepositOptimumList": [
      {
        "StrategyID": "6",
        "FutAccountInfo": "FF0210132243219588",
        "Qty": "3",
        "BuySell1": "S",
        "BuySell2": "B",
        "DealPrice1": "379",
        "DealPrice2": "485",
        "Decimal1": "3",
        "CurrentIM1": "287850",
        "CurrentIM2": "0",
        "SaveIM": "287850",
        "CommodityID1": "TXO",
        "CallPut1": "C",
        "SettlementMonth1": "202509",
        "StrikePrice1": "24950.0",
        "StkName1": "台指選 09 24950 C",
        "CommodityID2": "TXO",
        "CallPut2": "C",
        "SettlementMonth2": "202509",
        "StrikePrice2": "24800.0",
        "StkName2": "台指選 09 24800 C"
      }
    ]
  }
}
```
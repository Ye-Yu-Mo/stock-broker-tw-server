---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%B8%B3%E5%8B%99/%E6%9C%9F%E8%B2%A8%E8%A4%87%E5%BC%8F%E5%96%AE%E5%BA%AB%E5%AD%98%E6%98%8E%E7%B4%B0%E6%9F%A5%E8%A9%A2/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## GetFutSprStore

期貨複式單庫存明細查詢

```
bool GetFutSprStore(Account, lng)
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

#### FutSprStoreResult 查詢期貨複式單庫存明細結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| FutSprStoreList | [List\<FutSprStore>](#futsprstore) | 結果清單 |  |

#### FutSprStore 期貨複式單物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| FutAccount | string | 帳號 |  |
| Trid | string | 商品代碼 | TX109100E4/TXO09000E4 |
| SeqNo | string | 流水號 |  |
| SprNum | Short | 組合編號 |  |
| BS | string | 買賣別 | B, S |
| CommodityID | string | 商品名稱 | TXO |
| CallPut | string | 買賣權 | C/P |
| SettlementMonth | Int | 商品年月 | 200708 |
| StrikePrice | double | 履約價 |  |
| Qty | Short | 口數 |  |
| TradeDate | TYuantaDate | 交易日期 | [參考物件-日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadate) |
| MatchPrice | double | 成交價 |  |
| StkName | string | 股票名稱 | Ex: '中鋼實 06 0030 C', '台指01', ' 櫃指選 03 00400 C' |

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
from YuantaOneAPI import YuantaSparkAPITrader, enumLogType, enumQuoteIndexType, enumMarketType, enumEnvironmentMode, enumQuoteFiveTickIndexType, FutSprStore

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

objYuantaSparkAPI.OnResponse += objApi_OnResponse;
objYuantaSparkAPI.SetLogType(enumLogType.ALL);

objYuantaSparkAPI.Open(enumEvenMode);
Thread.Sleep(1000);
objYuantaSparkAPI.Login(Account, Password);
Thread.Sleep(1000);

List<FutSprStore> FutSprStoreList = new List<FutSprStore>();
objYuantaSparkAPI.GetFutSprStore(Account);
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

                    case 'GetFutSprStore':
                        # 期貨複式單庫存明細
                        fResult = objValue
                        futList = fResult.FutSprStoreList

                        global FutSprStoreList
                        FutSprStoreList = futList

                        result += '#期貨複式單庫存明細:\r\n'
                        result += '期貨複式單庫存筆數:{0}\r\n'.format(futList.Count)

                        for i in range(futList.Count):
                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},'.format(
                                futList[i].FutAccount,futList[i].Trid,futList[i].SeqNo,futList[i].SprNum,futList[i].BS,futList[i].CommodityID,futList[i].CallPut,str(futList[i].SettlementMonth),str(futList[i].StrikePrice),
                                str(futList[i].Qty))
                            #yuantaDate = TYuantaDate()
                            yuantaDate = futList[i].TradeDate
                            date= '{0}/{1}/{2}'.format(yuantaDate.ushtYear, yuantaDate.bytMon, yuantaDate.bytDay)
                            result += '{0},{1},{2}\r\n'.format(date,str(futList[i].MatchPrice),futList[i].StkName)

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

FutSprStoreList= List[FutSprStore]()
objYuantaSparkAPI.GetFutSprStore('FF0210132243219588')
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
            else if (strIndex == "GetFutSprStore")
            {
                var result = (FutSprStoreResult)objValue;
                try
                {
                    strResult += "期貨複式單庫存查詢: " + result.FutSprStoreList.Count + "筆\r\n";
                    result.FutSprStoreList.ForEach(x =>
                    {
                        strResult += $"{x.FutAccount},{x.Trid},{x.SeqNo},{x.SprNum},{x.BS}," +
                                    $"{x.CommodityID},{x.CallPut},{x.SettlementMonth},{x.StrikePrice},{x.Qty},";
                        TYuantaDate date = x.TradeDate;
                        strResult += $"{date.ushtYear}/{date.bytMon}/{date.bytDay},{x.MatchPrice},{x.StkName}\r\n";
                    });

                    FutSprStoreList = result.FutSprStoreList;
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
    "FutSprStoreList": [
      {
        "FutAccount": "FF0210132243219588",
        "Trid": "TXO27700/27500B6",
        "SeqNo": "3",
        "SprNum": "1",
        "BS": "S",
        "CommodityID": "TXO",
        "CallPut": "C",
        "SettlementMonth": "202602",
        "StrikePrice": "27700.0",
        "Qty": "1",
        "TradeDate": "202602",
        "MatchPrice": "1240.0",
        "StkName": "台指選 02 27700 C"
      }
    ]
  }
}
```
---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E8%A1%8C%E6%83%85/%E7%95%B6%E6%97%A5%E5%88%86%E6%99%82%E6%98%8E%E7%B4%B0%E6%9F%A5%E8%A9%A2/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## GetStkTickDetail

當日分時明細查詢

```
bool GetStkTickDetail(Account, MarketType, StkCode, SelectType, Stime, Etime, LastCount, lng)
```

### 回傳

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 | 證券: S + 分公司代號(4) + 帳號(7)   例如 S98875005091   期貨: F + 分公司代號(7+3) + 帳號(7)   例如 FF021000P001234567 |
| MarketType | enumMarketType | 市場類別 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| StkCode | string | 商品代號 |  |
| SelectType | enumStkTickSelectType | 查詢種類 | [參考列舉物件-分時明細查詢類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumstktickselecttype) |
| Stime | string | 開始時間 | 預設為 00:00:00 |
| Etime | string | 結束時間 | 預設為 23:59:59 |
| LastCount | int | 最後筆數 | 預設為 20 |
| lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   Normal: Big5   UTF8: UTF8   SC: 簡體中文 |

---

### Output Parameters

#### StickDetailResult 當日分時明細查詢結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MarketNo | enumMarketType | 市場代碼 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| StockCode | string | 商品代碼 |  |
| StickDetailList | List\<StickDetail> | 結果清單 |  |

---

#### StickDetail 當日分時明細物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| TimeStamp | DateTime | 時間 |  |
| DealPrice | double | 成交價 |  |
| DealVol | int | 成交量 |  |
| BuyPrice | double | 買價 |  |
| SellPrice | double | 賣價 |  |
| SeqNo | int | 序號 |  |
| InOutFlag | int | 內外盤 | 0：內盤   1：外盤 |

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

objYuantaSparkAPI.GetStkTickDetail(Account, enumMarketType.TWSE, "2885", (enumStkTickSelectType)1);
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

                    case 'GetStkTickDetail':
                        SResult = objValue
                        sResult = SResult.StickDetailList
                        result += '當日分時明細查詢結果:\r\n'
                        result += '市場代碼:{0}, 商品代碼:{1}\r\n'.format(SResult.MarketNo, SResult.StockCode)
                        for i in range(sResult.Count):  
                            result += '{0},{1},{2},{3},{4},{5},{6}\r\n'.format(str(sResult[i].TimeStamp),sResult[i].DealPrice,sResult[i].DealVol,sResult[i].BuyPrice,sResult[i].SellPrice,sResult[i].SeqNo,sResult[i].InOutFlag)

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

objYuantaSparkAPI.GetStkTickDetail('S98875005091', enumMarketType.TWSE, '2330', enumStkTickSelectType(1))

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

            if (strIndex == "GetStkTickDetail")
            {
                var result = (StickDetailResult)objValue;
                try
                {
                    strResult += $"當日分時明細查詢: {result.MarketNo} {result.StockCode}\r\n";
                    result.StickDetailList.ForEach(s =>
                    {
                        strResult += $"{s.TimeStamp} {s.DealPrice} {s.DealVol} {s.BuyPrice} {s.SellPrice} {s.SeqNo} {s.InOutFlag}\r\n";
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
    "StickDetailList": [
      {
        "TimeStamp": "2026/01/27 10:28:27",
        "DealPrice": "37",
        "DealVol": "2",
        "BuyPrice": "37",
        "SellPrice": "0",
        "SeqNo": "1",
        "InOutFlag": "1"
      }
    ]
  }
}
```
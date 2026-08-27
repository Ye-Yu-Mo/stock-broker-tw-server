---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E4%BA%A4%E6%98%93/%E6%9C%9F%E8%B2%A8%E8%A4%87%E5%BC%8F%E5%96%AE%E6%8B%86%E8%A7%A3/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## SendFutureApart

期貨複式單拆解

```
bool SendFutureApart(LoginAcno, futureApart, lng)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| LoginAcno | string | 帳號 | 期貨:F+分公司代號(7+3)+帳號(7)   例如 FF021000P001234567 |
| futureApart | [FutureApart](#futureapart) | 拆解物件 |  |
| Lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   \- Normal：Big5   \- UTF8：UTF8   \- SC：簡體中文 |

#### FutureApart 複式單拆解物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| FutAccount | string | 帳號 | 期貨:F+分公司代號(7+3)+帳號(7)   例如 FF021000P001234567 |
| TradeDate | TYuantaDate | 交易日期 | [參考物件-日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadate) |
| SeqNo | string | 流水號 |  |
| Trid | string | 商品代碼 | TX109100E4/TXO09000E4 |
| Qty | Short | 口數 |  |

---

### Output Parameters

#### FutureApartResult 複式單拆解結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| ResultCount | [OrderStatus](#orderstatus) | 交易狀態 |  |
| ResultList | [FutureApartData](#futureapartdata) | 複式單拆解明細 |  |

#### OrderStatus 交易狀態

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MsgCode | string | 訊息代碼 | 0001:執行成功 其它:失敗 |
| MsgContent | string | 訊息內容 |  |
| Count | Int | 筆數 |  |

#### FutureApartData 複式單拆解結果明細

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Identify | Int | 識別碼 |  |
| ReplyCode | Short | 委託結果代碼 | 0:委託成功 others:委託失敗 |
| ErrType | string | 錯誤類別 |  |
| ErrNO | string | 錯誤代號 |  |
| Advisory | string | 錯誤說明 |  |

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
from YuantaOneAPI import YuantaSparkAPITrader, enumLogType, enumEnvironmentMode, LoginResult, FutSprStore, FutureApart

# 建立 API 物件
objYuantaSparkAPI = YuantaSparkAPITrader()
objYuantaSparkAPI.SetLogType(enumLogType.COMMON)
```

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;
using YuantaOneAPI;

YuantaSparkAPITrader objYuantaSparkAPI = new YuantaSparkAPITrader();
string Account = "FF021919F000168885";
string Password = "abcd123";
ManualResetEvent loginCompleted = new ManualResetEvent(false);

enumEnvironmentMode enumEvenMode = enumEnvironmentMode.UAT;
List<FutSprStore> FutSprStoreList = new List<FutSprStore>();

objYuantaSparkAPI.OnResponse += objApi_OnResponse;
objYuantaSparkAPI.SetLogType(enumLogType.ALL);

objYuantaSparkAPI.Open(enumEvenMode);
Thread.Sleep(1000);
objYuantaSparkAPI.Login(Account, Password);

Thread.Sleep(1000);

//呼叫複式單庫存
objYuantaSparkAPI.GetFutSprStore(Account);
Thread.Sleep(2000);
objYuantaSparkAPI.SendFutureApart(Account, FutSprStoreList);
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

                    case 'SendFutureApart':
                        fResult = objValue
                        status = fResult.ResultCount       
                        datas = fResult.Result             
                        result += '期貨複式單拆解結果:\n'
                        result += '{0},{1},拆解筆數:{2}\r\n'.format(status.MsgCode,status.MsgContent,str(status.Count))
                        for i in range(datas.Count):
                            result += '{0},{1},{2},{3},{4}\r\n'.format(str(datas[i].Identify),str(datas[i].ReplyCode),str(datas[i].ErrType),datas[i].ErrNO,datas[i].Advisory)

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
time.sleep(2)

result =  FutSprStoreList 
if result:
    lstFutSprStore = FutSprStoreList
    objYuantaSparkAPI.SendFutureApart('FF021919F000168885', lstFutSprStore)
else:
    print('查無複式單庫存資料')      
# 測試環境傳送後要休息一下
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

            else if (strIndex == "SendFutureApart")
            {
                var result = (FutureApartResult)objValue;
                try
                {
                    strResult += $"複式單拆解結果：{result.ResultCount.MsgCode},{result.ResultCount.MsgContent},{result.ResultCount.Count}筆\r\n";
                    result.ResultList.ForEach(x =>
                    {
                        strResult += $"{x.Identify},{x.ReplyCode},{x.ErrType},{x.ErrNO},{x.Advisory}\r\n";
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
            else if (strIndex == "GetFutSprStore")
            {
                var result = (FutSprStoreResult)objValue;
                try
                {
                    strResult += "期貨複式單庫存查詢: " + result.FutSprStoreList.Count + "筆\r\n";
                    result.FutSprStoreList.ForEach(x =>
                    {
                        strResult += $"{x.FutAccount},{x.Trid},{x.SeqNo},{x.SprNum},{x.BS},{x.CommodityID},{x.CallPut},{x.SettlementMonth},{x.StrikePrice},{x.Qty},";
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
    "ResultCount": {
        "MsgCode": "0001",
        "MsgContent": "執行成功",
        "Count": 1,
    },
    "ResultList":[{
      "Identify": "0",
      "ReplyCode": "0",
      "ErrType": "A",
      "ErrNO": "999",
      "Advisory": "執行拆解 資料筆數 1 筆"
    }]
  }
}
```
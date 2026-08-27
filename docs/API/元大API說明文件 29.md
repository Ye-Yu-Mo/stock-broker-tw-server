---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E6%A2%9D%E4%BB%B6%E5%96%AE/%E5%88%AA%E9%99%A4%E6%A2%9D%E4%BB%B6%E5%96%AE/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## DeleteAlgoCOOdrStrategy

刪除條件單

```
bool DeleteAlgoCOOdrStrategy(Account, lstStrategy, lng)
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
| lstStrategy | List\<DeleteStrategy> | 刪除清單 |  |
| lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   \- Normal：Big5   \- UTF8：UTF8   \- SC：簡體中文 |

> [!tip] Tip
> 註1：限證券使用

#### DeleteStrategy 刪除條件單物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 | 證券:S+分公司代號(4)+帳號(7)   例如 S98875005091 |
| StrategyType | StrategyType | 策略類型 | [參考列舉物件-條件單類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#strategytype) |
| StrategyNo | string | 策略編號 |  |

---

### Output Parameters

#### OrderStrategyResult 條件單委託結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| ResultList | List\<OrderStrategyStatus> | 條件單委託結果清單 |  |

#### OrderStrategyStatus 條件單委託狀態

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| OrdStatus | SStatus | 委託狀態 | [參考列舉物件-策略狀態](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#sstatus) |
| OrderNo | String | 委託編號 |  |
| EffTime | DateTime | 策略起始日 |  |
| ExpTime | DateTime | 策略終止日 |  |
| Msg | string | 訊息中文 |  |

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
                        DeleteStrategy, StrategyType)

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

string targetStrategyNo = "k263R000000056";  // 填入欲刪除的策略單號

List<DeleteStrategy> lstDelete = new List<DeleteStrategy>();
lstDelete.Add(new DeleteStrategy
{
    Account = Account,
    StrategyType = (StrategyType)1,     // 策略類型：1:停損利 2:移動鎖利 3:二擇一 4:母子單 5:多條件
    StrategyNo = targetStrategyNo.Trim()
});

objYuantaSparkAPI.DeleteAlgoCOOdrStrategy(Account, lstDelete);
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

                    case 'DeleteAlgoCOOdrStrategy':
                        DResult = objValue
                        dResult = DResult.ResultList

                        result = ''
                        result += "刪除條件單:\r\n"

                        for i in range(dResult.Count):  
                            result += '{0},{1},{2},{3},{4}\r\n'.format(dResult[i].OrdStatus,dResult[i].OrderNo,dResult[i].EffTime,dResult[i].ExpTime,dResult[i].Msg)

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

target_strategy_no = 'k263R000000056'
DeleteStrategyList = List[DeleteStrategy]()
delete_obj = DeleteStrategy()
delete_obj.Account = "S98875005091"
delete_obj.StrategyType = StrategyType(1)  # 策略類型
delete_obj.StrategyNo = target_strategy_no.strip()   # 策略單號ID

DeleteStrategyList.Add(delete_obj)
objYuantaSparkAPI.DeleteAlgoCOOdrStrategy("S98875005091", DeleteStrategyList)

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

            if (strIndex == "DeleteAlgoCOOdrStrategy")
            {
                var result = (OrderStrategyResult)objValue;
                try
                {
                    strResult += "刪除條件單:\r\n";
                    result.ResultList?.ForEach(r =>
                    {
                        strResult += $"{r.OrdStatus} {r.OrderNo} {r.EffTime:yyyy/MM/dd} {r.ExpTime:yyyy/MM/dd} {r.Msg}\r\n";
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
    "ResultList": [
      {
        "OrdStatus": "SstCanceled",
        "OrderNo": "k263R000000044",
        "EffTime": "2026/03/09",
        "ExpTime": "2026/06/03",
        "Msg": "策略已取消"
      }
    ]
  }
}
```
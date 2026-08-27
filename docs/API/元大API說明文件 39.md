---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%B8%B3%E5%8B%99/%E9%8A%80%E8%A1%8C%E9%A4%98%E9%A1%8D%E6%9F%A5%E8%A9%A2/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## GetBankBalance

銀行餘額查詢

```
bool GetBankBalance(Account, lng)
```

### 回傳

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 | 證券：S + 分公司代號(4) + 帳號(7)   例如：S98875005091   註：限證券使用 |
| lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   \- Normal：Big5   \- UTF8：UTF8   \- SC：簡體中文 |

---

### Output Parameters

#### BankBalanceResult（銀行餘額查詢結果）

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| BankBalanceList | List\<BankBalance> | 結果清單 |  |

---

#### BankBalance（銀行餘額物件）

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 |  |
| ResponseTime | string | 系統回覆時間 | HH:mm:ss |
| BankAccount | string | 銀行帳號 |  |
| AvailableBalance | double | 可用餘額 |  |
| Message | string | 說明 | 異常訊息 |

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
from YuantaOneAPI import YuantaSparkAPITrader, enumLogType, enumMarketType, enumEnvironmentMode

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
string Account = "S981r1691656";
string Password = "abcd123";
enumEnvironmentMode enumEvenMode = enumEnvironmentMode.UAT;

objYuantaSparkAPI.OnResponse += objApi_OnResponse;
objYuantaSparkAPI.SetLogType(enumLogType.ALL);

objYuantaSparkAPI.Open(enumEvenMode);
Thread.Sleep(1000);
objYuantaSparkAPI.Login(Account, Password);
Thread.Sleep(1000);

objYuantaSparkAPI.GetBankBalance(Account);
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

                    case 'GetBankBalance':
                        BResult = objValue
                        bResult = BResult.BankBalanceList
                        result += '銀行餘額查詢結果:\r\n'
                        for i in range(bResult.Count):  
                            result += '{0},{1},{2},{3},{4}\r\n'.format(bResult[i].Account,bResult[i].ResponseTime,bResult[i].BankAccount,bResult[i].AvailableBalance,bResult[i].Message)

        if result:
            print('##================================================##\n')
            print(result)

    except Exception as error:
        print(f"處理回應時發生錯誤: {error}")

objYuantaSparkAPI.OnResponse += on_response
#測試環境帳號:UAT 正式環境:PROD
objYuantaSparkAPI.Open(enumEnvironmentMode.UAT)
time.sleep(2)
objYuantaSparkAPI.Login('S981r1691656', 'abcd123')
time.sleep(2)

objYuantaSparkAPI.GetBankBalance('S981r1691656')

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

            if (strIndex == "GetBankBalance")
            {
                var result = (BankBalanceResult)objValue;
                try
                {
                    strResult += "銀行餘額查詢:\r\n";
                    result.BankBalanceList.ForEach(b =>
                    {
                        strResult += $"{b.Account} {b.ResponseTime} {b.BankAccount} {b.AvailableBalance} {b.Message}\r\n";
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
    "BankBalanceList": [
      {
        "Account": "S98875005091",
        "ResponseTime": "2026/01/01 14:30:15",
        "BankAccount": "S98875005091",
        "AvailableBalance": "1000000",
        "Message": ""
      }
    ]
  }
}
```
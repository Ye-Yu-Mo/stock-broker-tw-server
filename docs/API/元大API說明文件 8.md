---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%99%BB%E5%85%A5/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## Login

登入

```
bool Login(Account, Pass)
```

```
bool Login(PfxPath, PfxPass , Account, Pass)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 登入帳號 | 證券：S + 分公司代號(4) + 帳號(7)   例： `S98875005091`      期貨：F + 分公司代號(7+3) + 帳號(7)   例： `FF021000P001234567` |
| Pass | string | 登入密碼 |  |

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| PfxPath | string | Pfx 憑證路徑 | 絕對路徑 |
| PfxPass | string | Pfx 憑證密碼 |  |
| Account | string | 登入帳號 | 證券：S + 分公司代號(4) + 帳號(7)   例： `S98875005091`      期貨：F + 分公司代號(7+3) + 帳號(7)   例： `FF021000P001234567` |
| Pass | string | 登入密碼 |  |

---

### Output Parameters

#### LoginResult 登入結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| LoginStatus | Status | 登入狀態 |  |
| LoginList | List | 登入取得資料清單 |  |

#### Status 登入狀態

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MsgCode | string | 訊息代碼 | 0000：執行失敗   0001：執行成功   0102：密碼凍結或未啟用   0112：無此權限使用功能 |
| MsgContent | string | 中文訊息 |  |
| Count | Int | 筆數 |  |

#### LoginData 登入取得資料

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 | 證券： `S98875005091`   期貨： `FF021000P001234567` |
| Name | string | 客戶姓名 |  |
| InvestorID | string | 身分證字號 |  |
| SellerNo | Short | 營業員代碼 |  |

---

### Logout

登出

| 函數名稱 | Logout |
| --- | --- |
| 功能說明 | 將之前透過API登入的帳號全數登出   bool LogOut() |
| C#範例 | objYuantaSparkAPI.LogOut(); |
| Python 範例 | objYuantaSparkAPI.LogOut(); |

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

        if result:
            print('##================================================##\n')
            print(result)

    except Exception as error:
        print(f"處理回應時發生錯誤: {error}")

objYuantaSparkAPI.OnResponse += on_response
objYuantaSparkAPI.Open(enumEnvironmentMode.UAT)
time.sleep(2)

#證券 (ex:S+98xxxxxxxxx)
objYuantaSparkAPI.Login('S98875005091', '1234') 
time.sleep(2)

#期貨 (ex:F+ F021xxxxxxxxxxxxx)
#objYuantaSparkAPI.Login('FF0210132243219588', 'abcd123')
time.sleep(2)

#Linux/MAC登入 需帶入憑證絕對路徑與憑證密碼
#objYuantaSparkAPI.Login('/home/yuanta/YuantaSparkAPI_NET6_Python/B110000005_TWCA.pfx','yuanta','S98875005091', '1234')
#time.sleep(2)

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
    "LoginStatus": {
      "MsgCode": "0001",
      "MsgContent": "執行成功!",
      "Count": 1
    },
    "LoginList": [
      {
        "Account": "S98875005091",
        "Name": "陳○○",
        "InvestorID": "B110000005",
        "SellerNo": "55"
      }
    ]
  }
}
```
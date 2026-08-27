---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E8%A1%8C%E6%83%85/%E6%A8%99%E7%9A%84%E8%B3%87%E8%A8%8A%E6%9F%A5%E8%A9%A2/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## GetStockInformation

標的資訊查詢

```
bool GetStockInformation(Account, StkList, lng)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 | 證券：S + 分公司代號(4) + 帳號(7)   例如：S98875005091   期貨：F + 分公司代號(7+3) + 帳號(7)   例如：FF021000P001234567 |
| StkList | List\<StkInfo> | 查詢商品清單 |  |
| lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   \- Normal：Big5   \- UTF8：UTF8   \- SC：簡體中文 |

#### StkInfo（標的資訊）

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MarketType | enumMarketType | 市場類別 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| StockCode | string | 商品代碼 |  |

---

### Output Parameters

#### StkInformationResult（標的資訊查詢結果）

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| StockInformationList | List\<StkInformation> | 結果清單 |  |

#### StkInformation（標的資訊物件）

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MarketNo | enumMarketType | 市場代碼 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| StockCode | string | 商品代碼 |  |
| Dayoffmark | string | 可否當沖 | X：現股當沖   Y：現股當沖(暫停先賣後買)   其他：不可現股當沖 |
| Creditpercent | int | 融資成數 |  |
| Lendpercent | int | 融券成數 |  |
| Creditremnants | int | 融資餘額 | 999999：無限制   \-1：停資   \-2：有限制 |
| Lendremnants | int | 融券餘額 | 999999：無限制   \-1：停券   0：無券 |
| LendSellMark | string | 平盤下可放空 | N：不可放空   Y：可放空 |
| RecallDate | string | 融券回補日期 | yyyyMMdd 民國年 |
| LendQty | long | 借賣配額 |  |
| StockWarning | List\<enumStkWarningType> | 股票警示狀態 | [參考列舉物件-股票警示類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumstkwarningtype) |
| UpdateDate | string | 更新日期 | yyyyMMdd 民國年 |

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
from YuantaOneAPI import YuantaSparkAPITrader, enumLogType, enumMarketType, enumEnvironmentMode, StkInfo

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

List<StkInfo> lstStkInfo = new List<StkInfo>();
StkInfo stkInfo = new StkInfo
{
    MarketType = enumMarketType.TWSE,
    StockCode = "2885"
};
lstStkInfo.Add(stkInfo);
objYuantaSparkAPI.GetStockInformation(Account, lstStkInfo);
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

                    case 'GetStockInformation':
                        SResult = objValue
                        sResult = SResult.StockInformationList
                        result += '標的資訊查詢結果:\r\n'
                        for i in range(sResult.Count):        
                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},'.format(str(sResult[i].MarketNo),sResult[i].StockCode,sResult[i].Dayoffmark,str(sResult[i].Creditpercent),
                                                                                        str(sResult[i].Lendpercent),str(sResult[i].Creditremnants),str(sResult[i].Lendremnants),sResult[i].LendSellMark,
                                                                                        sResult[i].RecallDate,str(sResult[i].LendQty))
                            for i in range(sResult[i].StockWarning.Count):
                                result += '{0},'.format(str(sResult[i].StockWarning[i]))
                            result += '{0}\r\n'.format(sResult[i].UpdateDate)

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

infoList = List[StkInfo]()
stkInfo = StkInfo()
stkInfo.MarketType = enumMarketType.TWSE
stkInfo.StockCode = '2330'
infoList.Add(stkInfo)
objYuantaSparkAPI.GetStockInformation('S98875005091',infoList)

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

            if (strIndex == "GetStockInformation")
            {
                var result = (StkInformationResult)objValue;
                try
                {
                    strResult += "標的資訊查詢結果: \r\n";
                    result.StockInformationList.ForEach(s =>
                    {
                        strResult += $"{s.MarketNo} {s.StockCode} {s.Dayoffmark} {s.Creditpercent} {s.Lendpercent} {s.Creditremnants} {s.Lendremnants} {s.LendSellMark} {s.RecallDate} {s.LendQty} ";
                        s.StockWarning.ForEach(sw => strResult += $"{sw} ");
                        strResult += $"{s.UpdateDate}\r\n";
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
    "StockInformationList": [
      {
        "MarketNo": "TWSE",
        "StockCode": "2885",
        "Dayoffmark": "X",
        "Creditpercent": "0",
        "Lendpercent": "0",
        "Creditremnants": "0",
        "Lendremnants": "0",
        "LendSellMark": "N",
        "RecallDate": "",
        "LendQty": "250591"
      }
    ]
  }
}
```
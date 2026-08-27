---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E8%A1%8C%E6%83%85/%E5%80%8B%E8%82%A1%E5%85%B6%E4%BB%96%E8%B3%87%E8%A8%8A%E8%A8%82%E9%96%B1/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## SubscribeStockInformation / UnSubscribeStockInformation

個股其他資訊訂閱 / 個股其他資訊解訂閱

```
bool SubscribeStockInformation(LoginAcno, LstStockInfo, Lng)
bool UnSubscribeStockInformation(LoginAcno, LstStockInfo, Lng)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| LoginAcno | string | 訂閱帳號 | 證券: S+分公司代號(4)+帳號(7)   例: S98875005091   期貨: F+分公司代號(7+3)+帳號(7)   例: FF021000P001234567 |
| LstStockInfo | [List\<StockOtherInformation>](#stockotherinformation) | 訂閱商品清單 |  |
| Lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   Normal: Big5   UTF8: UTF8   SC: 簡體中文 |

#### StockOtherInformation 個股其他資訊物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MarketType | enumMarketType | 市場類別 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| StockCode | string | 商品代碼 |  |

---

### Output Parameters

#### StockOtherInfoResult 個股其他資訊回傳結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Key | string | 鍵值 | MarketNo + StkCode (不足補 0) |
| MarketType | enumMarketType | 市場類別 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| StkCode | string | 股票代碼 |  |
| IndexFlag | enumQuoteStkInfoIndexType | 索引值 | [參考列舉物件-訂閱個股其他資訊索引值類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumquotestkinfoindextype)   僅提供試搓成交時間 |
| TradeTime | TYuantaTime | 試搓成交時間 | [參考物件-時間物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantaime) |

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
from YuantaOneAPI import YuantaSparkAPITrader, enumLogType, enumQuoteIndexType, enumMarketType, enumEnvironmentMode, enumQuoteFiveTickIndexType, StockOtherInformation

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

List<StockOtherInformation> lstStkInfo = new List<StockOtherInformation>();
StockOtherInformation stkInfo = new StockOtherInformation
{
    MarketType = enumMarketType.TWSE,
    StockCode = "2330"
};
lstStkInfo.Add(stkInfo);

objYuantaSparkAPI.SubscribeStockInformation(Account, lstStkInfo);
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

            case 2:  # 訂閱回應資訊
                match strIndex:
                    case 'SubscribeStockInformation':
                        # 個股其他資訊訂閱結果
                        sResult = objValue

                        result += '個股其他資訊訂閱結果:\r\n'
                        #yuantaTime = TYuantaTime()
                        yuantaTime = sResult.TradeTime
                        time= '{0}:{1}:{2}.{3}'.format(str(yuantaTime.bytHour), str(yuantaTime.bytMin), str(yuantaTime.bytSec), str(yuantaTime.ushtMSec))        
                        result += '{0},{1},{2},{3}:{4}\r\n'.format(
                            sResult.Key,str(sResult.MarketType),sResult.StkCode,str(sResult.IndexFlag),time)

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
objYuantaSparkAPI.Login('S98875005091', '1234')
time.sleep(2)

infoList = List[StockOtherInformation]()
stkInfo = StockOtherInformation()
stkInfo.MarketType = enumMarketType.TWSE
stkInfo.StockCode = '2330'
infoList.Add(stkInfo)
#個股其他資訊訂閱
objYuantaSparkAPI.SubscribeStockInformation('S98875005091',infoList)

#測試環境傳送後要休息一下
time.sleep(10)

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

        if (intMark == 2)
        {
            if (strIndex == "SubscribeStockInformation")
            {
                var result = (StockOtherInfoResult)objValue;

                try
                {
                    strResult += "個股其他資訊訂閱結果: \r\n";
                    strResult += $"{result.Key},{result.MarketType},{result.StkCode},{result.IndexFlag}:";
                    TYuantaTime tradeTime = result.TradeTime;
                    strResult += $"{tradeTime.bytHour}:{tradeTime.bytMin}:{tradeTime.bytSec}.{tradeTime.ushtMSec}\r\n";
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
    "Key": "2330",
    "MarketType": "TWSE",
    "StkCode": "2330",
    "IndexFlag": "試搓成交時間",
    "TradeTime": "8:35:35.33"
  }
}
```
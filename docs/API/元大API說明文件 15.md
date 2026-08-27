---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E8%A1%8C%E6%83%85/%E5%88%86%E6%99%82%E6%98%8E%E7%B4%B0%E8%A8%82%E9%96%B1/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## SubscribeStockTick/ UnSubscribeStockTick

分時明細訂閱/分時明細解訂閱

```
bool SubscribeStockTick(LoginAcno, LstStocktick, Lng)
bool UnSubscribeStockTick(LoginAcno, LstStocktick, Lng)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| LoginAcno | string | 訂閱帳號 | 證券: S + 分公司代號(4) + 帳號(7)   例如 S98875005091   期貨: F + 分公司代號(7+3) + 帳號(7)   例如 FF021000P001234567 |
| LstStocktick | [List\<Stocktick>](#stocktick) | 訂閱商品清單 |  |
| Lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   Normal: Big5   UTF8: UTF8   SC: 簡體中文 |

#### Stocktick 分時明細物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MarketType | enumMarketType | 市場類別 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| StockCode | string | 商品代碼 |  |

---

### Output Parameters

#### StockTickResult 分時明細回傳結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Key | string | 鍵值 | MarketNo + StkCode (不足補0) |
| MarketType | enumMarketType | 市場類別 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| StkCode | string | 股票代碼 |  |
| SerialNo | int | 序號 | 以股票代碼個別編序號，從1開始，-1代表商品清盤 |
| Time | TYuantaTime | 時間 | [參考物件-時間物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantaime) |
| BuyPrice | double | 買價 | 當 SerialNo=-1 時，此欄位代表漲停價   市價買: 999999999 |
| SellPrice | double | 賣價 | 當 SerialNo=-1 時，此欄位代表跌停價   市價賣: -999999999 |
| DealPrice | double | 成交價 | 當 SerialNo=-1 時，此欄位代表開盤參考價 |
| DealVol | Int | 成交量 | 海外期貨之現貨單位是千股 |
| InOutFlag | Byte | 內外盤註記 | 0: 內盤   1: 外盤   2: 定價內盤   3: 定價外盤   10: 一般揭示   11: 暫緩撮合且瞬間趨跌   12: 暫緩撮合且瞬間趨漲   13: 試算後延後收盤   14: 暫停交易   15: 恢復交易   註1: 當是10,11,12,13時,只有市場碼與股票代碼有值,其餘欄位皆為0   註2: 當是14,15時,只有市場碼、股票代碼與時間有值,其餘欄位皆為0 |
| Type | Byte | 明細類別 | 0: Normal |

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
from YuantaOneAPI import YuantaSparkAPITrader, enumLogType, enumQuoteIndexType, enumMarketType, enumEnvironmentMode, StockTick

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

List<StockTick> lstStocktick = new List<StockTick>();
StockTick stkInfo = new StockTick
{
    MarketType = enumMarketType.TWSE,
    StockCode = "2330"
};
lstStocktick.Add(stkInfo);

objYuantaSparkAPI.SubscribeStockTick(Account, lstStocktick);
Thread.Sleep(2000);
```

#### Onresponse

```python
#回應事件
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
                    case 'SubscribeStockTick':
                        # 分時明細訂閱結果
                        sResult = objValue

                        result += '分時明細訂閱結果:\r\n'
                        #yuantaTime = TYuantaTime()
                        yuantaTime = sResult.Time
                        time= '{0}:{1}:{2}.{3}'.format(str(yuantaTime.bytHour), str(yuantaTime.bytMin), str(yuantaTime.bytSec), str(yuantaTime.ushtMSec))        
                        result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10}\r\n'.format(
                            sResult.Key,str(sResult.MarketType),sResult.StkCode,str(sResult.SerialNo),time,str(sResult.BuyPrice),str(sResult.SellPrice),str(sResult.DealPrice),str(sResult.DealVol),str(sResult.InOutFlag),str(sResult.Type))

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

stocktickList = List[StockTick]()
stocktick = StockTick()
stocktick.MarketType = enumMarketType.TWSE
stocktick.StockCode = '2330'
stocktickList.Add(stocktick)

#分時明細訂閱
objYuantaSparkAPI.SubscribeStockTick('S98875005091',stocktickList)
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
            if (strIndex == "SubscribeStockTick")
            {
                var result = (StockTickResult)objValue;
                try
                {
                    strResult += "分時明細訂閱結果: \r\n";
                    TYuantaTime yuantaTime = result.Time;
                    strResult += $"{result.Key},{result.MarketType},{result.StkCode},{result.SerialNo}," +
                        $"{yuantaTime.bytHour}:{yuantaTime.bytMin}:{yuantaTime.bytSec}.{yuantaTime.ushtMSec}," +
                        $"{result.BuyPrice},{result.SellPrice},{result.DealPrice},{result.DealVol},{result.InOutFlag},{result.Type}\r\n";
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
    "SerialNo": "6213",
    "Time": "13:3:18.37",
    "BuyPrice": "1420.0",
    "SellPrice": "1425.0",
    "DealPrice": "1425.0",
    "DealVol": "1",
    "InOutFlag": "1",
    "Type": "0"
  }
}
```
---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E8%A1%8C%E6%83%85/%E8%A1%8C%E6%83%85%E5%A0%B1%E5%83%B9%E8%A1%A8%E8%A8%82%E9%96%B1/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## SubscribeWatchlistAll/UnSubscribeWatchlistAll

行情報價表訂閱/行情報價表解訂閱

```
bool SubscribeWatchlistAll(LoginAcno, LstWatchlistAll, Lng)
bool UnSubscribeWatchlistAll(LoginAcno, LstWatchlistAll, Lng)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| LoginAcno | string | 訂閱帳號 | 證券：S + 分公司代號(4) + 帳號(7)   例如：S98875005091   期貨：F + 分公司代號(7+3) + 帳號(7)   例如：FF021000P001234567 |
| LstWatchlistAll | List\<WatchlistAll> | 訂閱商品清單 |  |
| Lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   \- Normal：Big5   \- UTF8：UTF8   \- SC：簡體中文 |

---

#### Watchlist 行情報價表（指定欄位）物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MarketType | enumMarketType | 市場類別 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| StockCode | string | 商品代碼 |  |

---

### Output Parameters

#### WatchListAllResult 行情報價表訂閱回傳結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Key | string | 鍵值 | MarketNo+StkCode (不足補0) |
| MarketType | enumMarketType | 市場類別 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| StkCode | string | 股票代碼 |  |
| SeqNo | Long | 序號 | 090000000000   後八碼代表序號，前四碼代表時間 |
| IndexFlag | enumQuoteIndexType | 索引值 | [參考列舉物件-訂閱索引值類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumquoteindextype) |
| Value | double | 資料值 | **此值定義請參考IndexFlag**      若IndexFlag=IndexFlag22、IndexFlag28、IndexFlag29則無值      IndexFlag=瞬間價格趨勢   10: 一般揭示   11: 暫緩撮合且瞬間趨跌   12: 暫緩撮合且瞬間趨漲   13: 試算後延後收盤   14: 暫停交易   15: 恢復交易   16: 試算後延後開盤      IndexFlag=交易狀態   0x00: 初始狀態   0x01: 收單階段   0x02: 不可刪單階段   0x03: 集合競價階段      IndexFlag=試撮量   最高位元的Bit,表示內/外盤的旗標,   0:內盤/1:外盤 |
|  |  |  |  |
| IndexFlag\_22 | [WatchListAll\_Flag22](#watchlistall_flag22-indexflag22) | 訂閱報價表Flag22 | IndexFlag=IndexFlag22才有值 |
| IndexFlag\_28 | [WatchListAll\_Flag28](#watchlistall_flag28-indexflag28) | 訂閱報價表Flag28 | IndexFlag=IndexFlag28才有值 |
| IndexFlag\_29 | [WatchListAll\_Flag29](#watchlistall_flag29-indexflag29) | 訂閱報價表Flag29 | IndexFlag=IndexFlag29才有值 |

#### WatchListAll\_Flag22 訂閱報價表IndexFlag22物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| BuyVol | Int | 第一買量 |  |
| SellVol | Int | 第一賣量 |  |

#### WatchListAll\_Flag28 訂閱報價表IndexFlag28物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| BuyPrice | double | 買價 | 市價買:999999999 |
| SellPrice | double | 賣價 | 市價賣:-999999999 |

#### WatchListAll\_Flag29 訂閱報價表IndexFlag29物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Time | TYuantaTime | 時間 | [參考物件-時間物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantaime) |
| TotalOutVol | Int | 累計外盤量 |  |
| TotalInVol | Int | 累計內盤量 |  |
| Deal | double | 成交價 |  |
| Vol | Int | 單量 | 最高位元的Bit，表示內/外盤的旗標，   0:內盤/1:外盤 |
| TotalVol | Int | 總成交量 | 海外期貨之現貨單位是千股 |
| TotalAmt | Int | 總成交金額 | 單位萬元 |

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
from YuantaOneAPI import YuantaSparkAPITrader, enumLogType, enumQuoteIndexType, enumMarketType, enumEnvironmentMode, WatchlistAll

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
string Account = "FF0210132243219588";
string Password = "abcd123";

enumEnvironmentMode enumEvenMode = enumEnvironmentMode.UAT;

objYuantaSparkAPI.OnResponse += objApi_OnResponse;
objYuantaSparkAPI.SetLogType(enumLogType.ALL);

objYuantaSparkAPI.Open(enumEvenMode);
Thread.Sleep(1000);
objYuantaSparkAPI.Login(Account, Password);
Thread.Sleep(1000);

List<WatchlistAll> lstWatchlistAll = new List<WatchlistAll>();

WatchlistAll stkInfo = new WatchlistAll
{
    MarketType = enumMarketType.TAIFEX,
    StockCode = "TXF8"
};

lstWatchlistAll.Add(stkInfo);

objYuantaSparkAPI.SubscribeWatchlistAll(Account, lstWatchlistAll);
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
                    case 'SubscribeWatchlistAll':
                        # 行情報價表訂閱結果
                        wResult = objValue

                        result += '行情報價表訂閱結果:\r\n'
                        result += '{0},{1},{2},{3},{4},'.format(wResult.Key,str(wResult.MarketType),wResult.StkCode,str(wResult.SeqNo),str(wResult.IndexFlag))
                        match wResult.IndexFlag:
                            case enumQuoteIndexType.IndexFlag22:
                                #flag22 = WatchListAll_Flag22()
                                flag22 = wResult.IndexFlag_22
                                result +='{0},{1}\r\n'.format(str(flag22.BuyVol),str(flag22.SellVol))
                            case enumQuoteIndexType.IndexFlag28:
                                #flag28 = WatchListAll_Flag28()
                                flag28 = wResult.IndexFlag_28
                                result +='{0},{1}\r\n'.format(str(flag28.BuyPrice),str(flag28.SellPrice))
                            case enumQuoteIndexType.IndexFlag29:
                                #flag29 = WatchListAll_Flag29()
                                flag29 = wResult.IndexFlag_29
                                #yuantaTime = TYuantaTime()
                                yuantaTime = flag29.Time
                                time= '{0}:{1}:{2}.{3}'.format(str(yuantaTime.bytHour), str(yuantaTime.bytMin), str(yuantaTime.bytSec), str(yuantaTime.ushtMSec))
                                result +='{0},{1},{2},{3},{4},{5},{6}\r\n'.format(time,str(flag29.TotalOutVol),str(flag29.TotalInVol),str(flag29.Deal),str(flag29.Vol),str(flag29.TotalVol),str(flag29.TotalAmt))
                            case _:
                                result +=str(wResult.Value)+'\r\n'

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
time.sleep(1)

WatchlistAllList = List[WatchlistAll]()
watch = WatchlistAll()
watch.MarketType = enumMarketType.TWSE
watch.StockCode = '2330'
WatchlistAllList.Add(watch)

#行情報價表訂閱
objYuantaSparkAPI.SubscribeWatchlistAll('S98875005091',WatchlistAllList)

#測試環境傳送後要休息一下
time.sleep(2)

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
            if (strIndex == "SubscribeWatchlistAll")
            {
                var result = (WatchListAllResult)objValue;
                try
                {
                    strResult += "報價表訂閱結果: \r\n";
                    strResult += $"{result.Key},{result.MarketType},{result.StkCode},{result.SeqNo},{result.IndexFlag}:";

                    switch (result.IndexFlag)
                    {
                        case enumQuoteIndexType.IndexFlag22:
                            WatchListAll_Flag22 IndexFlag22 = result.IndexFlag_22;
                            strResult += $"{IndexFlag22.BuyVol},{IndexFlag22.SellVol}";
                            break;

                        case enumQuoteIndexType.IndexFlag28:
                            WatchListAll_Flag28 IndexFlag28 = result.IndexFlag_28;
                            strResult += $"{IndexFlag28.BuyPrice},{IndexFlag28.SellPrice}";
                            break;

                        case enumQuoteIndexType.IndexFlag29:
                            WatchListAll_Flag29 IndexFlag29 = result.IndexFlag_29;
                            TYuantaTime yuantaTime = IndexFlag29.Time;
                            strResult += $"{yuantaTime.bytHour}:{yuantaTime.bytMin}:{yuantaTime.bytSec}.{yuantaTime.ushtMSec},";
                            strResult += $"{IndexFlag29.TotalOutVol},{IndexFlag29.TotalInVol},{IndexFlag29.Deal},{IndexFlag29.Vol},{IndexFlag29.TotalVol},{IndexFlag29.TotalAmt}";
                            break;

                        default:
                            strResult += result.Value;
                            break;
                    }
                    strResult += "\r\n";
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
            return;
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
    "SeqNo":"114400421551",
    "Value": {
      "IndexFlag22": {
        "BuyVol": "3525",
        "SellVol": "777"
      },
      "IndexFlag29": {
        "Time": "11:25:4.611",
        "TotalOutVol": "6995",
        "TotalInVol": "7997",
        "Deal": "1420.0",
        "Vol": "6",
        "TotalVol": "14992",
        "TotalAmt": "2146118"
      }
    }
  }
}
```
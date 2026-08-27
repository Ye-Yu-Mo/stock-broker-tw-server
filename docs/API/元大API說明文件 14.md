---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E8%A1%8C%E6%83%85/%E6%9C%80%E4%BD%B3%E4%BA%94%E6%AA%94%E8%A1%8C%E6%83%85%E8%A8%82%E9%96%B1/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## SubscribeFiveTickA / UnSubscribeFiveTickA

最佳五檔行情訂閱/最佳五檔行情解訂閱

```
bool SubscribeFiveTickA(LoginAcno, LstFiveTickA, Lng)
bool UnSubscribeFiveTickA(LoginAcno, LstFiveTickA, Lng)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 訂閱帳號 | 證券：S + 分公司代號(4) + 帳號(7)   例如：S98875005091   期貨：F + 分公司代號(7+3) + 帳號(7)   例如：FF021000P001234567 |
| FiveTickA | [List\<FiveTickA>](#fiveticka) | 查詢商品清單 |  |
| Lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   \- Normal：Big5   \- UTF8：UTF8   \- SC：簡體中文 |

#### FiveTickA 最佳五檔行情物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MarketType | enumMarketType | 市場類別 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| StockCode | string | 商品代碼 |  |

---

### Output Parameters

#### FiveTickAResult 最佳五檔行情回傳結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Key | string | 鍵值 | MarketNo+StkCode (不足補0) |
| MarketType | enumMarketType | 市場類別 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| StkCode | string | 股票代碼 |  |
| IndexFlag | enumQuoteFiveTickIndexType | 索引值 | [參考列舉物件-訂閱五檔索引值類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumquotefivetickindextype) |
| Value | double | 資料值 | 此值定義請參考 IndexFlag   若 IndexFlag=20、21、42、43、50、51 則無值 |
| IndexFlag\_20 | [FiveTick\_Flag20](#fivetick_flag20-indexflag20) | 五檔報價 Flag20 | IndexFlag=20 才有值 |
| IndexFlag\_21 | [FiveTick\_Flag21](#fivetick_flag21-indexflag21) | 五檔報價 Flag21 | IndexFlag=21 才有值 |
| IndexFlag\_42 | [FiveTick\_Flag42](#fivetick_flag42-indexflag42) | 五檔報價 Flag42 | IndexFlag=42 才有值 |
| IndexFlag\_43 | [FiveTick\_Flag43](#fivetick_flag43-indexflag43) | 五檔報價 Flag43 | IndexFlag=43 才有值 |
| IndexFlag\_50 | [FiveTick\_Flag50](#fivetick_flag50-indexflag50) | 五檔報價 Flag50 | IndexFlag=50 才有值 |
| IndexFlag\_51 | [FiveTick\_Flag51](#fivetick_flag51-indexflag51) | 五檔報價 Flag51 | IndexFlag=51 才有值 |

#### FiveTick\_Flag20 五檔報價 IndexFlag20 物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Price1 | double | 第一買價 |  |
| Price2 | double | 第二買價 |  |
| Price3 | double | 第三買價 |  |
| Price4 | double | 第四買價 |  |
| Price5 | double | 第五買價 |  |
| Vol1 | Int | 第一買量 |  |
| Vol2 | Int | 第二買量 |  |
| Vol3 | Int | 第三買量 |  |
| Vol4 | Int | 第四買量 |  |
| Vol5 | Int | 第五買量 |  |

#### FiveTick\_Flag21 五檔報價 IndexFlag21 物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Price1 | double | 第一賣價 |  |
| Price2 | double | 第二賣價 |  |
| Price3 | double | 第三賣價 |  |
| Price4 | double | 第四賣價 |  |
| Price5 | double | 第五賣價 |  |
| Vol1 | Int | 第一賣量 |  |
| Vol2 | Int | 第二賣量 |  |
| Vol3 | Int | 第三賣量 |  |
| Vol4 | Int | 第四賣量 |  |
| Vol5 | Int | 第五賣量 |  |

#### FiveTick\_Flag42 五檔報價 IndexFlag42 物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Price1 | double | 第六買價 |  |
| Price2 | double | 第七買價 |  |
| Price3 | double | 第八買價 |  |
| Price4 | double | 第九買價 |  |
| Price5 | double | 第十買價 |  |
| Vol1 | Int | 第六買量 |  |
| Vol2 | Int | 第七買量 |  |
| Vol3 | Int | 第八買量 |  |
| Vol4 | Int | 第九買量 |  |
| Vol5 | Int | 第十買量 |  |

#### FiveTick\_Flag43 五檔報價 IndexFlag43 物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Price1 | double | 第六賣價 |  |
| Price2 | double | 第七賣價 |  |
| Price3 | double | 第八賣價 |  |
| Price4 | double | 第九賣價 |  |
| Price5 | double | 第十賣價 |  |
| Vol1 | Int | 第六賣量 |  |
| Vol2 | Int | 第七賣量 |  |
| Vol3 | Int | 第八賣量 |  |
| Vol4 | Int | 第九賣量 |  |
| Vol5 | Int | 第十賣量 |  |

#### FiveTick\_Flag50 五檔報價 IndexFlag50 物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| BuyPrice1 | double | 第一買價 |  |
| BuyPrice2 | double | 第二買價 |  |
| BuyPrice3 | double | 第三買價 |  |
| BuyPrice4 | double | 第四買價 |  |
| BuyPrice5 | double | 第五買價 |  |
| BuyVol1 | Int | 第一買量 |  |
| BuyVol2 | Int | 第二買量 |  |
| BuyVol3 | Int | 第三買量 |  |
| BuyVol4 | Int | 第四買量 |  |
| BuyVol5 | Int | 第五買量 |  |
| SellPrice1 | double | 第一賣價 |  |
| SellPrice2 | double | 第二賣價 |  |
| SellPrice3 | double | 第三賣價 |  |
| SellPrice4 | double | 第四賣價 |  |
| SellPrice5 | double | 第五賣價 |  |
| SellVol1 | Int | 第一賣量 |  |
| SellVol2 | Int | 第二賣量 |  |
| SellVol3 | Int | 第三賣量 |  |
| SellVol4 | Int | 第四賣量 |  |
| SellVol5 | Int | 第五賣量 |  |

#### FiveTick\_Flag51 五檔報價 IndexFlag51 物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| BuyPrice1 | double | 第六買價 |  |
| BuyPrice2 | double | 第七買價 |  |
| BuyPrice3 | double | 第八買價 |  |
| BuyPrice4 | double | 第九買價 |  |
| BuyPrice5 | double | 第十買價 |  |
| BuyVol1 | Int | 第六買量 |  |
| BuyVol2 | Int | 第七買量 |  |
| BuyVol3 | Int | 第八買量 |  |
| BuyVol4 | Int | 第九買量 |  |
| BuyVol5 | Int | 第十買量 |  |
| SellPrice1 | double | 第六賣價 |  |
| SellPrice2 | double | 第七賣價 |  |
| SellPrice3 | double | 第八賣價 |  |
| SellPrice4 | double | 第九賣價 |  |
| SellPrice5 | double | 第十賣價 |  |
| SellVol1 | Int | 第六賣量 |  |
| SellVol2 | Int | 第七賣量 |  |
| SellVol3 | Int | 第八賣量 |  |
| SellVol4 | Int | 第九賣量 |  |
| SellVol5 | Int | 第十賣量 |  |

> 註：買價市價買 999999999，賣價市價賣 -999999999

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
from YuantaOneAPI import YuantaSparkAPITrader, enumLogType, enumQuoteIndexType, enumMarketType, enumEnvironmentMode, enumQuoteFiveTickIndexType, FiveTickA

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

List<FiveTickA> lstFiveTick = new List<FiveTickA>();

FiveTickA stkInfo = new FiveTickA
{
    MarketType = enumMarketType.TWSE,
    StockCode = "2330"
};

lstFiveTick.Add(stkInfo);

objYuantaSparkAPI.SubscribeFiveTickA(Account, lstFiveTick);
Thread.Sleep(2000);
```

#### Onresponse

```
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
                    case 'SubscribeFiveTickA':
                        # 五檔訂閱結果
                        fResult = objValue

                        result += '五檔訂閱結果:\r\n'
                        result += '{0},{1},{2},{3},'.format(fResult.Key,str(fResult.MarketType),fResult.StkCode,str(fResult.IndexFlag))
                        match fResult.IndexFlag:
                            case enumQuoteFiveTickIndexType.IndexFlag20:
                                #flag20 = FiveTick_Flag20()
                                flag20 = fResult.IndexFlag_20
                                result +='{0},{1},{2},{3},{4},{5},{6},{7},{8},{9}\r\n'.format(
                                    str(flag20.Price1),str(flag20.Price2),str(flag20.Price3),str(flag20.Price4),str(flag20.Price5),str(flag20.Vol1),str(flag20.Vol2),str(flag20.Vol3, str(flag20.Vol4),str(flag20.Vol5)))
                            case enumQuoteFiveTickIndexType.IndexFlag21:
                                #flag21 = FiveTick_Flag21()
                                flag21 = fResult.IndexFlag_21
                                result +='{0},{1},{2},{3},{4},{5},{6},{7},{8},{9}\r\n'.format(
                                    str(flag21.Price1),str(flag21.Price2),str(flag21.Price3),str(flag21.Price4),str(flag21.Price5),str(flag21.Vol1),str(flag21.Vol2),str(flag21.Vol3),str(flag21.Vol4),str(flag21.Vol5))
                            case enumQuoteFiveTickIndexType.IndexFlag42:
                                #flag42 = FiveTick_Flag42()
                                flag42 = fResult.IndexFlag_42
                                result +='{0},{1},{2},{3},{4},{5},{6},{7},{8},{9}\r\n'.format(
                                    str(flag42.Price1),str(flag42.Price2),str(flag42.Price3),str(flag42.Price4),str(flag42.Price5),str(flag42.Vol1),str(flag42.Vol2),str(flag42.Vol3),str(flag42.Vol4),str(flag42.Vol5))
                            case enumQuoteFiveTickIndexType.IndexFlag43:
                                #flag43 = FiveTick_Flag43()
                                flag43 = fResult.IndexFlag_43
                                result +='{0},{1},{2},{3},{4},{5},{6},{7},{8},{9}\r\n'.format(
                                    str(flag43.Price1),str(flag43.Price2),str(flag43.Price3),str(flag43.Price4),str(flag43.Price5),str(flag43.Vol1),str(flag43.Vol2),str(flag43.Vol3),str(flag43.Vol4),str(flag43.Vol5))
                            case enumQuoteFiveTickIndexType.IndexFlag50:
                                #flag50 = FiveTick_Flag50()
                                flag50 = fResult.IndexFlag_50
                                result +='{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19}\r\n'.format(
                                    str(flag50.BuyPrice1),str(flag50.BuyPrice2),str(flag50.BuyPrice3),str(flag50.BuyPrice4),str(flag50.BuyPrice5),str(flag50.BuyVol1),str(flag50.BuyVol2),str(flag50.BuyVol3),str(flag50.BuyVol4),
                                    str(flag50.BuyVol5),str(flag50.SellPrice1),str(flag50.SellPrice2),str(flag50.SellPrice3),str(flag50.SellPrice4),str(flag50.SellPrice5),str(flag50.SellVol1),str(flag50.SellVol2),str(flag50.SellVol3),
                                    str(flag50.SellVol4),str(flag50.SellVol5))
                            case enumQuoteFiveTickIndexType.IndexFlag51:
                                #flag51 = FiveTick_Flag51()
                                flag51 = fResult.IndexFlag_51
                                result +='{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19}\r\n'.format(
                                    str(flag51.BuyPrice1),str(flag51.BuyPrice2),str(flag51.BuyPrice3),str(flag51.BuyPrice4),str(flag51.BuyPrice5),str(flag51.BuyVol1),str(flag51.BuyVol2),str(flag51.BuyVol3),str(flag51.BuyVol4),
                                    str(flag51.BuyVol5),str(flag51.SellPrice1),str(flag51.SellPrice2),str(flag51.SellPrice3),str(flag51.SellPrice4),str(flag51.SellPrice5),str(flag51.SellVol1),str(flag51.SellVol2),str(flag51.SellVol3),
                                    str(flag51.SellVol4),str(flag51.SellVol5))
                            case _:
                                result += str(fResult.Value)+'\r\n'

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

fivetickList = List[FiveTickA]()
fivetick = FiveTickA()
fivetick.MarketType = enumMarketType.TWSE
fivetick.StockCode = '2330'
fivetickList.Add(fivetick)

#最佳五檔行情訂閱
objYuantaSparkAPI.SubscribeFiveTickA('S98875005091',fivetickList)

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
            if (strIndex == "SubscribeFiveTickA")
            {
                var result = (FiveTickAResult)objValue;

                try
                {
                    strResult += "五檔訂閱結果: \r\n";
                    strResult += $"{result.Key},{result.MarketType},{result.StkCode},{result.IndexFlag}:";

                    string datas = string.Empty;
                    dynamic flag1 = null;
                    dynamic flag2 = null;

                    switch (result.IndexFlag)
                    {
                        case enumQuoteFiveTickIndexType.IndexFlag20:
                            flag1 = result.IndexFlag_20;
                            break;
                        case enumQuoteFiveTickIndexType.IndexFlag21:
                            flag1 = result.IndexFlag_21;
                            break;
                        case enumQuoteFiveTickIndexType.IndexFlag42:
                            flag1 = result.IndexFlag_42;
                            break;
                        case enumQuoteFiveTickIndexType.IndexFlag43:
                            flag1 = result.IndexFlag_43;
                            break;
                        case enumQuoteFiveTickIndexType.IndexFlag50:
                            flag2 = result.IndexFlag_50;
                            break;
                        case enumQuoteFiveTickIndexType.IndexFlag51:
                            flag2 = result.IndexFlag_51;
                            break;
                        default:
                            datas += result.Value;
                            break;
                    }

                    if (flag1 != null)
                    {
                        datas = string.Empty;
                        datas += $"{flag1.Price1},{flag1.Price2},{flag1.Price3},{flag1.Price4},{flag1.Price5}," +
                                $"{flag1.Vol1},{flag1.Vol2},{flag1.Vol3},{flag1.Vol4},{flag1.Vol5}";
                    }
                    else if (flag2 != null)
                    {
                        datas = string.Empty;
                        datas += $"{flag2.BuyPrice1},{flag2.BuyPrice2},{flag2.BuyPrice3},{flag2.BuyPrice4},{flag2.BuyPrice5}," +
                                $"{flag2.BuyVol1},{flag2.BuyVol2},{flag2.BuyVol3},{flag2.BuyVol4},{flag2.BuyVol5}," +
                                $"{flag2.SellPrice1},{flag2.SellPrice2},{flag2.SellPrice3},{flag2.SellPrice4},{flag2.SellPrice5}," +
                                $"{flag2.SellVol1},{flag2.SellVol2},{flag2.SellVol3},{flag2.SellVol4},{flag2.SellVol5}";
                    }

                    strResult += datas + "\r\n";
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
    "IndexFlag": "IndexFlag50",
    "Value": {
      "BuyPrices": ["1420.0", "1415.0", "1410.0", "1405.0", "1400.0"],
      "BuyVols": ["326", "2397", "1623", "844", "1100"],
      "SellPrices": ["1425.0", "1430.0", "1435.0", "1440.0", "1445.0"],
      "SellVols": ["1635", "2215", "931", "1143", "908"]
    }
  }
}
```
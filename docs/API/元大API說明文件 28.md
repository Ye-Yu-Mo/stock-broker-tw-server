---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E6%A2%9D%E4%BB%B6%E5%96%AE/%E6%96%B0%E5%A2%9E%E6%A2%9D%E4%BB%B6%E5%96%AE/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## SendAlgoCOOdrStrategy

新增條件單

```
bool SendAlgoCOOdrStrategy(Account, lstStrategy, lng)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 | 證券:S+分公司代號(4)+帳號(7)   例如 S98875005091      註：僅可使用證券帳號 |
| lstStrategy | List< [STOStrategy](#stostrategy) >,   List< [MLPStrategy](#mlpstrategy) >,   List< [OCOStrategy](#ocostrategy) >,   List< [SpiderStrategy](#spiderstrategy) >,   List< [MS\_SpiderStrategy](#ms_spiderstrategy) >,   List< [MS\_DayTradeSpiderStrategy](#ms_daytradespiderstrategy) > | 條件單物件清單 | STOStrategy 停損利   MLPStrategy 移動鎖利   OCOStrategy 二擇一   SpiderStrategy 多條件   MS\_SpiderStrategy 母子單   MS\_DayTradeSpiderStrategy 當沖母子單      註：單次僅能同策略 |
| lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   \- Normal：Big5   \- UTF8：UTF8   \- SC：簡體中文 |

#### STOStrategy 停損利單物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 | 證券:S+分公司代號(4)+帳號(7)   例如 S98875005091 |
| EffTime | DateTime | 策略起始日 | 盤中區間限制:當日~90天內   盤後區間限制:下一交易日~90天內 |
| ExpTime | DateTime | 策略終止日 | 盤中區間限制:當日~90天內   盤後區間限制:下一交易日~90天內 |
| Order | StrategyOrder1 | 下單方式 | [參考列舉物件-條件單下單方式1](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#strategyorder1-1) |
| StrategySettings | [StrategySettings](#strategysettings) | 條件設定 |  |
| OrderSettings | [OrderSettings1](#ordersettings1tt1-1) <OrderType1,OrderPriceType1> | 下單設定 | 僅提供庫存賣出 |

#### MLPStrategy 移動鎖利單物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 | 證券:S+分公司代號(4)+帳號(7)   例如 S98875005091 |
| EffTime | DateTime | 策略起始日 | 盤中區間限制:當日~90天內   盤後區間限制:下一交易日~90天內 |
| ExpTime | DateTime | 策略終止日 | 盤中區間限制:當日~90天內   盤後區間限制:下一交易日~90天內 |
| Order | StrategyOrder1 | 下單方式 | [參考列舉物件-條件單下單方式1](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#strategyorder1-1) |
| StrategySettings | [MLPStrategySettings](#MLPStrategySettings) | 條件設定 |  |
| OrderSettings | [OrderSettings1](#ordersettings1tt1-1) <OrderType1,OrderPriceType2> | 下單設定 |  |

#### OCOStrategy 二擇一單物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 | 證券:S+分公司代號(4)+帳號(7)   例如 S98875005091 |
| EffTime | DateTime | 策略起始日 | 盤中區間限制:當日~90天內      盤後區間限制:下一交易日~90天內 |
| ExpTime | DateTime | 策略終止日 | 盤中區間限制:當日~90天內      盤後區間限制:下一交易日~90天內 |
| Order | StrategyOrder1 | 下單方式 | [參考列舉物件-條件單下單方式1](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#strategyorder1-1)   限輸入:成交就停、觸發就停 |
| StrategySettings1 | [StrategySettings](#strategysettings) | 條件1條件設定 | 條件1與條件2 商品需一致 |
| StrategySettings2 | [StrategySettings](#strategysettings) | 條件2條件設定 | 條件1與條件2 商品需一致 |
| OrderSettings1 | [OrderSettings2](#ordersettings2tt1-2) <OrderType2, OrderPriceType1> | 條件1下單設定 |  |
| OrderSettings2 | [OrderSettings2](#ordersettings2tt1-2) <OrderType2, OrderPriceType1> | 條件2下單設定 |  |

#### SpiderStrategy 多條件單物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 | 證券:S+分公司代號(4)+帳號(7)   例如 S98875005091 |
| EffTime | DateTime | 策略起始日 | 盤中區間限制:當日~90天內      盤後區間限制:下一交易日~90天內 |
| ExpTime | DateTime | 策略終止日 | 盤中區間限制:當日~90天內      盤後區間限制:下一交易日~90天內 |
| Order | StrategyOrder1 | 下單方式 | [參考列舉物件-條件單下單方式1](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#strategyorder1-1) |
| Settings | [SpiderSettings](#spidersettings) | 設定 |  |

#### MS\_SpiderStrategy 母子單物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 | 證券:S+分公司代號(4)+帳號(7)   例如 S98875005091 |
| EffTime | DateTime | 策略起始日 | 盤中區間限制:當日~90天內      盤後區間限制:下一交易日~90天內 |
| ExpTime | DateTime | 策略終止日 | 盤中區間限制:當日~90天內      盤後區間限制:下一交易日~90天內 |
| Order | StrategyOrder2 | 下單方式 | [參考列舉物件-條件單下單方式2](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#strategyorder2-2)   限選交易到設定單位全部成交 |
| DayTrade | bool | 是否當沖 | 固定false |
| M\_SpiderStrategy | [SpiderSettings](#spidersettings) | 母單設定 |  |
| S\_SpiderStrategy | [SpiderSettings](#spidersettings) | 子單設定 |  |

#### MS\_DayTradeSpiderStrategy 當沖母子單物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 | 證券:S+分公司代號(4)+帳號(7)   例如 S98875005091 |
| EffTime | DateTime | 策略起始日 | 盤中限填當日(僅當日有效)      盤後限填下一交易日(僅下一交易日當日有效) |
| ExpTime | DateTime | 策略終止日 | 盤中限填當日(僅當日有效)      盤後限填下一交易日(僅下一交易日當日有效) |
| Order | StrategyOrder2 | 下單方式 | [參考列舉物件-條件單下單方式2](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#strategyorder2-2)   限選母單成交子單就立即下單 |
| DayTrade | bool | 是否當沖 | 固定true |
| M\_SpiderStrategy | [DayTradeSpiderSettings](#daytradespidersettings) | 母單設定 |  |
| OrderSettings | [OrderSettings2](#ordersettings2tt1-2) <OrderType3, OrderPriceType1> | 子單下單設定 | 僅提供母單反向 |

#### StrategySettings 條件設定

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MarketType | enumMarketType | 市場類別 | 僅支援上市、上櫃商品 |
| StkCode | string | 商品代號 |  |
| Condition | StrategyCondition1 | 條件種類 | [參考列舉物件-條件單條件1](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#strategycondition1-1) |
| Direction | int | 條件方向 | 1:大於等於      2:小於等於(成交價才可使用) |
| Value | double | 條件數值 | 限制：      成交價(開盤參考價x0.7~1.7倍)      總量(單位:張)      當日漲跌幅(0.01~10)% |

#### MLPStrategySettings 移動鎖利條件設定

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MarketType | enumMarketType | 市場類別 | 僅支援上市、上櫃商品 |
| StkCode | string | 商品代號 |  |
| Price | double | 基準價 | 限制：開盤參考價x0.7~1.7倍 |
| Pullback\_Uint | int | 區間高點回檔單位 | 1:百分比      2:元 |
| Pullback\_Value | double | 區間高點回檔數值 | 百分比:0.1~100%      元:0.01<=設定值<=開盤參考價 |

#### OrderSettings1<T,T1> 下單設定1

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| OrderType | T | 委託種類 | 停損利、移動鎖利:OrderType1   [參考列舉物件-委託種類](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#ordertype1-1) |
| TimeInforce | int | 委託時間效期 | 0:ROD      3:IOC      4:FOK |
| PriceType | T1 | 委託價格種類 | 停損利:OrderPriceType1      移動鎖利:OrderPriceType2      [參考列舉物件-委託價格種類](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#orderpricetype1-1) |
| OrderValue | double | 委託數值 | 非限價、成交價請填0      限制:   限價(開盤參考價x0.7~1.7倍)      成交價(+-0~8)tick |
| OrderQty | int | 委託單位 | 張 |

#### OrderSettings2<T,T1> 下單設定2

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MarketType | enumMarketType | 市場類別 | 僅支援上市、上櫃商品 |
| StkCode | string | 商品代號 |  |
| OrderType | T | 委託種類 | 二擇一、多條件、母子單:OrderType2      當沖母子單:OrderType3      [參考列舉物件-委託種類](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#ordertype1-1) |
| TimeInforce | int | 委託時間效期 | 0:ROD      3:IOC      4:FOK |
| PriceType | T1 | 委託價格種類 | OrderPriceType1   [參考列舉物件-委託價格種類](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#orderpricetype1-1) |
| OrderValue | double | 委託數值 | 非限價、成交價請填0      限制:      限價(開盤參考價x0.7~1.7倍)      成交價(+-0~8)tick |
| OrderQty | int | 委託單位 | 張 |

#### SpiderSettings 多條件設定

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| lstSettings | List< [SpiderStrategySettings](#spiderstrategysettings) > | 條件設定 | \*最多8個、不得為0個   \*同商品同種類同方向不可重複      \*當全部符合:同商品漲與跌不可同時設定   1.當日漲幅、當日跌幅不可同時設定      2.總漲幅、總跌幅不可同時設定      3.當日漲停、當日跌停不可同時設定   4.當日上漲、當日下跌不可同時設定 |
| OrderSettings | [OrderSettings2](#ordersettings2tt1-2) <OrderType2, OrderPriceType1> | 下單設定 |  |
| Eligible | int | 符合條件 | 1:擇一符合      2:全部符合 |

#### DayTradeSpiderSettings 當沖條件設定

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| lstSettings | List< [SpiderStrategySettings](#spiderstrategysettings) > | 條件設定 | \*最多8個、不得為0個   \*同商品同種類同方向不可重複      \*當全部符合:同商品漲與跌不可同時設定   1.當日漲幅、當日跌幅不可同時設定      2.總漲幅、總跌幅不可同時設定      3.當日漲停、當日跌停不可同時設定   4.當日上漲、當日下跌不可同時設定 |
| OrderSettings | [OrderSettings2](#ordersettings2) <OrderType3, OrderPriceType1> | 下單設定 |  |
| Eligible | int | 符合條件 | 1:擇一符合      2:全部符合 |

#### SpiderStrategySettings 多條件條件設定

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MarketType | enumMarketType | 市場類別 | 僅支援上市、上櫃商品 |
| StkCode | string | 商品代號 |  |
| StrategyConditions | StrategyCondition2 | 條件種類 | [參考列舉物件-條件單條件2](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#strategycondition2-2) |
| Direction | int | 條件方向 | 1:大於等於      2:小於等於(成交價才可使用)      3:無(漲停或跌停) |
| Price | double | 基準價 | 條件種類非總漲幅、總跌幅填0   限制:開盤參考價0.7~1.7倍 |
| Value | double | 條件數值 | 當日漲停、當日跌停填0      限制:      成交價(現價0.7~1.7倍)      總量(單位:張)      當日漲跌幅(0.01~10)%      總漲跌幅(0.01~100)%      當日上漲下跌(0.01~9999) |

---

### Output Parameters

#### OrderStrategyResult 條件單委託結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| ResultList | List< [OrderStrategyStatus](#orderstrategystatus) > | 條件單委託結果清單 |  |

#### OrderStrategyStatus 條件單委託狀態

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| OrdStatus | SStatus | 委託狀態 | [參考列舉物件-策略狀態](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#sstatus) |
| OrderNo | String | 委託編號 |  |
| EffTime | DateTime | 策略起始日 |  |
| ExpTime | DateTime | 策略終止日 |  |
| Msg | string | 訊息中文 |  |

---

### 範例 (停損利)

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
                        enumMarketType, enumEnvironmentMode,
                        STOStrategy, StrategyOrder1, StrategySettings, StrategyCondition1, OrderSettings1, 
                        OrderType1, OrderPriceType1)

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

// 條件單 STO
List<STOStrategy> lstSTO = new List<STOStrategy>();
lstSTO.Add(new STOStrategy
{
    Account = Account,
    EffTime = new DateTime(2026, 4, 3),
    ExpTime = new DateTime(2026, 4, 30),
    Order = (StrategyOrder1)2,  
    StrategySettings = new StrategySettings
    {
        MarketType = enumMarketType.TWSE,
        StkCode = "2885",
        Condition = (StrategyCondition1)1,  
        Direction = 1,
        Value = 46.2
    },
    OrderSettings = new OrderSettings1<OrderType1, OrderPriceType1>
    {
        OrderType = (OrderType1)2,  
        TimeInforce = 0,
        PriceType = (OrderPriceType1)0,  
        OrderValue = 46.2,
        OrderQty = 10
    }
});

objYuantaSparkAPI.SendAlgoCOOdrStrategy(Account, lstSTO);
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

                    case 'SendAlgoCOOdrStrategy':
                        SResult = objValue
                        sResult = SResult.ResultList

                        result = ''
                        result += "新增條件單:\r\n"

                        for i in range(sResult.Count):  
                            result += '{0},{1},{2},{3},{4}\r\n'.format(sResult[i].OrdStatus,sResult[i].OrderNo,sResult[i].EffTime,sResult[i].ExpTime,sResult[i].Msg)

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

sto_list  = List[STOStrategy]()
sto_obj = STOStrategy()
sto_obj.Account = "S98875005091"
sto_obj.EffTime =  System.DateTime(2026, 3, 31)
sto_obj.ExpTime =  System.DateTime(2026, 4, 30)
sto_obj.Order = StrategyOrder1(2)

sto_obj.StrategySettings = StrategySettings() 
sto_obj.StrategySettings.MarketType = enumMarketType.TWSE
sto_obj.StrategySettings.StkCode = "2885"
sto_obj.StrategySettings.Condition = StrategyCondition1(1)
sto_obj.StrategySettings.Direction = 1
sto_obj.StrategySettings.Value = 46.2

sto_obj.OrderSettings = OrderSettings1[OrderType1, OrderPriceType1]()
sto_obj.OrderSettings.OrderType = OrderType1(2)
sto_obj.OrderSettings.TimeInforce = 0
sto_obj.OrderSettings.PriceType = OrderPriceType1(0)    # 限價：0
sto_obj.OrderSettings.OrderValue = 46.2
sto_obj.OrderSettings.OrderQty = 10

sto_list.Add(sto_obj)
objYuantaSparkAPI.SendAlgoCOOdrStrategy[STOStrategy]('S98875005091',sto_list)  
time.sleep(1)

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

            if (strIndex == "SendAlgoCOOdrStrategy")
            {
                var result = (OrderStrategyResult)objValue;
                try
                {
                    strResult += "新增條件單:\r\n";
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
        "OrdStatus": "SstBuilt",
        "OrderNo": "k263R000000056",
        "EffTime": "2026/04/03",
        "ExpTime": "2026/04/30",
        "Msg": "策略已建立"
      }
    ]
  }
}
```

---

### 範例 (移動鎖利)

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
                        StrategyOrder1, MLPStrategySettings, OrderSettings1, OrderType1, OrderPriceType2, MLPStrategy)

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

// 移動損利單 MLP
List<MLPStrategy> lstMLP = new List<MLPStrategy>();
lstMLP.Add(new MLPStrategy
{
    Account = Account,
    EffTime = new DateTime(2026, 4, 2),
    ExpTime = new DateTime(2026, 4, 30),
    Order = (StrategyOrder1)2,  // StrategyOrder1(2) = 觸發就停
    StrategySettings = new MLPStrategySettings
    {
        MarketType = enumMarketType.TWSE,
        StkCode = "2885",
        Price = 46.5,               // 基準價
        Pullback_Uint = 2,          // 區間高點回檔單位  1:百分比 2:元
        Pullback_Value = 0.5        // 區間高點回檔數值
    },
    OrderSettings = new OrderSettings1<OrderType1, OrderPriceType2>
    {
        OrderType = (OrderType1)2,          // OrderType1(2)
        TimeInforce = 0,
        PriceType = (OrderPriceType2)1,     // OrderPriceType2(1) 市價
        OrderValue = 0,
        OrderQty = 5
    }
});

objYuantaSparkAPI.SendAlgoCOOdrStrategy(Account, lstMLP);
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

                    case 'SendAlgoCOOdrStrategy':
                        SResult = objValue
                        sResult = SResult.ResultList

                        result = ''
                        result += "新增條件單:\r\n"

                        for i in range(sResult.Count):  
                            result += '{0},{1},{2},{3},{4}\r\n'.format(sResult[i].OrdStatus,sResult[i].OrderNo,sResult[i].EffTime,sResult[i].ExpTime,sResult[i].Msg)

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

mlp_list  = List[MLPStrategy]()
mlp_obj = MLPStrategy()

mlp_obj.Account = "S98875005091"
mlp_obj.EffTime =  System.DateTime(2026, 4, 1)
mlp_obj.ExpTime =  System.DateTime(2026, 4, 31)
mlp_obj.Order = StrategyOrder1(2)

mlp_obj.StrategySettings = MLPStrategySettings() 
mlp_obj.StrategySettings.MarketType = enumMarketType.TWSE
mlp_obj.StrategySettings.StkCode = "2885"
mlp_obj.StrategySettings.Price = 46.5                  # 基準價
mlp_obj.StrategySettings.Pullback_Uint = 2             # 區間高點回檔單位  1:百分比 2:元 
mlp_obj.StrategySettings.Pullback_Value = 0.5          # 區間高點回檔數值

mlp_obj.OrderSettings = OrderSettings1[OrderType1, OrderPriceType2]()
mlp_obj.OrderSettings.OrderType = OrderType1(2)
mlp_obj.OrderSettings.TimeInforce = 0
mlp_obj.OrderSettings.PriceType = OrderPriceType2(1)    #限價：0  市價：1 成交價：2 漲停：3 平盤：4 跌停：5 
mlp_obj.OrderSettings.OrderValue = 0
mlp_obj.OrderSettings.OrderQty = 5

mlp_list.Add(mlp_obj)
objYuantaSparkAPI.SendAlgoCOOdrStrategy[MLPStrategy]('S98875005091', mlp_list)
time.sleep(1)

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

            if (strIndex == "SendAlgoCOOdrStrategy")
            {
                var result = (OrderStrategyResult)objValue;
                try
                {
                    strResult += "新增條件單:\r\n";
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

---

### 範例 (二擇一)

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
                        enumMarketType, enumEnvironmentMode, 
                        StrategyOrder1,StrategyCondition1, OCOStrategy, StrategySettings, OrderSettings2, OrderType2, OrderPriceType1)

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

// 二擇一單 OCO
List<OCOStrategy> lstOCO = new List<OCOStrategy>();
lstOCO.Add(new OCOStrategy
{
    Account = Account,
    EffTime = new DateTime(2026, 4, 2),
    ExpTime = new DateTime(2026, 4, 30),
    Order = (StrategyOrder1)1,          // 成交就停：1 觸發就停：2

    // 條件1：止盈
    StrategySettings1 = new StrategySettings
    {
        MarketType = enumMarketType.TWSE,
        StkCode = "2885",
        Condition = (StrategyCondition1)1,  // 成交價：1
        Direction = 1,                      // 大於等於
        Value = 46.7
    },

    // 條件2：止損
    StrategySettings2 = new StrategySettings
    {
        MarketType = enumMarketType.TWSE,
        StkCode = "2885",
        Condition = (StrategyCondition1)1,  // 成交價：1
        Direction = 2,                      // 小於等於
        Value = 45.5
    },

    // 條件1下單：止盈下單
    OrderSettings1 = new OrderSettings2<OrderType2, OrderPriceType1>
    {
        MarketType = enumMarketType.TWSE,
        StkCode = "2885",
        OrderType = (OrderType2)2,          // 現股賣出：2
        TimeInforce = 0,
        PriceType = (OrderPriceType1)0,     // 限價：0 市價：1
        OrderValue = 46.7,
        OrderQty = 1
    },

    // 條件2下單：止損下單
    OrderSettings2 = new OrderSettings2<OrderType2, OrderPriceType1>
    {
        MarketType = enumMarketType.TWSE,
        StkCode = "2885",
        OrderType = (OrderType2)2,          // 現股賣出：2
        TimeInforce = 0,
        PriceType = (OrderPriceType1)0,     // 限價：0 市價：1
        OrderValue = 45.5,
        OrderQty = 1
    }
});

objYuantaSparkAPI.SendAlgoCOOdrStrategy(Account, lstOCO);
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

                    case 'SendAlgoCOOdrStrategy':
                        SResult = objValue
                        sResult = SResult.ResultList

                        result = ''
                        result += "新增條件單:\r\n"

                        for i in range(sResult.Count):  
                            result += '{0},{1},{2},{3},{4}\r\n'.format(sResult[i].OrdStatus,sResult[i].OrderNo,sResult[i].EffTime,sResult[i].ExpTime,sResult[i].Msg)

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

oco_list  = List[OCOStrategy]()
oco_obj = OCOStrategy()

oco_obj.Account = "S98875005091"
oco_obj.EffTime =  System.DateTime(2026, 4, 1)
oco_obj.ExpTime =  System.DateTime(2026, 4, 31)
oco_obj.Order = StrategyOrder1(1)       # 限輸入:成交就停、觸發就停 ，成交就停：1 觸發就停：2

#條件1:止盈
oco_obj.StrategySettings1 = StrategySettings() 
profit_cond = oco_obj.StrategySettings1 
profit_cond.MarketType = enumMarketType.TWSE
profit_cond.StkCode = "2885"
profit_cond.Condition = StrategyCondition1(1)
profit_cond.Direction = 1       # 大於等於
profit_cond.Value = 46.7

#條件2:止損
oco_obj.StrategySettings2 = StrategySettings() 
loss_cond = oco_obj.StrategySettings2 
loss_cond.MarketType = enumMarketType.TWSE
loss_cond.StkCode = "2885"
loss_cond.Condition = StrategyCondition1(1)
loss_cond.Direction = 2         # 小於等於
loss_cond.Value = 45.5

#條件1:止盈下單
oco_obj.OrderSettings1 = OrderSettings2[OrderType2, OrderPriceType1]()
profit_order = oco_obj.OrderSettings1 
profit_order.MarketType = enumMarketType.TWSE
profit_order.StkCode = "2885"
profit_order.OrderType = OrderType2(2)              # 現股賣出：2
profit_order.TimeInforce = 0
profit_order.PriceType = OrderPriceType1(0)         # 限價：0 市價 :1
profit_order.OrderValue = 46.7
profit_order.OrderQty = 1
#條件2:止損下單
oco_obj.OrderSettings2 = OrderSettings2[OrderType2, OrderPriceType1]()
loss_order = oco_obj.OrderSettings2
loss_order.MarketType = enumMarketType.TWSE
loss_order.StkCode = "2885"
loss_order.OrderType = OrderType2(2)                # 現股賣出：2
loss_order.TimeInforce = 0
loss_order.PriceType = OrderPriceType1(0)           # 限價：0 市價 :1
loss_order.OrderValue = 45.5
loss_order.OrderQty = 1
oco_list.Add(oco_obj)

objYuantaSparkAPI.SendAlgoCOOdrStrategy[OCOStrategy]('S98875005091', oco_list)
time.sleep(1)

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

            if (strIndex == "SendAlgoCOOdrStrategy")
            {
                var result = (OrderStrategyResult)objValue;
                try
                {
                    strResult += "新增條件單:\r\n";
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
        "OrdStatus": "SstBuilt",
        "OrderNo": "k263R000000056",
        "EffTime": "2026/04/03",
        "ExpTime": "2026/04/30",
        "Msg": "策略已建立"
      }
    ]
  }
}
```

---

### 範例 (多條件)

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
                        SpiderStrategy, SpiderSettings, SpiderStrategySettings, StrategyCondition2, StrategyOrder1, OrderSettings2, OrderType2, OrderPriceType1)

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

// 多條件單 Spider
List<SpiderStrategySettings> lstSettings = new List<SpiderStrategySettings>();

// 條件1：成交價 >= 47.0
lstSettings.Add(new SpiderStrategySettings
{
    MarketType = enumMarketType.TWSE,
    StkCode = "2885",
    StrategyConditions = (StrategyCondition2)1,  // 成交價：1
    Direction = 1,                                // 大於等於：1
    Price = 0,                                    // 非總漲跌幅填 0
    Value = 47.0
});

// 條件2：當日漲幅 >= 1%
lstSettings.Add(new SpiderStrategySettings
{
    MarketType = enumMarketType.TWSE,
    StkCode = "2885",
    StrategyConditions = (StrategyCondition2)3,  // 當日漲幅：3
    Direction = 1,                                // 大於等於：1
    Price = 0,                                    // 非總漲跌幅填 0
    Value = 1                                     // 當日漲跌幅(0.01~10)%
});

List<SpiderStrategy> lstSpider = new List<SpiderStrategy>();
lstSpider.Add(new SpiderStrategy
{
    Account = Account,
    EffTime = new DateTime(2026, 4, 2),
    ExpTime = new DateTime(2026, 4, 30),
    Order = (StrategyOrder1)1,              // 成交就停：1
    Settings = new SpiderSettings
    {
        Eligible = 2,                       // 1:擇一符合 2:全部符合
        lstSettings = lstSettings,
        OrderSettings = new OrderSettings2<OrderType2, OrderPriceType1>
        {
            MarketType = enumMarketType.TWSE,
            StkCode = "2885",
            OrderType = (OrderType2)1,      // 現股買進：1
            TimeInforce = 0,
            PriceType = (OrderPriceType1)1, // 市價：1
            OrderValue = 0,
            OrderQty = 2
        }
    }
});

objYuantaSparkAPI.SendAlgoCOOdrStrategy(Account, lstSpider);
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

                    case 'SendAlgoCOOdrStrategy':
                        SResult = objValue
                        sResult = SResult.ResultList

                        result = ''
                        result += "新增條件單:\r\n"

                        for i in range(sResult.Count):  
                            result += '{0},{1},{2},{3},{4}\r\n'.format(sResult[i].OrdStatus,sResult[i].OrderNo,sResult[i].EffTime,sResult[i].ExpTime,sResult[i].Msg)

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

spider_list  = List[SpiderStrategy]()
spider_obj = SpiderStrategy()

spider_obj.Account = "S98875005091"
spider_obj.EffTime =  System.DateTime(2026, 4, 1)
spider_obj.ExpTime =  System.DateTime(2026, 4, 31)
spider_obj.Order = StrategyOrder1(1)

spider_obj.Settings = SpiderSettings()              #下單設定

lstSettings =  List[SpiderStrategySettings]()
#條件1
cond_1 = SpiderStrategySettings()
cond_1.MarketType = enumMarketType.TWSE       
cond_1.StkCode = "2885"                         
cond_1.StrategyConditions = StrategyCondition2(1)   # 成交價
cond_1.Direction = 1                            # 1:大於等於 2:小於等於(成交價才可使用) 3:無(漲停或跌停) 
cond_1.Price = 0                                # 非總漲跌幅填 0
cond_1.Value = 47.0                                 # 觸發數值
#條件2
cond_2 = SpiderStrategySettings()
cond_2.MarketType = enumMarketType.TWSE             # 上市
cond_2.StkCode = "2885"                             # 商品代號
cond_2.StrategyConditions = StrategyCondition2(3)   # 當日漲幅：3
cond_2.Direction = 1                                # 1:大於等於 2:小於等於(成交價才可使用) 3:無(漲停或跌停) 
cond_2.Price = 0                                    # 非總漲跌幅填 0
cond_2.Value = 1                                    # 當日漲跌幅(0.01~10)%

lstSettings.Add(cond_1)
lstSettings.Add(cond_2)
spider_obj.Settings.lstSettings = lstSettings

spider_obj.Settings.OrderSettings = OrderSettings2[OrderType2, OrderPriceType1]()
s_order = spider_obj.Settings.OrderSettings
s_order.MarketType = enumMarketType.TWSE
s_order.StkCode = "2885" 
s_order.OrderType = OrderType2(1)
s_order.TimeInforce = 0
s_order.PriceType = OrderPriceType1(1)  #OrderPriceType1 1:市價
s_order.OrderValue = 0
s_order.OrderQty = 2

spider_obj.Settings.Eligible = 2 # 1:擇一符合 2:全部符合

spider_list.Add(spider_obj)
objYuantaSparkAPI.SendAlgoCOOdrStrategy[SpiderStrategy]('S98875005091', spider_list)
time.sleep(1)

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

            if (strIndex == "SendAlgoCOOdrStrategy")
            {
                var result = (OrderStrategyResult)objValue;
                try
                {
                    strResult += "新增條件單:\r\n";
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
        "OrdStatus": "SstBuilt",
        "OrderNo": "k263R000000056",
        "EffTime": "2026/04/03",
        "ExpTime": "2026/04/30",
        "Msg": "策略已建立"
      }
    ]
  }
}
```

---

### 範例 (母子單)

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
                        MS_SpiderStrategy, SpiderSettings, SpiderStrategySettings, StrategyCondition2, StrategyOrder2, OrderSettings2, OrderType2, OrderPriceType1)

# 建立 API 物件
objYuantaSparkAPI = YuantaSparkAPITrader()
objYuantaSparkAPI.SetLogType(enumLogType.COMMON)
```

```java
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

// 母子單 MS_SpiderStrategy
// 母單條件
List<SpiderStrategySettings> lstMSettings = new List<SpiderStrategySettings>();
lstMSettings.Add(new SpiderStrategySettings
{
    MarketType = enumMarketType.TWSE,
    StkCode = "2885",
    StrategyConditions = (StrategyCondition2)1,  // 成交價：1
    Direction = 1,                                // 大於等於：1
    Price = 0,                                    // 非總漲跌幅填 0
    Value = 47.0                                  // 觸發數值
});

// 子單條件
List<SpiderStrategySettings> lstSSettings = new List<SpiderStrategySettings>();
lstSSettings.Add(new SpiderStrategySettings
{
    MarketType = enumMarketType.TWSE,
    StkCode = "2883",
    StrategyConditions = (StrategyCondition2)1,  // 成交價：1
    Direction = 1,                                // 大於等於：1
    Price = 0,                                    // 非總漲跌幅填 0
    Value = 20.4                                  // 觸發數值
});

List<MS_SpiderStrategy> lstMS = new List<MS_SpiderStrategy>();
lstMS.Add(new MS_SpiderStrategy
{
    Account = Account,
    EffTime = new DateTime(2026, 4, 1),
    ExpTime = new DateTime(2026, 4, 30),
    Order = (StrategyOrder2)5,              // 交易到設定單位全部成交：5

    // 母單設定
    M_SpiderStrategy = new SpiderSettings
    {
        Eligible = 1,                       // 1:擇一符合 2:全部符合
        lstSettings = lstMSettings,
        OrderSettings = new OrderSettings2<OrderType2, OrderPriceType1>
        {
            MarketType = enumMarketType.TWSE,
            StkCode = "2885",
            OrderType = (OrderType2)1,      // 現股買進：1
            TimeInforce = 0,
            PriceType = (OrderPriceType1)1, // 市價：1
            OrderValue = 0,
            OrderQty = 1
        }
    },

    // 子單設定
    S_SpiderStrategy = new SpiderSettings
    {
        Eligible = 1,                       // 1:擇一符合 2:全部符合
        lstSettings = lstSSettings,
        OrderSettings = new OrderSettings2<OrderType2, OrderPriceType1>
        {
            MarketType = enumMarketType.TWSE,
            StkCode = "2883",
            OrderType = (OrderType2)1,      // 現股買進：1
            TimeInforce = 0,
            PriceType = (OrderPriceType1)1, // 市價：1
            OrderValue = 0,
            OrderQty = 1
        }
    }
});

objYuantaSparkAPI.SendAlgoCOOdrStrategy(Account, lstMS);
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

                    case 'SendAlgoCOOdrStrategy':
                        SResult = objValue
                        sResult = SResult.ResultList

                        result = ''
                        result += "新增條件單:\r\n"

                        for i in range(sResult.Count):  
                            result += '{0},{1},{2},{3},{4}\r\n'.format(sResult[i].OrdStatus,sResult[i].OrderNo,sResult[i].EffTime,sResult[i].ExpTime,sResult[i].Msg)

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

ms_list  = List[MS_SpiderStrategy]()
ms_obj = MS_SpiderStrategy()

ms_obj.Account = "S98875005091"
ms_obj.EffTime =  System.DateTime(2026, 4, 1)
ms_obj.ExpTime =  System.DateTime(2026, 4, 31)
ms_obj.Order = StrategyOrder2(5)                    #限選交易到設定單位全部成交:5

ms_obj.M_SpiderStrategy = SpiderSettings() 
ms_obj.S_SpiderStrategy = SpiderSettings() 
#母單條件設定------------------------------------------------------------------------------------------------------
m_lstSettings =  List[SpiderStrategySettings]()
cond_1 = SpiderStrategySettings()
cond_1.MarketType = enumMarketType.TWSE       
cond_1.StkCode = "2885"                         
cond_1.StrategyConditions = StrategyCondition2(1)   # 成交價
cond_1.Direction = 1                                # 1:大於等於 2:小於等於(成交價才可使用) 3:無(漲停或跌停) 
cond_1.Price = 0                                    # 非總漲跌幅填 0
cond_1.Value = 47.0                                 # 觸發數值:買進

m_lstSettings.Add(cond_1)

ms_obj.M_SpiderStrategy.lstSettings = m_lstSettings
ms_obj.M_SpiderStrategy.Eligible = 1
#母單下單設定------------------------------------------------------------------------------------------------------
ms_obj.M_SpiderStrategy.OrderSettings = OrderSettings2[OrderType2, OrderPriceType1]()
m_order = ms_obj.M_SpiderStrategy.OrderSettings
m_order.MarketType = enumMarketType.TWSE
m_order.StkCode = "2885" 
m_order.OrderType = OrderType2(1)
m_order.TimeInforce = 0
m_order.PriceType = OrderPriceType1(1)  #OrderPriceType1 1:市價
m_order.OrderValue = 0
m_order.OrderQty = 1

#子單條件設定------------------------------------------------------------------------------------------------------
s_lstSettings =  List[SpiderStrategySettings]()
cond_1 = SpiderStrategySettings()
cond_1.MarketType = enumMarketType.TWSE       
cond_1.StkCode = "2883"                         
cond_1.StrategyConditions = StrategyCondition2(1)       # 成交價
cond_1.Direction = 1                                    # 1:大於等於 2:小於等於(成交價才可使用) 3:無(漲停或跌停) 
cond_1.Price = 0                                        # 非總漲跌幅填 0
cond_1.Value = 20.4

s_lstSettings.Add(cond_1)

ms_obj.S_SpiderStrategy.lstSettings = s_lstSettings
ms_obj.S_SpiderStrategy.Eligible = 1

#子單下單設定------------------------------------------------------------------------------------------------------
ms_obj.S_SpiderStrategy.OrderSettings = OrderSettings2[OrderType2, OrderPriceType1]()
s_order = ms_obj.S_SpiderStrategy.OrderSettings

s_order.MarketType = enumMarketType.TWSE
s_order.StkCode = "2883" 
s_order.OrderType = OrderType2(1)
s_order.TimeInforce = 0
s_order.PriceType = OrderPriceType1(1)                  # OrderPriceType1 1:市價
s_order.OrderValue = 0
s_order.OrderQty = 1

ms_list.Add(ms_obj)
objYuantaSparkAPI.SendAlgoCOOdrStrategy[MS_SpiderStrategy]('S98875005091', ms_list)
time.sleep(1)

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

            if (strIndex == "SendAlgoCOOdrStrategy")
            {
                var result = (OrderStrategyResult)objValue;
                try
                {
                    strResult += "新增條件單:\r\n";
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
        "OrdStatus": "SstBuilt",
        "OrderNo": "k263R000000056",
        "EffTime": "2026/04/03",
        "ExpTime": "2026/04/30",
        "Msg": "策略已建立"
      }
    ]
  }
}
```

---

### 範例 (當沖母子單)

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
                        MS_DayTradeSpiderStrategy, StrategyOrder2, StrategyCondition2,
                        DayTradeSpiderSettings, SpiderStrategySettings, OrderSettings2, OrderType3, OrderPriceType1)

# 建立 API 物件
objYuantaSparkAPI = YuantaSparkAPITrader()
objYuantaSparkAPI.SetLogType(enumLogType.COMMON)
```

```java
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

// 當沖母子單 MS_DayTradeSpiderStrategy
// 母單條件
List<SpiderStrategySettings> lstMSettings = new List<SpiderStrategySettings>();

// 條件1：成交價 >= 47.0
lstMSettings.Add(new SpiderStrategySettings
{
    MarketType = enumMarketType.TWSE,
    StkCode = "2885",
    StrategyConditions = (StrategyCondition2)1,  // 成交價：1
    Direction = 1,                                // 大於等於：1
    Price = 0,                                    // 非總漲跌幅填 0
    Value = 47.0
});

// 條件2：當日漲幅 >= 1%
lstMSettings.Add(new SpiderStrategySettings
{
    MarketType = enumMarketType.TWSE,
    StkCode = "2885",
    StrategyConditions = (StrategyCondition2)3,  // 當日漲幅：3
    Direction = 1,                                // 大於等於：1
    Price = 0,                                    // 非總漲跌幅填 0
    Value = 1                                     // 當日漲跌幅(0.01~10)%
});

List<MS_DayTradeSpiderStrategy> lstMSDay = new List<MS_DayTradeSpiderStrategy>();
lstMSDay.Add(new MS_DayTradeSpiderStrategy
{
    Account = Account,
    EffTime = new DateTime(2026, 4, 2),
    ExpTime = new DateTime(2026, 4, 2),
    Order = (StrategyOrder2)6,              // 母單成交子單就立即下單：6

    // 母單設定
    M_SpiderStrategy = new DayTradeSpiderSettings
    {
        Eligible = 1,                       // 1:擇一符合 2:全部符合
        lstSettings = lstMSettings,
        OrderSettings = new OrderSettings2<OrderType3, OrderPriceType1>
        {
            MarketType = enumMarketType.TWSE,
            StkCode = "2885",
            OrderType = (OrderType3)1,      // 現股買進：1
            TimeInforce = 0,
            PriceType = (OrderPriceType1)1, // 市價：1
            OrderValue = 0,
            OrderQty = 1
        }
    },

    // 子單設定（當沖賣出）
    OrderSettings = new OrderSettings2<OrderType3, OrderPriceType1>
    {
        MarketType = enumMarketType.TWSE,
        StkCode = "2885",
        OrderType = (OrderType3)2,          // 現股賣出：2
        TimeInforce = 0,
        PriceType = (OrderPriceType1)0,     // 限價：0
        OrderValue = 48,
        OrderQty = 1
    }
});

objYuantaSparkAPI.SendAlgoCOOdrStrategy(Account, lstMSDay);
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

                    case 'SendAlgoCOOdrStrategy':
                        SResult = objValue
                        sResult = SResult.ResultList

                        result = ''
                        result += "新增條件單:\r\n"

                        for i in range(sResult.Count):  
                            result += '{0},{1},{2},{3},{4}\r\n'.format(sResult[i].OrdStatus,sResult[i].OrderNo,sResult[i].EffTime,sResult[i].ExpTime,sResult[i].Msg)

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

ms_day_list  = List[MS_DayTradeSpiderStrategy]()
ms_day_obj = MS_DayTradeSpiderStrategy()
ms_day_obj.Account = "S98875005091"
ms_day_obj.EffTime =  System.DateTime(2026, 3, 30)
ms_day_obj.ExpTime =  System.DateTime(2026, 3, 30)
ms_day_obj.Order = StrategyOrder2(6)                    #限選母單成交子單就立即下單 :6

ms_day_obj.M_SpiderStrategy = DayTradeSpiderSettings()

#母單條件設定------------------------------------------------------------------------------------------------------
m_lstSettings =  List[SpiderStrategySettings]()
cond_1 = SpiderStrategySettings()
cond_1.MarketType = enumMarketType.TWSE       
cond_1.StkCode = "2885"                         
cond_1.StrategyConditions = StrategyCondition2(1)       # 成交價
cond_1.Direction = 1                                    # 1:大於等於 2:小於等於(成交價才可使用) 3:無(漲停或跌停) 
cond_1.Price = 0                                        # 非總漲跌幅填 0
cond_1.Value = 47.0                                     # 觸發數值

cond_2 = SpiderStrategySettings()
cond_2.MarketType = enumMarketType.TWSE                 # 上市
cond_2.StkCode = "2885"                                 # 商品代號
cond_2.StrategyConditions = StrategyCondition2(3)       # 當日漲幅：3
cond_2.Direction = 1                                    # 1:大於等於 2:小於等於(成交價才可使用) 3:無(漲停或跌停) 
cond_2.Price = 0                                        # 非總漲跌幅填 0
cond_2.Value = 1                                        # 當日漲跌幅(0.01~10)%

m_lstSettings.Add(cond_1)
m_lstSettings.Add(cond_2)
ms_day_obj.M_SpiderStrategy.lstSettings = m_lstSettings
ms_day_obj.M_SpiderStrategy.Eligible = 1
#母單下單設定------------------------------------------------------------------------------------------------------
ms_day_obj.M_SpiderStrategy.OrderSettings = OrderSettings2[OrderType3, OrderPriceType1]()
m_order = ms_day_obj.M_SpiderStrategy.OrderSettings
m_order.MarketType = enumMarketType.TWSE
m_order.StkCode = "2885" 
m_order.OrderType = OrderType3(1)                       # 現股買進：1
m_order.TimeInforce = 0
m_order.PriceType = OrderPriceType1(1)                  # OrderPriceType1 1:市價

m_order.OrderValue = 0
m_order.OrderQty = 1
#子單設定--------------------------------------------
ms_day_obj.OrderSettings = OrderSettings2[OrderType3, OrderPriceType1]()
s_order = ms_day_obj.OrderSettings

s_order.MarketType = enumMarketType.TWSE
s_order.StkCode = "2885" 
s_order.OrderType = OrderType3(2)                       # 現股賣出：2
s_order.TimeInforce = 0
s_order.PriceType = OrderPriceType1(0)                  # OrderPriceType1 0:限價
s_order.OrderValue = 48  
s_order.OrderQty = 1

ms_day_list.Add(ms_day_obj)
objYuantaSparkAPI.SendAlgoCOOdrStrategy[MS_DayTradeSpiderStrategy]('S98875005091', ms_day_list)
time.sleep(1)

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

            if (strIndex == "SendAlgoCOOdrStrategy")
            {
                var result = (OrderStrategyResult)objValue;
                try
                {
                    strResult += "新增條件單:\r\n";
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
        "OrdStatus": "SstBuilt",
        "OrderNo": "k263R000000056",
        "EffTime": "2026/04/03",
        "ExpTime": "2026/04/30",
        "Msg": "策略已建立"
      }
    ]
  }
}
```
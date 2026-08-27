---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E4%BA%A4%E6%98%93/%E5%9C%8B%E5%85%A7%E6%9C%9F%E8%B2%A8%E4%B8%8B%E5%96%AE/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## SendFutureOrder

國內期貨下單

```
bool SendFutureOrder(LoginAcno, lstFutureOrder, lng)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| LoginAcno | string | 下單帳號 | 期貨:F+分公司代號(7+3)+帳號(7)      例如 FF021000P001234567 |
| lstFutureOrder | [List\<FutureOrder>](#futureorder) | 下單物件清單 |  |
| lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   Normal: Big5   UTF8: UTF8   SC: 簡體中文 |

#### FutureOrder 國內期貨下單物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Identity | Int | 識別碼 |  |
| Account | string | 下單帳號 | 期貨:F+分公司代號(7+3)+帳號(7)   例如 FF021000P001234567 |
| OrderNo | string | 委託書編號 | 委託新單不需填 |
| TradeDate | string | 交易日期 | yyyy/MM/dd |
| FunctionCode | short | 功能別 | 00:委託單      04:取消      05:改量      07:改價      (Opt複式單沒有改價) |
| CommodityID1 | string | 商品名稱1 | 請參考 FunctionList.xlsx      股名檔對照表的下單代碼      如:台指FITX      如:台指選TXO |
| CallPut1 | string | 買賣權1 | "C":Call      "P":Put   (選擇權才需填值) |
| SettlementMonth1 | Int | 商品月份1 | 如:201912 |
| Price | double | 委託價格 | 非限價請填0 |
| StrikePrice1 | double | 履約價1 |  |
| OrderQty1 | short | 委託口數1 |  |
| BuySell1 | string | 買賣別1 | "B":買      "S":賣 |
| CommodityID2 | string | 商品名稱2 |  |
| CallPut2 | string | 買賣權2 | "C":Call      "P":Put   (選擇權才需填值) |
| SettlementMonth2 | Int | 商品月份2 | 如:201912 |
| StrikePrice2 | double | 履約價2 |  |
| OrderQty2 | short | 委託口數2 |  |
| BuySell2 | string | 買賣別2 | "B":買      "S":賣 |
| OpenOffsetKind | string | 新平倉 | 0:新倉      1:平倉      2:自動 |
| DayTradeID | string | 當沖註記 | "Y":當沖      " ":空白 |
| OrderType | string | 委託方式 | 1:市價      2:限價      3:範圍市價 |
| OrderCond | string | 委託條件 | " ":ROD      I:FOK      2:IOC |
| SellerNo | short | 營業員代碼 | 請填0 |
| BasketNo | string | BasketNo | 目前無作用 |
| Session | string | 盤別 | 1:預約      其他:盤中單 |

---

### Output Parameters

#### FutOrderResult 國內期貨下單結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| ResultCount | [OrderStatus](#orderstatus) | 交易狀態 |  |
| ResultList | List\<FutOrderData> | 國內期貨下單結果清單 |  |

#### OrderStatus 交易類狀態

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MsgCode | string | 訊息代碼 | 0001:執行成功 其它:失敗 |
| MsgContent | string | 訊息內容 |  |
| Count | Int | 筆數 |  |

#### FutOrderData 國內期貨下單結果明細

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Identify | Int | 識別碼 |  |
| ReplyCode | Short | 委託結果代碼 | 0:委託成功 others:委託失敗 |
| OrderNO | string | 委託書編號 |  |
| TradeDate | TYuantaDate | 交易日期 | [參考物件-日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadate) |
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
from YuantaOneAPI import YuantaSparkAPITrader, enumLogType, enumEnvironmentMode, FutureOrder

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

List<FutureOrder> lstFutureOrder = new List<FutureOrder>();
FutureOrder futureOrder = new FutureOrder
{
    Identify = 1,
    Account = Account,
    FunctionCode = 0,
    CommodityID1 = "FITX",
    CallPut1 = "",
    SettlementMonth1 = 202506,
    StrikePrice1 = 0,
    Price = 21000,
    OrderQty1 = 1,
    BuySell1 = "B",
    CommodityID2 = "",
    CallPut2 = "",
    SettlementMonth2 = 0,
    StrikePrice2 = 0,
    OrderQty2 = 0,
    BuySell2 = "",
    OpenOffsetKind = "2",
    DayTradeID = " ",
    OrderType = "2",
    OrderCond = " ",
    SellerNo = 0,
    OrderNo = "",
    TradeDate = DateTime.Today.ToString("yyyy/MM/dd"),
    BasketNo = "",
    Session = " "
};

lstFutureOrder.Add(futureOrder);

objYuantaSparkAPI.SendFutureOrder(Account, lstFutureOrder);
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

                    case 'SendFutureOrder':
                        futOrderResult = objValue
                        status = futOrderResult.ResultCount
                        futOrderDatas = futOrderResult.ResultList
                        result += '期貨下單結果:\n'
                        Rcount = status.Count
                        result += f"{status.MsgCode},{status.MsgContent},下單筆數:{Rcount}\n"
                        for i in range(Rcount):
                            yuantaDate = futOrderDatas[i].TradeDate
                            date = '{0}/{1}/{2}'.format(yuantaDate.Year, yuantaDate.Month, yuantaDate.Day)
                            result += '{0},{1},{2},{3},{4},{5},{6}\r\n'.format(str(futOrderDatas[i].Identify),str(futOrderDatas[i].ReplyCode),futOrderDatas[i].OrderNO,date,str(futOrderDatas[i].ErrType),futOrderDatas[i].ErrNO,futOrderDatas[i].Advisory)

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

futureOrder = FutureOrder()
futureOrder.Identify = 1
futureOrder.Account = 'FF0210132243219588'
futureOrder.FunctionCode = 0
futureOrder.CommodityID1 = 'FITX'    
futureOrder.CallPut1 = ''
futureOrder.SettlementMonth1 = 202512
futureOrder.StrikePrice1 = 0
futureOrder.Price = 27000
futureOrder.OrderQty1 = 1
futureOrder.BuySell1 = 'B'
futureOrder.CommodityID2 = ''
futureOrder.CallPut2 = ''
futureOrder.SettlementMonth2 = 0
futureOrder.StrikePrice2 = 0
futureOrder.OrderQty2 = 0
futureOrder.BuySell2 = ''
futureOrder.OpenOffsetKind = '2'
futureOrder.DayTradeID = ' '
futureOrder.OrderType = '2'
futureOrder.OrderCond = ' '
futureOrder.SellerNo = 0
futureOrder.OrderNo=''
futureOrder.TradeDate = datetime.today().strftime('%Y/%m/%d') 
futureOrder.BasketNo = ''
futureOrder.Session = ' '

lstFutureOrder = List[FutureOrder]()
lstFutureOrder.Add(futureOrder)

#傳送下單
objYuantaSparkAPI.SendFutureOrder('FF0210132243219588', lstFutureOrder)
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
            if (strIndex == "SendFutureOrder")
            {
                var result = (FutOrderResult)objValue;
                try
                {
                    strResult += $"期貨下單結果：{result.ResultCount.MsgCode},{result.ResultCount.MsgContent},{result.ResultCount.Count}筆\r\n";
                    result.ResultList.ForEach(x =>
                    {
                        strResult += $"{x.Identify},{x.ReplyCode},{x.OrderNO},{x.TradeDate:yyyy/MM/dd},{x.ErrType},{x.ErrNO},{x.Advisory}\r\n";
                    });
                }
                catch
                {
                    strResult = "";
                }

                Console.WriteLine("\n======================");
                Console.WriteLine(strResult.ToString());
                Console.WriteLine("======================\n");
                return;
            }
            Console.WriteLine($"{Convert.ToString(objValue)}");
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
    "ResultCount": {
      "MsgCode": "0001",
      "MsgContent": "執行成功",
      "Count": 1
    },
    "ResultList": [
      {
        "Identify": "1",
        "ReplyCode": "0",
        "OrderNO": "4a002",
        "TradeDate": "2025/1/1",        
        "ErrType": "",
        "ErrNO": "",
        "Advisory": ""
      }
    ]
  }
}
```
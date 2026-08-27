---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E4%BA%A4%E6%98%93/%E5%9C%8B%E5%85%A7%E8%AD%89%E5%88%B8%E4%B8%8B%E5%96%AE/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## SendStockOrder

國內證券下單

```
bool SendStockOrder(LoginAcno, lstStockOrder, lng)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| LoginAcno | string | 下單帳號 | 證券: S+分公司代號(4)+帳號(7)   例: S98875005091 |
| lstStockOrder | [List\<StockOrder>](#stockorder) | 下單物件清單 |  |
| lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   Normal: Big5   UTF8: UTF8   SC: 簡體中文 |

#### StockOrder 國內現貨下單物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Identity | int | 識別碼 |  |
| Account | string | 下單帳號 | 證券: S+分公司代號(4)+帳號(7)   例: S98875005091 |
| OrderNo | string | 委託書編號 | 委託新單不需填 |
| TradeDate | string | 交易日期 | yyyy/MM/dd |
| APCode | short | 交易單市場別 | 0: 一般   2: 零股   4: 盤中零股   7: 盤後 |
| TradeKind | short | 交易性質 | 00: 委託單   03: 改量   04: 取消   07: 改價 |
| OrderType | string | 委託種類 | "0": 現貨   "3": 融資   "4": 融券   "5": 策略借券(賣出)   "6": 避險借券(賣出)   "9": 現股當沖委託控管 |
| StkCode | string | 股票代號 |  |
| BuySell | string | 買賣記號 | "B": 買   "S": 賣 |
| PriceFlag | string | 價格種類 | H: 漲停   \-: 平盤   L: 跌停   " ": 限價   M: 市價單 |
| Price | double | 委託價格 | 非限價請填 0 |
| BasketNo | string | 使用者自訂欄位 | 限 32 個英數字 |
| OrderQty | long | 委託單位 |  |
| Time\_in\_force | string | 委託時間效期 | 0: ROD   3: IOC   4: FOK |

---

### Output Parameters

#### StkOrderResult 國內證券下單結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| ResultCount | [OrderStatus](#orderstatus) | 交易狀態 |  |
| ResultList | [List\<StkOrderData>](#stkorderdata) | 國內證券下單結果清單 |  |

---

#### OrderStatus 交易狀態

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MsgCode | string | 訊息代碼 | 0001: 執行成功   其他: 失敗 |
| MsgContent | string | 訊息內容 |  |
| Count | int | 筆數 |  |

---

#### StkOrderData 國內證券下單結果明細

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Identify | int | 識別碼 |  |
| ReplyCode | short | 委託結果代碼 | 0: 委託成功   Others: 委託失敗 |
| OrderNO | Tbyte5 | 委託書編號 |  |
| TradeDate | TYuantaDate | 交易日期 | [參考物件-日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadate) |
| ErrType | string | 錯誤類別 |  |
| ErrNO | string | 錯誤代號 | A003: 預約單不支援改價或無此委託單   A004: 委託已成交，無法改價   A005: 委託已取消，無法改價 |
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
from YuantaOneAPI import YuantaSparkAPITrader, enumLogType, enumEnvironmentMode, StockOrder

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

List<StockOrder> lstStockOrder = new List<StockOrder>();

StockOrder stockorder = new StockOrder
{
    Identify = 1,
    Account = Account,
    APCode = 0,
    TradeKind = 0,
    OrderType = "0",
    StkCode = "2885",
    PriceFlag = "M",
    Price = 0,
    OrderQty = 1,
    BuySell = "B",
    OrderNo = "",
    TradeDate = DateTime.Today.ToString("yyyy/MM/dd"),
    BasketNo = "",
    Time_in_force = "0"
};

lstStockOrder.Add(stockorder);

objYuantaSparkAPI.SendStockOrder(Account, lstStockOrder);
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

                    case 'SendStockOrder':
                        stkOrderResult = objValue
                        status = stkOrderResult.ResultCount
                        stkOrderDatas = stkOrderResult.ResultList
                        result += '現貨下單結果:\n'
                        Rcount = status.Count
                        result += '{0},{1},下單筆數:{2}\r\n'.format(status.MsgCode,status.MsgContent,str(Rcount))
                        for i in range(Rcount):
                            yuantaDate = stkOrderDatas[i].TradeDate

                            date= '{0}/{1}/{2}'.format(yuantaDate.Year, yuantaDate.Month, yuantaDate.Day) 
                            result += '{0},{1},{2},{3},{4},{5},{6}\r\n'.format(str(stkOrderDatas[i].Identify),str(stkOrderDatas[i].ReplyCode),stkOrderDatas[i].OrderNO,date,str(stkOrderDatas[i].ErrType),stkOrderDatas[i].ErrNO,stkOrderDatas[i].Advisory)

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

# 建立下單物件
stockorder = StockOrder()
stockorder.Identify = 1
stockorder.Account = 'S98875005091'
stockorder.APCode = 0
stockorder.TradeKind = 0
stockorder.OrderType = '0'
stockorder.StkCode = '2885'
stockorder.PriceFlag = ''
stockorder.Price = 35.15
stockorder.OrderQty = 1
stockorder.BuySell = 'B'
stockorder.OrderNo = ''
stockorder.TradeDate = datetime.today().strftime('%Y/%m/%d')
stockorder.BasketNo = ''
stockorder.Time_in_force = '0'

# 建立清單並加入訂單
lstStockOrder = List[StockOrder]()
lstStockOrder.Add(stockorder)
# 傳送下單
objYuantaSparkAPI.SendStockOrder('S98875005091', lstStockOrder)

# 測試環境傳送後休息一下
time.sleep(1)
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

            if (strIndex == "SendStockOrder")
            {
                var result = (StkOrderResult)objValue;

                try
                {
                    strResult += $"現貨下單結果：{result.ResultCount.MsgCode},{result.ResultCount.MsgContent},{result.ResultCount.Count}筆\r\n";
                    result.ResultList.ForEach(x =>
                    {
                        strResult += $"{x.Identify},{x.ReplyCode},{x.OrderNO},{x.TradeDate.ToString("yyyy/MM/dd")},{x.ErrType},{x.ErrNO},{x.Advisory}\r\n";
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
        "OrderNO": "f001",
        "TradeDate": "2025/1/1",
        "ErrType": "",
        "ErrNO": "",
        "Advisory": ""
      }
    ]
  }
}
```
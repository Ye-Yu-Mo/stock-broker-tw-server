---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%B8%B3%E5%8B%99/%E5%9C%8B%E9%9A%9B%E6%9C%9F%E8%B2%A8%E5%BA%AB%E5%AD%98%E7%B8%BD%E8%A1%A8%E6%9F%A5%E8%A9%A2/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## GetOVFutStoreSummary

國際期貨庫存總表查詢

```
bool GetOVFutStoreSummary(Account, lng)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 | 期貨:F+分公司代號(7+3)+帳號(7)   例如 FF021000P001234567 |
| Lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   \- Normal：Big5   \- UTF8：UTF8   \- SC：簡體中文 |

---

### Output Parameters

#### OVFutStoreSummaryResult 查詢國際期貨庫存總表結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| OVFutStoreList | [List \<OVFutStore>](#ovfutstore) | 國際期貨庫存清單 |  |

#### OVFutStore 國際期貨庫存物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| FutAccount | string | 帳號 |  |
| Kind | string | 委託種類 | 期貨(F)/選擇權(O) |
| Trid | string | 商品代碼 |  |
| BS | string | 買賣別 | 買(B)/賣(S) |
| Qty | Int | 未平倉口數 |  |
| Amt | double | 總成交點數 |  |
| Commodity1 | string | 商品代碼1 | EC, URO |
| CallPut1 | string | 買賣權1 | C/P |
| SettlementMonth1 | Int | 交易月份1 | 201101 |
| StkName1 | string | 商品名稱1 | 中文名稱 |
| StrikePrice1 | double | 履約價1 |  |
| Commodity2 | string | 商品代碼2 | EC |
| CallPut2 | string | 買賣權2 | C/P |
| SettlementMonth2 | Int | 交易月份2 | 201101 |
| StkName2 | string | 商品名稱2 | 中文名稱 |
| StrikePrice2 | double | 履約價2 |  |
| Fee | double | 手續費 |  |
| CurrencyType | string | 幣別 | AUD澳幣,EUR歐元,GBP英鎊,HKD港幣,JPY日幣,NTD新台幣,SGD新加坡幣,USD美金 |
| DayTradeID | string | 當沖註記 | "Y":當沖 " ":空白 |
| BS1 | string | 買賣別1 | 買(B)/賣(S) |
| BS2 | string | 買賣別2 | 買(B)/賣(S) |
| OptProdKind1 | string | 選擇權商品種類1 | <第1支腳>   "0":期貨選擇權   "1":現貨選擇權 |
| OptProdKind2 | string | 選擇權商品種類2 | <第2支腳>   "0":期貨選擇權   "1":現貨選擇權 |
| MarketNo1 | enumMarketType | 市場代碼1 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype)   <第1支腳> |
| StkCode1 | string | 行情報價代碼1 | <第1支腳> |
| MarketNo2 | enumMarketType | 市場代碼2 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype)   <第2支腳> |
| StkCode2 | string | 行情股票代碼2 | <第2支腳> |
| BuyPrice1 | double | 買入價1 | <第1支腳> |
| SellPrice1 | double | 賣出價1 | <第1支腳> |
| MarketPrice1 | double | 市價1 | <第1支腳>   盤前市價若為0 則給開盤參考價 |
| BuyPrice2 | double | 買入價2 | <第2支腳> |
| SellPrice2 | double | 賣出價2 | <第2支腳> |
| MarketPrice2 | double | 市價2 | <第2支腳>   盤前市價若為0 則給開盤參考價 |
| Decimal | Short | 小數位數 | +為小數位數,-為分數分母, 0為整數 |
| TickDiff | Int | 檔差 | 檔差不是固定的就為0，例如台股都為0；   海外股票跟海外期貨預留用的；   若檔差是0.05，且他的小數位是3位，檔差就是50 |

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
string Account = "FF021919F000168885";
string Password = "abcd123";
enumEnvironmentMode enumEvenMode = enumEnvironmentMode.UAT;

objYuantaSparkAPI.OnResponse += objApi_OnResponse;
objYuantaSparkAPI.SetLogType(enumLogType.ALL);

objYuantaSparkAPI.Open(enumEvenMode);
Thread.Sleep(1000);

objYuantaSparkAPI.Login(Account, Password);
Thread.Sleep(1000);
objYuantaSparkAPI.GetOVFutStoreSummary(Account);
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

                    case 'GetOVFutStoreSummary':
                        OVfResult = objValue
                        OVfutList = OVfResult.OVFutStoreList

                        result += '國外期貨庫存總表:\r\n'
                        result += '國外期貨庫存筆數:{0}\r\n'.format(OVfutList.Count)
                        for i in range(OVfutList.Count):
                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29},{30},{31},{32},{33},{34}\r\n'.format(
                                OVfutList[i].FutAccount,OVfutList[i].Kind,OVfutList[i].Trid,OVfutList[i].BS,int(OVfutList[i].Qty),str(OVfutList[i].Amt),OVfutList[i].Commodity1,OVfutList[i].CallPut1,str(OVfutList[i].SettlementMonth1),
                                OVfutList[i].StkName1,str(OVfutList[i].StrikePrice1),OVfutList[i].Commodity2,OVfutList[i].CallPut2,str(OVfutList[i].SettlementMonth2),OVfutList[i].StkName2,str(OVfutList[i].StrikePrice2),
                                str(OVfutList[i].Fee),OVfutList[i].CurrencyType,OVfutList[i].DayTradeID,OVfutList[i].BS1,OVfutList[i].BS2,OVfutList[i].OptProdKind1,OVfutList[i].OptProdKind2,str(OVfutList[i].MarketNo1),
                                OVfutList[i].StkCode1,str(OVfutList[i].MarketNo2),OVfutList[i].StkCode2,str(OVfutList[i].BuyPrice1),str(OVfutList[i].SellPrice1),str(OVfutList[i].MarketPrice1),str(OVfutList[i].BuyPrice2),
                                str(OVfutList[i].SellPrice2),str(OVfutList[i].MarketPrice2),str(OVfutList[i].Decimal),str(OVfutList[i].TickDiff)) 
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

#國際期貨庫存總表
objYuantaSparkAPI.GetOVFutStoreSummary('FF0210132243219588')

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

            if (strIndex == "GetOVFutStoreSummary")
            {
                var result = (OVFutStoreSummaryResult)objValue;
                try
                {
                    strResult += "國際期貨庫存筆數: " + result.OVFutStoreList.Count + "筆\r\n";
                    result.OVFutStoreList.ForEach(x =>
                    {
                        strResult += $"{x.FutAccount},{x.Kind},{x.Trid},{x.BS},{x.Qty},{x.Amt},{x.Commodity1},{x.CallPut1},{x.SettlementMonth1},{x.StkName1},{x.StrikePrice1}," +
                                    $"{x.Commodity2},{x.CallPut2},{x.SettlementMonth2},{x.StkName2},{x.StrikePrice2},{x.Fee},{x.CurrencyType},{x.DayTradeID},{x.BS1},{x.BS2},{x.OptProdKind1}," +
                                    $"{x.OptProdKind2},{x.MarketNo1},{x.StkCode1},{x.MarketNo2},{x.StkCode2},{x.BuyPrice1},{x.SellPrice1},{x.MarketPrice1},{x.BuyPrice2},{x.SellPrice2},{x.MarketPrice2}," +
                                    $"{x.Decimal},{x.TickDiff}\r\n";
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
    "OVFutStoreList": [
      {
        "FutAccount": "FF0210132243219588",
        "Kind": "F",
        "Trid": "BZZ2602",
        "BS": "S",
        "Qty": "2",
        "Amt": "148000.0",
        "Fee": "10.0",
        "Tax": "0.0",
        "CurrencyType": "USD",
        "DayTradeID": "N",
        "Commodity1": "BZ",
        "CallPut1": "F",
        "SettlementMonth1": "202602",
        "StrikePrice1": "0.0",
        "BS1": "S",
        "StkName1": "布侖特2602",
        "MarketNo1": "CME",
        "StkCode1": "BZ",
        "Commodity2": "",
        "CallPut2": "",
        "SettlementMonth2": "0",
        "StrikePrice2": "0.0",
        "BS2": "",
        "StkName2": "",
        "MarketNo2": "",
        "StkCode2": "",
        "BuyPrice1": "73.98",
        "SellPrice1": "74.01",
        "MarketPrice1": "74.00",
        "BuyPrice2": "0.0",
        "SellPrice2": "0.0",
        "MarketPrice2": "0.0",
        "Decimal": "2",
        "Decimal2": "",
        "TickDiff": "0.01",
      }
    ]
  }
}
```
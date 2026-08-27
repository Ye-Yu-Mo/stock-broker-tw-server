---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%B8%B3%E5%8B%99/%E6%9C%9F%E8%B2%A8%E5%BA%AB%E5%AD%98%E7%B8%BD%E8%A1%A8%E6%9F%A5%E8%A9%A2/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## GetFutStoreSummary

期貨庫存總表查詢

```
bool GetFutStoreSummary(Account, lng)
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

#### FutStoreSummaryResult 查詢期貨庫存總表結果

| Name | Type | Description |
| --- | --- | --- |
| FutStoreList | [List\<FutStore>](#futstore) | 期貨庫存清單 |

#### FutStore 期貨庫存物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| FutAccount | string | 帳號 |  |
| Kind | string | 期權別 | 期貨(F)/選擇權(O)/期貨+選擇權(C) |
| Trid | string | 商品代碼 | TX109100E4/TXO09000E4 |
| BS | string | 買賣別 | 買(B)/賣(S) |
| Qty | Int | 未平倉口數 |  |
| Amt | double | 總成交點數 |  |
| Fee | double | 手續費 |  |
| Tax | double | 交易稅 |  |
| CurrencyType | string | 幣別 | NTD:台幣 |
| DayTradeID | string | 當沖註記 | "Y":當沖 " ":空白 |
| Commodity1 | string | 商品代碼1 | TXO |
| CallPut1 | string | 買賣權1 | C/P |
| SettlementMonth1 | Int | 商品月份1 | 200712 |
| StrikePrice1 | double | 履約價1 |  |
| BS1 | string | 買賣別1 | 買(B)/賣(S) |
| StkName1 | string | 商品名稱1 | Ex: '中鋼實 06 0030 C', '台指01', '櫃指選 03 00400 C' |
| MarketNo1 | enumMarketType | 市場代碼1 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| StkCode1 | string | 行情報價代碼1 | 7799,TXO04600A9 |
| Commodity2 | string | 商品代碼2 | TXO |
| CallPut2 | string | 買賣權2 | C/P |
| SettlementMonth2 | Int | 商品月份2 | 200712 |
| StrikePrice2 | double | 履約價2 |  |
| BS2 | string | 買賣別2 | 買(B)/賣(S) |
| StkName2 | string | 股票名稱2 | Ex: '中鋼實 06 0030 C', '台指01', '櫃指選 03 00400 C' |
| MarketNo2 | enumMarketType | 市場代碼2 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| StkCode2 | string | 行情報價代碼2 | 7799,TXO04700A9 |
| BuyPrice1 | double | 買入價1 |  |
| SellPrice1 | double | 賣出價1 |  |
| MarketPrice1 | double | 市價1 | 盤前市價若為0 則給開盤參考價 |
| BuyPrice2 | double | 買入價2 |  |
| SellPrice2 | double | 賣出價2 |  |
| MarketPrice2 | double | 市價2 | 盤前市價若為0 則給開盤參考價 |
| Decimal | Short | 小數位數 | +為小數位數,-為分數分母,0為整數 |
| ProductType1 | string | 商品類別1 | "F":期貨 "O":選擇權 |
| ProductKind1 | string | 商品屬性1 | "I":指數 "R":利率 "B":債券 "C":商品 "S":股票 |
| ProductType2 | string | 商品類別2 | "F":期貨 "O":選擇權 |
| ProductKind2 | string | 商品屬性2 | "I":指數 "R":利率 "B":債券 "C":商品 "S":股票 |
| UpStopPrice1 | double | 漲停價1 |  |
| DownStopPrice1 | double | 跌停價1 |  |
| UpStopPrice2 | double | 漲停價2 |  |
| DownStopPrice2 | double | 跌停價2 |  |
| StkCode1opp | string | 行情股票代碼1反向 | <第1支腳> |
| StkCode2opp | string | 行情股票代碼2反向 | <第2支腳> |

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
objYuantaSparkAPI.GetFutStoreSummary(Account);
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

                    case 'GetFutStoreSummary':
                        fResult = objValue
                        futList = fResult.FutStoreList

                        result += '期貨庫存總表:\n'
                        result += f'期貨庫存筆數:{futList.Count}\n'
                        for i in range(futList.Count):
                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29},{30},{31},{32},{33},{34},{35},{36},{37},{38},{39},{40},{41},{42}\r\n'.format(
                                futList[i].FutAccount,futList[i].Kind,futList[i].Trid,futList[i].BS,str(futList[i].Qty),str(futList[i].Amt),str(futList[i].Fee),str(futList[i].Tax),futList[i].CurrencyType,futList[i].DayTradeID,
                                futList[i].Commodity1,futList[i].CallPut1,str(futList[i].SettlementMonth1),str(futList[i].StrikePrice1),futList[i].BS1,futList[i].StkName1,str(futList[i].MarketNo1),futList[i].StkCode1,
                                futList[i].Commodity2,futList[i].CallPut2,str(futList[i].SettlementMonth2),str(futList[i].StrikePrice2),futList[i].BS2,futList[i].StkName2,str(futList[i].MarketNo2),futList[i].StkCode2,
                                str(futList[i].BuyPrice1),str(futList[i].SellPrice1),float(futList[i].MarketPrice1),str(futList[i].BuyPrice2),str(futList[i].SellPrice2),str(futList[i].MarketPrice2),str(futList[i].Decimal),
                                futList[i].ProductType1,futList[i].ProductKind1,futList[i].ProductType2,futList[i].ProductKind2,str(futList[i].UpStopPrice1),str(futList[i].DownStopPrice1),str(futList[i].UpStopPrice2),
                                str(futList[i].DownStopPrice2),futList[i].StkCode1opp,futList[i].StkCode2opp)

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

#期貨庫存總表
objYuantaSparkAPI.GetFutStoreSummary('FF0210132243219588')

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

            if (strIndex == "GetFutStoreSummary")
            {
                var result = (FutStoreSummaryResult)objValue;
                try
                {
                    strResult += "期貨庫存筆數: " + result.FutStoreList.Count + "筆\r\n";
                    result.FutStoreList.ForEach(x =>
                    {
                        strResult += $"{x.FutAccount},{x.Kind},{x.Trid},{x.BS},{x.Qty},{x.Amt},{x.Fee},{x.Tax},{x.CurrencyType},{x.DayTradeID},{x.Commodity1},{x.CallPut1}," +
                                    $"{x.SettlementMonth1},{x.StrikePrice1},{x.BS1},{x.StkName1},{x.MarketNo1},{x.StkCode1},{x.Commodity2},{x.CallPut2},{x.SettlementMonth2},{x.StrikePrice2}," +
                                    $"{x.BS2},{x.StkName2},{x.MarketNo2},{x.StkCode2},{x.BuyPrice1},{x.SellPrice1},{x.MarketPrice1},{x.BuyPrice2},{x.SellPrice2},{x.MarketPrice2},{x.Decimal}," +
                                    $"{x.ProductType1},{x.ProductKind1},{x.ProductType2},{x.ProductKind2},{x.UpStopPrice1},{x.DownStopPrice1},{x.UpStopPrice2},{x.DownStopPrice2},{x.StkCode1opp},{x.StkCode2opp}\r\n";
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
    "FutStoreList": [
      {
        "FutAccount": "FF0210132243219588",
        "Kind": "F",
        "Trid": "FITXL5",
        "BS": "B",
        "Qty": "4",
        "Amt": "109275.0",
        "Fee": "1000.0",
        "Tax": "438.0",
        "CurrencyType": "NTD",
        "DayTradeID": "N",
        "Commodity1": "FITX",
        "CallPut1": "F",
        "SettlementMonth1": "202512",
        "StrikePrice1": "0.0",
        "BS1": "B",
        "StkName1": "台指12",
        "MarketNo1": "TAIFEX",
        "StkCode1": "TXFPML5",
        "Commodity2": "",
        "CallPut2": "",
        "SettlementMonth2": "0",
        "StrikePrice2": "0.0",
        "BS2": "",
        "StkName2": "",
        "MarketNo2": "",
        "StkCode2": "",
        "BuyPrice1": "27567.0",
        "SellPrice1": "27569.0",
        "MarketPrice1": "27567.0",
        "BuyPrice2": "0.0",
        "SellPrice2": "0.0",
        "MarketPrice2": "0.0",
        "Decimal": "3",
        "ProductType1": "F",
        "ProductKind1": "I",
        "ProductType2": "0",
        "ProductKind2": "",
        "UpStopPrice1": "30336.0",
        "DownStopPrice1": "24822.0",
        "UpStopPrice2": "0.0",
        "DownStopPrice2": "0.0",
        "StkCode1opp": "TXFL5",
        "StkCode2opp": ""
      }
    ]
  }
}
```
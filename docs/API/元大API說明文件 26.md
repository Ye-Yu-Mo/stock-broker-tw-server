---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E4%BA%A4%E6%98%93/%E6%9C%9F%E8%B2%A8%E8%A4%87%E5%BC%8F%E5%96%AE%E7%B5%84%E5%90%88/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## SendFutureCombined

期貨複式單組合

```
bool SendFutureCombined(LoginAcno, lstDepositOptimum, lng)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| LoginAcno | string | 組合帳號 | 期貨:F+分公司代號(7+3)+帳號(7)   例如 FF021000P001234567 |
| lstDepositOptimum | List | 組合物件清單 | **建議由保證金最佳化查詢結果篩選代入** |
| lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   \- Normal：Big5   \- UTF8：UTF8   \- SC：簡體中文 |

#### DepositOptimum 期貨保證金最佳化物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| StrategyID | Byte | 策略ID | 6.買賣權混合部位(跨式,勒式)   7.多頭價差   8.Put空頭價差   9.溫跌作莊   10.溫漲作莊   11.Call時間價差   12.Put時間價差 |
| FutAccountInfo | string | 期貨帳號 |  |
| Qty | Short | 口數 |  |
| BuySell1 | string | 買賣別1 | B, S |
| BuySell2 | string | 買賣別2 | B, S |
| DealPrice1 | double | 成交價1 | 此值即為市價 |
| DealPrice2 | double | 成交價2 | 此值即為市價 |
| Decimal1 | Short | 小數位數1 | +為小數位數,-為分數分母,0為整數 |
| CurrentIM1 | Int | 商品一保證金 |  |
| CurrentIM2 | Int | 商品二保證金 |  |
| SaveIM | Int | 可節省保證金 |  |
| CommodityID1 | string | 商品ID1 | TXO |
| CallPut1 | string | 買賣權1 | C/P |
| SettlementMonth1 | Int | 商品年月1 | 202502 |
| StrikePrice1 | double | 履約價1 |  |
| StkName1 | string | 商品名稱1 | 台指選 02 22800 P |
| CommodityID2 | string | 商品ID2 | TXO |
| CallPut2 | string | 買賣權2 | C/P |
| SettlementMonth2 | Int | 商品年月2 | 202502 |
| StrikePrice2 | double | 履約價2 |  |
| StkName2 | string | 商品名稱2 | 台指選 02 23000 P |

---

### Output Parameters

#### FutCombinedResult 複合式組合下單結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| ResultCount | [OrderStatus](#orderstatus) | 交易狀態 |  |
| ResultList | [List\<FutCombinedData>](#futcombineddata) | 複合式組合下單結果清單 |  |

#### OrderStatus 交易類狀態

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| MsgCode | string | 訊息代碼 | 0001:執行成功 其它:失敗 |
| MsgContent | string | 訊息內容 |  |
| Count | Int | 筆數 |  |

#### FutCombinedData 複合式組合下單結果明細

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Identify | Int | 識別碼 |  |
| ReplyCode | Short | 委託結果代碼 | 0:委託成功 others:委託失敗 |
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
from YuantaOneAPI import YuantaSparkAPITrader, enumLogType, enumEnvironmentMode, LoginResult, DepositOptimum

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
string Account = "FF0210132243219588";
string Password = "abcd123";
enumEnvironmentMode enumEvenMode = enumEnvironmentMode.UAT;

List<DepositOptimum> DepositOptimumList = new List<DepositOptimum>();

objYuantaSparkAPI.OnResponse += objApi_OnResponse;
objYuantaSparkAPI.SetLogType(enumLogType.ALL);

objYuantaSparkAPI.Open(enumEvenMode);
Thread.Sleep(1000);
objYuantaSparkAPI.Login(Account, Password);
Thread.Sleep(1000);

objYuantaSparkAPI.GetFutDepositOptimum(Account);
Thread.Sleep(1000);
objYuantaSparkAPI.SendFutureCombined(Account, DepositOptimumList);
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

                    case 'GetFutDepositOptimum':
                        # 期貨保證金最佳化查詢
                        fResult = objValue

                        # 最佳化清單（保留到全域變數）
                        global DepositOptimumList
                        DepositOptimumList = fResult.DepositOptimumList

                        result += '期貨保證金最佳化查詢:\r\n'
                        result += '最佳化筆數:{0}\r\n'.format(DepositOptimumList.Count)

                        for i in range(DepositOptimumList.Count):
                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20}\r\n'.format(
                                str(DepositOptimumList[i].StrategyID),DepositOptimumList[i].FutAccountInfo,str(DepositOptimumList[i].Qty),DepositOptimumList[i].BuySell1,DepositOptimumList[i].BuySell2,str(DepositOptimumList[i].DealPrice1),
                                str(DepositOptimumList[i].DealPrice2),str(DepositOptimumList[i].Decimal1),str(DepositOptimumList[i].CurrentIM1),str(DepositOptimumList[i].CurrentIM2),str(DepositOptimumList[i].SaveIM),DepositOptimumList[i].CommodityID1,
                                DepositOptimumList[i].CallPut1,str(DepositOptimumList[i].SettlementMonth1),str(DepositOptimumList[i].StrikePrice1),DepositOptimumList[i].StkName1,DepositOptimumList[i].CommodityID2,DepositOptimumList[i].CallPut2,
                                str(DepositOptimumList[i].SettlementMonth2),str(DepositOptimumList[i].StrikePrice2),DepositOptimumList[i].StkName2)

                    case 'SendFutureCombined':  # 期貨複式單組合回應
                        fResult = objValue
                        status = fResult.ResultCount     # 包含 MsgCode/MsgContent/Count
                        datas = fResult.ResultList       # 明細列表

                        result += '期貨複式單組合結果:\n'
                        Rcount = status.Count
                        result += '{0},{1},組合筆數:{2}\r\n'.format(status.MsgCode,status.MsgContent,str(Rcount))

                        # 循環處理回應資料
                        for i in range(Rcount):
                            result += '{0},{1},{2},{3},{4}\r\n'.format(str(datas[i].Identify),str(datas[i].ReplyCode),str(datas[i].ErrType),datas[i].ErrNO,datas[i].Advisory)
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
objYuantaSparkAPI.Login('FF0210132243219588', 'abcd123')
time.sleep(2)

DepositOptimumList = List[DepositOptimum]()
objYuantaSparkAPI.GetFutDepositOptimum('FF0210132243219588')
time.sleep(3)

objYuantaSparkAPI.SendFutureCombined('FF0210132243219588',DepositOptimumList)

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
            else if (strIndex == "GetFutDepositOptimum")
            {
                var result = (DepositOptimumResult)objValue;

                try
                {
                    var list = result?.DepositOptimumList;
                    int intCount = list?.Count ?? 0;

                    strResult += $"保證金最佳化：{intCount}筆 \r\n";

                    if (list != null && list.Count > 0)
                    {
                        list.ForEach(x =>
                        {
                            strResult +=
                                $"{x.StrategyID},{x.FutAccountInfo},{x.Qty},{x.BuySell1},{x.BuySell2},{x.DealPrice1},{x.DealPrice2}," +
                                $"{x.Decimal1},{x.CurrentIM1},{x.CurrentIM2},{x.SaveIM}," +
                                $"{x.CommodityID1},{x.CallPut1},{x.SettlementMonth1},{x.StrikePrice1},{x.StkName1}," +
                                $"{x.CommodityID2},{x.CallPut2},{x.SettlementMonth2},{x.StrikePrice2},{x.StkName2}\r\n";
                        });

                        // 保存至全域（供後續送單）
                        DepositOptimumList = list;
                    }
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
            else if (strIndex == "SendFutureCombined")
            {
                var result = (FutCombinedResult)objValue;
                try
                {
                    strResult += $"期貨複式單組合：{result.ResultCount.MsgCode},{result.ResultCount.MsgContent},{result.ResultCount.Count}筆\r\n";
                    result.ResultList.ForEach(x =>
                    {
                        strResult += $"{x.Identify},{x.ReplyCode},{x.ErrType},{x.ErrNO},{x.Advisory}\r\n";
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
    "ResultCount": {
      "MsgCode": "0001",
      "MsgContent": "執行成功",
      "Count": 1
    },
    "ResultList": [
      {
        "Identify": "9999",
        "ReplyCode": "0",
        "ErrType": "E",
        "ErrNO": "EEE",
        "Advisory": "申請組合 資料筆數1筆,總口數3口"
      }
    ]
  }
}
```
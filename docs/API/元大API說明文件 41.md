---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%B8%B3%E5%8B%99/%E6%9C%9F%E8%B2%A8%E6%AC%8A%E7%9B%8A%E6%95%B8%E6%9F%A5%E8%A9%A2/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## GetFutInterestStore

期貨權益數查詢

```
bool GetFutInterestStore(Account, Type, Currency, lng)
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
| Type | string | 型態 | 1:基本幣別 2:明細幣別 |
| Currency | string | 幣別 | TWD:台幣   USA:美金   CNA:人民幣   JPA:日圓 |
| Lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   \- Normal：Big5   \- UTF8：UTF8   \- SC：簡體中文 |

---

### Output Parameters

#### FutInterestStoreResult 查詢期貨權益數結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| ReplyCode | Short | 委託結果代碼 | 0:委託成功 others:委託失敗 |
| Advisory | String | 錯誤說明 |  |
| Type | String | 型態 | 1:基本幣別 2:明細幣別 |
| Currency | String | 幣別 | TWD:台幣   USA:美金   CNA:人民幣   JPA:日圓 |
| Equity | double | 權益數 |  |
| AllFullIm | double | 全額原始保證金 |  |
| CanuseMargin | double | 可運用保證金 |  |
| RiskRate | String | 權益比率 |  |
| DaytradeRisk | String | 當沖風險指標 |  |
| AllRiskRate | String | 風險指標 |  |
| CashForward | double | 前日餘額 |  |
| OpenGlYes | double | 昨日未平倉損益 |  |
| UpdateTime | TYuantaDateTime | 風險更新時間 | [參考物件-時間日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadatetime) |
| Accounting | double | 存/提 |  |
| FloatMargin | double | 未沖銷期貨浮動損益 |  |
| FloatPremium | double | 未沖銷買方選擇權市值+ 未沖銷賣方選擇權市值 |  |
| CommissionAll | double | 手續費 |  |
| TotalValue | double | 權益總值 |  |
| TaxRate | double | 期交稅 |  |
| AllIm | double | 原始保證金 |  |
| CallMargin | double | 追繳保證金 |  |
| Grantal | double | 本日期貨平倉損益淨額+ 到期履約損益 |  |
| AllMm | double | 維持保證金 |  |
| OrderIm | double | 委託保證金 |  |
| Premium | double | 權利金收入與支出 |  |
| OrderPremium | double | 委託權利金 |  |
| Balance | double | 本日餘額 |  |
| CanusePremium | double | 可動用(出金)保證金(含抵委) |  |
| CoveredOim | double | 委託抵繳保證金 |  |
| BondAmt | double | 債券實物交割款 |  |
| NobondAmt | double | 債券實物不足交割款 |  |
| BondMargin | double | 債券待交割保證金 |  |
| CoveredIm | double | 有價證券抵繳總額 |  |
| ReduceIm | double | 期貨多空減收保證金 |  |
| IncreaseIm | double | 加收保證金 |  |
| YTotalValue | double | 昨日權益總值 |  |
| Rate | double | 匯率 |  |
| BestFlag | string | 客戶保證金計收方式 | ' ': 傳統(策略)   'S':整戶風險(SPAN)   'Y':保證金最佳化 |
| GlToday | double | 本日損益 |  |
| DspEquity | double | 風險權益總值 |  |
| DspFloatmargin | double | 未沖銷期貨風險浮動損益 |  |
| DspFloatpremium | double | 未沖銷買方選擇權風險市值+未沖銷賣方選擇權風險市值 |  |
| DspIM | double | 風險原始保證金 |  |
| DspRiskRate | double | 盤後風險指標 |  |

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
from YuantaOneAPI import YuantaSparkAPITrader, enumLogType, enumQuoteIndexType, enumMarketType, enumEnvironmentMode, enumQuoteFiveTickIndexType, FutSprStore

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

objYuantaSparkAPI.OnResponse += objApi_OnResponse;
objYuantaSparkAPI.SetLogType(enumLogType.ALL);

objYuantaSparkAPI.Open(enumEvenMode);
Thread.Sleep(1000);
objYuantaSparkAPI.Login(Account, Password);
Thread.Sleep(1000);

objYuantaSparkAPI.GetFutInterestStore(Account, "1", "TWD");
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

            case 1:  # 查詢/回應資訊
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

                    case 'GetFutInterestStore':
                        fResult = objValue

                        result += '期貨權益數:\r\n'

                        #dateTime=TYuantaDateTime()
                        dateTime = fResult.UpdateTime

                        Date= '{0}/{1}/{2}'.format(dateTime.Year, dateTime.Month, dateTime.Day)
                        Time= '{0}:{1}:{2}.{3}'.format(str(dateTime.Hour), str(dateTime.Minute), str(dateTime.Second), str(dateTime.Millisecond))

                        result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12} {13},{14},{15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29},{30},{31},{32},{33},{34},{35},{36},{37},{38},{39},{40},{41},{42},{43},{44}\r\n'.format(
                            str(fResult.ReplyCode),fResult.Advisory,fResult.Type,fResult.Currency,str(fResult.Equity),str(fResult.AllFullIm),str(fResult.CanuseMargin),fResult.RiskRate,fResult.DaytradeRisk,
                            fResult.AllRiskRate,str(fResult.CashForward),str(fResult.OpenGlYes),Date,Time,str(fResult.Accounting),str(fResult.FloatMargin),str(fResult.FloatPremium),str(fResult.CommissionAll),
                            str(fResult.TotalValue),str(fResult.TaxRate),str(fResult.AllIm),str(fResult.CallMargin),str(fResult.Grantal),str(fResult.AllMm),str(fResult.OrderIm),str(fResult.Premium),
                            str(fResult.OrderPremium),str(fResult.Balance),str(fResult.CanusePremium),str(fResult.CoveredOim),str(fResult.BondAmt),str(fResult.NobondAmt),str(fResult.BondMargin),str(fResult.CoveredIm),
                            str(fResult.ReduceIm),str(fResult.IncreaseIm),str(fResult.YTotalValue),str(fResult.Rate),fResult.BestFlag,str(fResult.GlToday),str(fResult.DspEquity),str(fResult.DspFloatmargin),
                            str(fResult.DspFloatpremium),str(fResult.DspIM),str(fResult.DspRiskRate))

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

objYuantaSparkAPI.GetFutInterestStore('FF0210132243219588','1','TWD')
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

            if (strIndex == "GetFutInterestStore")
            {
                var result = (FutInterestStoreResult)objValue;
                try
                {
                    strResult += "期貨權益數:\r\n";
                    strResult += $"{result.ReplyCode},{result.Advisory},{result.Type},{result.Currency},{result.Equity},{result.AllFullIm},{result.CanuseMargin},{result.RiskRate}," +
                        $"{result.DaytradeRisk},{result.AllRiskRate},{result.CashForward},{result.OpenGlYes},{result.UpdateTime.ToString()} " +
                        $"{result.Accounting},{result.FloatMargin},{result.FloatPremium},{result.CommissionAll}," +
                        $"{result.TotalValue},{result.TaxRate},{result.AllIm},{result.CallMargin},{result.Grantal},{result.AllMm},{result.OrderIm},{result.Premium},{result.OrderPremium}," +
                        $"{result.Balance},{result.CanusePremium},{result.CoveredOim},{result.BondAmt},{result.NobondAmt},{result.BondMargin},{result.CoveredIm},{result.ReduceIm}," +
                        $"{result.IncreaseIm},{result.YTotalValue},{result.Rate},{result.BestFlag},{result.GlToday},{result.DspEquity},{result.DspFloatmargin},{result.DspFloatpremium}," +
                        $"{result.DspIM},{result.DspRiskRate}\r\n";
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
      "ReplyCode": "0",
      "Advisory": "查詢成功",
      "Type": "1",
      "Currency": "TWD",
      "Equity": "50094758.0",
      "AllFullIm": "306000.0",
      "CanuseMargin": "49753758.0",
      "RiskRate": "999.00",
      "DaytradeRisk": "999.00",
      "AllRiskRate": "999.00",
      "CashForward": "49998958.0",
      "OpenGlYes": "60800.0",
      "UpdateDate": "2025/9/8",
      "UpdateTime": "16:17:49.0",
      "Accounting": "0.0",
      "FloatMargin": "95800.0",
      "FloatPremium": "0.0",
      "CommissionAll": "0.0",
      "TotalValue": "50094758",
      "TaxRate": "",
      "AllIm": "",
      "CallMargin": "",
      "Grantal": "",
      "AllMm": "",
      "OrderIm": "",
      "Premium": "",
      "OrderPremium": "",
      "Balance": "",
      "CanusePremium": "",
      "CoveredOim": "",
      "BondAmt": "",
      "NobondAmt": "",
      "BondMargin": "",
      "CoveredIm": "",
      "ReduceIm": "",
      "IncreaseIm": "",
      "YTotalValue": "",
      "Rate": "",
      "BestFlag": "",
      "GlToday": "",
      "DspEquity": "",
      "DspFloatmargin": "",
      "DspFloatpremium": "",
      "DspIM": "",
      "DspRiskRate": ""
  }
}
```
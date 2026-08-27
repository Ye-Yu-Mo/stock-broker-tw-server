---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9B%9E%E5%A0%B1/%E5%8D%B3%E6%99%82%E5%9B%9E%E5%A0%B1%E8%A8%82%E9%96%B1/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## RR\_RealReport

即時回報訂閱

### 回傳：

> 登入即訂閱，結果請從回應事件OnResponse接收

---

### Output Parameters

#### RealReport 即時回報物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 |  |
| RptType | byte | 回報類別 | 50:股票委託   51:股票成交   2:期貨委託   3:期貨成交   4:期貨價差成交回報   5:期貨委託減量取消   10:選擇權委託回報   11:單式成交回報   12:複式成交回報   13:選擇權減量取消回報   21:組合拆解回報   22:改變新/平倉回報   30:海外期貨委託   31:海外期貨成交 |
| OrderNo | string | 委託單號 |  |
| MarketNo | enumMarketType | 市場代碼 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| CompanyNo | string | 商品代碼 | 2854、05311   FITX 200709   URO200709   FIGTL7/C8   TXO09000T7   TXO08000/08100U7 |
| StkCName | string | 商品名稱 |  |
| OrderDate | TYuantaDate | 交易日 | [參考物件-日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadate) |
| OrderTime | TYuantaTime | 交易時間 | [參考物件-時間物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantatime)   委託時間 / 成交時間 |
| OrderType | string | 委託種類 | **現貨**   0:普通   1,3:資   2,4:券   5,6:借券(賣出)      **期權**   M:市價   L:限價   P:範圍市價      **海外期**   LMT:限價單   MKT:市價單   STP:停損單   SWL:停損限價單   CXL:取消單 |
| BS | string | 買賣別 | B:買   S:賣 |
| Price | double | 價格 | 委託價 / 成交價   例：23.50、1.0585   0000125 → 23.5(海外期) |
| TouchPrice | double | 停損執行價 |  |
| BeforeQty | int | 改量前數量 |  |
| OrderQty | int | 數量 | 委託股數 / 成交股數 |
| OpenOffsetKind | string | 新增 / 沖銷別 | **期貨**   0:新增   1:沖銷   2:新倉且當日沖銷單      **選擇權**   0:新增   1:沖銷 |
| DayTrade | string | 當沖記號 | **證券**: ' ' 或 X   **期權**: ' ' 或 Y |
| OrderCond | string | 委託條件 | **證券**   0:ROD   3:IOC   4:FOK      **期權**   R:ROD   I:IOC   F:FOK      **海外期**   0:DAY   1:FOK   2:IOC   N:非GTC單 |
| OrderErrorNo | string | 錯誤碼 | P201   證券錯誤碼改5碼，使用另一欄位 |
| TradeKind | byte | 交易性質 | **現貨**   1:B   2:S   3:改量   4:取消   5:查詢   6:改價   9:交易所主動刪單      **期權**   1:新增   2:減量   3:取消   5:查詢   6:改價 |
| APCode | byte | 委託類別 | **現貨**   0:現股   2:零股   4:盤中零股   7:盤後   99:興櫃      **組合拆解回報**   83:拆解   67:組合      **改變新/平倉回報**   83:新轉平   79:平轉新 |
| BasketNo | string | 一籃子下單編號 |  |
| OrderStatus | short | 狀態碼 | 0:委託成功   1:委託失敗   2:取消成功   3:取消失敗   4:減量成功   5:減量失敗   6:查詢成功   7:查詢失敗   8:已成交   10:組合成功   11:拆解成功   12:平轉新   13:新轉平   18:委託收到   19:取消收到   20:改價成功   21:改價失敗   23:取消成交   24:委託失效   25:價穩失效 |
| StkType1 | byte | 屬性1 | Bit1:管理商品   Bit2:交易記號   Bit3:受益憑證   Bit4:ETF商品   Bit5:權證記號   Bit6:特別股   Bit7:存託憑證   Bit8:外國股票 |
| StkType2 | byte | 屬性2 | Bit1:可轉換公司債   Bit2:附認股權公司債   Bit3:警示股   Bit4:指數記號   Bit5:期貨   Bit6:個股選擇權   Bit7:指數選擇權   Bit8:保留 |
| BelongMarketNo | byte | 所屬市場代碼 |  |
| BelongStkCode | string | 所屬股票代碼 |  |
| SeqNo | uint | 成交序號 | 股票/期貨成交單使用   (複委託、國際期為0)   若 OrderStatus=25 且 StkErrCode=13051、19351，此欄位帶入成交數量 |
| PriceType | string | 價格型態 | 僅證券使用   1:市價   2:限價   H:漲停   L:跌停   \-:平盤 |
| StkErrorNo | string | 證券回報錯誤碼 | 證券回報錯誤碼 |

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
from YuantaOneAPI import YuantaSparkAPITrader, enumLogType, enumQuoteIndexType, enumMarketType, enumEnvironmentMode, enumQuoteFiveTickIndexType

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
string Account = "S98875005091";
string Password = "1234";
enumEnvironmentMode enumEvenMode = enumEnvironmentMode.UAT;

objYuantaSparkAPI.OnResponse += objApi_OnResponse;
objYuantaSparkAPI.SetLogType(enumLogType.ALL);

objYuantaSparkAPI.Open(enumEvenMode);
Thread.Sleep(1000);
objYuantaSparkAPI.Login(Account, Password);
Thread.Sleep(1000);
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
                    case 'RR_RealReport':
                        # 即時回報
                        realReport = objValue

                        result += '即時回報:\r\n'

                        #yuantaDate = TYuantaDate()
                        yuantaDate = realReport.OrderDate
                        date= '{0}/{1}/{2}'.format(yuantaDate.ushtYear, yuantaDate.bytMon, yuantaDate.bytDay)
                        #yuantaTime = TYuantaTime()
                        yuantaTime = realReport.OrderTime
                        time= '{0}:{1}:{2}.{3}'.format(str(yuantaTime.bytHour), str(yuantaTime.bytMin), str(yuantaTime.bytSec), str(yuantaTime.ushtMSec))

                        result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28}\r\n'.format(
                            realReport.Account,str(realReport.RptType),realReport.OrderNo,str(realReport.MarketNo),realReport.CompanyNo,realReport.StkCName,date,time,realReport.OrderType,realReport.BS,str(realReport.Price),
                            str(realReport.TouchPrice),str(realReport.BeforeQty),str(realReport.OrderQty),realReport.OpenOffsetKind,realReport.DayTrade,realReport.OrderCond,realReport.OrderErrorNo,str(realReport.TradeKind),
                            str(realReport.APCode),realReport.BasketNo,str(realReport.OrderStatus),str(realReport.StkType1),str(realReport.StkType2),str(realReport.BelongMarketNo),realReport.BelongStkCode,str(realReport.SeqNo),
                            realReport.PriceType,realReport.StkErrorNo)

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

# 保持程式運行
while True:
    time.sleep(1)
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
        }

        if (intMark == 2)
        {
            if (strIndex == "RR_RealReport")
            {
                var report = (YuantaOneAPI.RealReport)objValue;
                try
                {
                    strResult += "===============\r\n即時回報(訂閱結果)\r\n===============\r\n";
                    strResult += $"帳號:{report.Account},回報類別:{report.RptType},委託單號:{report.OrderNo},{report.MarketNo},{report.CompanyNo},{report.StkCName},";
                    TYuantaDate yuantaDate = report.OrderDate;
                    strResult += String.Format("{0}/{1}/{2}", yuantaDate.ushtYear, yuantaDate.bytMon, yuantaDate.bytDay) + ",";
                    TYuantaTime yuantaTime = report.OrderTime;
                    strResult += String.Format("{0}:{1}:{2}.{3}", yuantaTime.bytHour, yuantaTime.bytMin, yuantaTime.bytSec, yuantaTime.ushtMSec) + ",";
                    strResult += $"{report.OrderType},{report.BS},{report.Price},{report.TouchPrice},{report.BeforeQty},{report.OrderQty},{report.OpenOffsetKind}," +
                    $"{report.DayTrade},{report.OrderCond},{report.OrderErrorNo},{report.TradeKind},{report.APCode},{report.BasketNo},{report.OrderStatus},{report.StkType1}," +
                    $"{report.StkType2},{report.BelongMarketNo},{report.BelongStkCode},{report.SeqNo},{report.PriceType},{report.StkErrorNo}\r\n";
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
    "RealReportList": [
      {
        "Account": "S98875400007",
        "RptType": "50",
        "OrderNo": "f0440",
        "MarketNo": "TWSE",
        "CompanyNo": "2330",
        "StkCName": "台積電",
        "OrderDate": "2025/12/1",
        "OrderTime": "13:8:7.377",
        "OrderType": "0",
        "BS": "B",
        "Price": "0.0",
        "TouchPrice": "0.0",
        "BeforeQty": "0",
        "OrderQty": "2000",
        "OpenOffsetKind": "",
        "DayTrade": "",
        "OrderCond": "0",
        "OrderErrorNo": "",
        "TradeKind": "1",
        "APCode": "0",
        "BasketNo": "",
        "OrderStatus": "0",
        "StkType1": "0",
        "StkType2": "0",
        "BelongMarketNo": "1",
        "BelongStkCode": "100026",
        "SeqNo": "0",
        "PriceType": "1",
        "StkErrorNo": "00000"
      }
    ]
  }
}
```
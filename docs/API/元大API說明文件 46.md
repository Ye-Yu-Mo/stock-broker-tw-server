---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9B%9E%E5%A0%B1/%E5%8D%B3%E6%99%82%E5%9B%9E%E5%A0%B1%E5%BD%99%E7%B8%BD%E6%9F%A5%E8%A9%A2/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## GetRealReportMerge

即時回報彙總查詢

```
bool GetRealReportMerge(Account, lng)
```

### 回傳：

| Type | Description |
| --- | --- |
| bool | `True` ：此功能執行成功;`False` ：此功能執行異常   （結果請從回應事件 **OnResponse** 接收） |

---

### Input Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 | 證券: S + 分公司代號(4) + 帳號(7)   例如 S98875005091   期貨: F + 分公司代號(7+3) + 帳號(7)   例如 FF021000P001234567 |
| Lng | enumLangType | 語系 | [參考列舉物件-語系](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlangtype)   預設為 `Normal`   Normal: Big5   UTF8: UTF8   SC: 簡體中文 |

---

### Output Parameters

#### RealReportMergeResult 即時回報彙總結果

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| RealReportMergeList | [List\<RealReportMerge>](#realreportmerge) | 結果清單 |  |

#### RealReportMerge 即時回報彙總物件

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| Account | string | 帳號 |  |
| RptType | Byte | 回報類別 | 1: 股票   2: 期貨   3: 選擇權   4: 海外期貨   5: 海外股票 |
| OrderNo | string | 委託單號 |  |
| MarketNo | enumMarketType | 市場代碼 | [參考列舉物件-市場類別](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enummarkettype) |
| CompanyNo | string | 商品代碼 | 2854, 05311, FITX 200709, URO200709, FIGTL7/C8, TXO09000T7, TXO08000/08100U7 |
| OrderDate | TYuantaDate | 交易日 | [參考物件-日期物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantadate) |
| OrderTime | TYuantaTime | 委託時間 | [參考物件-時間物件](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html#tyuantatime) |
| OrderType | string | 委託種類 | 現貨: 0:普通,1,3:資,2,4:券,5:策略借券,6:避險借券,7:資沖,8:券沖   期權: M:市價,L:限價,P:範圍市價   海外期: LMT:限價單,MKT:市價單,STP:停損單,SWL:停損限價單,CXL:取消單   海外股票:1:Market,2:Limit 限價單 |
| BS | string | 買賣別 | S:賣, B:買 |
| Price | double | 委託價 | Ex. 23.50,1.0585, 0000125’23.5(海外期) |
| TouchPrice | double | 停損執行價 | 000116'21.75 |
| LastDealPrice | double | 最新成交價 |  |
| AvgDealPrice | double | 成交均價 |  |
| BeforeQty | Int | 改量前數量 |  |
| OrderQty | Int | 委託股數 | 股數/口數 (有效數量含成交) |
| OkQty | Int | 成交股數 | 股數/口數 |
| OpenOffsetKind | string | 新增/沖銷別 | 期: 0:新增,1:沖銷,2:新倉且當日沖銷單   權: 0:新增,1:沖銷   海外股票(SettleType):0:外幣,1:台幣 |
| DayTrade | string | 當沖記號 | 證券：' ' OR 'X', 期權：' ' OR 'Y' |
| OrderCond | string | 委託條件 | 證券: 3:IOC,4:FOK,0:ROD   期權:F:FOK,I:IOC,R:ROD   海外期:0:DAY,2:IOC,1:FOK,N:非GTC單   海外股票:0:DAY,3:IOC,4:FOK |
| OrderErrorNo | string | 錯誤碼 | 證券以外的錯誤碼 |
| APCode | Byte | 委託類別 | 現貨:0:現股,2:零股,4:盤中零股,7:盤後,99:興櫃 |
| OrderStatus | Short | 狀態碼 | 0:傳輸中,5:預約單,10:委託失敗,20:委託成功,24:委託失效,25:價穩失效,30:取消 |
| LastOrderStatus | Byte | 最新一筆即回資料狀態 | 0:委託成功,1:委託失敗,2:取消成功,3:取消失敗,4:減量成功,5:減量失敗,6:查詢成功,7:查詢失敗,8:已成交,10:組合成功,11:拆解成功,12:平轉新,13:新轉平,18:委託收到,19:取消收到(國外股票),20:改價成功,21:改價失敗,23:取消成交(國外股票),24:委託失效,25:價穩失效 |
| StkCName | string | 商品名稱 |  |
| TradeCode | string | 實體交易代號 | 放下單格式: 台股證券:"2854","03038","03152P"; 台股期權:"FITX 200903","XIO C200811"; 港股證券:"0001","14200"; 港股期權:"HSIK8","HSI19800K8","HSI198I8/194U8"; 美股:"A","MSFT" |
| StrikePrice | double | 履約價 |  |
| BasketNo | string | 一籃子下單編號 |  |
| StkType1 | Byte | 屬性1 | Bit 1:管理商品,2:交易記號,3:受益憑證,4:ETF商品,5:權證記號,6:特別股,7:存託憑證,8:外國股票 |
| StkType2 | Byte | 屬性2 | Bit 1:可轉換公司債,2:附認股權公司債,3:警示股,4:指數記號,5:期貨,6:個股選擇權,7:指數選擇權,8:保留 |
| BelongMarketNo | Byte | 所屬市場代碼 |  |
| BelongStkCode | string | 所屬股票代碼 |  |
| StkType | string | 價格種類 | 證券使用: 1:市價, 2:限價, H:漲停, L:跌停, "-":平盤 |
| StkErrorNo | string | 證券回報錯誤碼 | 證券專用的錯誤碼 |

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
string Account = "S98875005091";
string Password = "1234";
enumEnvironmentMode enumEvenMode = enumEnvironmentMode.UAT;

objYuantaSparkAPI.OnResponse += objApi_OnResponse;
objYuantaSparkAPI.SetLogType(enumLogType.ALL);

objYuantaSparkAPI.Open(enumEvenMode);
Thread.Sleep(1000);
objYuantaSparkAPI.Login(Account, Password);
Thread.Sleep(1000);

objYuantaSparkAPI.GetRealReportMerge(Account);
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

                    case 'GetRealReportMerge':
                        # 即時回報彙總查詢
                        RResult = objValue
                        reportList = RResult.RealReportMergeList

                        result += '即時回報彙總查詢:\r\n'

                        for i in range(reportList.Count):
                            yuantaDate = reportList[i].OrderDate
                            date = '{0}/{1}/{2}'.format(yuantaDate.ushtYear, yuantaDate.bytMon, yuantaDate.bytDay)

                            yuantaTime = reportList[i].OrderTime
                            time = '{0}:{1}:{2}.{3}'.format(str(yuantaTime.bytHour), str(yuantaTime.bytMin), str(yuantaTime.bytSec), str(yuantaTime.ushtMSec))

                            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29},{30},{31},{32}\r\n'.format(
                                reportList[i].Account, str(reportList[i].RptType), reportList[i].OrderNo, str(reportList[i].MarketNo), reportList[i].CompanyNo, date, time,
                                reportList[i].OrderType, reportList[i].BS, str(reportList[i].Price), str(reportList[i].TouchPrice), str(reportList[i].LastDealPrice),
                                str(reportList[i].AvgDealPrice), str(reportList[i].BeforeQty), str(reportList[i].OrderQty), str(reportList[i].OkQty),
                                reportList[i].OpenOffsetKind, reportList[i].DayTrade, reportList[i].OrderCond, reportList[i].OrderErrorNo, str(reportList[i].APCode),
                                str(reportList[i].OrderStatus), str(reportList[i].LastOrderStatus), reportList[i].StkCName, reportList[i].TradeCode,
                                str(reportList[i].StrikePrice), reportList[i].BasketNo, str(reportList[i].StkType1), str(reportList[i].StkType2),
                                str(reportList[i].BelongMarketNo), reportList[i].BelongStkCode, reportList[i].StkType, reportList[i].StkErrorNo
                            )

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

#即時回報彙總查詢
objYuantaSparkAPI.GetRealReportMerge('S98875005091')
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

            else if (strIndex == "GetRealReportMerge")
            {
                var result = (RealReportMergeResult)objValue;
                try
                {
                    int nRowCount = result.RealReportMergeList.Count;
                    strResult += "===============\r\n即時回報彙總(查詢結果) 筆數:" + nRowCount.ToString() + "\r\n===============\r\n";

                    result.RealReportMergeList.ForEach(report =>
                    {
                        strResult += $"{report.Account},{report.RptType},{report.OrderNo},{report.MarketNo},{report.CompanyNo},";
                        TYuantaDate yuantaDate = report.OrderDate;
                        strResult += String.Format("{0}/{1}/{2}", yuantaDate.ushtYear, yuantaDate.bytMon, yuantaDate.bytDay) + ",";
                        TYuantaTime yuantaTime = report.OrderTime;
                        strResult += String.Format("{0}:{1}:{2}.{3}", yuantaTime.bytHour, yuantaTime.bytMin, yuantaTime.bytSec, yuantaTime.ushtMSec) + ",";
                        strResult += $"{report.OrderType},{report.BS},{report.Price},{report.TouchPrice},{report.LastDealPrice},{report.AvgDealPrice}," +
                        $"{report.BeforeQty},{report.OrderQty},{report.OkQty},{report.OpenOffsetKind},{report.DayTrade},{report.OrderCond},{report.OrderErrorNo}," +
                        $"{report.APCode},{report.OrderStatus},{report.LastOrderStatus},{report.StkCName},{report.TradeCode},{report.StrikePrice},{report.BasketNo}," +
                        $"{report.StkType1},{report.StkType2},{report.BelongMarketNo},{report.BelongStkCode},{report.StkType},{report.StkErrorNo}\r\n";
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
    "RealReportMergeList": [
      {
        "Account": "S98875005091",
        "RptType": "1",
        "OrderNo": "f0440",
        "MarketNo": "TWSE",
        "CompanyNo": "2330",
        "OrderDate": "2025/12/1",
        "OrderTime": "13:8:7.0",
        "OrderType": "0",
        "BS": "B",
        "Price": "0.0",
        "TouchPrice": "0.0",
        "LastDealPrice": "0.0",
        "AvgDealPrice": "0.0",
        "BeforeQty": "0",
        "OrderQty": "2000",
        "OkQty": "0",
        "OpenOffsetKind": "",
        "DayTrade": "",
        "OrderCond": "0",
        "OrderErrorNo": "",
        "APCode": "0",
        "OrderStatus": "20",
        "LastOrderStatus": "0",
        "StkCName": "台積電",
        "TradeCode": "2330",
        "StrikePrice": "0.0",
        "BasketNo": "",
        "StkType1": "0",
        "StkType2": "0",
        "BelongMarketNo": "1",
        "BelongStkCode": "100026",
        "StkType": "1",
        "StkErrorNo": ""
      }
    ]
  }
}
```
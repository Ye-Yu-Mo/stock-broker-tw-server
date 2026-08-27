###程式名稱:YSendOrder.py
###程式用途說明:本程式為透過YuantaSparkAPI.dll進行各功能的範例程式
###Windows與Linux/MAC登入方式不同，請參考內文Login()
###物件內容請參考各功能說明文件

import os
#import clr_loader
import time
import datetime
import struct
import pathlib
import sys
from datetime import datetime
from pathlib import Path
from pythonnet import load

# 指定 Python.Runtime.dll 的路徑
#os.environ["PYTHONNET_PYDLL"] = r"C:\Users\*\AppData\Local\Programs\Python\Python38\python38.dll"

# 使用 clr-loader 載入 .NET Core/.NET 8
load("coreclr")

#其他載入寫法
#from clr_loader import get_coreclr
#from pythonnet import set_runtime
#rt = get_coreclr()
#set_runtime(rt)
#export PYTHONNET_RUNTIME=coreclr

import clr
import System
##透過Clr引用系統標準函式
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from System.Reflection import BindingFlags
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
    
##匯入YuantaSparkAPI物件
from YuantaOneAPI import (YuantaSparkAPITrader, enumLangType,enumEnvironmentMode,OnResponseEventHandler,enumLogType,enumLangType,StockOrder,FutureOrder,LoginResult,Status,LoginData,StkOrderResult,FutOrderResult,OVFutOrderResult,
                          OrderStatus,StkOrderData,FutOrderData,OVFutOrderData,RealReport,RealReportMerge,TYuantaDate,TYuantaTime,Quote,enumMarketType,QueryWatchListResult,QueryWatchList,
                          RealReportResult,RealReportMergeResult,OrderTradeReportResult,StkOrder,StkTrade,FutOrder,FutTrade,OVStkOrder,OVStkTrade,OVFutOrder,OVFutTrade,TYuantaDateTime,StoreSummaryResult,
                          StkStore,OVStkStore,FutStoreSummaryResult,FutStore,OVFutStoreSummaryResult,OVFutStore,FutInterestStoreResult,DepositOptimumResult,DepositOptimum,FutCombinedResult,
                          FutCombinedData,Watchlist,enumQuoteIndexType,WatchListResult,WatchlistAll,WatchListAllResult,StockTick,StockTickResult,FiveTickA,enumQuoteFiveTickIndexType,FiveTickAResult,MarketInformation,
                          MarketInfoResult,StockOtherInformation,StockOtherInfoResult,SubQuoteListResult,FutSprStoreResult,FutSprStore,FutureApart,FutureApartResult,StkInfo,StkInformationResult,enumStkTickSelectType,StickDetailResult,
                          StkClassifyPriceResult,UnGainLossDetailResult,RealizedGainLoss,StrategyOrder1,StrategyOrder2,STOStrategy,MLPStrategy,OCOStrategy,SpiderStrategy,MS_SpiderStrategy,MS_DayTradeSpiderStrategy,StrategySettings,MLPStrategySettings,
                          SpiderSettings,SpiderStrategySettings,StrategyCondition1,StrategyCondition2,OrderSettings1,OrderSettings2,OrderType1,OrderType2,OrderType3,OrderPriceType1,OrderPriceType2,DayTradeSpiderSettings,StrategyType,DeleteStrategy,KLineType) 


#登入回應 Login
def login_out_response(LoResult):    
    try:
        #loginResult = LoginResult() 
        loginResult = LoResult
        #status = Status()        
        status = loginResult.LoginStatus
        result = ''          

        strMsgCode = status.MsgCode # 訊息代碼
        strMsgContent = status.MsgContent # 訊息內容
        intCount = status.Count # 筆數
        result = '{0},{1},帳號筆數:{2}\r\n'.format(strMsgCode,strMsgContent, str(intCount))

        if strMsgCode == '0001' or strMsgCode == '00001' or intCount > 0 :
            #datas = List[LoginData]()
            datas = loginResult.LoginList
            for i in range(intCount):
                result += '{0},{1},{2},{3}\r\n'.format(datas[i].Account ,datas[i].Name ,datas[i].InvestorID ,str(datas[i].SellerNo))

    except Exception as error:
        result = error

    return result


#現貨下單回應 SendStockOrder
def stk_order_out_response(StkResult):    
    try:
        #stkOrderResult = StkOrderResult()
        stkOrderResult = StkResult
        #status = OrderStatus()        
        status = stkOrderResult.ResultCount
        #stkOrderDatas = List[StkOrderData]()
        stkOrderDatas = stkOrderResult.ResultList
        result = ''

        
        result += '現貨下單結果:\r\n'
        Rcount = status.Count
        print(Rcount)
        result += '{0},{1},下單筆數:{2}\r\n'.format(status.MsgCode,status.MsgContent,str(Rcount))

		#循環處理回應資料
        for i in range(Rcount):
            yuantaDate = stkOrderDatas[i].TradeDate

            date= '{0}/{1}/{2}'.format(yuantaDate.Year, yuantaDate.Month, yuantaDate.Day) 
            result += '{0},{1},{2},{3},{4},{5},{6}\r\n'.format(str(stkOrderDatas[i].Identify),str(stkOrderDatas[i].ReplyCode),stkOrderDatas[i].OrderNO,date,str(stkOrderDatas[i].ErrType),stkOrderDatas[i].ErrNO,stkOrderDatas[i].Advisory)
           
    except Exception as error:
        result = error

    return result

#期貨下單回應 SendFutureOrder
def future_order_out_response(FutResult):    
    try:
        #futOrderResult = FutOrderResult()
        futOrderResult = FutResult
        #status = OrderStatus()        
        status = futOrderResult.ResultCount
        #futOrderDatas = List[FutOrderData]()
        futOrderDatas = futOrderResult.ResultList
        result = ''

        result += '期貨下單結果:\r\n'
        Rcount = status.Count
        result += '{0},{1},下單筆數:{2}\r\n'.format(status.MsgCode,status.MsgContent,str(Rcount))

		#循環處理回應資料
        for i in range(Rcount):
            yuantaDate = futOrderDatas[i].TradeDate

            date = '{0}/{1}/{2}'.format(yuantaDate.Year, yuantaDate.Month, yuantaDate.Day)
            result += '{0},{1},{2},{3},{4},{5},{6}\r\n'.format(str(futOrderDatas[i].Identify),str(futOrderDatas[i].ReplyCode),futOrderDatas[i].OrderNO,date,str(futOrderDatas[i].ErrType),futOrderDatas[i].ErrNO,
                                                               futOrderDatas[i].Advisory)

    except Exception as error:
        result = error

    return result


#即時回報彙總回應 RR_RealReportMerge
def stk_order_real_reportMerge(report):       
    try:
        #realReport = RealReportMerge()
        realReport = report

        result = ''
        result += '即時回報彙總:\r\n'

        #yuantaDate = TYuantaDate()
        yuantaDate = realReport.OrderDate
        date= '{0}/{1}/{2}'.format(yuantaDate.ushtYear, yuantaDate.bytMon, yuantaDate.bytDay)
        #yuantaTime = TYuantaTime()
        yuantaTime = realReport.OrderTime
        time= '{0}:{1}:{2}.{3}'.format(str(yuantaTime.bytHour), str(yuantaTime.bytMin), str(yuantaTime.bytSec), str(yuantaTime.ushtMSec))

        result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29},{30},{31},{32}\r\n'.format(
            realReport.Account,str(realReport.RptType),realReport.OrderNo,str(realReport.MarketNo),realReport.CompanyNo,date,time,realReport.OrderType,realReport.BS,str(realReport.Price),
            str(realReport.TouchPrice),str(realReport.LastDealPrice),str(realReport.AvgDealPrice),str(realReport.BeforeQty),str(realReport.OrderQty),str(realReport.OkQty),realReport.OpenOffsetKind,
            realReport.DayTrade,realReport.OrderCond,realReport.OrderErrorNo,str(realReport.APCode),str(realReport.OrderStatus),str(realReport.LastOrderStatus),realReport.StkCName,realReport.TradeCode,
            str(realReport.StrikePrice),realReport.BasketNo,str(realReport.StkType1),str(realReport.StkType2),str(realReport.BelongMarketNo),realReport.BelongStkCode,str(realReport.StkType),str(realReport.StkErrorNo))        
        
    except Exception as error:
        result = error
    #time.sleep(3)
    return result

#即時回報回應 RR_RealReport
def stk_order_real_report(report):  
    try:
        #realReport = RealReport()
        realReport = report

        result = ''
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
           
    except Exception as error:
        result = error
    #time.sleep(3)
    return result

#讀取報價表 GetWatchListAll
def ReadWatchListAll_Out(WResult):
    try:
        #Qresult = QueryWatchListResult()
        Qresult = WResult
        #QueryWatchList = List[QueryWatchList]()   
        QueryWatchList = Qresult.QueryWatchList

        result = ''
        result += '報價表:\r\n'
        for i in range(QueryWatchList.Count):
            #yuantaTime = TYuantaTime()
            yuantaTime = QueryWatchList[i].Time
            time= '{0}:{1}:{2}.{3}'.format(str(yuantaTime.Hour), str(yuantaTime.Minute), str(yuantaTime.Second), str(yuantaTime.Millisecond))
            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29},{30},{31},{32},{33},{34},{35},{36},{37},{38},{39},{40},{41},{42},{43},{44},{45},{46},{47},{48},{49}\r\n'.format(
                QueryWatchList[i].MarketNo,QueryWatchList[i].StkCode,QueryWatchList[i].StkName,str(QueryWatchList[i].YstPrice),str(QueryWatchList[i].OpenRefPrice),str(QueryWatchList[i].UpStopPrice),
               str(QueryWatchList[i].DownStopPrice),str(QueryWatchList[i].YstVol),QueryWatchList[i].ExtName,str(QueryWatchList[i].Decimal),int(QueryWatchList[i].CreditPercent),int(QueryWatchList[i].LenBondPercent),
               str(QueryWatchList[i].OpenPrice),QueryWatchList[i].HighPrice,str(QueryWatchList[i].LowPrice),str(QueryWatchList[i].BuyPrice),str(QueryWatchList[i].TotalOutVol),str(QueryWatchList[i].SellPrice),
               str(QueryWatchList[i].TotalInVol),str(QueryWatchList[i].DealPrice),str(QueryWatchList[i].TotalDealAmt),str(QueryWatchList[i].VolFlag),str(QueryWatchList[i].Vol),int(QueryWatchList[i].TotalVol),
               str(QueryWatchList[i].FixedPriceVol),str(QueryWatchList[i].ReserveVol),str(QueryWatchList[i].SettlementPrice),str(QueryWatchList[i].HiContractPrice),QueryWatchList[i].LoContractPrice,
               str(QueryWatchList[i].OrderBuyCount),str(QueryWatchList[i].OrderBuyQty),str(QueryWatchList[i].OrderSellCount),str(QueryWatchList[i].OrderSellQty),str(QueryWatchList[i].DealBuyCount),str(QueryWatchList[i].DealSellCount),
               str(QueryWatchList[i].Volatility),time,QueryWatchList[i].TimeDiff,str(QueryWatchList[i].StkType2),str(QueryWatchList[i].ReserveVolDiff),QueryWatchList[i].BelongCode,QueryWatchList[i].IndustryName,
               str(QueryWatchList[i].PrincipalPercent),str(QueryWatchList[i].UpDownDay),str(QueryWatchList[i].BidQty),str(QueryWatchList[i].AskQty),str(QueryWatchList[i].PriceTrends),str(QueryWatchList[i].EstDealPrice),
               str(QueryWatchList[i].EstDealVol),str(QueryWatchList[i].EstDealVolFlag))

    except Exception as error:
        result = error
    #time.sleep(3)
    return result

#即時回報查詢
def get_real_report_response(report):
    try:
        #RResult = RealReportResult()
        RResult = report
        #reportList = List[RealReport]()
        reportList = RResult.RealReportList 

        result = ''
        result += '即時回報查詢:\r\n'

        for i in range(reportList.Count):

            #yuantaDate = TYuantaDate()
            yuantaDate = reportList[i].OrderDate
            date= '{0}/{1}/{2}'.format(yuantaDate.ushtYear, yuantaDate.bytMon, yuantaDate.bytDay)
            #yuantaTime = TYuantaTime()
            yuantaTime = reportList[i].OrderTime
            time= '{0}:{1}:{2}.{3}'.format(str(yuantaTime.bytHour), str(yuantaTime.bytMin), str(yuantaTime.bytSec), str(yuantaTime.ushtMSec))

            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28}\r\n'.format(
                reportList[i].Account,str(reportList[i].RptType),reportList[i].OrderNo,str(reportList[i].MarketNo),reportList[i].CompanyNo,reportList[i].StkCName,date,time,reportList[i].OrderType,
                reportList[i].BS,str(reportList[i].Price),str(reportList[i].TouchPrice),str(reportList[i].BeforeQty),str(reportList[i].OrderQty),reportList[i].OpenOffsetKind,reportList[i].DayTrade,
                reportList[i].OrderCond,reportList[i].OrderErrorNo,str(reportList[i].TradeKind),str(reportList[i].APCode),reportList[i].BasketNo,str(reportList[i].OrderStatus),str(reportList[i].StkType1),
                str(reportList[i].StkType2),str(reportList[i].BelongMarketNo),reportList[i].BelongStkCode,str(reportList[i].SeqNo),reportList[i].PriceType,reportList[i].StkErrorNo)
           
    except Exception as error:
        result = error
    #time.sleep(3)
    return result

#即時回報彙總查詢
def get_real_report_merge_response(report):
    try:
        #RResult = RealReportMergeResult()
        RResult = report
        #reportList = List[RealReportMerge]()
        reportList = RResult.RealReportMergeList 

        result = ''
        result += '即時回報彙總查詢:\r\n'

        for i in range(reportList.Count):

            #yuantaDate = TYuantaDate()
            yuantaDate = reportList[i].OrderDate
            date= '{0}/{1}/{2}'.format(yuantaDate.ushtYear, yuantaDate.bytMon, yuantaDate.bytDay)
            #yuantaTime = TYuantaTime()
            yuantaTime = reportList[i].OrderTime
            time= '{0}:{1}:{2}.{3}'.format(str(yuantaTime.bytHour), str(yuantaTime.bytMin), str(yuantaTime.bytSec), str(yuantaTime.ushtMSec))

            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29},{30},{31},{32}\r\n'.format(
                reportList[i].Account,str(reportList[i].RptType),reportList[i].OrderNo,str(reportList[i].MarketNo),reportList[i].CompanyNo,date,time,reportList[i].OrderType,reportList[i].BS,
                str(reportList[i].Price),str(reportList[i].TouchPrice),str(reportList[i].LastDealPrice),str(reportList[i].AvgDealPrice),str(reportList[i].BeforeQty),str(reportList[i].OrderQty),
                str(reportList[i].OkQty),reportList[i].OpenOffsetKind,reportList[i].DayTrade,reportList[i].OrderCond,reportList[i].OrderErrorNo,str(reportList[i].APCode),str(reportList[i].OrderStatus),
                str(reportList[i].LastOrderStatus),reportList[i].StkCName,reportList[i].TradeCode,str(reportList[i].StrikePrice),reportList[i].BasketNo,str(reportList[i].StkType1),str(reportList[i].StkType2),
                str(reportList[i].BelongMarketNo),reportList[i].BelongStkCode,reportList[i].StkType,reportList[i].StkErrorNo)
           
    except Exception as error:
        result = error
    #time.sleep(3)
    return result

#委託成交綜合回報
def stk_OrderTradeReport(OResult):
    try:
        #orderTradeReport = OrderTradeReportResult()
        orderTradeReport = OResult
        #SOList = List[StkOrder]()
        SOList = orderTradeReport.StkOrderList
        #STList = List[StkTrade]()
        STList = orderTradeReport.StkTradeList
        #FOList = List[FutOrder]()
        FOList = orderTradeReport.FutOrderList
        #FTList = List[FutTrade]()
        FTList = orderTradeReport.FutTradeList
        #OVSOList = List[OVStkOrder]()
        OVSOList = orderTradeReport.OVStkOrderList
        #OVSTList = List[OVStkTrade]()
        OVSTList = orderTradeReport.OVStkTradeList
        #OVFOList = List[OVFutOrder]()
        OVFOList = orderTradeReport.OVFutOrderList
        #OVFTList = List[OVFutTrade]()
        OVFTList = orderTradeReport.OVFutTradeList

        result = ''
        result += '委託成交綜合回報:\r\n'
        result += '現貨委託筆數:{0}\r\n'.format(SOList.Count)
        for i in range(SOList.Count):
            #tradeDate = TYuantaDate()
            tradeDate = SOList[i].TradeDate
            Tdate= '{0}/{1}/{2}'.format(tradeDate.ushtYear, tradeDate.bytMon, tradeDate.bytDay)
            #acceptDate = TYuantaDate()
            acceptDate = SOList[i].AcceptDate
            Adate= '{0}/{1}/{2}'.format(acceptDate.ushtYear, acceptDate.bytMon, acceptDate.bytDay)        
            #acceptTime = TYuantaTime()
            acceptTime = SOList[i].AcceptTime
            Atime= '{0}:{1}:{2}.{3}'.format(str(acceptTime.bytHour), str(acceptTime.bytMin), str(acceptTime.bytSec), str(acceptTime.ushtMSec))
            #updateDate = TYuantaDate()
            updateDate = SOList[i].UpdateDate
            Udate= '{0}/{1}/{2}'.format(updateDate.ushtYear, updateDate.bytMon, updateDate.bytDay)
            #updateTime = TYuantaTime()
            updateTime = SOList[i].UpdateTime
            Utime= '{0}:{1}:{2}.{3}'.format(str(updateTime.bytHour), str(updateTime.bytMin), str(updateTime.bytSec), str(updateTime.ushtMSec))

            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14} {15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29},{30},{31},{32},{33},{34},{35},{36},{37} {38}\r\n'.format(
                SOList[i].Account,Tdate,str(SOList[i].MarketNo),SOList[i].MarketName,SOList[i].CompanyNo,SOList[i].StkName,str(SOList[i].OrderType),SOList[i].BS,str(SOList[i].Price),SOList[i].PriceFlag,
                str(SOList[i].BeforeQty),str(SOList[i].AfterQty),str(SOList[i].OkQty),str(SOList[i].OrderStatus),Adate,Atime,SOList[i].OrderNo,SOList[i].ErrorNo,SOList[i].ErrorMessage,str(SOList[i].Seller),
                SOList[i].Channel,str(SOList[i].APCode),str(SOList[i].OTax),str(SOList[i].OCharge),str(SOList[i].ODueAmt),SOList[i].CancelFlag,SOList[i].ReduceFlag,SOList[i].TraditionFlag,SOList[i].BasketNo,
                SOList[i].TradeCurrency,SOList[i].Time_in_Force,SOList[i].Order_Success,SOList[i].Reduce_Flag,SOList[i].Chg_Prz_Flag,SOList[i].TSE_Cancel,str(SOList[i].CancelQty),str(SOList[i].OR_QTY),Udate,Utime)

        result += '現貨成交筆數:{0}\r\n'.format(STList.Count)
        for i in range(STList.Count):
            dateTime=STList[i].DateTime

            Date= '{0}/{1}/{2}'.format(dateTime.Year, dateTime.Month, dateTime.Day)
            Time= '{0}:{1}:{2}.{3}'.format(str(dateTime.Hour), str(dateTime.Minute), str(dateTime.Second), str(dateTime.Millisecond))

            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10} {11},{12},{13},{14},{15}\r\n'.format(
                STList[i].Account,str(STList[i].MarketNo),STList[i].MarketName,STList[i].CompanyNo,STList[i].StkName,str(STList[i].OrderType),STList[i].BS,str(STList[i].OkQty),str(STList[i].OPrice),
                str(STList[i].SPrice),Date,Time,STList[i].OrderNo,STList[i].TradeCurrency,STList[i].Price_Flag,str(STList[i].Exchange_Code))

        result += '期貨委託筆數:{0}\r\n'.format(FOList.Count)
        for i in range(FOList.Count):
            #tradeDate = TYuantaDate()
            tradeDate = FOList[i].TradeDate
            Tdate= '{0}/{1}/{2}'.format(tradeDate.ushtYear, tradeDate.bytMon, tradeDate.bytDay)
            #acceptDate = TYuantaDate()
            acceptDate = FOList[i].AcceptDate
            Adate= '{0}/{1}/{2}'.format(acceptDate.ushtYear, acceptDate.bytMon, acceptDate.bytDay)        
            #acceptTime = TYuantaTime()
            acceptTime = FOList[i].AcceptTime
            Atime= '{0}:{1}:{2}.{3}'.format(str(acceptTime.bytHour), str(acceptTime.bytMin), str(acceptTime.bytSec), str(acceptTime.ushtMSec))

            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19} {20},{21},{22},{23},{24},{25},{26},{27},{28},{29},{30},{31},{32},{33},{34},{35},{36},{37},{38},{39},{40},{41},{42}\r\n'.format(
                FOList[i].Account,Tdate,str(FOList[i].MarketNo),FOList[i].MarketName,FOList[i].Commodity1,str(FOList[i].SettlementMonth1),str(FOList[i].StrikePrice1),FOList[i].BuySellKind1,FOList[i].Commodity2,
                str(FOList[i].SettlementMonth2),str(FOList[i].StrikePrice2),FOList[i].BuySellKind2,FOList[i].OpenOffsetKind,FOList[i].OrderCondition,FOList[i].OrderPrice,str(FOList[i].BeforeQty),str(FOList[i].AfterQty),
                str(FOList[i].OkQty),str(FOList[i].OrderStatus),Adate,Atime,FOList[i].ErrorNo,FOList[i].ErrorMessage,FOList[i].OrderNo,FOList[i].ProductType,str(FOList[i].Seller),str(FOList[i].TotalMatFee),
                str(FOList[i].TotalMatExchTax),str(FOList[i].TotalMatPremium),FOList[i].DayTradeID,FOList[i].CancelFlag,FOList[i].ReduceFlag,FOList[i].StkName1,FOList[i].StkName2,FOList[i].TraditionFlag,
                FOList[i].TRID,FOList[i].CurrencyType,FOList[i].CurrencyType2,FOList[i].BasketNo,str(FOList[i].MarketNo1),FOList[i].StkCode1,str(FOList[i].MarketNo2),FOList[i].StkCode2)

        result += '期貨成交筆數:{0}\r\n'.format(FTList.Count)
        for i in range(FTList.Count):
            #date = TYuantaDate()
            date = FTList[i].MatchDate
            Mdate= '{0}/{1}/{2}'.format(date.ushtYear, date.bytMon, date.bytDay)        
            #time = TYuantaTime()
            time = FTList[i].MatchTime
            Mtime= '{0}:{1}:{2}.{3}'.format(str(time.bytHour), str(time.bytMin), str(time.bytSec), str(time.ushtMSec))

            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9} {10} {11},{12},{13},{14},{15},{16},{17},{18},{19} {20},{21},{22},{23},{24},{25},{26},{27}\r\n'.format(
                FTList[i].Account,str(FTList[i].MarketNo),FTList[i].MarketName,FTList[i].Commodity1,str(FTList[i].SettlementMonth1),FTList[i].BuySellKind1,str(FTList[i].OkQty),str(FTList[i].MatchPrice1),
                str(FTList[i].MatchPrice2),Mdate,Mtime,FTList[i].OrderNo,str(FTList[i].StrikePrice1),FTList[i].Commodity2,str(FTList[i].SettlementMonth2),FTList[i].BuySellKind2,str(FTList[i].StrikePrice2),
                FTList[i].RecType,FTList[i].ProductType,str(FTList[i].OrderPrice),FTList[i].StkName1,FTList[i].StkName2,FTList[i].DayTradeID,str(FTList[i].SprMatchPrice),FTList[i].TRID,FTList[i].CurrencyType,
                FTList[i].CurrencyType2,FTList[i].SubNo)

        result += '國外現貨委託筆數:{0}\r\n'.format(OVSOList.Count)
        for i in range(OVSOList.Count):
            #tradeDate = TYuantaDate()
            tradeDate = OVSOList[i].TradeDate
            Tdate= '{0}/{1}/{2}'.format(tradeDate.ushtYear, tradeDate.bytMon, tradeDate.bytDay)
            
            dateTime=OVSOList[i].OrderTime

            Date= '{0}/{1}/{2}'.format(dateTime.Year, dateTime.Month, dateTime.Day)
            Time = '{0}:{1}:{2}.{3}'.format(dateTime.Hour, dateTime.Minute, dateTime.Second, dateTime.Millisecond)

            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13} {14},{15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26}\r\n'.format(
                OVSOList[i].Account,Tdate,str(OVSOList[i].MarketNo),OVSOList[i].MarketName,OVSOList[i].CompanyNo,OVSOList[i].StkName,OVSOList[i].BS,OVSOList[i].CurrencyType,str(OVSOList[i].Price),
                OVSOList[i].PriceType,str(OVSOList[i].OrderQty),str(OVSOList[i].OkQty),str(OVSOList[i].OrderStatus),Date,Time,OVSOList[i].OrderType,OVSOList[i].OrderNo,str(OVSOList[i].Fee),str(OVSOList[i].PolarisAMT),
                OVSOList[i].ErrorNo,OVSOList[i].ErrorMessage,OVSOList[i].CurrencyType2,OVSOList[i].CancelFlag,OVSOList[i].ReduceFlag,OVSOList[i].TraditionFlag,OVSOList[i].SettleType,OVSOList[i].BasketNo)

        result += '國外現貨成交筆數:{0}\r\n'.format(OVSTList.Count)
        for i in range(OVSTList.Count):
            dateTime=OVSTList[i].DateTime

            Date= '{0}/{1}/{2}'.format(dateTime.Year, dateTime.Month, dateTime.Day)
            Time= '{0}:{1}:{2}.{3}'.format(str(dateTime.Hour), str(dateTime.Minute), str(dateTime.Second), str(dateTime.Millisecond))

            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9} {10} {11},{12},{13},{14},{15}\r\n'.format(
                OVSTList[i].Account,str(OVSTList[i].MarketNo),OVSTList[i].MarketName,OVSTList[i].CompanyNo,OVSTList[i].StkName,OVSTList[i].BS,OVSTList[i].CurrencyType,str(OVSTList[i].OkQty),
                str(OVSTList[i].OrderPrice),str(OVSTList[i].MatchPrice),Date,Time,str(OVSTList[i].Fee),OVSTList[i].OrderNo,str(OVSTList[i].SettlementAMT),OVSTList[i].CurrencyType2)

        result += '國外期貨委託筆數:{0}\r\n'.format(OVFOList.Count)
        for i in range(OVFOList.Count):
            #tradeDate = TYuantaDate()
            tradeDate = OVFOList[i].TradeDate
            Tdate= '{0}/{1}/{2}'.format(tradeDate.ushtYear, tradeDate.bytMon, tradeDate.bytDay)
            #acceptDate = TYuantaDate()
            acceptDate = OVFOList[i].AcceptDate
            Adate= '{0}/{1}/{2}'.format(acceptDate.ushtYear, acceptDate.bytMon, acceptDate.bytDay)        
            #acceptTime = TYuantaTime()
            acceptTime = OVFOList[i].AcceptTime
            Atime= '{0}:{1}:{2}.{3}'.format(str(acceptTime.bytHour), str(acceptTime.bytMin), str(acceptTime.bytSec), str(acceptTime.ushtMSec))

            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14} {15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29},{30},{31},{32},{33}\r\n'.format(
                OVFOList[i].Account,Tdate,str(OVFOList[i].MarketNo),OVFOList[i].MarketName,OVFOList[i].CompanyNo,str(OVFOList[i].SettlementMonth),OVFOList[i].StkName,OVFOList[i].BS,OVFOList[i].OrderType,
                str(OVFOList[i].Price),OVFOList[i].TouchPrice,str(OVFOList[i].OrderQty),str(OVFOList[i].OkQty),str(OVFOList[i].OrderStatus),Adate,Atime,OVFOList[i].ErrorNo,OVFOList[i].ErrorMessage,
                OVFOList[i].OrderNo,OVFOList[i].DayTradeID,OVFOList[i].CancelFlag,OVFOList[i].ReduceFlag,str(OVFOList[i].UtPrice),str(OVFOList[i].UtPrice2),str(OVFOList[i].MinPrice2),str(OVFOList[i].UtPrice4),
                str(OVFOList[i].UtPrice5),str(OVFOList[i].UtPrice6),OVFOList[i].TraditionFlag,OVFOList[i].BasketNo,str(OVFOList[i].MarketNo1),OVFOList[i].StkCode1,OVFOList[i].CurrencyType,OVFOList[i].CurrencyType2)

        result += '國外期貨成交筆數:{0}\r\n'.format(OVFTList.Count)
        for i in range(OVFTList.Count):
            #date = TYuantaDate()
            date = OVFTList[i].MatchDate
            Date= '{0}/{1}/{2}'.format(date.ushtYear, date.bytMon, date.bytDay)        
            #time = TYuantaTime()
            time = OVFTList[i].MatchTime
            Time= '{0}:{1}:{2}.{3}'.format(str(time.bytHour), str(time.bytMin), str(time.bytSec), str(time.ushtMSec))

            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10} {11},{12},{13},{14}\r\n'.format(
                OVFTList[i].Account,str(OVFTList[i].MarketNo),OVFTList[i].MarketName,OVFTList[i].CompanyNo,str(OVFTList[i].SettlementMonth),OVFTList[i].StkName,OVFTList[i].BS,str(OVFTList[i].OkQty),
                str(OVFTList[i].OrderPrice),str(OVFTList[i].MatchPrice),Date,Time,OVFTList[i].OrderNo,OVFTList[i].CurrencyType,OVFTList[i].CurrencyType2)

    except Exception as error:
        result = error
    #time.sleep(3)
    return result

#股票庫存綜合總表
def stk_SummaryReport(SResult):
    try:
        #RResult = StoreSummaryResult()
        sResult = SResult
        #stkList = List[StkStore]()
        stkList = sResult.StkStoreList
        #OVstkList = List[OVStkStore]() 
        OVstkList=sResult.OVStkStoreList

        result = ''
        result += '股票庫存綜合總表:\r\n'
        result += '現貨庫存筆數:{0}\r\n'.format(stkList.Count)
        for i in range(stkList.Count):
            result +='{0},{1},{2},{3},{4},{5},{6},{7}\r\n'.format(int(stkList[i].TradeKind),str(stkList[i].MarketNo),stkList[i].StkCode,stkList[i].StkName,stkList[i].StockQty,stkList[i].Price,stkList[i].ReturnAmt,stkList[i].MarketAmt)
            #所有欄位資料太多印不出來
            """ result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29}\r\n'.format(
                stkList[i].Account,str(stkList[i].TradeKind),str(stkList[i].MarketNo),stkList[i].MarketName,stkList[i].StkCode,stkList[i].StkName,str(stkList[i].StockQty),str(stkList[i].Price),str(stkList[i].Cost),
                str(stkList[i].Interest),str(stkList[i].BuyNotInNos),str(stkList[i].SellNotInNos),str(stkList[i].TradingQty),str(stkList[i].Loan),float(stkList[i].TaxRate),str(stkList[i].LotSize),float(stkList[i].MarketPrice),
                int(stkList[i].Decimal),int(stkList[i].StkType1),int(stkList[i].StkType2),float(stkList[i].BuyPrice),float(stkList[i].SellPrice),float(stkList[i].UpStopPrice),float(stkList[i].DownStopPrice),
                str(stkList[i].PriceMultiplier),stkList[i].CurrencyType,str(stkList[i].CDQTY),str(stkList[i].OddTradingQty),float(stkList[i].ReturnAmt),float(stkList[i].MarketAmt)) """

        result += '國外現貨庫存筆數:{0}\r\n'.format(OVstkList.Count)
        for i in range(OVstkList.Count):
            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13} {14},{15},{16},{17}\r\n'.format(
                OVstkList[i].Account,OVstkList[i].CurrencyType,str(OVstkList[i].MarketNo),OVstkList[i].MarketName,OVstkList[i].StkCode,OVstkList[i].StkName,OVstkList[i].StkFullName,str(OVstkList[i].StockQty),
                str(OVstkList[i].TradingQty),str(OVstkList[i].Price),str(OVstkList[i].Cost),str(OVstkList[i].CloseRate),int(OVstkList[i].RateKind),str(OVstkList[i].LotSize),float(OVstkList[i].MarketPrice),
                int(OVstkList[i].Decimal),str(OVstkList[i].BuyPrice),str(OVstkList[i].SellPrice))

    except Exception as error:
        result = error
    #time.sleep(3)
    return result

#期貨庫存總表
def fut_SummaryReport(FResult):
    try:
        #fResult = FutStoreSummaryResult()
        fResult = FResult
        #futList = List[FutStore]()
        futList = fResult.FutStoreList

        result = ''
        result += '期貨庫存總表:\r\n'
        result += '期貨庫存筆數:{0}\r\n'.format(futList.Count)
        for i in range(futList.Count):
            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29},{30},{31},{32},{33},{34},{35},{36},{37},{38},{39},{40},{41},{42}\r\n'.format(
                futList[i].FutAccount,futList[i].Kind,futList[i].Trid,futList[i].BS,str(futList[i].Qty),str(futList[i].Amt),str(futList[i].Fee),str(futList[i].Tax),futList[i].CurrencyType,futList[i].DayTradeID,
                futList[i].Commodity1,futList[i].CallPut1,str(futList[i].SettlementMonth1),str(futList[i].StrikePrice1),futList[i].BS1,futList[i].StkName1,str(futList[i].MarketNo1),futList[i].StkCode1,
                futList[i].Commodity2,futList[i].CallPut2,str(futList[i].SettlementMonth2),str(futList[i].StrikePrice2),futList[i].BS2,futList[i].StkName2,str(futList[i].MarketNo2),futList[i].StkCode2,
                str(futList[i].BuyPrice1),str(futList[i].SellPrice1),float(futList[i].MarketPrice1),str(futList[i].BuyPrice2),str(futList[i].SellPrice2),str(futList[i].MarketPrice2),str(futList[i].Decimal),
                futList[i].ProductType1,futList[i].ProductKind1,futList[i].ProductType2,futList[i].ProductKind2,str(futList[i].UpStopPrice1),str(futList[i].DownStopPrice1),str(futList[i].UpStopPrice2),
                str(futList[i].DownStopPrice2),futList[i].StkCode1opp,futList[i].StkCode2opp)

    except Exception as error:
        result = error
    #time.sleep(3)
    return result

#國際期貨庫存總表
def OVfut_SummaryReport(OVFResult):
    try:
        #OVfResult = OVFutStoreSummaryResult()
        OVfResult = OVFResult
        #OVfutList = List[OVFutStore]()
        OVfutList = OVfResult.OVFutStoreList

        result = ''
        result += '國外期貨庫存總表:\r\n'
        result += '國外期貨庫存筆數:{0}\r\n'.format(OVfutList.Count)
        for i in range(OVfutList.Count):
            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29},{30},{31},{32},{33},{34}\r\n'.format(
                OVfutList[i].FutAccount,OVfutList[i].Kind,OVfutList[i].Trid,OVfutList[i].BS,int(OVfutList[i].Qty),str(OVfutList[i].Amt),OVfutList[i].Commodity1,OVfutList[i].CallPut1,str(OVfutList[i].SettlementMonth1),
                OVfutList[i].StkName1,str(OVfutList[i].StrikePrice1),OVfutList[i].Commodity2,OVfutList[i].CallPut2,str(OVfutList[i].SettlementMonth2),OVfutList[i].StkName2,str(OVfutList[i].StrikePrice2),
                str(OVfutList[i].Fee),OVfutList[i].CurrencyType,OVfutList[i].DayTradeID,OVfutList[i].BS1,OVfutList[i].BS2,OVfutList[i].OptProdKind1,OVfutList[i].OptProdKind2,str(OVfutList[i].MarketNo1),
                OVfutList[i].StkCode1,str(OVfutList[i].MarketNo2),OVfutList[i].StkCode2,str(OVfutList[i].BuyPrice1),str(OVfutList[i].SellPrice1),str(OVfutList[i].MarketPrice1),str(OVfutList[i].BuyPrice2),
                str(OVfutList[i].SellPrice2),str(OVfutList[i].MarketPrice2),str(OVfutList[i].Decimal),str(OVfutList[i].TickDiff))                              
            
    except Exception as error:
        result = error
    #time.sleep(3)
    return result        

#期貨權益數
def FutInterestStoreReport(FResult):
    try:
        #fResult=FutInterestStoreResult()
        fResult=FResult

        result = ''
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
   
    except Exception as error:
        result = error
    #time.sleep(3)
    return result        

#期貨保證金最佳化查詢
def FutDepositOptimumReport(FResult):
    try:
        #fResult=DepositOptimumResult()
        fResult=FResult
        #最佳化清單
        global DepositOptimumList 
        DepositOptimumList = fResult.DepositOptimumList

        result = ''
        result += '期貨保證金最佳化查詢:\r\n'
        result += '最佳化筆數:{0}\r\n'.format(DepositOptimumList.Count)
        for i in range(DepositOptimumList.Count):
            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20}\r\n'.format(
                str(DepositOptimumList[i].StrategyID),DepositOptimumList[i].FutAccountInfo,str(DepositOptimumList[i].Qty),DepositOptimumList[i].BuySell1,DepositOptimumList[i].BuySell2,str(DepositOptimumList[i].DealPrice1),
                str(DepositOptimumList[i].DealPrice2),str(DepositOptimumList[i].Decimal1),str(DepositOptimumList[i].CurrentIM1),str(DepositOptimumList[i].CurrentIM2),str(DepositOptimumList[i].SaveIM),DepositOptimumList[i].CommodityID1,
                DepositOptimumList[i].CallPut1,str(DepositOptimumList[i].SettlementMonth1),str(DepositOptimumList[i].StrikePrice1),DepositOptimumList[i].StkName1,DepositOptimumList[i].CommodityID2,DepositOptimumList[i].CallPut2,
                str(DepositOptimumList[i].SettlementMonth2),str(DepositOptimumList[i].StrikePrice2),DepositOptimumList[i].StkName2)

    except Exception as error:
        result = error
    #time.sleep(3)
    return result        

#期貨複式單組合
def FutCombined_order_out_response(FResult):
    try:
        #fResult=FutCombinedResult()
        fResult = FResult
        #status = OrderStatus()        
        status = fResult.ResultCount
        #datas = List[FutCombinedData]()
        datas = fResult.ResultList

        result = ''
        result += '期貨複式單組合結果:\r\n'
        Rcount = status.Count 
        result += '{0},{1},組合筆數:{2}\r\n'.format(status.MsgCode,status.MsgContent,str(Rcount))

		#循環處理回應資料
        for i in range(Rcount):
            result += '{0},{1},{2},{3},{4}\r\n'.format(str(datas[i].Identify),str(datas[i].ReplyCode),str(datas[i].ErrType),datas[i].ErrNO,datas[i].Advisory)

    except Exception as error:
        result = error
    #time.sleep(3)
    return result        

#期貨複式單庫存明細查詢
def FutSprStoreReport(FResult):
    try:
        #fResult=FutSprStoreResult()
        fResult = FResult
        #futList = List[FutSprStore]()
        futList = fResult.FutSprStoreList

        #複式單庫存明細
        global FutSprStoreList 
        FutSprStoreList = futList

        result = ''
        result += '#期貨複式單庫存明細:\r\n'
        result += '期貨複式單庫存筆數:{0}\r\n'.format(futList.Count)
        for i in range(futList.Count):
            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},'.format(
                futList[i].FutAccount,futList[i].Trid,futList[i].SeqNo,futList[i].SprNum,futList[i].BS,futList[i].CommodityID,futList[i].CallPut,str(futList[i].SettlementMonth),str(futList[i].StrikePrice),
                str(futList[i].Qty))
            #yuantaDate = TYuantaDate()
            yuantaDate = futList[i].TradeDate
            date= '{0}/{1}/{2}'.format(yuantaDate.ushtYear, yuantaDate.bytMon, yuantaDate.bytDay)
            result += '{0},{1},{2}\r\n'.format(date,str(futList[i].MatchPrice),futList[i].StkName)

    except Exception as error:
        result = error
    #time.sleep(3)
    return result        

#期貨複式單拆解
def FutApart_order_out_response(FResult):
    try:
        #fResult=FutureApartResult()
        fResult = FResult
        #status = OrderStatus()
        status = fResult.ResultCount
        #datas = List[FutureApartData]()
        datas = fResult.ResultList

        result = ''
        result += '期貨複式單拆解結果:\r\n'
        result += '{0},{1},拆解筆數:{2}\r\n'.format(status.MsgCode,status.MsgContent,str(status.Count))
        for i in range(datas.Count):
            result += '{0},{1},{2},{3},{4}\r\n'.format(str(datas[i].Identify),str(datas[i].ReplyCode),str(datas[i].ErrType),datas[i].ErrNO,datas[i].Advisory)

    except Exception as error:
        result = error
    #time.sleep(3)
    return result

#取得己訂閱即時報價商品清單
def GetQuoteList_Out(QResult):
    try:    
        #qResult=SubQuoteListResult()
        qResult=QResult
        #list = List[Quote]()
        list = qResult.QuoteList

        result = ''
        result += '{0} 己訂閱報價商品列表 筆數{1}:\r\n'.format(qResult.Account,list.Count)
        for i in range(list.Count):
            result += '{0},{1}\r\n'.format(str(list[i].MarketType),list[i].StockCode)

    except Exception as error:
        result = error
    #time.sleep(3)
    return result

#行情報價表訂閱(指定欄位)
def SubscribeWatchlist_Out(WResult):
    try:
        #wResult = WatchListResult()
        wResult = WResult

        result = ''
        result += 'Watchlist指定欄位結果:\r\n'
        result += '{0},{1},{2},{3},{4}\r\n'.format(wResult.Key,str(wResult.MarketType),wResult.StkCode,str(wResult.IndexFlag),str(wResult.Value))

    except Exception as error:
        result = error
    #time.sleep(3)
    return result

#行情報價表訂閱
def SubscribeWatchlistAll_Out(WResult):
    try:
        #wResult = WatchListAllResult()
        wResult = WResult

        result = ''
        result += '行情報價表訂閱結果:\r\n'
        result += '{0},{1},{2},{3},{4},'.format(wResult.Key,str(wResult.MarketType),wResult.StkCode,str(wResult.SeqNo),str(wResult.IndexFlag))
        match wResult.IndexFlag:
            case enumQuoteIndexType.IndexFlag22:
                #flag22 = WatchListAll_Flag22()
                flag22 = wResult.IndexFlag_22
                result +='{0},{1}\r\n'.format(str(flag22.BuyVol),str(flag22.SellVol))
            case enumQuoteIndexType.IndexFlag28:
                #flag28 = WatchListAll_Flag28()
                flag28 = wResult.IndexFlag_28
                result +='{0},{1}\r\n'.format(str(flag28.BuyPrice),str(flag28.SellPrice))
            case enumQuoteIndexType.IndexFlag29:
                #flag29 = WatchListAll_Flag29()
                flag29 = wResult.IndexFlag_29
                #yuantaTime = TYuantaTime()
                yuantaTime = flag29.Time
                time= '{0}:{1}:{2}.{3}'.format(str(yuantaTime.bytHour), str(yuantaTime.bytMin), str(yuantaTime.bytSec), str(yuantaTime.ushtMSec))
                result +='{0},{1},{2},{3},{4},{5},{6}\r\n'.format(time,str(flag29.TotalOutVol),str(flag29.TotalInVol),str(flag29.Deal),str(flag29.Vol),str(flag29.TotalVol),str(flag29.TotalAmt))
            case _:
                result +=str(wResult.Value)+'\r\n'

    except Exception as error:
        result = error
    #time.sleep(3)
    return result

#分時明細訂閱
def SubscribeStocktick_out(SResult):
    try:
        #sResult = StockTickResult()
        sResult = SResult

        result = ''
        result += '分時明細訂閱結果:\r\n'
        #yuantaTime = TYuantaTime()
        yuantaTime = sResult.Time
        time= '{0}:{1}:{2}.{3}'.format(str(yuantaTime.bytHour), str(yuantaTime.bytMin), str(yuantaTime.bytSec), str(yuantaTime.ushtMSec))        
        result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10}\r\n'.format(
            sResult.Key,str(sResult.MarketType),sResult.StkCode,str(sResult.SerialNo),time,str(sResult.BuyPrice),str(sResult.SellPrice),str(sResult.DealPrice),str(sResult.DealVol),str(sResult.InOutFlag),str(sResult.Type))

    except Exception as error:
        result = error
    #time.sleep(3)
    return result

#最佳五檔行情訂閱
def SubscribeFiveTick_out(FResult):
    try:
        #fResult = FiveTickAResult()
        fResult = FResult

        result = ''
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

    except Exception as error:
        result = error
    #time.sleep(3)
    return result

#個股盤前資訊訂閱
def SubscribeMarketInformation_out(MResult):
    try:
        #mResult = MarketInfoResult()
        mResult = MResult

        result = ''
        result += '個股盤前資訊訂閱結果:\r\n'
        #yuantaTime = TYuantaTime()
        yuantaTime = mResult.Time
        time= '{0}:{1}:{2}.{3}'.format(str(yuantaTime.bytHour), str(yuantaTime.bytMin), str(yuantaTime.bytSec), str(yuantaTime.ushtMSec))        
        result += '{0},{1},{2},{3},{4},{5},{6}\r\n'.format(
            mResult.Key,str(mResult.MarketType),mResult.StkCode,str(mResult.DealPrice),str(mResult.TickVol),time,str(mResult.TradeStatus))

    except Exception as error:
        result = error
    #time.sleep(3)
    return result

#個股其他資訊訂閱
def SubscribeStockInformation_out(SResult):
    try:
        #sResult = StockOtherInfoResult()
        sResult = SResult

        result = ''
        result += '個股其他資訊訂閱結果:\r\n'
        #yuantaTime = TYuantaTime()
        yuantaTime = sResult.TradeTime
        time= '{0}:{1}:{2}.{3}'.format(str(yuantaTime.bytHour), str(yuantaTime.bytMin), str(yuantaTime.bytSec), str(yuantaTime.ushtMSec))        
        result += '{0},{1},{2},{3},{4}\r\n'.format(
            sResult.Key,str(sResult.MarketType),sResult.StkCode,str(sResult.IndexFlag),time)

    except Exception as error:
        result = error
    #time.sleep(3)
    return result

#標的資訊查詢
def GetStockInformation_out(SResult):
    try:
        #sResult = StkInformationResult()
        sResult = SResult.StockInformationList

        result = ''
        result += '標的資訊查詢結果:\r\n'
        
        for i in range(sResult.Count):        
            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},'.format(str(sResult[i].MarketNo),sResult[i].StockCode,sResult[i].Dayoffmark,str(sResult[i].Creditpercent),
                                                                        str(sResult[i].Lendpercent),str(sResult[i].Creditremnants),str(sResult[i].Lendremnants),sResult[i].LendSellMark,
                                                                        sResult[i].RecallDate,str(sResult[i].LendQty))
            for j in range(sResult[i].StockWarning.Count):
                result += '{0},'.format(str(sResult[i].StockWarning[j]))
            result += '{0}\r\n'.format(sResult[i].UpdateDate)

    except Exception as error:
        result = error
    #time.sleep(3)
    return result

#當日分時明細查詢
def GetStkTickDetail_out(SResult):
    try:
        #sResult = StickDetailResult()
        sResult = SResult.StickDetailList

        result = ''
        result += '當日分時明細查詢結果:\r\n'
        result += '市場代碼:{0}, 商品代碼:{1}\r\n'.format(SResult.MarketNo, SResult.StockCode)
        for i in range(sResult.Count):  
            result += '{0},{1},{2},{3},{4},{5},{6}\r\n'.format(str(sResult[i].TimeStamp),sResult[i].DealPrice,sResult[i].DealVol,sResult[i].BuyPrice,sResult[i].SellPrice,sResult[i].SeqNo,sResult[i].InOutFlag)
            


    except Exception as error:
        result = error
    #time.sleep(3)
    return result

#分價量表查詢
def GetStkClassifyPrice_out(SResult):
    try:
        #sResult = StkClassifyPriceResult()
        sResult = SResult.ClassifyPriceList

        result = ''
        result += '分價量表查詢結果:\r\n'
        result += '日期:{0}, 市場代碼:{1}, 商品代碼:{2}\r\n'.format(SResult.Date,SResult.MarketNo,SResult.StockCode)
        for i in range(sResult.Count):  
            result += '{0},{1},{2},{3}\r\n'.format(sResult[i].Price,sResult[i].InDealVol,sResult[i].OutDealVol,sResult[i].TotalDealVol)
            


    except Exception as error:
        result = error
    #time.sleep(3)
    return result    

#未實現損益明細查詢
def GetUnrealizedGainLossDetail_out(GResult):
    try:
        gResult = GResult.UnGainLossDetailList

        result = '未實現損益明細結果:\r\n'
        for item in gResult:
            f = item.GetType().GetField('Cost', BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.DeclaredOnly)
            cost = f.GetValue(item)
            result += f'{item.Account},{item.TradeKind},{item.MarketNo},{item.StkCode},{item.StockQty},{item.Price},{item.TradeDate},{cost},{item.Interest},{item.ReturnAmt},{item.MarketAmt}\r\n'

    except Exception as error:
        result = error
    #time.sleep(3)    
    return result

#已實現損益查詢
def GetHisRealizedGainLoss_out(GResult):
    try:
        #gResult = RealizedGainLossResult()
        gResult = GResult.RealizedGainLossList

        global RealizedGainLossList

        RealizedGainLossList = gResult
        
        result = ''
        result += '已實現損益查詢結果:\r\n'
        for i in range(gResult.Count):  
            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14}\r\n'.format(
                 gResult[i].Account, gResult[i].MarketNo, gResult[i].StkCode, gResult[i].TradeDate, gResult[i].TradeKind, gResult[i].Price, gResult[i].Qty, gResult[i].ProfitLoss, gResult[i].OrderNo, gResult[i].TermSplit, gResult[i].TermExt, gResult[i].Charge, gResult[i].Cost, gResult[i].Tax, gResult[i].TotalAMT)

    
    except Exception as error:
        result = error
    #time.sleep(3)
    return result 



#沖銷明細查詢
def GetStkHistoryReportReversal_out(GResult):
    try:
        gResult = GResult.ReversalReportList

        result = ''
        result += '沖銷明細查詢:\r\n'
        for i in range(gResult.Count):  
            result += '{0},{1},{2},{3},{4}\r\n'.format(gResult[i].Account,gResult[i].ReversalDate,gResult[i].ReversalPrice,gResult[i].ReversalQty,gResult[i].GlAmt)
    
    
    except Exception as error:
        result = error
    #time.sleep(3)
    return result     


#銀行餘額查詢
def GetBankBalance_out(BResult):
    try:
        #bResult = GetBankBalanceResult()
        bResult = BResult.BankBalanceList

        result = ''
        result += '銀行餘額查詢結果:\r\n'
        for i in range(bResult.Count):  
            result += '{0},{1},{2},{3},{4}\r\n'.format(bResult[i].Account,bResult[i].ResponseTime,bResult[i].BankAccount,bResult[i].AvailableBalance,bResult[i].Message)
    
    
    except Exception as error:
        result = error
    #time.sleep(3)
    return result 

#現貨交割款查詢(台幣)
def GetStkTransactionOutlay_out(TResult):
    try:
        tResult = TResult.TransactionOutlayList

        result = ''
        result += '交割款查詢結果:\r\n'
        for i in range(tResult.Count):  
            result += '{0},{1},{2}\r\n'.format(tResult[i].Account,tResult[i].SettlementDay,tResult[i].SettlementAmt)
    
    
    except Exception as error:
        result = error
    #time.sleep(3)
    return result 

#新增條件單
def SendAlgoCOOdrStrategy_out(SResult):
    try:
        sResult = SResult.ResultList

        result = ''
        result += "新增條件單:\r\n"

        for i in range(sResult.Count):  
            result += '{0},{1},{2},{3},{4}\r\n'.format(sResult[i].OrdStatus,sResult[i].OrderNo,sResult[i].EffTime,sResult[i].ExpTime,sResult[i].Msg)
    
    except Exception as error:
        result = error
    #time.sleep(3)
    return result 
    
#有效策略查詢
def GetConditionStrategy_out(GResult):
    try:
        #gResult = ConditionStrategyResult()
        gResult = GResult.ConditionStrategyList

        result = ''
        result += "有效策略查詢結果:\r\n"

        for i in range(gResult.Count):  
            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18}\r\n'.format(
                gResult[i].Account,gResult[i].StrategyType,gResult[i].StrategyNo,gResult[i].OrdDateTime,gResult[i].StrategyStatus,
                gResult[i].OrdStatus,gResult[i].MarketType,gResult[i].StkCode,gResult[i].Condition,gResult[i].OrderKind,
                gResult[i].Price,gResult[i].OrderQty,gResult[i].DealQty,gResult[i].RestQty,
                gResult[i].SDate,gResult[i].EDate,gResult[i].OrderTypeMsg,gResult[i].HighPx,gResult[i].TriggerPx)
            dList = gResult[i].DetailList
            for j in range(dList.Count):
                result += '  {0},{1},{2},{3},{4},{5},{6}\r\n'.format(
                    dList[j].DealTime,dList[j].OrderPrice,dList[j].AveragePrice,dList[j].DealQty,
                    dList[j].Memo,dList[j].TrigTime,dList[j].TrigCondition)
    
    except Exception as error:
        result = error
    #time.sleep(3)
    return result 
#歷史策略查詢
def GetHisConditionStrategy_out(GResult):
    try:
        #gResult = HisConditionStrategyResult()
        gResult = GResult.HisConditionStrategyList

        result = ''
        result += "歷史策略查詢結果:\r\n"

        for i in range(gResult.Count):
            result += '{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20}\r\n'.format(
                gResult[i].Account,gResult[i].StrategyType,gResult[i].StrategyNo,gResult[i].OrdDateTime,gResult[i].TermiateDate,
                gResult[i].CancelDate,gResult[i].StrategyStatus,gResult[i].OrdStatus,gResult[i].MarketType,gResult[i].StkCode,
                gResult[i].Condition,gResult[i].OrderKind,gResult[i].Price,gResult[i].OrderQty,gResult[i].DealQty,
                gResult[i].RestQty,gResult[i].SDate,gResult[i].EDate,gResult[i].OrderTypeMsg,gResult[i].HighPx,gResult[i].TriggerPx)
            dList = gResult[i].DetailList
            for j in range(dList.Count):
                result += '  {0},{1},{2},{3},{4},{5},{6}\r\n'.format(
                    dList[j].DealTime,dList[j].OrderPrice,dList[j].AveragePrice,dList[j].DealQty,
                    dList[j].Memo,dList[j].TrigTime,dList[j].TrigCondition)
    
    except Exception as error:
        result = error
    #time.sleep(3)
    return result 

#刪除條件單
def DeleteAlgoCOOdrStrategy_out(DResult):
    try:
        #dResult = DeleteStrategyResult()
        dResult = DResult.ResultList

        result = ''
        result += "刪除條件單:\r\n"

        for i in range(dResult.Count):  
            result += '{0},{1},{2},{3},{4}\r\n'.format(dResult[i].OrdStatus,dResult[i].OrderNo,dResult[i].EffTime,dResult[i].ExpTime,dResult[i].Msg)
    
    except Exception as error:
        result = error
    #time.sleep(3)
    return result


#K線查詢
def GetKLine_out(KResult):
    try:
        #kResult = KLineResult()
        kResult = KResult.KLineList

        result = ''
        result += 'K線查詢結果:\r\n'
        result += '市場代碼:{0}, 商品代碼:{1}\r\n'.format(KResult.MarketNo, KResult.StockCode)
        for i in range(kResult.Count):  
            result += '{0},{1},{2},{3},{4},{5}\r\n'.format(kResult[i].TimeStamp,kResult[i].OpenPrice,kResult[i].HighPrice,kResult[i].LowPrice,kResult[i].ClosePrice,kResult[i].DealVol)
    
    
    except Exception as error:
        result = error
    #time.sleep(3)
    return result

def SendPrefundedMargin_out(PResult):
    try:
        pResult = PResult

        result = ''
        result += '預繳款項申請:\r\n'
        result += '{0},{1},{2},{3},{4},{5}\r\n'.format(pResult.Account, pResult.Market, pResult.Currency, pResult.TradeAmt, pResult.ExeResult, pResult.ExeMessage)

    except Exception as error:
        result = error
    #time.sleep(3)
    return result

def SendStockEarmark_out(EResult):
    try:
        eResult = EResult

        result = ''
        result += '股票圈存申請:\r\n'
        result += '{0},{1},{2},{3},{4}\r\n'.format(eResult.Account, eResult.StkCode, eResult.BlockQty, eResult.ExeResult, eResult.ExeMessage)

    except Exception as error:
        result = error
    #time.sleep(3)
    return result


#回應事件
def objApi_OnResponse(intMark, dwIndex, strIndex, objHandle, objValue):
    try:    
        result = ''        
        match intMark:
            case 0:  # 系統回應資訊
                result = str(objValue)
            case 1:  # 查詢回應資訊
                match strIndex:
                    case 'Login':
                        result = login_out_response(objValue)
                    case 'SendStockOrder':
                        result = stk_order_out_response(objValue)
                    case 'SendFutureOrder':
                        result = future_order_out_response(objValue)
                    case 'GetWatchListAll':
                        result = ReadWatchListAll_Out(objValue)
                    case 'GetRealReport':
                        result = get_real_report_response(objValue)
                    case 'GetRealReportMerge':
                        result = get_real_report_merge_response(objValue)
                    case 'GetOrderTradeReport':
                        result = stk_OrderTradeReport(objValue)
                    case 'GetStoreSummary':
                        result = stk_SummaryReport(objValue)
                    case 'GetFutStoreSummary':
                        result = fut_SummaryReport(objValue)
                    case 'GetOVFutStoreSummary':
                        result = OVfut_SummaryReport(objValue)
                    case 'GetFutInterestStore':
                        result = FutInterestStoreReport(objValue)
                    case 'GetFutDepositOptimum':
                        result = FutDepositOptimumReport(objValue)
                    case 'SendFutureCombined':
                        result = FutCombined_order_out_response(objValue)
                    case 'GetFutSprStore':
                        result = FutSprStoreReport(objValue)
                    case 'SendFutureApart':
                        result = FutApart_order_out_response(objValue)
                    case 'GetQuoteList':
                        result = GetQuoteList_Out(objValue)
                    case 'GetStockInformation':
                        result = GetStockInformation_out(objValue)
                    case 'GetStkTickDetail':
                        result = GetStkTickDetail_out(objValue)
                    case 'GetStkClassifyPrice':
                        result = GetStkClassifyPrice_out(objValue)
                    case 'GetUnrealizedGainLossDetail':
                        result = GetUnrealizedGainLossDetail_out(objValue) 
                    case 'GetHisRealizedGainLoss':
                        result = GetHisRealizedGainLoss_out(objValue)
                    case 'GetStkHistoryReportReversal':
                        result = GetStkHistoryReportReversal_out(objValue)
                    case 'GetBankBalance':
                        result = GetBankBalance_out(objValue) 
                    case 'GetStkTransactionOutlay':
                        result = GetStkTransactionOutlay_out(objValue)
                    case 'SendAlgoCOOdrStrategy':
                        result = SendAlgoCOOdrStrategy_out(objValue) 
                    case 'GetConditionStrategy':
                        result = GetConditionStrategy_out(objValue)
                    case 'GetHisConditionStrategy':                                                                                 
                        result = GetHisConditionStrategy_out(objValue)
                    case 'DeleteAlgoCOOdrStrategy':
                        result = DeleteAlgoCOOdrStrategy_out(objValue)
                    case 'GetKLine':
                        result = GetKLine_out(objValue)
                    case 'SendPrefundedMargin':
                        result = SendPrefundedMargin_out(objValue)
                    case 'SendStockEarmark':
                        result = SendStockEarmark_out(objValue)
                    case _:
                        if strIndex == '':
                            result = str(objValue)
                        else:
                            result = '{0},{1}'.format(strIndex, objValue)
            case 2:  # 訂閱回應資訊
                match strIndex:
                    case 'RR_RealReport':
                        result = stk_order_real_report(objValue)
                    case 'RR_RealReportMerge':
                        result = stk_order_real_reportMerge(objValue)
                    case 'SubscribeWatchlist':
                        result = SubscribeWatchlist_Out(objValue)
                    case 'SubscribeWatchlistAll':
                        result = SubscribeWatchlistAll_Out(objValue)
                    case 'SubscribeStockTick':
                        result = SubscribeStocktick_out(objValue)
                    case 'SubscribeFiveTickA':
                        result = SubscribeFiveTick_out(objValue)
                    case 'SubscribeMarketInformation':
                        result = SubscribeMarketInformation_out(objValue)
                    case 'SubscribeStockInformation':
                        result = SubscribeStockInformation_out(objValue)
                    case _:
                        if strIndex == '':
                            result = str(objValue)
                        else:
                            result = '{0},{1}'.format(strIndex, objValue)

    except Exception as error:
        result = error

    if result:
        print('##================================================##\n')
        print(result,'\n')

##############################################################################################################

#Open		
def open_api(yuanta):
    yuanta.Open(enumEnvironmentMode.UAT)
    #time.sleep(3)
    #測試環境:UAT、正式環境:PROD

#Login
def login_api(yuanta):
    #現貨
    #Windows登入
    #證券 (ex:S+98xxxxxxxxx)
    yuanta.Login('S98875005091', '1234')
    #yuanta.Login('S981r1691656', 'abcd123')  #請用此帳戶使用銀行餘額查詢功能

    #期貨 (ex:F+ F021xxxxxxxxxxxxx)
    #期貨帳號僅供程式寫法參考，測試環境無提供期貨帳號使用
    #yuanta.Login('FF0210132241234567', 'abcd123')
    
    #Linux/MAC登入 需帶入憑證絕對路徑與憑證密碼
    #yuanta.Login('/home/yuanta/YuantaSparkAPI_NET6_Python/B110000005_TWCA.pfx','yuanta','S98875005091', '1234')
    #time.sleep(3)

#LogOut
def LogOut_api(yuanta): 
    yuanta.LogOut()

#close
def Close_api(yuanta):
    LogOut_api(yuanta)
    objYuantaSparkAPI.Close()
    objYuantaSparkAPI.Dispose()

#SendStockOrder    
def send_stock_order(yuanta):
    stockorder = StockOrder()
    stockorder.Identify = 1
    stockorder.Account = 'S98875005091'
    stockorder.APCode = 0
    stockorder.TradeKind = 0
    stockorder.OrderType = '0' 
    stockorder.StkCode = '2885'
    stockorder.PriceFlag = 'M'
    stockorder.Price = 35.0
    stockorder.OrderQty = 3
    stockorder.BuySell = 'B' 
    stockorder.OrderNo = ''
    stockorder.TradeDate = datetime.today().strftime('%Y/%m/%d') 
    stockorder.BasketNo = '' 
    stockorder.Time_in_force = '0'
	
    lstStockOrder = List[StockOrder]()
    lstStockOrder.Add(stockorder)

	#傳送下單
    yuanta.SendStockOrder('S98875005091', lstStockOrder)
	#測試環境傳送後要休息一下
    time.sleep(1)

#SendFutureOrder
def send_future_order(yuanta):
    futureOrder = FutureOrder()
    futureOrder.Identify = 1
    futureOrder.Account = 'FF0210132241234567'
    futureOrder.FunctionCode = 0
    futureOrder.CommodityID1 = 'FITX'    
    futureOrder.CallPut1 = ''
    futureOrder.SettlementMonth1 = 202602
    futureOrder.StrikePrice1 = 0
    futureOrder.Price = 30129
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
    futureOrder.OrderType = '0'
    futureOrder.OrderCond = ''
    futureOrder.SellerNo = 0
    futureOrder.OrderNo=''
    futureOrder.TradeDate = datetime.today().strftime('%Y/%m/%d') 
    futureOrder.BasketNo = ''
    futureOrder.Session = ' '
	
    lstFutureOrder = List[FutureOrder]()
    lstFutureOrder.Add(futureOrder)

	#傳送下單
    yuanta.SendFutureOrder('FF0210132241234567', lstFutureOrder)
	#測試環境傳送後要休息一下
    time.sleep(2)


#GetWatchListAll
def ReadWatchListAll_api(yuanta):
    quoteList = List[Quote]()
    quote = Quote()
    quote.MarketType = enumMarketType.TWSE
    quote.StockCode = '2885'
    quoteList.Add(quote)
    yuanta.GetWatchListAll('S98875005091', quoteList)

#GetRealReport
def GetRealReport(yuanta):
    yuanta.GetRealReport('S98875005091')

#GetRealReportMerge
def GetRealReportMerge(yuanta):
    yuanta.GetRealReportMerge('S98875005091')

#GetOrderTradeReport
def OrderTradeReport_api(yuanta):
    yuanta.GetOrderTradeReport(False,'S98875005091')
    #yuanta.GetOrderTradeReport(False,'FF0210132241234567')

#GetStoreSummary
def SummaryReport_api(yuanta):
    yuanta.GetStoreSummary('S98875005091')
    time.sleep(2)
#GetFutStoreSummary
def FutStoreSummaryReport_api(yuanta):
    yuanta.GetFutStoreSummary('FF021919F001234567')

#GetOVFutStoreSummary
def OVFutStoreSummaryReport_api(yuanta):
    yuanta.GetOVFutStoreSummary('FF0210006701234567')

#GetFutInterestStore
def FutInterestStore_api(yuanta):
    yuanta.GetFutInterestStore('FF021919F001234567','1','TWD')

#GetFutDepositOptimum
def FutDepositOptimum_api(yuanta):
    yuanta.GetFutDepositOptimum('FF021919F001234567')

#SendFutureCombined
def SendFutureCombined_api(yuanta,list):
    yuanta.SendFutureCombined('FF021919F001234567',list)

#SubscribeWatchlist
def SubscribeWatchlist_api(yuanta):
    watchlist = List[Watchlist]()
    watch = Watchlist()
    watch.IndexFlag = enumQuoteIndexType(7)
    watch.MarketType = enumMarketType.TWSE
    watch.StockCode = '2885'
    watchlist.Add(watch)
    
    yuanta.SubscribeWatchlist('S98875005091',watchlist)

#UnSubscribeWatchlist
def UnSubscribeWatchlist_api(yuanta):
    watchlist = List[Watchlist]()
    watch = Watchlist()
    watch.IndexFlag = enumQuoteIndexType(7)
    watch.MarketType = enumMarketType.TWSE
    watch.StockCode = '2885'
    watchlist.Add(watch)
 
    yuanta.UnSubscribeWatchlist('S98875005091',watchlist)

#SubscribeWatchlistAll
def SubscribeWatchlistAll_api(yuanta):
    WatchlistAllList = List[WatchlistAll]()
    watch = WatchlistAll()
    watch.MarketType = enumMarketType.TWSE
    watch.StockCode = '2885'
    WatchlistAllList.Add(watch)

    yuanta.SubscribeWatchlistAll('S98875005091',WatchlistAllList)

#UnSubscribeWatchlistAll
def UnSubscribeWatchlistAll_api(yuanta):
    WatchlistAllList = List[WatchlistAll]()
    watch = WatchlistAll()
    watch.MarketType = enumMarketType.TWSE
    watch.StockCode = '2885'
    WatchlistAllList.Add(watch)

    yuanta.UnSubscribeWatchlistAll('S98875005091',WatchlistAllList)

#SubscribeStockTick
def SubscribeStocktick_api(yuanta):
    stocktickList = List[StockTick]()
    stocktick = StockTick()
    stocktick.MarketType = enumMarketType.TAIFEX
    stocktick.StockCode = 'TXFPM1'
    stocktickList.Add(stocktick)

    yuanta.SubscribeStockTick('S98875005091',stocktickList)

#UnSubscribeStockTick
def UnSubscribeStocktick_api(yuanta):
    stocktickList = List[StockTick]()
    stocktick = StockTick()
    stocktick.MarketType = enumMarketType.TAIFEX
    stocktick.StockCode = 'TXFPM1'
    stocktickList.Add(stocktick)

    yuanta.UnSubscribeStockTick('S98875005091',stocktickList)

#SubscribeFiveTickA
def SubscribeFiveTick_api(yuanta):
    fivetickList = List[FiveTickA]()
    fivetick = FiveTickA()
    fivetick.MarketType = enumMarketType.TAIFEX
    fivetick.StockCode = 'TXFPM1'
    fivetickList.Add(fivetick)

    yuanta.SubscribeFiveTickA('S98875005091',fivetickList)

#UnSubscribeFiveTickA
def UnSubscribeFiveTick_api(yuanta):
    fivetickList = List[FiveTickA]()
    fivetick = FiveTickA()
    fivetick.MarketType = enumMarketType.TAIFEX
    fivetick.StockCode = 'TXFPM1'
    fivetickList.Add(fivetick)

    yuanta.UnSubscribeFiveTickA('S98875005091',fivetickList)

#SubscribeMarketInformation
def SubscribeMarketInformation_api(yuanta):
    infoList = List[MarketInformation]()
    marketInfo = MarketInformation()
    marketInfo.MarketType = enumMarketType.TWSE
    marketInfo.StockCode = '2885'
    infoList.Add(marketInfo)

    yuanta.SubscribeMarketInformation('S98875005091',infoList)

#UnSubscribeMarketInformation
def UnSubscribeMarketInformation_api(yuanta):
    infoList = List[MarketInformation]()
    marketInfo = MarketInformation()
    marketInfo.MarketType = enumMarketType.TWSE
    marketInfo.StockCode = '2885'
    infoList.Add(marketInfo)

    yuanta.UnSubscribeMarketInformation('S98875005091',infoList)

#SubscribeStockInformation
def SubscribeStockInformation_api(yuanta):
    infoList = List[StockOtherInformation]()
    stkInfo = StockOtherInformation()
    stkInfo.MarketType = enumMarketType.TWSE
    stkInfo.StockCode = '2885'
    infoList.Add(stkInfo)

    yuanta.SubscribeStockInformation('S98875005091',infoList)

#UnSubscribeStockInformation
def UnSubscribeStockInformation_api(yuanta):
    infoList = List[StockOtherInformation]()
    stkInfo = StockOtherInformation()
    stkInfo.MarketType = enumMarketType.TWSE
    stkInfo.StockCode = '2885'
    infoList.Add(stkInfo)

    yuanta.UnSubscribeStockInformation('S98875005091',infoList)

#GetQuoteList
def GetQuoteList_api(yuanta):
    yuanta.GetQuoteList('S98875005091')

#GetFutSprStore
def GetFutSprStore_api(yuanta):
    yuanta.GetFutSprStore('FF021919F001234567')

#SendFutureApart
def SendFutureApart_api(yuanta,FutSprStoreList):
    
    result =  FutSprStoreList 

    if result:
        lstFutSprStore = FutSprStoreList
        yuanta.SendFutureApart('FF021919F001234567', lstFutSprStore)
    else:
        print('查無複式單庫存資料')  

    #測試環境傳送後要休息一下
    time.sleep(2)

def GetStockInformation_api(yuanta):
    infoList = List[StkInfo]()
    stkInfo = StkInfo()
    stkInfo.MarketType = enumMarketType.TWSE
    stkInfo.StockCode = '2885'
    infoList.Add(stkInfo)
    yuanta.GetStockInformation('S98875005091',infoList)

def GetStkTickDetail_api(yuanta):
    yuanta.GetStkTickDetail('S98875005091', enumMarketType.TWSE, '2885', enumStkTickSelectType(1))

def GetStkClassifyPrice_api(yuanta): 
    yuanta.GetStkClassifyPrice('S98875005091', enumMarketType.TWSE, '2885')

def GetUnrealizedGainLossDetail_api(yuanta):
    yuanta.GetUnrealizedGainLossDetail('S98875005091',enumMarketType.TWSE,'2330')  


def GetHisRealizedGainLoss_api(yuanta):
    yuanta.GetHisRealizedGainLoss('S98875005091','2025/06/01','2025/06/12')  
    time.sleep(2)


def GetStkHistoryReportReversal_api(yuanta, ReGainLoss):
    for item in ReGainLoss:
        if "2885" in str(item.StkCode):  # 只顯示 2885 的資料
            print(f"帳號={item.Account}, 股票代號={item.StkCode}")
            success = yuanta.GetStkHistoryReportReversal('S98875005091', item)


def GetBankBalance_api(yuanta):
    yuanta.GetBankBalance('S981r1691656')  
    time.sleep(2)

def GetStkTransactionOutlay_api(yuanta):
    yuanta.GetStkTransactionOutlay('S98875005091')  
    time.sleep(2)

#停損利
def STOStrategy_api(yuanta):
    sto_list  = List[STOStrategy]()
    sto_obj = STOStrategy()

    sto_obj.Account = "S98875005091"
    sto_obj.EffTime =  System.DateTime(2026, 4, 1)
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
    
    yuanta.SendAlgoCOOdrStrategy[STOStrategy]('S98875005091', sto_list)
    time.sleep(1)
#--------------------------------------------------------------------------------
#移動鎖利   
def MLPStrategy_api(yuanta):
    mlp_list  = List[MLPStrategy]()
    mlp_obj = MLPStrategy()

    mlp_obj.Account = "S98875005091"
    mlp_obj.EffTime =  System.DateTime(2026, 4, 1)
    mlp_obj.ExpTime =  System.DateTime(2026, 4, 30)
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
    mlp_obj.OrderSettings.PriceType = OrderPriceType2(1)    #市價：1 成交價：2 漲停：3 平盤：4 跌停：5 
    mlp_obj.OrderSettings.OrderValue = 0
    mlp_obj.OrderSettings.OrderQty = 5
    
    mlp_list.Add(mlp_obj)
    
    yuanta.SendAlgoCOOdrStrategy[MLPStrategy]('S98875005091', mlp_list)
#--------------------------------------------------------------------------------
#二擇一
def OCOStrategy_api(yuanta):
    oco_list  = List[OCOStrategy]()
    oco_obj = OCOStrategy()

    oco_obj.Account = "S98875005091"
    oco_obj.EffTime =  System.DateTime(2026, 4, 1)
    oco_obj.ExpTime =  System.DateTime(2026, 4, 30)
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
    loss_cond = oco_obj.StrategySettings1 
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
    
    yuanta.SendAlgoCOOdrStrategy[OCOStrategy]('S98875005091', oco_list)
#--------------------------------------------------------------------------------
#多條件
def SpiderStrategy_api(yuanta):
    spider_list  = List[SpiderStrategy]()
    spider_obj = SpiderStrategy()

    spider_obj.Account = "S98875005091"
    spider_obj.EffTime =  System.DateTime(2026, 4, 1)
    spider_obj.ExpTime =  System.DateTime(2026, 4, 30)
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
    yuanta.SendAlgoCOOdrStrategy[SpiderStrategy]('S98875005091', spider_list)

#--------------------------------------------------------------------------------
#母子單
def MS_SpiderStrategy_api(yuanta):
    ms_list  = List[MS_SpiderStrategy]()
    ms_obj = MS_SpiderStrategy()

    ms_obj.Account = "S98875005091"
    ms_obj.EffTime =  System.DateTime(2026, 4, 1)
    ms_obj.ExpTime =  System.DateTime(2026, 4, 30)
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
    yuanta.SendAlgoCOOdrStrategy[MS_SpiderStrategy]('S98875005091', ms_list)


#--------------------------------------------------------------------------------
#當沖母子單
def MS_DayTradeSpiderStrategy_api(yuanta):
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
    yuanta.SendAlgoCOOdrStrategy[MS_DayTradeSpiderStrategy]('S98875005091', ms_day_list)



def GetConditionStrategy_api(yuanta):
    yuanta.GetConditionStrategy('S98875005091', 1, " ") # 策略類型: 1:停損利 2:移動鎖利 3:二擇一 4:母子單 5:多條件 6:全部

def GetHisConditionStrategy_api(yuanta):
    yuanta.GetHisConditionStrategy('S98875005091', 1, " ", "2025/03/01", "2025/03/26")  # 策略類型: 1:停損利 2:移動鎖利 3:二擇一 4:母子單 5:多條件 6:全部

def DeleteAlgoCOOdrStrategy_api(yuanta):
    target_strategy_no = 'k263R000000056'
    DeleteStrategyList = List[DeleteStrategy]()
    delete_obj = DeleteStrategy()
    delete_obj.Account = "S98875005091"
    delete_obj.StrategyType = StrategyType(1)  # 策略類型
    delete_obj.StrategyNo = target_strategy_no.strip()   # 策略單號ID

    DeleteStrategyList.Add(delete_obj)

    yuanta.DeleteAlgoCOOdrStrategy("S98875005091", DeleteStrategyList)


def GetKLine_api(yuanta):
    daily_kline_type = KLineType(11)    #日K
    #weekly_kline_type = KLineType(12)   #週K
    #monthly_kline_type = KLineType(13)  #月K
    yuanta.GetKLine('S98875005091', daily_kline_type, enumMarketType.TWSE, "2885", "2025/01/01", "2025/03/26")

def SendPrefundedMargin_api(yuanta):
    yuanta.SendPrefundedMargin('S98875005091', 10000, 'TWD', 'ALL')
    time.sleep(2)

def SendStockEarmark_api(yuanta):
    yuanta.SendStockEarmark('S98875005091', '2885', 1000)
    time.sleep(2)

##########################################################################
objYuantaSparkAPI = YuantaSparkAPITrader()
#自行設定log路徑
#objYuantaSparkAPI = YuantaSparkAPITrader('/home/yuanta/log')
objYuantaSparkAPI.OnResponse += OnResponseEventHandler(objApi_OnResponse)
objYuantaSparkAPI.SetLogType(enumLogType.COMMON) 
###########################################################################

open_api(objYuantaSparkAPI)
time.sleep(1)

login_api(objYuantaSparkAPI)
time.sleep(2)
#登入後需休息一下，主機端會控制快速重複登入

#登出
#LogOut_api(objYuantaSparkAPI)

#關閉
#Close_api(objYuantaSparkAPI)

#現貨下單
#send_stock_order(objYuantaSparkAPI)

#期貨下單
#send_future_order(objYuantaSparkAPI)

#報價表查詢
#ReadWatchListAll_api(objYuantaSparkAPI)

#即時回報查詢
#GetRealReport(objYuantaSparkAPI)

#即時回報彙總查詢
#GetRealReportMerge(objYuantaSparkAPI)

#委託成交綜合回報
#OrderTradeReport_api(objYuantaSparkAPI)

#股票庫存綜合總表
#SummaryReport_api(objYuantaSparkAPI)

#期貨庫存總表
#FutStoreSummaryReport_api(objYuantaSparkAPI)

#國際期貨庫存總表
#OVFutStoreSummaryReport_api(objYuantaSparkAPI)

#期貨權益數
#FutInterestStore_api(objYuantaSparkAPI)

#期貨保證金最佳化查詢
#DepositOptimumList = List[DepositOptimum]()
#FutDepositOptimum_api(objYuantaSparkAPI)
#time.sleep(3)

#期貨複式單組合
#SendFutureCombined_api(objYuantaSparkAPI,DepositOptimumList)

#行情報價表訂閱(指定欄位)
#SubscribeWatchlist_api(objYuantaSparkAPI)
#time.sleep(10)

#行情報價表解訂閱(指定欄位)
#UnSubscribeWatchlist_api(objYuantaSparkAPI)

#行情報價表訂閱
#SubscribeWatchlistAll_api(objYuantaSparkAPI)
#time.sleep(10)

#行情報價表解訂閱
#UnSubscribeWatchlistAll_api(objYuantaSparkAPI)

#分時明細訂閱
#SubscribeStocktick_api(objYuantaSparkAPI)
#time.sleep(10)

#分時明細解訂閱
#UnSubscribeStocktick_api(objYuantaSparkAPI)

#最佳五檔行情訂閱
#SubscribeFiveTick_api(objYuantaSparkAPI)
#time.sleep(10)

#最佳五檔行情解訂閱
#UnSubscribeFiveTick_api(objYuantaSparkAPI)

#個股盤前資訊訂閱
#SubscribeMarketInformation_api(objYuantaSparkAPI)
#time.sleep(10)

#個股盤前資訊解訂閱
#UnSubscribeMarketInformation_api(objYuantaSparkAPI)

#個股其他資訊訂閱
#SubscribeStockInformation_api(objYuantaSparkAPI)
#time.sleep(10)

#個股其他資訊解訂閱
#UnSubscribeStockInformation_api(objYuantaSparkAPI)

#期貨複式單庫存查詢
#FutSprStoreList= List[FutSprStore]()
#GetFutSprStore_api(objYuantaSparkAPI) 
#time.sleep(5)

#期貨複式單拆解
#SendFutureApart_api(objYuantaSparkAPI,FutSprStoreList)

#取得己訂閱即時報價商品清單
#GetQuoteList_api(objYuantaSparkAPI)

#標的資訊查詢
#GetStockInformation_api(objYuantaSparkAPI)

#分時明細查詢
#GetStkTickDetail_api(objYuantaSparkAPI)

#分價量表查詢
#GetStkClassifyPrice_api(objYuantaSparkAPI)

#未實現損益明細查詢
#GetUnrealizedGainLossDetail_api(objYuantaSparkAPI)

#已實現損益明細查詢
#GetHisRealizedGainLoss_api(objYuantaSparkAPI)

#沖銷明細查詢
#GetStkHistoryReportReversal_api(objYuantaSparkAPI,RealizedGainLossList)

#銀行餘額查詢
#GetBankBalance_api(objYuantaSparkAPI)

#交割款查詢
#GetStkTransactionOutlay_api(objYuantaSparkAPI)

#停損利單
#STOStrategy_api(objYuantaSparkAPI)

#移動鎖利單
#MLPStrategy_api(objYuantaSparkAPI)

#二擇一單
#OCOStrategy_api(objYuantaSparkAPI)

#多條件單
#SpiderStrategy_api(objYuantaSparkAPI)

#母子單
#MS_SpiderStrategy_api(objYuantaSparkAPI)

#當沖母子單
#MS_DayTradeSpiderStrategy_api(objYuantaSparkAPI)

#查詢條件單
#GetConditionStrategy_api(objYuantaSparkAPI)

#查詢歷史條件單
#GetHisConditionStrategy_api(objYuantaSparkAPI)

#刪除條件單
#DeleteAlgoCOOdrStrategy_api(objYuantaSparkAPI)

#K線查詢
#GetKLine_api(objYuantaSparkAPI)

#預繳款項申請
#SendPrefundedMargin_api(objYuantaSparkAPI)

#股票圈存申請
#SendStockEarmark_api(objYuantaSparkAPI)
############################################################################

while True:
    time.sleep(10)
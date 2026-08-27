---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%9B%9E%E6%87%89%E4%BA%8B%E4%BB%B6/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## 回應事件 OnResponses

接收封包事件 Server資料回應至Client端時所觸發的事件

```
OnResponseEventHandler(intMark, dwIndex, strIndex, objHandle, objValue)
```

---

### Output Parameters

| Name | Type | Description | Memo |
| --- | --- | --- | --- |
| intMark | int | 回應種類 | 0: 系統資訊回應   1: 查詢資訊回應   2: 訂閱資訊回應 |
| dwIndex | uint | 回應狀態 | **intMark為0** ：   0:其他訊息   1:Connect   2:Disconect   3:網路異常   4:需下載新版API   5:尚未連線   6:系統公告      **intMark為1** ：   0:總帳/子帳登入   3:尚未登入   4:輸入的登入帳號錯誤   5:功能代碼錯誤或權限不足   6:訂閱即時回報失敗   7:SocketRPRead失敗   9:加簽失敗/憑證異常   10: Logout!   11:帳號資訊異常   12:取得己訂閱商品清單異常   其他: FunctionID (EX:1E640A1F)      **intMark為2** ：   1:訂閱/取消訂閱失敗   其他: FunctionID (EX:1E640A1F) |
| strIndex | string | 功能名稱 | 字串型別的Function (EX: SendStockOrder)   Function請參考FunctionList   若strIndex為空值，代表功能查詢/訂閱有錯誤，請用string格式解析objValue |
| objHandle | object | Handle值 | 回傳訂閱事件時所傳入的Handle值(不處理) |
| objValue | object | 回傳資料 | 連線相關系統回應請用string格式解析   各功能回傳值依說明文件進行轉型並解析   非功能對照表功能請依舊元件方式解析byte\[\]   請參考FunctionList |
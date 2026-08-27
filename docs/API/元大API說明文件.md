---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/1.%E5%89%8D%E8%A8%80/1.%E7%B0%A1%E4%BB%8B/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## 元大SPARK API

## 概述

元大SPARK API 是一套完整的程式交易工具，讓您即時掌握市場動態、靈活執行交易策略，輕鬆打造自動化與專業級的投資應用

## 特色

支援跨平台：支援Windows、Linux、MacOS等作業系統。

支援多語言：支援C#、Python等市場主流語言

支援條件單：支援停損利、移動鎖利、二擇一、多條件、母子單

## 主要功能

行情接收：支援分時明細、五檔報價、分價量表等多樣化行情資料查詢與訂閱

下單交易：提供證券(含條件單)及期貨等多元化交易下單功能

帳務查詢：涵蓋未實現損益、已實現損益與交割款等帳務查詢服務

## 說明事項

- YuantaSparkAPI元件使用.NET8 C#開發，支援Windows、Linux、MacOS環境
- 電腦環境請用戶自行安裝.NET8的SDK
- 使用時請包含範例程式中所有.dll、.so、.dylib副檔名之檔案
- 範例程式僅為API功能呼叫寫法參考，不保證程式效能最佳化，請用戶自行調整
- 本地log檔路徑，windows環境預設為C:\\Yuanta\\YuantaSparkAPI\\Log
- 本地log檔路徑，Linux與MacOS環境預設為\\$Home\\ Log
- 考量資料存放空間，Log檔僅保留30天內檔案，超過者系統將自動移除
- API功能對照表、即時回報情境、現貨下單錯誤代碼，可參考元件內FunctionList.xls
- 下單代碼與訂閱報價商品代碼可能不同，可參考元件內FunctionList.xls 股名檔對照表
- API相關問題請致電本公司客服中心詢問：02-2718-5886。
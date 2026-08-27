---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/1.%E5%89%8D%E8%A8%80/3.%E4%BD%BF%E7%94%A8%E9%99%90%E5%88%B6%E8%AA%AA%E6%98%8E/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## 使用限制說明

為避免影響其他使用者連線，請遵守以下使用規範

## 單一連線使用限制：

| 功能 | 商品/次數限制 |
| --- | --- |
| 已登入的帳號，不允許重複呼叫登入作業 | 1 |
| 若登入失敗，不允許太頻繁執行登入作業 | 每4秒1次 |
| 不同FunctionID，所有訂閱報價商品總數上限 | 2000 |
| 同FunctionID，一秒內能發送的訂閱次數 | 10 |
| 同FunctionID，單次訂閱商品數上限      (若其中有訂閱報價表指定欄位watchlist，則商品數為商品x指定欄位數) | 200 |
| 同FunctionID，一秒內報價/帳務類能發送次數 (不含K線查詢(GetKline)) | 3 |
| K線查詢(GetKline)一秒內能發送次數 | 1 |
| 同FunctionID，一秒內交易類能發送次數 | 10 |
| 同FunctionID，單次交易最多筆數 | 30 |
| 報價表50.0.0.16，單次查詢商品上限 | 600 |

## 單一帳號使用限制：

| 項目 | 商品/ 次數限制 |
| --- | --- |
| 同時最高連線數 | 10 |
| 登入數限制 | 1000次/日 |
| 總訂閱數商品數      (若其中有訂閱報價表指定欄位watchlist，則商品數為商品x指定欄位數) | 3000檔 |
| 呼叫次數限制(註1)： |  |
| 不同FunctionID，行情類總呼叫數 | 1200次/1分鐘 |
| 不同FunctionID，帳務類總呼叫數 | 600次/1分鐘 |
| 不同FunctionID，交易類總呼叫數 | 3000次/1分鐘 |

註1：

- 當超過呼叫次數限制，系統將會 **暫停服務1分鐘** ，並回傳錯誤訊息：  
	例如：行情類呼叫次數過多，請稍後再試 ![](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/1.%E5%89%8D%E8%A8%80/image/later.png)
- 若一小時內暫停次數達10次，將停止該帳號使用API服務
- 若有使用問題，請洽所屬營業員協助處理
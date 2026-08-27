---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E9%80%A3%E7%B7%9A%E8%88%87%E9%9B%A2%E7%B7%9A/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## 連線與離線

| 函數名稱 | Open |
| --- | --- |
| 功能說明 | 開啟API連線   void Open(enumEnvironmentMode Mode); |
| 參數 | enumEnvironmentMode   Mode： [連線環境參數](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumenvironmentmode) |
| C#範例 | objYuantaSparkAPI.Open(enumEnvironmentMode.UAT); |
| Python 範例 | objYuantaSparkAPI.Open(enumEnvironmentMode.UAT) |

| 函數名稱 | Close |
| --- | --- |
| 功能說明 | 關閉API連線   void Close(); |
| C#範例 | objYuantaSparkAPI.Close(); |
| Python 範例 | objYuantaSparkAPI.Close() |

| 函數名稱 | Dispose |
| --- | --- |
| 功能說明 | 釋放API連線   void Dispose(); |
| C#範例 | objYuantaSparkAPI.Dispose(); |
| Python 範例 | objYuantaSparkAPI.Dispose() |
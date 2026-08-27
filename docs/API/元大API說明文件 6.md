---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/API%E7%9B%B8%E9%97%9C%E8%A8%AD%E5%AE%9A/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## API相關設定

| 函數名稱 | SetLogType |
| --- | --- |
| 功能說明 | 設定API Log類別   void SetLogType(enumLogType logType); |
| 參數 | [enumLogType](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E5%88%97%E8%88%89%E7%89%A9%E4%BB%B6/index.html#enumlogtype-log)   logType：Log類別 |
| C#範例 | objYuantaSparkAPI.SetLogType(enumLogType.COMMON); |
| Python 範例 | objYuantaSparkAPI.SetLogType(enumLogType.COMMON) |

| 函數名稱 | SetPMMServerCheck |
| --- | --- |
| 功能說明 | 是否檢查PMMServer   void SetPMMServerCheck(bool flag); |
| 參數 | bool   flag：True=檢查(預設)；False=不檢查 |
| C#範例 | objYuantaSparkAPI.SetPMMServerCheck(false); |
| Python 範例 | objYuantaSparkAPI.SetPMMServerCheck(false) |
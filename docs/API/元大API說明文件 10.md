---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%89%A9%E4%BB%B6/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## 物件

### TYuantaDateTime 時間日期物件

| Name | Type | Memo |
| --- | --- | --- |
| struDate | TYuantaDate | 日期物件 |
| struTime | TYuantaTime | 時間物件 |

### TYuantaDate 日期物件

| Name | Type | Memo |
| --- | --- | --- |
| ushtYear | ushort | 西元年 |
| bytMon | byte | 月 |
| bytDay | byte | 日期 |

### TYuantaTime 時間物件

| Name | Type | Memo |
| --- | --- | --- |
| bytHour | byte | 小時 |
| bytMin | byte | 分鐘 |
| bytSec | byte | 秒鐘 |
| ushtMSec | ushort | 毫秒 |
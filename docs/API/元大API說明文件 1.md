---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/1.%E5%89%8D%E8%A8%80/2.%E6%B8%AC%E8%A9%A6%E7%92%B0%E5%A2%83%26%E6%AD%A3%E5%BC%8F%E7%92%B0%E5%A2%83%E8%AA%AA%E6%98%8E/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## 測試環境&正式環境

### 測試環境說明

- 測試環境使用前請向所屬營業員申請開通API權限，並提供固定IP開通防火牆設定，開通完成後便可連線至測試環境。
- 測試環境僅提供證券測試帳號登入，測試帳號：  
	帳號種類輸入\[S\]，帳號\[98875005091\]，密碼\[1234\]，環境\[測試環境\]
- 測試憑證請 [下載](https://ys.yuanta.com.tw/quartet/api/B110000005_TWCA.zip) 憑證並匯入至電腦即可使用。
- 測試環境使用屬加值服務，僅為提供客戶串接測試，不保證穩定提供服務。
- YuantaSparkAPI.dll元件函數說明：
- Server **物件YuantaSparkAPI**
	- 請實作YuantaSparkAPITrader，並以此物件呼叫對應功能function。  
		範例：YuantaSparkAPITrader objYuantaSparkAPI = new YuantaSparkAPITrader();
		- 若需指定本地log檔儲存位置，可於宣告物件時添加指定路徑  
		範例：YuantaSparkAPITrader objYuantaSparkAPI = new YuantaSparkAPITrader ("D: \\\\Log");
- 測試環境交易規則

<table><thead><tr><th>委託條件</th><th>委託書號尾末碼</th><th>狀態</th></tr></thead><tbody><tr><td rowspan="5"><p>ROD</p></td><td><p>0, 5, A, K,U, a, k, u, F, P, Z, f, p, z</p></td><td><p>不成交</p></td></tr><tr><td><p>6, G, Q, g, q</p></td><td><p>隨機成交</p></td></tr><tr><td rowspan="2"><p>7, H, R, h, r</p></td><td><p>限價單 => 完全成交</p></td></tr><tr><td><p>市價單<br>若委託量=1 => 不成交，之後價穩失效</p><p>(模擬情境: 市價委託成功後，掛單一陣子後被價穩失效)<br>若委託量>1 => 成交1, 剩餘價穩失效</p><p>(模擬情境: 市價委託時，立刻部分成交、部分被價穩失效)</p></td></tr><tr><td><p>其他</p></td><td><p>完全成交</p></td></tr><tr><td rowspan="4"><p>IOC</p></td><td><p>0, 5, A, K,U, a, k, u, F, P, Z, f, p, z</p></td><td><p>價穩失效</p></td></tr><tr><td><p>6, G, Q, g, q</p></td><td><p>成交一半</p></td></tr><tr><td><p>7, H, R, h, r</p></td><td><p>若委託量>1 => 成交1, 剩餘價穩失效</p></td></tr><tr><td><p>其他</p></td><td><p>完全成交</p></td></tr><tr><td rowspan="2"><p>FOK</p></td><td><p>0, 5, A, K,U, a, k, u, F, P, Z, f, p, z, 6, G, Q, g, q</p></td><td><p>委託失敗</p></td></tr><tr><td><p>其他</p></td><td><p>完全成交</p></td></tr><tr><td><p>集合競價</p></td><td></td><td><p>只要下 4904(遠傳) 市價/IOC/FOK</p><p>就出現"集合競價時段不接受市價、IOC、FOK"</p></td></tr><tr><td><p>價穩措施</p></td><td></td><td><p>只要下 5203(訊連) 市價/IOC/FOK，就出現價穩失效</p></td></tr></tbody></table>

### 正式環境說明

- 請先向所屬營業員申請開通API權限，開通完成便可連線至正式環境。
- 正式環境可使用證券正式帳號及期貨正式帳號登入，帳號範例：  
	【證券帳號】：  
	帳號種類輸入\[S\]，帳號\[輸入自己的正式帳號\]，密碼\[輸入自己的電子密碼\]，環境\[正式環境\]。  
	種類：S，帳號格式：4+7，共11碼。 例：S98875005091  
	【期貨帳號】：  
	帳號種類輸入\[F\]，帳號\[輸入自己的正式帳號\]，密碼\[輸入自己的電子密碼\]，環境\[正式環境\]。  
	種類：F，帳號格式：7+3+7，共17碼。 例：FF021000P001234567
- 正式憑證請至網站上 [申請憑證](https://www.yuanta.com.tw/eYuanta/Securities/Node/Index?MainId=00414&C1=2018031206314695&ID=2018031206314695&Level=1) ，若已申請過請將憑證匯入至電腦即可使用。
- 正式環境為正式交易環境，透過API所送出的所有委託皆視為有效交易指令。一經成交，即具有法律效力，投資人須自行承擔相關交易風險，並負有履行交割與結算義務。操作前請務必確認指令內容正確無誤，審慎評估後再行下單。
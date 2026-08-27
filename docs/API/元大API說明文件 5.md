---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
## 一、元大 Spark API 說明

本文件提供以 Python 語言使用 YuantaSparkAPI 之基本範例，在正式環境進行下單及收委成回報的簡單範例程式，並包含其他功能之使用寫法供參考，協助開發者快速上手。

YuantaSparkAPI 使用方式為讀取 C# 元件 `YuantaSparkAPI.dll` 以執行 API 呼叫。由於 Python 無法直接載入 C# 元件，故需使用外部套件達成元件引用。本範例使用 `pythonnet` 套件，使 Python 程式可呼叫.NET 元件，達成 API 測試與功能開發。

---

### 執行環境需求

1. 建議 Python 版本為 3.8 以上。
2. 使用 `pythonnet` 套件：
```bash
pip install pythonnet
```

`YSendOrder.py` 為使用 `pythonnet` 之範例程式，於 Python 環境內安裝即可直接執行 `.py` 檔。

---

### 二、環境建置

#### 1\. 安裝.NET SDK 8.0

- `YuantaSparkAPI.dll` 為.NET 8 開發，請安裝.NET 8.0。
- 依據自身電腦作業系統選擇不同的 SDK 安裝檔。
- 下載連結： [下載.NET 8.0 (Linux、macOS 和 Windows) |.NET](https://dotnet.microsoft.com/zh-tw/download/dotnet/8.0)

![下載 .NET 8.0 頁面](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image1.png)

- 點擊執行安裝檔。

![安裝流程畫面 1](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image2.png) ![安裝流程畫面 2](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image3.png) ![安裝流程畫面 3](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image4.png)

- 至選擇的安裝路徑確認是否有 `dotnet` 資料夾。

![確認 dotnet 資料夾](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image5.png)

- 確認 `dotnet` 版本是否安裝正確。

![確認 dotnet 版本](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image6.png)

#### 2\. 安裝 Python（若已安裝可省略）

- 至官網下載 Python： [https://www.python.org/downloads/](https://www.python.org/downloads/)

![Python 下載頁面 1](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image7.png) ![Python 下載頁面 2](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image8.png)

- 若下載時未勾選「Add python.exe to PATH」，可手動將路徑加入 `PATH` 。
- 確認安裝位置，於 CMD 執行：
```bash
where python
```

![where python 結果](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image9.png)

1. 新增安裝路徑至 `PATH` 。

![新增 PATH 步驟 1](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image10.png) ![新增 PATH 步驟 2](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image11.png) ![新增 PATH 步驟 3](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image12.png)

#### 3\. 安裝 pythonnet 套件

1. 確認 Python 環境是否安裝 `pip` ：
```bash
pip --version
```
- 未安裝請參考官網說明： [https://pip.pypa.io/en/stable/installation](https://pip.pypa.io/en/stable/installation)

![確認 pip 版本](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image13.png)

1. 安裝 `pythonnet` 套件：
```bash
pip install pythonnet
```

![安裝 pythonnet](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image14.png)

---

### 三、範例程式操作說明

### (一) Windows

#### 1\. 測試環境憑證匯入

![安裝憑證步驟 1](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image15.png)

- 安裝測試憑證在目前帳號上。

![安裝憑證步驟 2](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image16.png)

- 開放系統允許安裝更新憑證。

![安裝憑證步驟 3](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image17.png)

- 安裝更新憑證。

![安裝憑證步驟 4](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image18.png)

- 憑證安裝密碼： `yuanta` 。

![安裝憑證步驟 5](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image19.png)

- 憑證安裝作業。

![安裝憑證步驟 6](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image20.png)

- 完成憑證安裝作業。

![安裝憑證完成](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image21.png)

#### 2\. 主程式 YSendOrder.py

- 編輯與確認範例程式（元件引用路徑與範例程式路徑相同）。

![編輯範例程式](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image22.png)

- 使用 `load` 函數載入.NET Core / 8 執行環境：
```python
load("coreclr")
```
- 讓 Python 可使用.NET 類別（例如 `System.Collections.Generic.List` ），並設定 DLL 路徑，確保 Python 可找到同資料夾下的 `YuantaSparkAPI.dll` ：
```python
import clr
import System
clr.AddReference('System.Collections')
from System.Collections.Generic import List
sys.path.append(Path(pathlib.Path(__file__).parent.resolve()))
os.add_dll_directory(Path(pathlib.Path(__file__).parent.resolve()))
```
- 嘗試載入 `YuantaSparkAPI.dll` ：
```python
try:
    clr.AddReference("YuantaSparkAPI")
except Exception as e:
    print(f"Error loading YuantaSparkAPI: {e}")
```
- 點擊執行範例程式，即可執行連線、登入、下單並收到即時回報資訊。
- 請確保所有元件與主程式（ `YSendOrder.py` ）位於同一目錄或指定路徑。

![執行範例程式](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image23.png)

- 程式下單部分為 `send_stock_order()` ，可更換股票代碼與下單股數。詳細內容可參考 [國內證券下單](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E4%BA%A4%E6%98%93/%E5%9C%8B%E5%85%A7%E8%AD%89%E5%88%B8%E4%B8%8B%E5%96%AE/index.html) 。

![下單範例](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image24.png)

- 報價表部分為 `ReadWatchListAll_api()` ，提供股票價格等當前資訊，可自行增加股票名單。詳細內容可參考 [報價表查詢](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E8%A1%8C%E6%83%85/%E5%A0%B1%E5%83%B9%E8%A1%A8%E6%9F%A5%E8%A9%A2/index.html) 。

![報價表範例](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image25.png)

### (二) macOS

#### 主程式 YSendOrder.py

- 編輯與確認範例程式。

![macOS 編輯範例程式](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image26.png)

- 使用 `load` 函數載入.NET Core / 8 執行環境：
```python
load("coreclr")
```
- 讓 Python 可使用.NET 類別（例如 `System.Collections.Generic.List` ），並設定 DLL 路徑（macOS 需指定路徑），確保可找到 `YuantaSparkAPI.dll` ：
```python
import clr
import System
clr.AddReference('System.Collections')
from System.Collections.Generic import List
os.add_dll_directory(指定的絕對路徑)
```
- 嘗試載入 `YuantaSparkAPI.dll` ：
```python
try:
    clr.AddReference("YuantaSparkAPI")
except Exception as e:
    print(f"Error loading YuantaSparkAPI: {e}")
```
- 調整登入寫法：macOS 需指定讀取的憑證才能登入，路徑請填寫絕對路徑。其他欄位說明可參考 [登入](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E5%9F%BA%E7%A4%8E/%E7%99%BB%E5%85%A5/index.html) 。

![macOS 登入設定](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image27.png)

- 於範例程式資料夾開啟終端機畫面。

![開啟終端機](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image28.png)

> 語法執行範例程式：  
> \- macOS 環境需輸入 Python 版本（ `python3` ）。  
> \- 即可執行連線、登入、下單並收到即時回報資訊。  
> \- 請確保所有元件與主程式（ `YSendOrder.py` ）位於同一目錄或指定路徑。

![macOS 執行範例程式](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image29.png)

- 程式下單部分為 `send_stock_order()` ，可更換股票代碼與下單股數。詳細內容可參考 [國內證券下單](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E4%BA%A4%E6%98%93/%E5%9C%8B%E5%85%A7%E8%AD%89%E5%88%B8%E4%B8%8B%E5%96%AE/index.html) 。

![macOS 下單範例](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image30.png)

- 報價表部分為 `ReadWatchListAll_api()` ，提供股票價格等當前資訊，可自行增加股票名單。詳細內容可參考 [報價表查詢](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E8%A1%8C%E6%83%85/%E5%A0%B1%E5%83%B9%E8%A1%A8%E6%9F%A5%E8%A9%A2/index.html) 。

![macOS 報價表範例](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image31.png)

### 四、備註

#### 1\. 可能出現的錯誤

- 未安裝.NET SDK。

![未安裝 .NET SDK 錯誤](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image32.png)

- 安裝.NET SDK 8 以下版本也會出現錯誤，建議更新至 8.0 以上版本。

![.NET 版本過低錯誤](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image33.png)

- 此錯誤代表未安裝 `pythonnet` 套件，安裝方法可參考第三點第一項。

![未安裝 pythonnet 錯誤](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image34.png)

- 此錯誤代表 Python 無法正確找到.NET。可將 `C:\Program Files\dotnet` 資料夾刪除並重新安裝.NET 8 以上版本。

![無法找到 .NET 錯誤](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image35.png)

- 若仍無法解決，可於「編輯系統環境變數」中加入： `DOTNET_ROOT=C:\Program Files\dotnet\` 。

![環境變數步驟 1](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image36.png)

- 點擊環境變數

![環境變數步驟 2](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image37.png)

- 新增系統變數

![環境變數步驟 3](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image38.png)

- 加入 `DOTNET_ROOT=C:\Program Files\dotnet\` 後，點擊確定並重新執行程式。

![環境變數完成](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image39.png)

#### 2\. 方法參數型別

Python 語言的數字型別為 `int` （整數）、 `float` （浮點數）。故使用各項功能傳遞參數時，若非文件說明為浮點數型別，請以 `int` 型別傳遞。

例如現貨下單：

`bool SendStockOrder(string, List<StockOrder>, enumLangType)`

| Field Name | Description | Type | Size | Memo |
| --- | --- | --- | --- | --- |
| StockOrder | 下單物件 | Class |  |  |
| TradeKind | 交易性質 | short |  | `00`: 委託單； `03`: 改量； `04`: 取消； `07`: 改價 |
| Price | 委託價格 | double |  | 非限價請填 `0` |

![方法參數型別示意](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Windows%E3%80%81Mac%E7%B3%BB%E7%B5%B1/image40.png)
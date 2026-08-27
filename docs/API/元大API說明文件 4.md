---
title: "元大API說明文件"
source: "https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Linux%E7%B3%BB%E7%B5%B1/index.html"
author:
published:
created: 2026-08-27
description:
tags:
  - "clippings"
---
### YuantaSparkAPI – Linux環境建置(Ubuntu24.04)

1.系統套件更新:

開啟命令列 -> sudo apt update -> 輸入密碼

![開啟命令列 -> sudo apt update -> 輸入密碼](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Linux%E7%B3%BB%E7%B5%B1/image001.png)

開啟命令列 -> sudo apt upgrade -y

2.安裝dotnet sdk(24.04已不支援dotnet6)

```bash
sudo apt-get install dotnet-sdk-8.0
```

![開啟命令列 -> sudo apt update -> 輸入密碼](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Linux%E7%B3%BB%E7%B5%B1/image003.png)

3.安裝 python3 -> sudo apt install python3 (Ubuntu24.04已內建)

![開啟命令列 -> sudo apt update -> 輸入密碼](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Linux%E7%B3%BB%E7%B5%B1/image004.png)

4.安裝 python3套件管理工具 -> sudo apt install python3-pip -> Y

![開啟命令列 -> sudo apt update -> 輸入密碼](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Linux%E7%B3%BB%E7%B5%B1/image005.png)

5.確認安裝狀況 -> python3 –version / pip3 --version

![開啟命令列 -> sudo apt update -> 輸入密碼](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Linux%E7%B3%BB%E7%B5%B1/image006.png)

6.安裝pythonnet套件

因內建python的PEP668限制無法直接透過pip install安裝 pythonnet,需要先建立虛擬環境venv:

```bash
sudo apt install python3.12-venv

python3 -m venv myenv

source myenv/bin/activate
```

進入myenv環境

![開啟命令列 -> sudo apt update -> 輸入密碼](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Linux%E7%B3%BB%E7%B5%B1/image007.png)

安裝pythonnet套件 pip install pythonnet

![開啟命令列 -> sudo apt update -> 輸入密碼](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Linux%E7%B3%BB%E7%B5%B1/image008.png)

7.執行python進行測試

![開啟命令列 -> sudo apt update -> 輸入密碼](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/2.Python%E8%A8%AD%E5%AE%9A/Linux%E7%B3%BB%E7%B5%B1/image009.png)

### 版本

```
Python 3.12.3
Pythonnet 3.0.5
Dotnet 8.0.112
Openssl 3.0.13
```
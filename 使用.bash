@echo off

echo 检查Python是否已安装...
where python3 >nul 2>nul
if errorlevel 1 (
    echo 正在安装Python...
    powershell -Command "Invoke-WebRequest https://mirrors.huaweicloud.com/python/3.9.9/python-3.9.9.exe -OutFile python-installer.exe"
    python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python-installer.exe
) else (
    echo Python已安装
)

echo 检查所需库是否已安装...
python3 -m pip freeze > installed_libraries.txt
findstr /L /I /G:requirements.txt installed_libraries.txt >nul
if errorlevel 1 (
    echo 正在安装所需的库...
    python3 -m pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
) else (
    echo 所需库已安装
)

echo 安装完成，正在运行 gui.py
python gui.py
exit
@echo on
chcp 65001

echo Checking if Python is installed...
where python >nul 2>nul
if errorlevel 1 (
echo Installing Python...
powershell -Command "Invoke-WebRequest https://mirrors.huaweicloud.com/python/3.9.9/python-3.9.9.exe -OutFile python-installer.exe"
python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
del python-installer.exe
) else (
echo Python is already installed
)
pause

echo Checking if required libraries are installed...
python -m pip freeze > installed_libraries.txt
findstr /L /I /G:requirements.txt installed_libraries.txt >nul
if errorlevel 1 (
echo Installing required libraries...
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
) else (
echo Required libraries are already installed
)
pause

echo Checking if "照片" folder exists...
if not exist "照片" (
echo Creating "照片" folder...
mkdir "照片"
) else (
echo "照片" folder already exists
)

echo Installation completed, launching gui.py
python gui.py
pause

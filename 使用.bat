@echo on
chcp 65001

echo 检查环境搭建...
where python >nul 2>nul
if errorlevel 1 (
echo 安装 Python...
powershell -Command "Invoke-WebRequest https://mirrors.huaweicloud.com/python/3.9.9/python-3.9.9.exe -OutFile python-installer.exe"
python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
del python-installer.exe
) else (
echo Python 已安装
)

python -m pip freeze > installed_libraries.txt
findstr /L /I /G:requirements.txt installed_libraries.txt >nul
if errorlevel 1 (
echo 安装python环境...
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
) else (
echo python环境已安装
)

where git >nul 2>nul
if errorlevel 1 (
    echo 安装 Git...
    powershell -Command "Invoke-WebRequest https://registry.npmmirror.com/-/binary/git-for-windows/v2.41.0.windows.1/Git-2.41.0-64-bit.exe -OutFile git-installer.exe"
    git-installer.exe /VERYSILENT
    del git-installer.exe
) else (
    echo Git 已安装！
)

echo 检查文件夹是否完整...
if not exist "照片" (
echo 新建 "照片" 文件夹...
mkdir "照片"
) else (
echo "照片" 文件夹检查无误！
)

if not exist "照片改" (
echo 新建 "照片改" 文件夹...
mkdir "照片改"
) else (
echo "照片改" 文件夹检查无误！
)

if not exist "头像" (
echo 新建 "头像" 文件夹...
mkdir "头像"
) else (
echo "头像" 文件夹检查无误！
)

if not exist "原头像" (
echo 新建 "原头像" 文件夹...
mkdir "原头像"
) else (
echo "原头像" 文件夹检查无误！
)

if not exist "排班表" (
echo 新建 "排班表" 文件夹...
mkdir "排班表"
) else (
echo "排班表" 文件夹检查无误！
)

if not exist "表格" (
echo Creating "表格" folder...
mkdir "表格"
) else (
echo "表格" 文件夹检查无误！
)

if not exist "桃花榜" (
echo 新建 "桃花榜" 文件夹...
mkdir "桃花榜"
) else (
echo "桃花榜" 文件夹检查无误！
)

echo 检查是否需要初始化...
if not exist HRTable\.git (
    echo 正在初始化...
    git clone https://gitee.com/prayerz/HRTable.git HRTable
) else (
    echo 无需初始化！
)
echo 更新中...
git pull
echo 更新完成！


echo 全部检查无误，开始主程序！
python gui.py

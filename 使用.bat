@echo on
chcp 65001

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

echo 更新中...
git pull
echo 更新完成！

echo 开始主程序！
python gui.py

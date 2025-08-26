@echo off
chcp 65001 >nul
echo 🗄️  数据库清空工具
echo ================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python，请先安装Python
    pause
    exit /b 1
)

echo ✅ Python已安装
echo.

REM 检查数据库文件是否存在
if not exist "tasks.db" (
    echo ❌ 错误：数据库文件 tasks.db 不存在
    echo 请确保在正确的目录下运行此脚本
    pause
    exit /b 1
)

echo 📁 发现数据库文件：tasks.db
echo.

REM 询问是否备份
set /p backup_choice="是否在清空前备份数据库？(y/N): "
if /i "%backup_choice%"=="y" (
    echo 💾 正在备份数据库...
    copy "tasks.db" "tasks.db.backup.%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
    if errorlevel 1 (
        echo ❌ 备份失败
    ) else (
        echo ✅ 备份完成
    )
    echo.
)

REM 确认清空操作
echo ⚠️  警告：此操作将清空数据库中的所有数据！
set /p confirm="确认要清空数据库吗？输入 'YES' 确认: "

if /i not "%confirm%"=="YES" (
    echo 操作已取消
    pause
    exit /b 0
)

echo.
echo 🗑️  正在清空数据库...

REM 执行Python清空脚本
python quick_clear_db.py

if errorlevel 1 (
    echo.
    echo 💥 数据库清空失败！
    pause
    exit /b 1
)

echo.
echo 🎉 数据库清空成功！
echo.
pause

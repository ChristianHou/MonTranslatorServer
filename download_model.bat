@echo off
chcp 65001 >nul
echo 🤖 蒙古语翻译模型下载工具
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

REM 检查模型是否已存在
if exist "cache\Billyyy_mn_nllb_1.3B_continue" (
    echo ⚠️  模型已存在，是否重新下载？
    set /p choice="输入 'y' 重新下载，其他键跳过: "
    if /i not "%choice%"=="y" (
        echo 跳过下载
        pause
        exit /b 0
    )
)

echo 🚀 开始下载蒙古语翻译模型...
echo 📥 模型: Billyyy/mn_nllb_1.3B_continue
echo 📁 下载目录: ./cache
echo.

REM 执行Python下载脚本
python quick_download_model.py

if errorlevel 1 (
    echo.
    echo 💥 模型下载失败！
    pause
    exit /b 1
)

echo.
echo 🎉 模型下载完成！
echo.
echo 📋 下一步操作:
echo 1. 重启翻译服务器
echo 2. 测试蒙古语翻译功能
echo.
pause

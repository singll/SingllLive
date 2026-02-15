@echo off
chcp 65001 >nul
title [直播] 程序员深夜电台
echo ========================================
echo   程序员深夜电台 - 启动中...
echo ========================================
echo.

:: 导航到项目根目录 (start.bat 在 scripts/windows/ 下，需要往上三级)
cd /d "%~dp0..\..\."

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python, 请先安装 Python 3.x
    pause
    exit /b 1
)

:: 升级 pip (可选但推荐，确保兼容性)
echo 检查 pip 版本...
python -m pip install --upgrade pip -q >nul 2>&1

:: 检查依赖
python -c "import PIL, aiohttp, blivedm" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    echo （使用预编译的 wheel 包，避免编译问题）
    pip install --prefer-binary -r requirements.txt
    if errorlevel 1 (
        echo 错误: 依赖安装失败
        echo.
        echo 解决方案:
        echo 1. 确保 Python 3.8+ 已正确安装
        echo 2. 尝试手动安装: pip install --prefer-binary blivedm bilibili-api-python aiohttp Pillow
        echo 3. 或升级 pip: python -m pip install --upgrade pip
        pause
        exit /b 1
    )
    echo 依赖安装完成！
    echo.
)

:: 检查配置
if not exist "config.ini" (
    echo 错误: config.ini 不存在
    echo 请复制 config.ini.example 为 config.ini 并填入实际配置
    pause
    exit /b 1
)

:: 启动
python cyber_live.py
pause

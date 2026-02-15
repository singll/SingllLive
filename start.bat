@echo off
chcp 65001 >nul
title [直播] 程序员深夜电台
echo ========================================
echo   程序员深夜电台 - 启动中...
echo ========================================
echo.

cd /d "%~dp0"

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python, 请先安装 Python 3.x
    pause
    exit /b 1
)

:: 检查依赖
python -c "import PIL, aiohttp, blivedm" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
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

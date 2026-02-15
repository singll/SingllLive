@echo off
chcp 65001 >nul
title [直播] 程序员深夜电台
echo ========================================
echo   程序员深夜电台 - 启动中...
echo ========================================
echo.

:: 确保在项目根目录
cd /d "%~dp0"

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

    :: 尝试方案 1: --only-binary :all: (最严格，只用预编译wheels)
    pip install --only-binary :all: -r requirements.txt
    if errorlevel 1 (
        echo.
        echo 尝试方案 2: 跳过 brotli，使用备用依赖集...
        :: brotli 是可选的，可以用其他压缩库替代
        pip install --prefer-binary blivedm bilibili-api-python aiohttp>=3.8.0 Pillow>=9.0.0
        if errorlevel 1 (
            echo.
            echo 错误: 依赖安装失败
            echo.
            echo 解决方案:
            echo 1. 确保 Python 3.8+ 已正确安装 (当前:
            python --version
            echo.
            echo 2. 尝试手动升级 pip 到最新版本:
            echo    python -m pip install --upgrade pip
            echo.
            echo 3. 如果问题仍存在，使用此命令（跳过 brotli）:
            echo    pip install --prefer-binary --no-binary brotli bilibili-api-python aiohttp Pillow
            echo.
            echo 4. 或从预编译轮子源安装:
            echo    pip install -i https://pypi.python.org/simple --prefer-binary -r requirements.txt
            pause
            exit /b 1
        )
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

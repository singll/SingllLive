@echo off
chcp 65001 >nul
title [直播] 程序员深夜电台
echo ========================================
echo   程序员深夜电台 - 启动中...
echo ========================================
echo.
echo 注意: brotli 已被禁用以避免 Python 3.14+ 兼容性问题
echo 详见: BROTLI_FIX.md
echo.

:: 确保在项目根目录（start.bat 所在目录）
cd /d "%~dp0"
echo 当前工作目录: %cd%
echo.

:: 验证必要的文件是否存在
if not exist "cyber_live.py" (
    echo 错误: 未找到 cyber_live.py，可能不在项目根目录
    echo 当前目录: %cd%
    echo.
    echo 请确保 start.bat 与 cyber_live.py 在同一目录
    pause
    exit /b 1
)

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
    echo.

    :: 尝试方案 1: --prefer-binary (推荐，优先使用预编译包)
    pip install --prefer-binary -r requirements.txt
    if errorlevel 1 (
        echo.
        echo 尝试方案 2: --only-binary :all: (最严格，仅使用预编译包)
        pip install --only-binary :all: -r requirements.txt
        if errorlevel 1 (
            echo.
            echo 错误: 依赖安装失败
            echo.
            echo 解决方案:
            echo 1. 确保 Python 3.8+ 已正确安装 (当前:
            python --version
            echo.
            echo 2. 卸载 brotli (如果已安装，会导致兼容性问题):
            echo    pip uninstall brotli -y
            echo.
            echo 3. 尝试手动升级 pip 到最新版本:
            echo    python -m pip install --upgrade pip
            echo.
            echo 4. 重新安装依赖:
            echo    pip install --prefer-binary -r requirements.txt
            echo.
            echo 注意: requirements.txt 中已移除 brotli 以避免 Python 3.14+ 兼容性问题
            pause
            exit /b 1
        )
    )
    echo 依赖安装完成！
    echo.
)

:: 检查配置
echo.
echo 检查配置文件...
echo 在以下位置寻找 config.ini:
echo   1. %cd%\config.ini
echo   2. %cd%\config\config.ini
echo.

if not exist "config.ini" (
    if not exist "config\config.ini" (
        if exist "config\config.ini.example" (
            echo 警告: config.ini 不存在
            echo.
            echo 请执行以下命令复制配置文件:
            echo   copy config\config.ini.example config.ini
            echo.
            echo 然后编辑 config.ini，填入你的 B站直播间号、UID 等信息
            echo.
            echo 当前目录: %cd%
            echo 模板文件: %cd%\config\config.ini.example
            echo.
        ) else (
            echo 错误: 找不到 config.ini 和 config\config.ini.example
            echo 当前目录: %cd%
            echo.
        )
        pause
        exit /b 1
    ) else (
        echo ✓ 在 config\config.ini 找到配置文件
    )
) else (
    echo ✓ 配置文件已找到: %cd%\config.ini
)
echo.

:: 启动
python cyber_live.py
pause

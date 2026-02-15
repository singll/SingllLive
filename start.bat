@echo off
chcp 65001 >nul
title [直播] 程序员深夜电台
echo ========================================
echo   程序员深夜电台 - 启动中...
echo ========================================
echo.
echo 注意:
echo   - brotli 已被禁用以避免 Python 3.14+ 兼容性问题
echo   - blivedm 从 GitHub 安装以获取正确的库版本
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

    :: 尝试方案 1: --prefer-binary (推荐，GitHub 部分包会从源码构建)
    pip install --prefer-binary -r requirements.txt
    if errorlevel 1 (
        echo.
        echo 尝试方案 2: 重新升级 pip 并再试一次
        python -m pip install --upgrade pip
        pip install --prefer-binary -r requirements.txt
        if errorlevel 1 (
            echo.
            echo 错误: 依赖安装失败
            echo.
            echo 解决方案:
            echo 1. 确保 Python 3.8+ 和 Git 已正确安装
            python --version
            git --version
            echo.
            echo 2. 卸载 brotli 如果已安装，会导致兼容性问题
            echo    pip uninstall brotli -y
            echo.
            echo 3. 尝试手动安装 (指定详细输出了解错误)
            echo    pip install --prefer-binary -r requirements.txt -v
            echo.
            echo 4. 检查网络连接，确保能访问 GitHub.com
            echo.
            echo 注意:
            echo   - requirements.txt 中已移除 brotli 以避免 Python 3.14+ 兼容性问题
            echo   - blivedm 从 GitHub 安装，需要网络连接和 Git
            echo   - 如果 GitHub 连接慢，可自行从 GitHub 克隆后离线安装
            echo      git clone https://github.com/xfgryujk/blivedm.git
            echo      pip install ./blivedm
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
        echo 已找到配置文件: config\config.ini
    )
) else (
    echo 已找到配置文件: %cd%\config.ini
)
echo.

:: 启动
python cyber_live.py
pause

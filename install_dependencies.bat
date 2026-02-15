@echo off
chcp 65001 >nul
title SingllLive 依赖安装工具
echo ========================================
echo   SingllLive - Python 依赖安装
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python 3.8+
    pause
    exit /b 1
)

echo 升级 pip 到最新版本...
python -m pip install --upgrade pip setuptools wheel -q >nul 2>&1
if errorlevel 1 (
    echo 警告: pip 升级失败，但继续进行...
)

echo.
echo 尝试方案 1: 直接安装（仅预编译 wheels）...
pip install --only-binary :all: blivedm bilibili-api-python aiohttp>=3.8.0 Pillow>=9.0.0

if errorlevel 1 (
    echo.
    echo 尝试方案 2: 使用 --prefer-binary（允许但不优先编译）...
    pip install --prefer-binary blivedm bilibili-api-python aiohttp>=3.8.0 Pillow>=9.0.0

    if errorlevel 1 (
        echo.
        echo 尝试方案 3: 跳过 brotli，使用纯 Python 依赖...
        pip install --prefer-binary --no-cache-dir --no-binary brotli^
            blivedm bilibili-api-python aiohttp>=3.8.0 Pillow>=9.0.0

        if errorlevel 1 (
            echo.
            echo ========================================
            echo   安装失败 - 需要手动干预
            echo ========================================
            echo.
            echo 可能的原因:
            echo 1. Python 版本不符合（需要 3.8+）
            echo 2. 网络连接问题
            echo 3. brotli 包在你的系统上无预编译版本
            echo.
            echo 解决方案:
            echo.
            echo 方案 A: 安装 Visual C++ Build Tools
            echo   下载: https://visualstudio.microsoft.com/visual-cpp-build-tools/
            echo.
            echo 方案 B: 使用预编译的 brotli wheel
            echo   1. 从以下链接下载 brotli wheel:
            echo      https://www.lfd.uci.edu/~gohlke/pythonlibs/#brotli
            echo   2. 运行: pip install brotli-xxx.whl
            echo   3. 然后再运行此脚本
            echo.
            echo 方案 C: 跳过 brotli 依赖
            echo   编辑 requirements.txt，删除 brotli 相关行
            echo.
            pause
            exit /b 1
        )
    )
)

echo.
echo ========================================
echo   依赖安装完成！
echo ========================================
echo.
echo 验证安装...
python -c "import PIL, aiohttp, blivedm; print('✓ 所有核心依赖已安装')"
if errorlevel 1 (
    echo.
    echo 警告: 某些依赖验证失败！
    pause
    exit /b 1
)

echo.
echo 现在可以运行: start.bat
echo.
pause

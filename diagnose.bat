@echo off
chcp 65001 >nul
title SingllLive 路径诊断工具
echo.
echo ========================================
echo   SingllLive - 路径诊断工具
echo ========================================
echo.

:: 获取脚本所在目录
cd /d "%~dp0"
set PROJECT_ROOT=%cd%

echo 诊断信息:
echo.

:: 1. Python 版本
echo [1] Python 版本
python --version
if errorlevel 1 (
    echo ✗ 未找到 Python
) else (
    echo ✓ Python 已安装
)
echo.

:: 2. 工作目录
echo [2] 当前工作目录
echo %PROJECT_ROOT%
echo.

:: 3. 关键文件检查
echo [3] 关键文件检查
echo.
if exist "cyber_live.py" (
    echo ✓ cyber_live.py 存在
) else (
    echo ✗ cyber_live.py 不存在
)

if exist "start.bat" (
    echo ✓ start.bat 存在
) else (
    echo ✗ start.bat 不存在
)

if exist "config\config.ini.example" (
    echo ✓ config\config.ini.example 存在
) else (
    echo ✗ config\config.ini.example 不存在
)

if exist "config.ini" (
    echo ✓ config.ini 存在（项目根目录）
) else (
    echo ✗ config.ini 不存在（项目根目录）
)

if exist "config\config.ini" (
    echo ✓ config\config.ini 存在（config 子目录）
) else (
    echo ✗ config\config.ini 不存在（config 子目录）
)
echo.

:: 4. 依赖检查
echo [4] Python 依赖检查
python -c "import PIL; print('✓ Pillow 已安装')" 2>nul
if errorlevel 1 echo ✗ Pillow 未安装

python -c "import aiohttp; print('✓ aiohttp 已安装')" 2>nul
if errorlevel 1 echo ✗ aiohttp 未安装

python -c "import blivedm; print('✓ blivedm 已安装')" 2>nul
if errorlevel 1 echo ✗ blivedm 未安装
echo.

:: 5. 建议
echo [5] 诊断建议
echo.
if not exist "config.ini" (
    if exist "config\config.ini.example" (
        echo ① 配置文件缺失！请执行:
        echo    copy config\config.ini.example config.ini
        echo.
    )
)

if not exist "cyber_live.py" (
    echo ② 找不到 cyber_live.py！
    echo    确保 start.bat 和 cyber_live.py 在同一目录
    echo    当前目录: %PROJECT_ROOT%
    echo.
)

echo ========================================
echo 诊断完成
echo ========================================
pause

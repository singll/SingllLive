@echo off
chcp 65001 >nul
echo 正在关闭直播控制系统...

:: 查找并终止 cyber_live.py 进程
for /f "tokens=2" %%i in ('tasklist /v /fi "IMAGENAME eq python.exe" ^| findstr "cyber_live"') do (
    taskkill /pid %%i /f >nul 2>&1
)

:: 备选: 如果上面没找到, 按窗口标题查找
taskkill /fi "WINDOWTITLE eq [直播]*" /f >nul 2>&1

echo 直播控制系统已关闭
echo.
echo 注意: VLC 和 OBS 需要手动关闭 (或使用下面的命令)
echo   关闭 VLC:  taskkill /im vlc.exe /f
echo   关闭 OBS:  taskkill /im obs64.exe /f
echo.
pause

# 极客工程师直播间 - 完整运营方案 v3.0

> 「一个程序员的深夜电台，代码、音乐交织的赛博空间」

---

## 目录

- [一、主播人设](#一主播人设)
- [二、直播内容规划](#二直播内容规划)
- [三、直播间布局与素材](#三直播间布局与素材)
- [四、OBS 完整配置](#四obs-完整配置)
- [五、挂机直播系统（核心）](#五挂机直播系统核心)
- [六、弹幕点歌系统](#六弹幕点歌系统)
- [七、弹幕命令系统（Python 机器人）](#七弹幕命令系统python-机器人)
- [八、PK 系统](#八pk-系统)
- [九、远程收音方案](#九远程收音方案)
- [十、B区信息面板](#十b区信息面板)
- [十一、一键启动与自动化](#十一一键启动与自动化)
- [十二、开播检查清单](#十二开播检查清单)
- [十三、推广与运营](#十三推广与运营)
- [十四、完整文件清单](#十四完整文件清单)

---

## 一、主播人设

### 1.1 真实身份

| 项目 | 内容 |
|------|------|
| **身份** | 科技公司工程师 |
| **领域** | 代码开发 / AI / 网络安全 / 运维 |
| **爱好** | 听歌、唱歌、折腾技术 |
| **直播风格** | 技术极客 + 深夜电台 + 偶尔真人互动 |

### 1.2 人设标签

```
#程序员 #工程师 #深夜电台 #技术宅 #赛博朋克 #音乐
```

### 1.3 直播间 Slogan

推荐：
- 「代码敲累了，来听首歌」
- 「程序员的深夜电台」
- 「Debug 人生，Play 音乐」

### 1.4 形象呈现

| 模式 | 说明 |
|------|------|
| **挂机模式** | VTS 虚拟形象 + 循环播放歌曲，全自动无人值守 |
| **互动模式** | 远程连入说话、回复弹幕、点歌互动 |
| **真人出镜** | 偶尔开摄像头唱歌/聊天（后期粉丝多了再做） |

---

## 二、直播内容规划

### 2.1 内容分类

| 类型 | 频率 | 内容 | 时长 |
|------|------|------|------|
| **歌曲轮播（主打）** | 日常 | 挂机播放喜欢的女主播翻唱作品 | 7×24 |
| **深夜电台** | 每晚 | 歌曲 + 赛博氛围，陪伴写代码/学习 | 22:00-02:00 |
| **点歌互动** | 有空时 | 弹幕点歌，聊天互动 | 1-2h |
| **技术折腾** | 不定期 | 代码、Homelab、AI 实验 | 1-2h |
| **唱歌直播** | 偶尔 | 真人出镜唱歌 | 1-2h |

### 2.2 日常时间表（挂机模式）

```
┌────────────────────────────────────────────────────────────┐
│  时段          内容                   风格                  │
├────────────────────────────────────────────────────────────┤
│  全天          女主播翻唱歌曲轮播      默认模式              │
│  有空时        远程连入互动           弹幕点歌/聊天          │
│  22:00-02:00   深夜电台(氛围加强)     主打女主播翻唱歌曲     │
└────────────────────────────────────────────────────────────┘
```

> 核心理念：**以挂机轮播为主，人在时就互动，不在时全自动运行。**

### 2.3 特色栏目（后续发展）

| 栏目名 | 时间 | 内容 |
|--------|------|------|
| 「深夜点歌台」 | 有空的晚上 | 弹幕点歌，聊天互动 |
| 「代码与咖啡」 | 不定期 | 边写代码边放歌，展示技术项目 |
| 「周末唱歌」 | 不定期 | 真人出镜唱几首 |

---

## 三、直播间布局与素材

### 3.1 三区划分（1920×1080）

**核心设计：A区屏幕精确 16:9 (1344×756)，播放 16:9 视频零黑边。**

> 为什么是 1344×756？
> - 16:9 视频在非 16:9 容器中播放时，OBS 默认不拉伸，会产生黑边
> - 1344÷756 = 1.778 = 精确 16:9，与 1920×1080 同比例
> - 右侧保留 532px 给信息面板和虚拟人，比例协调
> - 显示器底部到底栏之间 208px 可选放音频可视化

```
┌────────────────────────────────┬──────────────┐
│                                │              │
│      A区 主内容区 (16:9)        │  B区 信息面板 │
│      屏幕: 1344×756            │  (532×488)   │
│      (精确 16:9, 零黑边)        │  终端风格     │
│                                ├──────────────┤
├────────────────────────────────┤              │
│  [显示器支架 + 可选音频可视化]    │  C区 虚拟人   │
│  (1364×200 可用空间)            │  (532×488)   │
│                                │  房间场景     │
├────────────────────────────────┴──────────────┤
│              底部信息条 (1920×80)                │
└────────────────────────────────────────────────┘
```

### 3.2 素材文件

所有素材源文件位于 `assets/` 目录下：

| 文件 | 位置 | 用途 |
|------|------|------|
| `background.svg` | `assets/designs/` | 赛博风格深色背景（网格+光晕+电路纹理） |
| `frame-overlay.svg` | `assets/designs/` | 带显示器/终端/房间场景的边框装饰层 |

**SVG 转 PNG 方法：**

两个 SVG 文件已设置 `viewBox="0 0 1920 1080"`，在线工具可正确渲染。

```batch
:: 方法1: 使用 Chrome 浏览器（推荐，无需安装额外软件）
:: 1. 用 Chrome 打开 SVG 文件
:: 2. F12 → Console 中检查画面是否填满 1920x1080
:: 3. Ctrl+Shift+P → "Capture full size screenshot"
:: 4. 或使用 Chrome 扩展 "SVG Export" 直接导出 PNG

:: 方法2: 在线工具 cloudconvert.com（推荐，支持设定分辨率）
:: 上传 SVG → 选择 PNG → 设置 1920x1080 → 转换下载

:: 方法3: 安装 Inkscape 后命令行转换
:: 下载 https://inkscape.org/ 安装后：
"C:\Program Files\Inkscape\bin\inkscape.exe" assets\designs\background.svg --export-type=png --export-width=1920 --export-height=1080 -o assets\background.png
"C:\Program Files\Inkscape\bin\inkscape.exe" assets\designs\frame-overlay.svg --export-type=png --export-width=1920 --export-height=1080 -o assets\frame-overlay.png
```

> 注意：`frame-overlay.png` 不需要透明背景，因为它作为**中间装饰层**使用（见 4.1 图层方案说明），各区域的实际内容（视频、面板、虚拟人）会在上层覆盖。

---

## 四、OBS 完整配置

### 4.1 图层方案说明

**frame-overlay 应作为中间层（装饰层），而非最顶层。**

分析 frame-overlay 的内部结构：
- A区：显示器边框是不透明的深色金属质感，但屏幕区域（18,18 ~ 1362,774）是透明的
- B区：终端窗口有不透明的深色背景 + 标题栏（红黄绿按钮）
- C区：房间场景完全不透明（墙壁、桌子、键盘、鼠标、咖啡杯）

如果把 frame-overlay 放在最顶层，B区和C区的不透明内容会**完全遮挡**下面的 HTML 面板和 VTube Studio。

正确的做法是：frame-overlay 放在 background 上面、实际内容源下面。这样：
- 显示器边框围住 A区视频
- 终端标题栏显示在 HTML 面板上方
- 房间场景（桌子键盘等）出现在虚拟人身后，角色看起来像坐在桌前

### 4.2 场景源层级（从下到上）

```
场景：「主直播-音乐」
│
├─ [1] 背景图 - background.png          ← 最底层
│       类型: 图像
│       位置: (0, 0) 全屏 1920×1080
│
├─ [2] 边框装饰 - frame-overlay.png     ← 装饰层（显示器框+终端框+房间场景）
│       类型: 图像
│       位置: (0, 0) 全屏 1920×1080
│       说明: 提供显示器边框、终端标题栏、房间桌面键盘等装饰
│
├─ [3] A区-媒体源（歌曲视频）
│       类型: VLC视频源 或 窗口捕获
│       位置: (18, 18)
│       大小: 1344×756
│       说明: 精确16:9，嵌入显示器屏幕区域，零黑边
│
├─ [4] B区-浏览器源（信息面板）
│       类型: 浏览器
│       URL: file:///D:/live/panels/terminal-panel.html
│       位置: (1385, 45)
│       大小: 522×440
│       说明: 嵌入终端内容区，标题栏(红黄绿按钮)从下层透出
│
├─ [5] C区-VTS 窗口捕获（虚拟人）
│       类型: 窗口捕获
│       窗口: [VTube Studio]
│       位置: (1380, 504)
│       大小: 532×488
│       滤镜: 色度键（去绿幕背景）
│       说明: 角色出现在房间场景上方，看起来坐在桌前
│
└─ [6] 底部滚动字幕 - 文本(GDI+)
        位置: (20, 1015)
        大小: 1880×50
        内容来源: 从文件读取 D:\live\data\ticker.txt
        滚动速度: 80
        字体: Consolas, 14px, #888888
```

**视觉效果示意：**

```
┌──────────────────────────────────────────────────────────────┐
│ background.png 赛博背景(可见于边角和A区下方空间)                │
│  ┌─[显示器边框从frame-overlay透出]──┐ ┌─[终端标题栏透出]──┐  │
│  │                                  │ │● ● ● bash:~/live │  │
│  │     [3] VLC 歌曲视频 (16:9)      │ │                   │  │
│  │     位于显示器屏幕内，零黑边      │ │ [4] HTML信息面板   │  │
│  │     1344×756                    │ │  当前播放/队列      │  │
│  └──────────────────────────────────┘ ├───────────────────┤  │
│  [显示器支架]                         │ [房间场景从下层透出] │  │
│  [A区下方: 可选音频可视化/氛围]        │ [5] VTube Studio   │  │
│                                      │  角色坐在桌前       │  │
│                                      └───────────────────┘  │
│  [$  ./broadcast.sh --mode=live           底部字幕滚动     ]  │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 A区媒体源详细配置

**方案 A：OBS VLC 视频源（推荐 - 最简单）**

OBS 原生支持 VLC 视频源（需安装 VLC）：

```
1. 添加源 → VLC 视频源
2. 播放列表：添加 D:\live\songs\ 下所有视频文件
3. 播放行为：循环 ✓ / 随机 ✓（可选）
4. 可见性切换：自动播放
```

优点：OBS 内置管理，无需外部播放器窗口。

**方案 B：VLC 独立窗口 + 窗口捕获**

```
1. VLC 播放器打开歌曲目录，设置循环播放
2. OBS 添加 → 窗口捕获 → 选择 VLC 窗口
3. 裁剪掉 VLC 的标题栏和控制条
```

优点：可以通过脚本控制 VLC 播放（点歌系统需要）。

**推荐：方案 B**，因为弹幕点歌系统需要通过命令行控制播放器。

### 4.3 音频输出

```
OBS → 设置 → 音频：
  桌面音频：默认（捕获 VLC 播放的歌曲声音）
  麦克风：VoiceMeeter Output（用于远程说话，见第九章）
```

### 4.4 虚拟摄像头输出

由于粉丝数不达标无法直接 OBS 推流，使用 OBS 虚拟摄像头：

```
1. OBS → 工具 → 虚拟摄像头 → 启动
2. 直播姬 → 选择摄像头 → OBS Virtual Camera
3. 直播姬 → 开始直播
```

> 后续粉丝数达标后可直接用 OBS 推流到 B站 RTMP 地址，画质更好。

---

## 五、挂机直播系统（核心）

这是日常运行的核心模式——无人值守自动播放女主播的歌曲作品。

### 5.1 歌曲库准备

```
D:\live\songs\
├─ 恋人心.mp4
├─ 起风了.mp4
├─ 晴天.mp4
├─ 告白气球.mp4
├─ 红色高跟鞋.mp4
├─ 我的秘密.mp4
└─ ...（从录播中剪辑出的单曲）
```

**命名规则：** `歌名.mp4`（纯歌名，方便弹幕匹配）

**从录播中剪辑歌曲：**

```batch
:: 使用 ffmpeg 从录播中剪辑单首歌曲
:: 格式: ffmpeg -i 录播文件 -ss 开始时间 -to 结束时间 -c copy 输出文件
ffmpeg -i "2024-01-15-直播录像.flv" -ss 00:15:30 -to 00:20:45 -c copy "恋人心.mp4"
ffmpeg -i "2024-01-15-直播录像.flv" -ss 00:25:10 -to 00:30:00 -c copy "起风了.mp4"
```

### 5.2 VLC 自动循环播放

创建 `D:\live\scripts\auto_play.bat`：

```batch
@echo off
chcp 65001 >nul
title [直播] 歌曲自动轮播

set "VLC=C:\Program Files\VideoLAN\VLC\vlc.exe"
set "SONGDIR=D:\live\songs"
set "NOWPLAY=D:\live\data\now_playing.txt"

:: 启动 VLC 循环播放整个目录
:: --loop: 列表循环  --random: 随机播放  --qt-start-minimized: 最小化启动
:: --one-instance: 单实例模式（后续点歌命令会控制这个实例）
start "" "%VLC%" "%SONGDIR%" --loop --random --one-instance --no-video-title-show

echo 歌曲轮播已启动
echo 播放目录: %SONGDIR%
```

### 5.3 VLC Web 接口（弹幕控制的关键）

VLC 内置 HTTP 接口，开启后可以通过 HTTP 请求控制播放、切歌、加入队列。这是实现弹幕点歌的技术基础。

**开启 VLC HTTP 接口：**

```
VLC → 工具 → 首选项 → 显示设置「全部」
→ 接口 → 主接口 → 勾选「Web」
→ 接口 → 主接口 → Lua → Lua HTTP
  → 密码设置为: 123456（随意设，本地使用）
→ 保存并重启 VLC
```

或通过命令行启动时直接带参数：

```batch
:: auto_play.bat（增强版，带 HTTP 接口）
@echo off
chcp 65001 >nul

set "VLC=C:\Program Files\VideoLAN\VLC\vlc.exe"
set "SONGDIR=D:\live\songs"

start "" "%VLC%" "%SONGDIR%" ^
    --loop --random ^
    --one-instance ^
    --no-video-title-show ^
    --extraintf=http ^
    --http-host=127.0.0.1 ^
    --http-port=9090 ^
    --http-password=123456

echo VLC 歌曲轮播已启动（HTTP 接口: http://127.0.0.1:9090）
```

**VLC HTTP 接口常用命令（浏览器或 curl 测试）：**

```
播放/暂停：  http://127.0.0.1:9090/requests/status.xml?command=pl_pause
下一首：    http://127.0.0.1:9090/requests/status.xml?command=pl_next
上一首：    http://127.0.0.1:9090/requests/status.xml?command=pl_previous
停止：      http://127.0.0.1:9090/requests/status.xml?command=pl_stop
当前状态：  http://127.0.0.1:9090/requests/status.xml
播放列表：  http://127.0.0.1:9090/requests/playlist.xml
添加并播放：http://127.0.0.1:9090/requests/status.xml?command=in_play&input=D:\live\songs\恋人心.mp4
加入队列：  http://127.0.0.1:9090/requests/status.xml?command=in_enqueue&input=D:\live\songs\恋人心.mp4
```

> 所有请求需要 HTTP Basic Auth，用户名留空，密码 `123456`。

### 5.4 Watchdog 看门狗（防止 VLC 崩溃）

创建 `D:\live\scripts\watchdog.bat`：

```batch
@echo off
chcp 65001 >nul
title [直播] 看门狗

:loop
:: 检查 VLC 是否在运行
tasklist /FI "IMAGENAME eq vlc.exe" | find "vlc.exe" >nul
if errorlevel 1 (
    echo [%date% %time%] VLC 已退出，正在重启...
    echo [%date% %time%] VLC 重启 >> D:\live\data\watchdog.log
    call D:\live\scripts\auto_play.bat
    timeout /t 5 >nul
)

:: 每 30 秒检查一次
timeout /t 30 >nul
goto loop
```

### 5.5 当前播放歌名同步

VLC HTTP 接口可以获取当前播放文件名。创建一个定时脚本来更新 `now_playing.txt`。

创建 `D:\live\scripts\sync_now_playing.bat`：

```batch
@echo off
chcp 65001 >nul
title [直播] 歌名同步

:loop
:: 通过 VLC HTTP 接口获取当前播放文件名
:: 使用 curl 获取状态（需要安装 curl，Win10 自带）
curl -s -u :123456 "http://127.0.0.1:9090/requests/status.xml" > D:\live\data\vlc_status.xml 2>nul

:: 用 PowerShell 从 XML 中提取文件名
powershell -Command ^
    "try { ^
        [xml]$x = Get-Content 'D:\live\data\vlc_status.xml'; ^
        $name = $x.root.information.category | Where-Object {$_.name -eq 'meta'} | ^
            ForEach-Object { $_.info } | Where-Object {$_.name -eq 'filename'} | ^
            ForEach-Object { $_.'#text' }; ^
        if ($name) { ^
            $song = [System.IO.Path]::GetFileNameWithoutExtension($name); ^
            Set-Content -Path 'D:\live\data\now_playing.txt' -Value $song -Encoding UTF8 ^
        } ^
    } catch {}"

timeout /t 5 >nul
goto loop
```

> 这个脚本每 5 秒从 VLC 获取当前播放的歌名，写入 `now_playing.txt`，B区面板会自动读取显示。

---

## 六、弹幕点歌系统

### 6.1 整体架构

```
观众发弹幕             Python弹幕机器人         VLC
「点歌 恋人心」 ──▶  blivedm 监听匹配 ──▶  HTTP接口播放
                          │                    │
                          ▼                    ▼
                   bilibili-api          更新 now_playing.txt
                   发送弹幕回复           更新 queue.txt
```

### 6.2 歌曲库索引生成

创建 `D:\live\scripts\build_index.bat`（每次新增歌曲后运行一次）：

```batch
@echo off
chcp 65001 >nul
:: 生成歌曲索引文件，列出所有可点歌曲
dir /b "D:\live\songs\*.mp4" "D:\live\songs\*.mp3" "D:\live\songs\*.flv" 2>nul | ^
    for /f "delims=." %%a in ('more') do @echo %%a
> "D:\live\data\song_list.txt"

echo 歌曲索引已更新：
type "D:\live\data\song_list.txt"
```

### 6.3 点歌脚本

创建 `D:\live\scripts\play_song.bat`：

```batch
@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "song=%~1"
set "SONGDIR=D:\live\songs"
set "NOWPLAY=D:\live\data\now_playing.txt"
set "QUEUE=D:\live\data\queue.txt"
set "VLC_HTTP=http://127.0.0.1:9090"
set "VLC_PASS=123456"

if "%song%"=="" (
    echo 用法: play_song.bat 歌名
    exit /b 1
)

:: 搜索歌曲文件（支持模糊匹配）
set "found="
for %%f in ("%SONGDIR%\*%song%*.*") do (
    set "found=%%f"
    for %%i in ("%%f") do set "name=%%~ni"
    goto :play
)

echo 未找到歌曲: %song%
exit /b 1

:play
echo 找到歌曲: !name! (!found!)

:: 更新当前播放
echo !name!> "%NOWPLAY%"

:: 通过 VLC HTTP 接口播放
curl -s -u ":!VLC_PASS!" "%VLC_HTTP%/requests/status.xml?command=in_play&input=!found!" >nul 2>&1

echo 已切换播放: !name!
exit /b 0
```

### 6.4 队列管理脚本

创建 `D:\live\scripts\add_to_queue.bat`：

```batch
@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "song=%~1"
set "SONGDIR=D:\live\songs"
set "QUEUE=D:\live\data\queue.txt"
set "VLC_HTTP=http://127.0.0.1:9090"
set "VLC_PASS=123456"

:: 搜索歌曲
set "found="
for %%f in ("%SONGDIR%\*%song%*.*") do (
    set "found=%%f"
    for %%i in ("%%f") do set "name=%%~ni"
    goto :enqueue
)

echo 未找到: %song%
exit /b 1

:enqueue
:: 加入VLC播放队列
curl -s -u ":!VLC_PASS!" "%VLC_HTTP%/requests/status.xml?command=in_enqueue&input=!found!" >nul 2>&1

:: 加入显示队列
echo !name!>> "%QUEUE%"

echo 已加入队列: !name!
exit /b 0
```

---

## 七、弹幕命令系统（Python 机器人）

### 7.1 技术选型

~~神奇弹幕（Bilibili-MagicalDanmaku）已于 2025 年底永久停止维护并归档。~~

替代方案使用两个活跃维护的 Python 库：

| 库 | 用途 | Stars | 最后更新 |
|----|------|-------|---------|
| [blivedm](https://github.com/xfgryujk/blivedm) | 接收直播弹幕（WebSocket） | 1300+ | 2026-02-07 (v1.1.5) |
| [bilibili-api-python](https://github.com/Nemo2011/bilibili-api) | 发送弹幕 / 调用 B站 API | 3400+ | 2026-02-12 (v17.4.1) |

**安装依赖：**

```batch
pip install blivedm bilibili-api-python aiohttp
```

### 7.2 命令一览表

| 弹幕命令 | 效果 | 权限 |
|----------|------|------|
| `点歌 恋人心` | 搜索并播放歌曲 | 所有人 |
| `切歌` | VLC 下一首 | 所有人（可限制房管） |
| `歌单` | 回复可点歌曲列表 | 所有人 |
| `当前` | 回复当前播放歌名 | 所有人 |
| `PK` | 向女主播发起 PK 请求 | 仅限主播本人 |

### 7.3 完整弹幕机器人代码

创建 `D:\live\scripts\danmaku_bot.py`：

```python
"""
B站直播弹幕机器人 v2.0
基于 blivedm（接收弹幕）+ bilibili-api-python（发送弹幕/API调用）
替代已停止维护的「神奇弹幕」

依赖安装: pip install blivedm bilibili-api-python aiohttp
"""

import os
import re
import glob
import asyncio
import logging
from datetime import datetime

import aiohttp
import blivedm
import blivedm.models.web as web_models
from bilibili_api import live as bili_live, Credential, Danmaku

# ====== 配置区 ======
ROOM_ID = 你的直播间号            # B站直播间号（数字）
MY_UID = 你的UID                  # 你自己的B站UID（用于PK权限校验）

# B站登录凭证（浏览器 F12 → Application → Cookies 获取）
SESSDATA = "你的SESSDATA"
BILI_JCT = "你的bili_jct"
BUVID3 = "你的buvid3"

# 歌曲相关路径
SONG_DIR = r"D:\live\songs"
NOW_PLAYING_FILE = r"D:\live\data\now_playing.txt"
QUEUE_FILE = r"D:\live\data\queue.txt"

# VLC HTTP 接口
VLC_HTTP = "http://127.0.0.1:9090"
VLC_PASS = "123456"

# PK 目标（女主播的直播间号）
PK_TARGET_ROOM_ID = 目标直播间号  # 替换为实际房间号
# ====== 配置区结束 ======

# 初始化日志
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("bot")

# 初始化凭证
credential = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)

# 命令冷却时间（秒）
COOLDOWNS = {"点歌": 5, "切歌": 10, "歌单": 30, "当前": 10, "PK": 60}
last_cmd_time = {}


def check_cooldown(cmd: str) -> bool:
    """检查命令冷却"""
    now = datetime.now().timestamp()
    cd = COOLDOWNS.get(cmd, 5)
    if cmd in last_cmd_time and now - last_cmd_time[cmd] < cd:
        return False
    last_cmd_time[cmd] = now
    return True


def find_song(keyword: str):
    """模糊搜索歌曲文件"""
    for ext in ["*.mp4", "*.mp3", "*.flv", "*.mkv"]:
        for f in glob.glob(os.path.join(SONG_DIR, ext)):
            name = os.path.splitext(os.path.basename(f))[0]
            if keyword.lower() in name.lower():
                return f, name
    return None, None


async def vlc_command(command: str, extra_params: str = "") -> bool:
    """发送 VLC HTTP 接口命令"""
    url = f"{VLC_HTTP}/requests/status.xml?command={command}{extra_params}"
    auth = aiohttp.BasicAuth("", VLC_PASS)
    try:
        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                return resp.status == 200
    except Exception as e:
        log.error(f"VLC 命令失败: {e}")
        return False


async def send_reply(text: str):
    """发送弹幕到自己直播间"""
    try:
        room = bili_live.LiveRoom(ROOM_ID, credential=credential)
        await room.send_danmaku(Danmaku(text[:30]))  # B站弹幕限30字
    except Exception as e:
        log.error(f"弹幕发送失败: {e}")


def update_now_playing(name: str):
    """更新当前播放文件"""
    with open(NOW_PLAYING_FILE, "w", encoding="utf-8") as f:
        f.write(name)


# ====== blivedm 事件处理器 ======

class LiveHandler(blivedm.BaseHandler):

    async def _on_danmaku(self, client: blivedm.BLiveClient, message: web_models.DanmakuMessage):
        """处理弹幕消息"""
        text = message.msg
        uid = message.uid
        uname = message.uname

        # --- 点歌 ---
        match = re.match(r"^点歌\s+(.+)$", text)
        if match:
            if not check_cooldown("点歌"):
                return
            keyword = match.group(1).strip()
            filepath, songname = find_song(keyword)
            if filepath:
                encoded_path = filepath.replace("\\", "/")
                await vlc_command("in_play", f"&input={encoded_path}")
                update_now_playing(songname)
                await send_reply(f">_ 正在播放：{songname}")
                log.info(f"[点歌] {uname}: {keyword} → {songname}")
            else:
                await send_reply(f">_ 未找到「{keyword}」")
                log.info(f"[点歌] {uname}: {keyword} → 未找到")
            return

        # --- 切歌 ---
        if text.strip() == "切歌":
            if not check_cooldown("切歌"):
                return
            await vlc_command("pl_next")
            await send_reply(">_ 已切歌~")
            log.info(f"[切歌] {uname}")
            return

        # --- 当前播放 ---
        if text.strip() == "当前":
            if not check_cooldown("当前"):
                return
            try:
                with open(NOW_PLAYING_FILE, "r", encoding="utf-8") as f:
                    song = f.read().strip()
                await send_reply(f">_ 当前：{song}")
            except FileNotFoundError:
                await send_reply(">_ 暂无播放")
            return

        # --- 歌单 ---
        if text.strip() == "歌单":
            if not check_cooldown("歌单"):
                return
            songs = []
            for ext in ["*.mp4", "*.mp3", "*.flv"]:
                for f in glob.glob(os.path.join(SONG_DIR, ext)):
                    songs.append(os.path.splitext(os.path.basename(f))[0])
            total = len(songs)
            preview = "、".join(songs[:5])
            await send_reply(f">_ 共{total}首：{preview}...")
            return

        # --- PK ---
        if text.strip() == "PK":
            if uid != MY_UID:
                await send_reply(">_ PK仅限主播发起")
                return
            if not check_cooldown("PK"):
                return
            success = await send_pk_request(PK_TARGET_ROOM_ID)
            if success:
                await send_reply(">_ PK请求已发送~")
            else:
                await send_reply(">_ PK失败，请手动操作")
            return

    async def _on_interact_word(self, client: blivedm.BLiveClient, message):
        """欢迎入场"""
        # blivedm 的 interact_word 事件
        pass  # 可选：取消注释下面的代码启用欢迎
        # uname = message.get("uname", "")
        # await send_reply(f"欢迎{uname}~发「点歌 歌名」点歌")


async def send_pk_request(target_room_id: int) -> bool:
    """通过B站API发起PK请求"""
    url = "https://api.live.bilibili.com/xlive/web-room/v1/index/pkInvite"
    headers = {
        "Cookie": f"SESSDATA={SESSDATA}; bili_jct={BILI_JCT}",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://live.bilibili.com/{ROOM_ID}",
    }
    data = {
        "room_id": ROOM_ID,
        "invite_room_id": target_room_id,
        "csrf_token": BILI_JCT,
        "csrf": BILI_JCT,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as resp:
                result = await resp.json()
                if result.get("code") == 0:
                    log.info(f"PK 请求已发送到房间 {target_room_id}")
                    return True
                else:
                    log.warning(f"PK 请求失败: {result.get('message')}")
                    return False
    except Exception as e:
        log.error(f"PK 请求异常: {e}")
        return False


async def main():
    log.info(f"弹幕机器人启动中... 直播间 {ROOM_ID}")
    log.info(f"支持命令: 点歌/切歌/当前/歌单/PK")
    log.info(f"使用 blivedm v{blivedm.__version__ if hasattr(blivedm, '__version__') else '?'} 监听弹幕")

    # 创建 blivedm 客户端
    # 需要传入 SESSDATA cookie 以获取完整弹幕（B站反爬要求）
    client = blivedm.BLiveClient(ROOM_ID, session=None)
    handler = LiveHandler()
    client.set_handler(handler)

    client.start()
    try:
        # 持续运行
        await asyncio.Future()
    finally:
        client.stop()
        await client.join()


if __name__ == "__main__":
    asyncio.run(main())
```

### 7.4 获取 B站凭证

```
1. 浏览器登录 B站 (bilibili.com)
2. F12 打开开发者工具
3. Application → Cookies → bilibili.com
4. 找到并复制以下三个值：
   - SESSDATA
   - bili_jct
   - buvid3
5. 填入 danmaku_bot.py 的配置区
```

> blivedm 需要登录态 Cookie 才能接收完整弹幕（B站反爬要求）。

### 7.5 启动弹幕机器人

创建 `D:\live\scripts\start_bot.bat`：

```batch
@echo off
title [直播] 弹幕机器人
cd /d D:\live\scripts
python danmaku_bot.py
pause
```

### 7.6 自动欢迎与感谢（可选）

在 `LiveHandler` 类中添加更多事件处理：

```python
    async def _on_gift(self, client, message):
        """感谢礼物"""
        uname = message.uname
        gift_name = message.gift_name
        await send_reply(f"感谢{uname}的{gift_name}！")

    async def _on_guard_buy(self, client, message):
        """感谢上舰"""
        uname = message.username
        await send_reply(f"感谢{uname}上舰！")
```

> blivedm 支持的事件类型参见 [blivedm README](https://github.com/xfgryujk/blivedm)。

---

## 八、PK 系统

### 8.1 PK 功能说明

B站直播 PK 功能允许两个主播连线互动。你可以通过弹幕命令快速向女主播发起 PK 请求。

### 8.2 方案 A：直播姬快捷操作（推荐新手）

直播姬自带 PK 功能，最简单的操作流程：

```
1. 直播姬 → 互动 → PK → 输入对方直播间号 → 发起
2. 等待对方接受
```

通过弹幕触发 PK 时，弹幕机器人会自动调用 B站 API 发送请求。

### 8.3 方案 B：通过 B站 API 自动发起 PK

弹幕机器人（`danmaku_bot.py`）已内置 PK 功能。在直播间发送 `PK` 即可触发，仅限主播本人 UID。

PK 相关代码见第七章 `send_pk_request()` 函数。

> 注意：此方案使用 B站非官方 API，可能随版本变化需要调整。

### 8.4 PK 安全控制

| 配置项 | 说明 |
|--------|------|
| 触发权限 | 仅限主播本人 UID 才能触发 PK |
| 目标固定 | PK 目标预设为女主播的直播间号 |
| 冷却时间 | 每次 PK 间隔至少 60 秒 |

---

## 九、远程收音方案

当你不在直播机旁边（比如用笔记本在客厅/外面），想远程连入直播间说话互动。

### 9.1 整体音频链路

```
你的笔记本/手机                       Win10 直播虚拟机 (PVE)
┌──────────────┐                    ┌──────────────────────────┐
│              │                    │                          │
│  麦克风      │                    │  Parsec 虚拟音频输入      │
│    │         │   Parsec 远程桌面   │    │                     │
│    ▼         │ ══════════════════▶│    ▼                     │
│  Parsec 客户端│  (音频通道传输)     │  VoiceMeeter Banana      │
│              │                    │    │                     │
└──────────────┘                    │    ├─▶ B1: OBS 麦克风    │
                                    │    └─▶ B2: VTS 口型驱动  │
                                    │                          │
                                    │  VLC 桌面音频 ─▶ OBS     │
                                    └──────────────────────────┘
```

### 9.2 直播机（Win10 虚拟机）配置

#### 第一步：安装 Parsec

```
1. 下载 Parsec: https://parsec.app/downloads
2. 安装并登录账号
3. 设置 → Host → Audio:
   - 勾选 "Enable microphone passthrough"（允许客户端麦克风传入）
```

#### 第二步：安装 VoiceMeeter Banana

```
1. 下载 VoiceMeeter Banana: https://vb-audio.com/Voicemeeter/banana.htm
2. 安装并重启
3. 打开 VoiceMeeter Banana 配置:

   HARDWARE INPUT 1:  选择 "Parsec Virtual Audio" (这是远程麦克风)
   HARDWARE INPUT 2:  （留空，或接本地麦克风备用）

   HARDWARE OUT A1:   选择你的声卡/默认输出（耳机/音响）
   HARDWARE OUT B1:   选择 VoiceMeeter Output（虚拟输出）

   INPUT 1 路由：     勾选 B1（发送到虚拟输出，给 OBS 用）
```

#### 第三步：OBS 音频设置

```
OBS → 设置 → 音频:
  桌面音频设备:  默认（捕获 VLC 歌曲播放声音）
  麦克风/辅助音频: VoiceMeeter Output (B1)

这样 OBS 同时捕获：歌曲声音 + 你的远程麦克风声音
```

#### 第四步：Windows 音频设置

```
Win10 → 设置 → 系统 → 声音:
  输出设备: 默认（或 VoiceMeeter Input）
  输入设备: VoiceMeeter Output（让系统默认麦克风指向虚拟设备）
```

### 9.3 本地电脑（你的笔记本/台式机）配置

```
1. 安装 Parsec 客户端
2. 登录同一账号
3. 连接到直播机
4. Parsec 设置 → Client:
   - Microphone: 选择你的实际麦克风
   - 勾选 "Send microphone to host"

连接后，你对着笔记本麦克风说话 → Parsec 传输到直播机 → OBS 捕获 → 直播间听到你说话
```

### 9.4 测试流程

```
1. Parsec 连接直播机
2. 说话，观察 VoiceMeeter 的 INPUT 1 音量条是否跳动
3. 观察 OBS 的麦克风音量条是否跳动
4. 在直播预览中确认能听到自己的声音
5. 调整音量比例（歌曲 vs 麦克风），避免说话时歌声太大盖过语音
```

### 9.5 备选方案

| 方案 | 优点 | 缺点 |
|------|------|------|
| **Parsec（推荐）** | 延迟低、音质好、可同时操作桌面 | 需注册账号 |
| **Moonlight + Sunshine** | 开源免费、延迟极低 | 需要显卡直通配置 Sunshine |
| **向日葵/ToDesk** | 简单 | 音频传输质量一般，延迟较高 |
| **Discord 自听** | 开一个 Discord 频道自己加入 | 需要绕一圈 |

> 你已经有显卡直通的 PVE 虚拟机，Parsec 和 Moonlight 都是很好的选择。Parsec 的麦克风穿透功能最成熟。

### 9.6 VoiceMeeter 进阶：说话时自动降低歌曲音量

VoiceMeeter Banana 支持 "ducking"——检测到麦克风输入时自动压低其他声音：

```
VoiceMeeter 设置:
  INPUT 1 (麦克风):
    - Gate: 开启（过滤环境噪音）
    - 音量: 调到合适水平

  在 OBS 中设置:
    - 高级音频属性 → 桌面音频音量: 70%
    - 高级音频属性 → 麦克风音量: 100%

  或使用 OBS 的「压缩器」滤镜:
    - 桌面音频 → 滤镜 → 添加「侧链/闪避压缩器」
    - 侧链源: 选择麦克风
    - 这样说话时歌声自动变小
```

---

## 十、B区信息面板

### 10.1 工作原理

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  cyber_live.py (主程序)                                        │
│  ├─ VLC 控制器 ──每5秒──▶ 读取当前播放歌名                     │
│  ├─ 弹幕机器人 ──检测命令──▶ 管理点歌队列                       │
│  ├─ 模式管理器 ──监控状态──▶ 选择当前播放模式                   │
│  │   (直播 > PK/点歌 > 轮播 > 其他)                             │
│  └─ 面板渲染器 ──每1秒──▶ 生成 data/panel.png                 │
│                                                                │
│  OBS 图像源 ◀──加载── data/panel.png                          │
│  (自动刷新，零GPU开销)  ◀── panel_refresh.lua (1秒刷新)        │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**优势对比:**
- ✓ 完全用 Python 实现，无需 HTML/JavaScript
- ✓ 使用 Pillow 图像库渲染，零 GPU/Chromium 开销
- ✓ 支持多种播放模式（直播/PK/点歌/轮播/其他）
- ✓ 1 秒刷新率，实时响应
- ✓ 字体可配置，充分利用 520×435 像素空间

### 10.2 面板文件和模式系统

面板由 `modules/panel.py` 动态生成，输出为 PNG 图片，支持 5 种模式：

| 模式 | 优先级 | 说明 | 显示内容 |
|------|--------|------|---------|
| **直播模式** (broadcast) | 1 (最高) | 直播进行中 | 直播间信息、在线人数、状态 |
| **PK模式** (pk) | 2 | PK 对战中 | PK 对手、分数、战况 |
| **点歌模式** (song_request) | 2 | 有点歌队列 | 当前歌曲、队列列表、请求人名 |
| **轮播模式** (playback) | 3 | 正常播放 | 当前歌曲、下一首、队列预览 |
| **其他模式** (other) | 4 (最低) | 空闲状态 | 欢迎信息、帮助提示 |

**优先级规则：**
- 自动检测高优先级状态并切换（如直播开始时自动切换到直播模式）
- 高优先级模式会阻止低优先级模式（如在直播模式下，点歌模式被堵塞，等待直播结束）
- 支持弹幕命令手动切换模式（如发送 "直播模式"、"轮播模式" 等）

### 10.3 数据文件配置

运行时数据存放在 `data/` 目录下：

```
data/
├─ panel.png          # B区面板图片（Python 每秒生成）
├─ now_playing.txt    # 当前播放歌名
├─ queue.txt          # 点歌队列（JSON 格式）
├─ mode.txt           # 当前模式状态
└─ status.json        # 系统状态（直播间、在线人数等）
```

**panel.png 规格：**
- 尺寸：520×435 像素
- 格式：PNG（8-bit RGB）
- 刷新率：1 秒/次
- 字体：JetBrains Mono，大小根据模式自动调整
- 颜色：终端风格（深色背景 #0d0d0d，青色/品红色文字）

### 10.4 面板配置参数

编辑 `config.ini` 中的 `[panel]` 部分自定义面板外观：

```ini
[panel]
# 面板尺寸（OBS 中也应该设为 520×435）
width = 520
height = 435

# 刷新间隔（秒）
refresh_interval = 1

# 字体配置
font_size_title = 20          # 标题字体
font_size_content = 14        # 内容字体
font_size_small = 12          # 小字体

# 颜色主题（十六进制）
color_bg = #0d0d0d            # 背景
color_text = #00ff00          # 正常文字（绿色）
color_highlight = #00ffff    # 强调文字（青色）
color_accent = #ff00ff        # 强调色（品红）
```

### 10.5 OBS 中添加面板

#### Step 1: 添加图像源

```
1. OBS → 场景 → [直播场景] → 右下角"源" → [+] 添加
2. 选择 "图像"
3. 名称填写: B区-终端面板
4. 点击 "创建新的" 或 "浏览"
```

#### Step 2: 配置图像源

```
属性窗口：
- 文件: D:\SingllLive\data\panel.png（选择 cyber_live.py 生成的 PNG）
- 宽度: 520
- 高度: 435
- 位置: x=1385, y=45（根据你的 OBS 布局调整）
- 混合方式: 正常
- 不透明度: 100
```

#### Step 3: 设置自动刷新脚本

由于 OBS 的图像源默认不会监控文件变化，需要加载 Lua 脚本来定时刷新：

**方案 A（推荐）：OBS 脚本自动刷新**

```
1. OBS → 工具 → 脚本
2. 点击右下角 [+] 添加脚本
3. 选择 SingllLive/scripts/panel_refresh.lua
4. 脚本会每 1 秒自动刷新 B区 图像源
```

**方案 B（备选）：手动刷新**

如果上述方案不可用，可在 OBS 中创建快捷键绑定：
1. OBS → 设置 → 快捷键
2. 搜索 "刷新"，为 "B区-终端面板" 的刷新操作绑定快捷键
3. 需要时手动按快捷键刷新（但自动脚本更方便）

### 10.6 启动面板服务

面板会随 `cyber_live.py` 自动启动：

```bash
# Windows
start.bat

# 或者直接运行
python cyber_live.py
```

检查日志输出，应该看到：
```
[2024-02-15 12:00:00] 面板渲染器启动完成
[2024-02-15 12:00:01] 面板已生成: data/panel.png
[2024-02-15 12:00:02] 面板已生成: data/panel.png
...
```

### 10.6a VLC 生命周期管理（模式驱动）

**重要变更**：VLC 不再在启动时无条件启动，而是根据播放模式自动启动/停止。

#### 工作流程

```
┌─────────────────────────────────────────────────────────┐
│                    VLC 模式驱动管理                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  轮播模式 (PLAYBACK)                                     │
│  ↓                                                      │
│  VLC 启动 → 循环播放歌曲 → 面板显示当前歌曲              │
│                                                         │
│  ├─ 用户点歌 → 自动切换到点歌模式                        │
│  │  VLC 继续播放 → 面板显示队列                          │
│  │                                                     │
│  │  ├─ 队列播完 → 回到轮播模式                           │
│  │  │  VLC 继续循环播放                                 │
│  │  │                                                  │
│  │  └─ 用户发送"直播模式" → 切换到直播模式              │
│  │     VLC 暂停 → 面板显示直播信息                      │
│  │     直播结束 → 恢复到轮播/点歌模式                    │
│  │                                                     │
│  └─ 用户发送"其他模式" → 空闲模式                        │
│     VLC 停止 → 面板显示欢迎信息                         │
│
└─────────────────────────────────────────────────────────┘
```

#### VLC 的状态转换表

| 当前模式 | 切换到 | VLC 行为 | 说明 |
|---------|--------|---------|------|
| 空闲 | 轮播 | ▶ 启动 | VLC 启动，开始循环播放 |
| 轮播 | 点歌 | ► 继续 | VLC 继续播放，不中断 |
| 点歌 | 轮播 | ► 继续 | 队列播完后自动回到轮播 |
| 轮播/点歌 | 直播/PK | ⏸ 暂停 | VLC 暂停，保留播放位置 |
| 直播/PK | 轮播/点歌 | ▶ 恢复 | VLC 恢复播放 |
| 任意模式 | 空闲 | ⏹ 停止 | VLC 完全停止 |

#### 日志示例

```
[14:24:06] main       程序员深夜电台 - 所有服务已启动
[14:24:06] main       VLC HTTP:  http://127.0.0.1:9090
[14:24:07] vlc        VLC 模式管理循环启动
[14:24:08] vlc        VLC 模式管理: None → PLAYBACK (轮播模式)
[14:24:08] vlc        启动 VLC (进入轮播/点歌模式)
[14:24:10] vlc        VLC 已启动: http://127.0.0.1:9090
[14:24:10] vlc        VLC 看门狗启动
[14:24:11] vlc        VLC 歌名同步启动
[14:24:15] panel      面板渲染器启动 (间隔 1.0s)

[14:35:22] danmaku    [点歌] user: 千本樱 -> 千本樱
[14:35:23] vlc        VLC 模式管理: PLAYBACK → SONG_REQUEST (点歌模式)
[14:35:23] vlc        恢复 VLC 播放 (从暂停状态)
[14:35:24] panel      面板已生成: data/panel.png (点歌模式)

[14:40:15] danmaku    [模式切换] user 切换到 BROADCAST
[14:40:15] vlc        VLC 模式管理: SONG_REQUEST → BROADCAST (直播模式)
[14:40:15] vlc        暂停 VLC (进入直播/PK模式)
[14:40:16] panel      面板已生成: data/panel.png (直播模式)

[14:50:30] danmaku    [模式切换] user 切换到 PLAYBACK
[14:50:30] vlc        VLC 模式管理: BROADCAST → PLAYBACK (轮播模式)
[14:50:30] vlc        恢复 VLC 播放 (从暂停状态)
```

#### 用户体验

**场景 1: 正常直播流程**

```
1. 启动 start.bat
   ↓
   系统启动 → 默认轮播模式 → VLC 自动启动并播放

2. 用户在直播间发送 "点歌 千本樱"
   ↓
   自动切换到点歌模式 → VLC 继续播放 → 面板显示队列

3. 直播结束，用户发送 "其他模式"
   ↓
   切换到空闲模式 → VLC 停止 → 面板显示欢迎
```

**场景 2: 只进行直播，不需要背景音乐**

```
1. 启动 start.bat
   ↓
   系统启动 → 默认轮播模式 → VLC 自动启动

2. 立即发送 "直播模式"
   ↓
   切换到直播模式 → VLC 暂停 → 面板显示直播信息

3. 直播期间可以进行PK、接收礼物等

4. 直播结束，发送 "轮播模式"
   ↓
   回到轮播模式 → VLC 恢复播放 → 面板显示歌曲

或直接关闭程序 (Ctrl+C) → VLC 自动停止
```

#### 手动控制 VLC

如果需要手动控制 VLC（不走模式系统）：

```bash
# 直接访问 VLC HTTP 接口
# 基础 URL: http://127.0.0.1:9090/requests

# 播放
curl http://127.0.0.1:9090/requests/status.xml?command=pl_play

# 暂停
curl http://127.0.0.1:9090/requests/status.xml?command=pl_pause

# 下一首
curl http://127.0.0.1:9090/requests/status.xml?command=pl_next

# 获取当前信息
curl http://127.0.0.1:9090/requests/status.xml
```

### 10.7 模式切换和弹幕命令

#### 自动模式切换

系统会根据以下条件自动切换模式：

1. **直播模式** → 检测到直播间在线（需配置）
2. **PK模式** → 检测到 PK 活动
3. **点歌模式** → 点歌队列有歌曲待播放
4. **轮播模式** → 正常播放歌曲
5. **其他模式** → 默认空闲状态

#### 弹幕命令手动切换

在直播间发送以下命令可手动切换模式（需要设置为管理员或有特殊权限）：

| 命令 | 说明 |
|------|------|
| `直播模式` | 切换到直播模式（高优先级） |
| `PK模式` | 切换到 PK 模式 |
| `点歌模式` | 切换到点歌模式 |
| `轮播模式` | 切换到轮播模式 |
| `其他模式` | 切换到其他模式 |
| `查看模式` | 查看当前模式和优先级 |

**示例：**
```
用户在直播间发送: 轮播模式
↓
弹幕机器人接收命令
↓
模式管理器切换到轮播模式
↓
panel.py 重新渲染面板（1秒内刷新）
↓
OBS 自动刷新图像源
↓
B区显示新的轮播模式面板
```

### 10.8 扩展和自定义

#### 添加新的模式

如需添加新的播放模式（如 "粉丝互动模式" 等），修改 `modules/modes.py`：

```python
# 在 Mode 枚举中添加新模式
class Mode(Enum):
    BROADCAST = (1, "直播模式")
    PK = (2, "PK模式")
    SONG_REQUEST = (2, "点歌模式")
    PLAYBACK = (3, "轮播模式")
    FAN_INTERACTION = (3, "粉丝互动")  # ← 新增
    OTHER = (4, "其他模式")

# 在 panel.py 中为新模式添加渲染逻辑
def render_fan_interaction_mode(self, draw, y):
    # 自定义粉丝互动模式的界面
    pass
```

#### 自定义面板外观

编辑 `config.ini` 的 `[panel]` 部分，调整字体大小、颜色、布局等。具体参数见 **10.4 面板配置参数**。

### 10.9 OBS 完整场景配置

#### 整体结构

```
OBS 场景树
├── [主场景] MScreen (16:9 直播场景)
│   ├── [源] background (背景图 - 最底层)
│   ├── [嵌套场景] AScreen (A区 - 视频内容)
│   ├── [嵌套场景] BScreen (B区 - 信息面板)
│   ├── [嵌套场景] CScreen (C区 - 虚拟人)
│   └── [源] frame-overlay (框架遮罩 - 最顶层)
│
├── [A区场景] AScreen
│   └── [源] VLC视频 (或其他视频源)
│
├── [B区场景] BScreen
│   └── [源] B区-终端面板 (图像源)
│
└── [C区场景] CScreen
    └── [源] VTubeStudio (虚拟人)
```

#### 详细配置步骤

**Step 1: 创建主场景 (MScreen)**

```
1. OBS → 场景 → [+] 新建
2. 名称: MScreen (主场景)
3. 确定
```

**Step 2: 添加背景**

```
在 MScreen 中：
1. 右下角"源" → [+] 添加
2. 选择 "图像" → 创建新的
3. 名称: background (背景)
4. 文件: D:\SingllLive\assets\background.png (或你的背景图)
5. 位置和大小: 全屏铺满整个 16:9 画布
6. 点击 [确定]
```

**Step 3: 创建 A区场景 (视频区)**

```
1. OBS → 场景 → [+] 新建
2. 名称: AScreen
3. 确定

在 AScreen 中：
1. 右下角"源" → [+] 添加
2. 选择 "VLC 视频源" (或其他视频源)
3. 名称: VLC视频
4. 文件: D:\SingllLive\songs (歌曲目录)
5. 播放列表: 启用 ☑
6. 循环: 启用 ☑
7. [确定]
```

**Step 4: 创建 B区场景 (面板区)**

```
1. OBS → 场景 → [+] 新建
2. 名称: BScreen
3. 确定

在 BScreen 中：
1. 右下角"源" → [+] 添加
2. 选择 "图像" → 创建新的
3. 名称: B区-终端面板
4. 文件: D:\SingllLive\data\panel.png
5. 位置: x=0, y=0
6. 大小: 宽=520, 高=435
7. [确定]
```

**Step 5: 创建 C区场景 (虚拟人区)**

```
1. OBS → 场景 → [+] 新建
2. 名称: CScreen
3. 确定

在 CScreen 中：
1. 右下角"源" → [+] 添加
2. 选择 "游戏捕获" 或 "窗口捕获"
3. 名称: VTubeStudio
4. 选择 VTubeStudio 的窗口
5. [确定]
```

**Step 6: 设置 OBS 脚本自动刷新 B区**

```
1. OBS → 工具 → 脚本
2. 右下角 [+] 添加脚本
3. 选择 D:\SingllLive\scripts\panel_refresh.lua
4. 脚本自动加载，每秒刷新 B区图像源
```

**Step 7: 组装主场景 (MScreen)**

```
1. OBS → 场景 → MScreen (切换到主场景)
2. 右下角"源" → [+] 添加
3. 选择 "嵌套场景" → 创建新的
4. 名称: background
5. 场景: (这里选择 background 图像源)
   实际上应该直接添加背景图：

   改为：
   1. [+] 添加 → 图像
   2. 名称: background
   3. 文件: D:\SingllLive\assets\background.png
   4. [确定]

再添加三个嵌套场景:
   1. [+] 添加 → 嵌套场景
   2. 名称: AScreen
   3. 场景: AScreen
   4. [确定]

   1. [+] 添加 → 嵌套场景
   2. 名称: BScreen
   3. 场景: BScreen
   4. 位置: x=1385, y=45 (B区位置)
   5. [确定]

   1. [+] 添加 → 嵌套场景
   2. 名称: CScreen
   3. 场景: CScreen
   4. [确定]

最后添加框架遮罩:
   1. [+] 添加 → 图像
   2. 名称: frame-overlay (最顶层)
   3. 文件: D:\SingllLive\assets\frame-overlay.png
   4. [确定]
```

#### 屏幕布局参考

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  A区 (视频)          │  B区 (面板)     │  背景   │
│  (1280×720)         │  (520×435)      │          │
│                     │ ┌──────────────┐ │          │
│                     │ │ [面板内容]   │ │          │
│                     │ │             │ │          │
│                     │ │             │ │          │
│                     │ └──────────────┘ │          │
│                     │                 │          │
│                     │  C区 (虚拟人)    │  背景   │
│                     │                 │          │
│                     └─────────────────┘          │
│                                                     │
└─────────────────────────────────────────────────────┘

总分辨率: 1920×1080 (16:9)
A区位置: x=0, y=0 (1280×720)
B区位置: x=1385, y=45 (520×435)
C区位置: x=1385, y=485 (可选，虚拟人)
```

#### 模式与显示的联动

| 模式 | A区 | B区显示 | C区 | 说明 |
|------|------|---------|-------|------|
| **直播模式** | VLC播放 | 直播信息<br/>在线人数<br/>运行时长 | 虚拟人笑脸 | 直播中，B区显示直播信息 |
| **PK模式** | VLC播放 | PK对战<br/>比分<br/>对手 | 虚拟人战斗 | PK进行中，B区显示战况 |
| **点歌模式** | VLC播放 | 当前歌<br/>队列列表<br/>请求提示 | 虚拟人跳舞 | 有点歌队列，B区显示队列 |
| **轮播模式** | VLC播放 | 当前歌<br/>下一首<br/>队列预览 | 虚拟人正常 | 正常播放，B区显示歌曲信息 |
| **其他模式** | 黑屏待机 | 欢迎信息<br/>帮助提示 | 虚拟人空闲 | 空闲状态，B区显示欢迎 |

**C区虚拟人配置** (可选，需自行集成):
- 直播模式: 设置为 "笑脸" 表情（通过 VTS API）
- PK模式: 设置为 "战斗" 表情
- 点歌模式: 设置为 "跳舞" 动作
- 轮播/其他: 保持默认

### 10.10 弹幕命令与模式交互

#### 支持的所有弹幕命令

| 命令 | 示例 | 说明 | 冷却 |
|------|------|------|------|
| **点歌** | `点歌 告白气球` | 搜索并播放指定歌曲 | 5秒 |
| **切歌** | `切歌` | 跳过当前歌曲，播放下一首 | 10秒 |
| **当前** | `当前` | 查询当前播放的歌曲 | 10秒 |
| **歌单** | `歌单` | 显示歌曲库的前5首 | 30秒 |
| **帮助** | `帮助` 或 `命令` | 显示所有支持的命令 | 5秒 |
| **直播模式** | `直播模式` | 切换到直播模式（优先级1） | 3秒 |
| **PK模式** | `PK模式` | 切换到PK模式（优先级2） | 3秒 |
| **点歌模式** | `点歌模式` | 切换到点歌模式（优先级2） | 3秒 |
| **轮播模式** | `轮播模式` | 切换到轮播模式（优先级3） | 3秒 |
| **其他模式** | `其他模式` | 切换到其他模式（优先级4） | 3秒 |
| **查看模式** | `查看模式` | 显示当前模式和优先级 | 2秒 |

#### 交互流程示例

**场景 1: 用户点歌**

```
观众在直播间发送: "点歌 千本樱"
    ↓
DanmakuBot 接收弹幕
    ↓
搜索歌曲库: 找到 "千本樱"
    ↓
VLCController 将歌曲加入队列
    ↓
_mode_auto_switch_loop 检测到队列有歌 (queue_count=1)
    ↓
ModeManager 自动切换到 SONG_REQUEST 模式
    ↓
PanelRenderer 下次渲染时（≤1秒）生成点歌模式 PNG
    ↓
OBS panel_refresh.lua 检测到 panel.png 变化
    ↓
OBS 自动刷新 B区图像源
    ↓
观众看到 B区 显示：
   [队列 1首]
   ▶ 当前歌曲
   1. 千本樱 (新添加)
```

**场景 2: 点歌被高优先级模式阻止**

```
直播中 (ModeManager.current_mode = BROADCAST, 优先级1)

观众发送: "点歌 青花瓷"
    ↓
歌曲加入队列 (queue_count=1)
    ↓
_mode_auto_switch_loop 尝试切换到 SONG_REQUEST (优先级2)
    ↓
ModeManager 检查优先级: SONG_REQUEST(2) < BROADCAST(1)
    ↓
切换被拒绝，设置 is_blocked=True
    ↓
B区 仍显示直播模式 (优先级更高)
    ↓
当直播结束，回到轮播模式时
    ↓
ModeManager 自动切换到 SONG_REQUEST
    ↓
B区 切换显示点歌队列
```

**场景 3: 用户命令触发模式切换**

```
观众发送: "轮播模式"
    ↓
DanmakuBot 识别模式命令
    ↓
ModeManager.set_mode(Mode.PLAYBACK, "弹幕命令")
    ↓
检查冷却: 模式切换命令 3秒冷却
    ↓
执行切换 (如果被允许)
    ↓
DanmakuBot 返回弹幕反馈
    ↓
PanelRenderer 切换到轮播模式布局
    ↓
OBS 自动刷新显示新面板
```

#### 调试模式切换

在 OBS 中可以通过以下方式验证模式切换：

1. **查看日志**：
   ```
   [14:24:02] main     模式管理器已初始化 (默认轮播模式)
   [14:24:02] danmaku  支持模式切换: 直播模式/PK模式/点歌模式/轮播模式/其他模式
   [14:30:15] panel    面板已生成: data/panel.png
   [14:35:22] panel    面板已生成: data/panel.png  (每1秒一次)
   ```

2. **通过弹幕验证**：
   - 发送 "查看模式" 验证当前模式
   - 发送 "点歌 歌名" 触发自动模式切换
   - 发送 "轮播模式" 手动切换模式

3. **监控 panel.png**：
   - 打开 D:\SingllLive\data\panel.png
   - 实时编辑时刷新查看文件更新
   - 观察面板内容是否变化（表示模式切换）

## 十一、一键启动与自动化

### 11.1 一键启动脚本

创建 `D:\live\start_all.bat`：

```batch
@echo off
chcp 65001 >nul
echo ========================================
echo   程序员深夜电台 - 一键启动
echo ========================================
echo.

:: 1. 创建数据目录（首次运行）
if not exist "D:\live\data" mkdir "D:\live\data"

:: 2. 初始化数据文件
if not exist "D:\live\data\now_playing.txt" echo 等待播放...> "D:\live\data\now_playing.txt"
if not exist "D:\live\data\queue.txt" type nul > "D:\live\data\queue.txt"
if not exist "D:\live\data\ticker.txt" (
    echo 欢迎来到程序员的深夜电台 ♫ 发「点歌 歌名」即可点歌 ♫ 感谢关注~> "D:\live\data\ticker.txt"
)

:: 3. 启动 HTTP 服务器（后台）
echo [1/6] 启动 HTTP 服务器...
start "HTTP-Server" /min cmd /c "cd /d D:\live\data && python -m http.server 8080"
timeout /t 2 >nul

:: 4. 启动 VLC 歌曲轮播（带 HTTP 接口）
echo [2/6] 启动 VLC 歌曲轮播...
start "" "C:\Program Files\VideoLAN\VLC\vlc.exe" "D:\live\songs" ^
    --loop --random ^
    --one-instance ^
    --no-video-title-show ^
    --extraintf=http ^
    --http-host=127.0.0.1 ^
    --http-port=9090 ^
    --http-password=123456
timeout /t 3 >nul

:: 5. 启动歌名同步
echo [3/6] 启动歌名同步服务...
start "NowPlaying-Sync" /min cmd /c "D:\live\scripts\sync_now_playing.bat"

:: 6. 启动 VTube Studio
echo [4/6] 启动 VTube Studio...
start "" "你的VTS安装路径\VTube Studio.exe"
timeout /t 5 >nul

:: 7. 启动 OBS
echo [5/6] 启动 OBS Studio...
start "" "C:\Program Files\obs-studio\bin\64bit\obs64.exe" --startrestreaming --startvirtualcam
timeout /t 5 >nul

:: 8. 启动 Watchdog
echo [6/6] 启动看门狗...
start "Watchdog" /min cmd /c "D:\live\scripts\watchdog.bat"

echo.
echo ========================================
echo   所有服务已启动！
echo   VLC HTTP 接口: http://127.0.0.1:9090
echo   HTTP 服务器:   http://localhost:8080
echo ========================================
echo.
echo 请手动操作：
echo   1. 检查 OBS 画面是否正常
echo   2. 启动直播姬，选择 OBS Virtual Camera
echo   3. 启动弹幕机器人（start_bot.bat）
echo   4. 在直播姬中开始直播
echo.
pause
```

### 11.2 开机自启动

将 `start_all.bat` 的快捷方式放入 Windows 启动文件夹：

```
Win + R → shell:startup → 将 start_all.bat 快捷方式放入
```

或创建 Windows 计划任务：

```batch
:: 创建开机自启动任务
schtasks /create /tn "LiveStreamAutoStart" /tr "D:\live\start_all.bat" /sc onlogon /rl highest
```

### 11.3 一键停止

创建 `D:\live\stop_all.bat`：

```batch
@echo off
echo 正在关闭所有直播相关进程...

taskkill /im vlc.exe /f 2>nul
taskkill /im obs64.exe /f 2>nul
taskkill /im "VTube Studio.exe" /f 2>nul

:: 关闭标题包含 [直播] 的 cmd 窗口
taskkill /fi "WINDOWTITLE eq [直播]*" /f 2>nul

echo 已全部关闭。
pause
```

---

## 十二、开播检查清单

### 挂机直播（日常）

- [ ] 运行 `start_all.bat` 一键启动
- [ ] 检查 VLC 是否在播放歌曲
- [ ] 检查 OBS 画面：A区视频 + B区面板 + C区虚拟人
- [ ] 检查 OBS 虚拟摄像头已开启
- [ ] 打开直播姬，选择 OBS Virtual Camera
- [ ] 启动弹幕机器人（`start_bot.bat`）
- [ ] 直播姬 → 开始直播
- [ ] 在手机 B站 App 上验证直播画面和声音正常

### 互动直播（有空时）

- [ ] 完成挂机直播全部步骤
- [ ] Parsec 连接直播机
- [ ] 测试麦克风音量（VoiceMeeter 输入跳动）
- [ ] OBS 检查麦克风音量条
- [ ] 调整歌曲 vs 语音音量比例

### 唱歌直播（偶尔）

- [ ] 完成基础步骤
- [ ] 接入麦克风/声卡
- [ ] 测试麦克风音量，避免爆音
- [ ] 准备歌单
- [ ] A区切换为歌词/纯色背景

---

## 十三、推广与运营

### 13.1 直播间标题模板

```
【深夜电台】程序员的音乐频道｜点歌/陪伴
【音乐轮播】翻唱歌曲不间断｜发「点歌 歌名」
【互动点歌】程序员的深夜电台｜聊天/音乐
```

### 13.2 简介模板

```
程序员的深夜电台
日常挂机播放喜欢的翻唱歌曲
偶尔折腾代码/AI/技术
偶尔真人唱歌

【点歌方法】发送「点歌 歌名」
【切歌】发送「切歌」
【当前播放】发送「当前」

歌曲来源: 主要是XX的翻唱作品
欢迎程序员/夜猫子/音乐爱好者
```

### 13.3 涨粉策略

| 阶段 | 策略 | 目标 |
|------|------|------|
| 0-100粉 | 挂机时间长、标题SEO、固定时段 | 被搜索到 |
| 100-1000粉 | 增加互动、点歌功能吸引回访 | 提高留存 |
| 1000+粉 | 达标后用OBS直推、画质提升 | 提升体验 |

> **关键指标：** 直播时长 > 互动频次。挂机时长越长，被推荐的概率越高。

---

## 十四、完整文件清单

### 14.1 项目文件结构 (SingllLive)

```
SingllLive/
├─ cyber_live.py              # 主程序 - 统一直播控制系统
├─ requirements.txt           # Python 依赖
├─ README.md                  # 项目说明
├─ start.bat                  # Win10 启动脚本
├─ stop.bat                   # Win10 停止脚本
│
├─ config/
│   └─ config.ini.example     # 配置模板（需复制为 config.ini）
│
├─ modules/                   # Python 模块
│   ├─ songs.py              # 歌曲搜索 + 队列管理
│   ├─ vlc_control.py        # VLC 控制 + 看门狗 + 歌名同步
│   ├─ panel.py              # Pillow 面板渲染器（替代 HTML）
│   └─ danmaku.py            # B站弹幕机器人
│
├─ assets/                    # 静态资源
│   ├─ fonts/
│   │   ├─ JetBrainsMono-Regular.ttf    # 英文等宽字体
│   │   └─ NotoSansCJKsc-Regular.otf    # 中文字体
│   └─ designs/               # OBS 设计素材
│       ├─ background.svg     # 赛博背景
│       └─ frame-overlay.svg  # 边框装饰
│
├─ scripts/                   # 脚本文件
│   └─ obs/
│       └─ panel_refresh.lua  # OBS 面板自动刷新脚本
│
├─ doc/
│   └─ singll-live-guide.md   # 完整使用指南
│
└─ data/                      # 运行时数据（自动生成，.gitignore）
    ├─ panel.png             # B区面板图片
    ├─ now_playing.txt       # 当前播放歌名
    └─ ticker.txt            # 底部字幕
```

### 14.2 部署指南（Windows / Linux）

#### 方案 A：SingllLive 作为项目根目录（推荐）

这是最简单的部署方式。直接克隆或复制 SingllLive 项目到工作目录：

```
/path/to/workspace/
├─ SingllLive/                     # 项目目录（从 GitHub 克隆）
│   ├─ cyber_live.py              # 主程序
│   ├─ config.ini                 # ← 配置文件（复制自 config/config.ini.example）
│   ├─ config/
│   │   └─ config.ini.example     # 配置模板
│   ├─ modules/
│   ├─ scripts/
│   ├─ assets/
│   ├─ start.bat                  # Windows 启动脚本
│   ├── data/                      # 运行时数据（自动生成）
│   │   ├─ panel.png              # B区面板
│   │   ├─ now_playing.txt        # 当前歌名
│   │   └─ ticker.txt             # 底部字幕
│   └─ ...
│
├─ songs/                         # 歌曲库（手动创建并添加音乐文件）
│   ├─ 歌曲1.mp4
│   ├─ 歌曲2.mp3
│   └─ ...
│
└─ （可选的共享数据目录）
    ├─ downloads/                # 临时下载文件
    └─ ...
```

**部署步骤：**

```bash
# 1. 克隆项目（或从 GitHub 下载 zip 解压）
git clone https://github.com/singll/SingllLive.git
cd SingllLive

# 2. 创建歌曲目录（如果不存在）
mkdir songs

# 3. 复制配置文件
cp config/config.ini.example config.ini    # Linux/macOS
# 或
copy config\config.ini.example config.ini  # Windows

# 4. 编辑配置（使用文本编辑器）
notepad config.ini                         # Windows
# 或
nano config.ini                            # Linux/macOS

# 5. 安装依赖（如果需要）
pip install -r requirements.txt
# 或使用专用脚本
python install_dependencies.py             # Python 版本
# install_dependencies.bat                 # Windows 批处理版本

# 6. 启动（Windows）
start.bat
# 或 Linux/macOS
python cyber_live.py
```

---

#### 方案 B：分散目录结构（高级用户）

如果你有多个项目或需要共享配置/数据，可以采用以下结构：

```
/path/to/workspace/
├─ SingllLive/                    # 项目目录（仅包含代码）
│   ├─ cyber_live.py
│   ├─ config/
│   │   └─ config.ini.example    # 模板
│   ├─ modules/
│   ├─ scripts/
│   └─ assets/
│
├─ config/
│   └─ config.ini                # ← 实际配置（需复制自 SingllLive/config/config.ini.example）
│                                 # 编辑此文件中的路径指向其他目录
│
├─ songs/                        # 歌曲库
│   ├─ 歌曲1.mp4
│   └─ ...
│
└─ data/                         # 运行时数据
    ├─ panel.png
    ├─ now_playing.txt
    └─ ticker.txt
```

**启动方式：**

```bash
# 需要明确指定配置文件路径
python SingllLive/cyber_live.py --config config/config.ini
```

---

#### 注意事项

**重要**: 无论采用哪种方案，以下路径必须正确：
- `config.ini` 所在目录（在方案 A 中为项目根目录）
- `config/config.ini.example` 模板文件位置
- `cyber_live.py` 与 `start.bat` 的位置

**调试技巧**：
- `start.bat` 启动时会显示当前工作目录（`当前工作目录: ...`）
- 确保 `config.ini` 与脚本在同一目录或按文档配置好路径

### 14.3 需要安装的软件
|------|------|----------|
| OBS Studio | 画面合成 + 虚拟摄像头 | obsproject.com |
| VLC | 歌曲播放 + HTTP 控制接口 | videolan.org |
| VTube Studio | 虚拟人形象 | Steam |
| B站直播姬 | B站直播推流 | live.bilibili.com |
| blivedm | 弹幕接收（WebSocket） | github.com/xfgryujk/blivedm |
| bilibili-api-python | 弹幕发送 / B站 API 调用 | pypi.org/project/bilibili-api-python |
| Parsec | 远程桌面 + 麦克风传输 | parsec.app |
| VoiceMeeter Banana | 虚拟音频路由 | vb-audio.com |
| Python 3.x | 弹幕机器人运行环境（可选） | python.org |

---

## 附录 A：常见问题

### Q1: OBS 虚拟摄像头画面是黑的？

```
原因: OBS 未启动虚拟摄像头
解决: OBS → 工具 → 虚拟摄像头 → 启动
```

### Q2: B区面板不显示歌名？

```
原因1: HTTP 服务器未启动
  → 运行 start_server.bat

原因2: sync_now_playing.bat 未运行
  → 运行该脚本，检查 now_playing.txt 是否有内容

原因3: VLC HTTP 接口未开启
  → 检查 VLC 启动参数是否包含 --extraintf=http
```

### Q3: 点歌命令没反应？

```
原因1: 弹幕机器人未启动或已崩溃
  → 检查 start_bot.bat 窗口是否在运行
  → 查看控制台有无报错

原因2: B站凭证过期（SESSDATA 有效期约1个月）
  → 重新从浏览器获取 SESSDATA、bili_jct、buvid3
  → 更新 danmaku_bot.py 中的配置

原因3: VLC HTTP 接口未开启
  → 检查 VLC 启动参数是否包含 --extraintf=http
  → 浏览器访问 http://127.0.0.1:9090 测试

原因4: 歌曲文件名不匹配
  → 在 cmd 中手动测试: python -c "import glob; print(glob.glob('D:\\live\\songs\\*恋人心*'))"
```

### Q4: 远程说话没有声音？

```
排查步骤:
1. Parsec 设置中是否开启了麦克风传输
2. VoiceMeeter INPUT 1 是否选了 Parsec Virtual Audio
3. VoiceMeeter INPUT 1 的 B1 按钮是否亮着
4. OBS 麦克风是否选了 VoiceMeeter Output
5. OBS 麦克风音量条是否跳动
```

### Q5: VLC 播放崩溃后自动恢复？

```
确保 watchdog.bat 在运行。它每30秒检查一次 VLC 进程，崩溃后自动重启。
```

---

## 附录 B：后续升级路线

| 阶段 | 升级内容 |
|------|---------|
| **v3.1** | 歌词滚动显示（A区叠加） |
| **v3.2** | AI 弹幕自动回复（接入大语言模型） |
| **v3.3** | 音频可视化波形效果（替代静态视频画面） |
| **v3.4** | 粉丝达标后切换 OBS 直推，提升画质 |
| **v3.5** | 定时任务（不同时段播放不同风格歌曲） |

---

> 版本: v3.0
> 更新日期: 2026-02-14
> 风格: 赛博极客 / 程序员深夜电台

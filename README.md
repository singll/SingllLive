# SingllLive - 程序员深夜电台 直播系统

> 一个统一的 Python 直播控制系统，专为低性能直播机优化

## 概述

**SingllLive** 是直播系统的核心项目，包含了用于控制和管理 B 站直播的所有 Python 服务和工具。

它替代了原来分散的 6+ 个 bat 脚本 + HTML 面板，实现了：
- ✅ VLC 音乐播放 + 自动重启看门狗
- ✅ 歌曲搜索、队列管理
- ✅ B 站弹幕机器人（点歌、切歌、PK）
- ✅ 高性能 B 区终端面板（Pillow 渲染，零 GPU 开销）

## 项目结构

```
SingllLive/
├── cyber_live.py              # 主入口 - 统一的直播控制系统
├── requirements.txt           # Python 依赖
├── README.md                  # 项目说明
├── start.bat                  # Win10 启动脚本
├── stop.bat                   # Win10 停止脚本
├── install_dependencies.bat   # 依赖安装工具（处理 brotli 编译问题）
├── install_dependencies.py    # 依赖安装工具（Python 版本）
├── pip.ini                    # pip 配置（优先预编译 wheels）
│
├── config/                    # 配置文件
│   └── config.ini.example     # 配置模板（需复制为 config.ini）
│
├── modules/                   # Python 模块
│   ├── songs.py              # 歌曲管理 + 队列
│   ├── vlc_control.py        # VLC 控制 + 看门狗 + 同步
│   ├── panel.py              # Pillow 面板渲染器
│   └── danmaku.py            # B站弹幕机器人
│
├── assets/                    # 静态资源
│   ├── fonts/
│   │   ├── JetBrainsMono-Regular.ttf    # 英文等宽字体
│   │   └── NotoSansCJKsc-Regular.otf    # 中文字体
│   └── designs/               # 设计资源（OBS 素材）
│       ├── background.svg    # 赛博背景
│       └── frame-overlay.svg # 边框装饰
│
├── scripts/                   # 脚本文件
│   └── obs/
│       └── panel_refresh.lua # OBS 自动刷新脚本
│
├── doc/                       # 文档
│   └── singll-live-guide.md  # 完整使用指南
│
└── data/                      # 运行时数据（.gitignore）
    ├── panel.png            # B区面板图片（自动生成）
    ├── now_playing.txt      # 当前歌名
    └── ticker.txt           # 底部字幕
```

## 快速开始

### 1. 配置

```bash
# 在项目根目录复制配置模板
copy config\config.ini.example config.ini

# 编辑 config.ini，填入：
# - [bilibili] 直播间号、UID、SESSDATA 等
# - [vlc] VLC 安装路径
# - [paths] 歌曲目录等
```

**重要**: `config.ini` 应该在**项目根目录**，而不是 `config/` 子目录！

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动

```bash
# Win10 直播机上：
.\start.bat

# 或手动启动：
python cyber_live.py
```

### 4. OBS 配置

1. **B区面板**: 添加 **图像源** -> 选择项目 `data` 目录下的 `panel.png`
   - 示例路径（Linux）: `/path/to/project/data/panel.png`
   - 示例路径（Windows）: `C:\Users\YourName\Projects\SingllLive\data\panel.png`
   - 或使用文件浏览器选择
2. **OBS 脚本**: 工具 → 脚本 → 加载 `scripts/obs/panel_refresh.lua`
3. 完成！面板会每 1 秒自动刷新（支持实时北京时间显示）

## ⚠️ 依赖安装故障排除

如果遇到 `brotli` 编译错误（`Microsoft Visual C++ 14.0 or greater is required`），请尝试以下方法：

### 方法 1：使用专用安装脚本（推荐）

```bash
# Windows 批处理脚本
.\install_dependencies.bat

# 或 Python 脚本
python install_dependencies.py
```

### 方法 2：手动指定 pip 参数

```bash
# 仅使用预编译 wheels（最严格）
pip install --only-binary :all: -r requirements.txt

# 优先预编译，允许回退编译
pip install --prefer-binary -r requirements.txt

# 跳过 brotli，安装其他依赖
pip install --prefer-binary --no-binary brotli blivedm bilibili-api-python aiohttp Pillow
```

### 方法 3：安装 Visual C++ Build Tools（根本解决）

1. 下载：https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. 安装（选择 "Desktop development with C++"）
3. 重启 Windows
4. 重新运行 `start.bat`

### 方法 4：使用 pip 配置文件

项目根目录已包含 `pip.ini`，自动优先使用预编译 wheels。如果仍有问题，可以手动编辑该文件。

## ⚠️ 路径和配置问题排除

如果遇到 `config.ini` 找不到或路径错误的问题：

### 使用诊断工具

```bash
# Windows
.\diagnose.bat

# Linux/macOS
python -c "
import os
import sys
print('项目根目录:', os.getcwd())
print('cyber_live.py:', 'exists' if os.path.exists('cyber_live.py') else 'missing')
print('config.ini:', 'exists' if os.path.exists('config.ini') else 'missing')
print('config/config.ini.example:', 'exists' if os.path.exists('config/config.ini.example') else 'missing')
"
```

### 常见问题

**Q: start.bat 显示 config.ini 不存在，但我已经复制了**

A: 这通常是因为：
1. `config.ini` 放在了错误的目录（应该在项目根目录，与 `cyber_live.py` 同级）
2. 脚本不在项目根目录运行（检查"当前工作目录"输出）

**Q: "当前工作目录" 显示的不是我的项目目录**

A: 确保 `start.bat` 与 `cyber_live.py` 在同一目录。脚本会自动切换到这个目录。

**Q: 我的项目目录名不是 `SingllLive`**

A: 这没有问题！脚本是相对路径的，与目录名无关。只要 `start.bat` 和 `cyber_live.py` 在一起就可以。

## 性能对比

| 指标 | 原方案 | SingllLive |
|------|--------|-----------|
| GPU 负担 | Chromium + CSS 动画 | **零** (静态PNG) |
| 运行进程 | ~8 个 | **3 个** (VLC+OBS+Python) |
| 内存 (B区面板) | ~150MB | **~30MB** |
| 启动时间 | 30+ 秒 | **5-10 秒** |

## 核心功能

### VLC 控制
- 自动启动、循环播放
- HTTP 接口控制（弹幕点歌）
- 自动重启看门狗（5秒检测一次）
- 歌名同步到文件（OBS 底部字幕用）

### 歌曲管理
- 自动扫描歌曲目录
- 模糊搜索（支持中文）
- 队列管理（支持弹幕添加）

### 弹幕机器人
- `点歌 歌名` - 播放歌曲
- `切歌` - 下一首
- `当前` - 显示当前播放
- `歌单` - 列出可点歌曲
- `PK` - 向女主播发起PK（仅主播）

### B区面板
- 终端风格（完全仿 HTML 原版）
- 绿/青/品红 配色
- 系统状态 + 当前歌名 + 北京时间 + 队列列表
- 增大字体尺寸，直播易于看清
- 实时北京时间显示（精确到秒）
- CJK 中文字体自动支持
- **零 GPU 开销**（相比 Chromium 节省 ~150MB 内存 + 显著 GPU 减压）

## 文档

详细使用指南见 [singll-live-guide.md](doc/singll-live-guide.md)

## 技术栈

- **Python 3.8+**
- **asyncio** - 异步并发
- **Pillow** - 图像渲染
- **aiohttp** - HTTP 客户端
- **blivedm** - B站弹幕接收
- **bilibili-api-python** - B站 API

## 环境要求

- Windows 10 或更新版本
- Python 3.8+
- VLC 播放器
- OBS Studio

## 许可证

MIT

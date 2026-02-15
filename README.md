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
│   ├── obs/
│   │   └── panel_refresh.lua # OBS 自动刷新脚本
│   └── windows/
│       ├── start.bat         # Win10 启动脚本
│       └── stop.bat          # Win10 停止脚本
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
# 复制配置模板
copy config\config.ini.example config\config.ini

# 编辑 config.ini，填入：
# - [bilibili] 直播间号、UID、SESSDATA 等
# - [vlc] VLC 安装路径
# - [paths] 歌曲目录等
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动

```bash
# Win10 直播机上：
.\scripts\windows\start.bat

# 或手动：
python cyber_live.py
```

### 4. OBS 配置

1. **B区面板**: 添加 **图像源** -> `D:\live\data\panel.png`
2. **OBS 脚本**: 工具 → 脚本 → 加载 `scripts/obs/panel_refresh.lua`
3. 完成！面板会每 3 秒自动刷新

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
- 系统状态 + 当前歌名 + 队列列表
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

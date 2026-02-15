# SingllLive - 程序员深夜电台 统一直播控制系统

> 完全自动化、多模式的 Python 直播系统 | 替代 6+ 个 bat 脚本 + HTML 面板

## 项目简介

**SingllLive** 是一个统一的 Python 直播控制系统，将原来分散的多个脚本和 HTML 面板整合成单一 Python 项目。

### 核心特性

- ✅ **多模式播放系统** - 5种模式（直播/PK/点歌/轮播/空闲）自动切换
- ✅ **VLC 自动管理** - 根据模式自动启动/暂停/停止，零资源浪费
- ✅ **B站弹幕机器人** - 实时点歌、切歌、PK、模式切换
- ✅ **高性能B区面板** - Pillow PNG 渲染，零 GPU 开销（替代 Chromium）
- ✅ **歌曲管理** - 自动索引、模糊搜索、队列管理

## 屏幕布局（ABC 三区制）

```
1920×1080 OBS 直播画布

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  A 区 (1344×756)              B 区 (520×435)   C 区 (520×595)│
│  VLC 16:9 视频内容           动态面板            VTubeStudio │
│  - 背景音乐                   - 直播信息          虚拟人      │
│  - 音乐视频                   - 队列列表                      │
│  - 循环播放                   - 歌曲信息                      │
│                               - 北京时间                      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 各区域说明

| 区域 | 尺寸 | 内容 | 数据源 |
|------|------|------|--------|
| **A区** | 1344×756 | VLC 播放的音乐/视频 | VLC HTTP API |
| **B区** | 520×435 | 模式相关的动态信息面板 | Python 生成 PNG |
| **C区** | 520×595 | VTubeStudio 虚拟人捕获 | 窗口捕获 |

详见 [完整配置指南](doc/singll-live-guide.md) 获取精确的像素坐标和 OBS 配置步骤。

## 快速开始

### 1️⃣ 配置

```bash
# 复制配置模板到项目根目录
copy config\config.ini.example config.ini

# 编辑 config.ini，填入：
# - [bilibili] 直播间号、UID、SESSDATA 等
# - [vlc] VLC 安装路径
# - [paths] 歌曲目录等
```

### 2️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

> ⚠️ 首次安装会从 GitHub 克隆 blivedm，需要 Git 已安装。详见 [配置详解](doc/singll-live-guide.md#四配置详解)

### 3️⃣ 启动系统

```bash
# Windows
.\start.bat

# 或手动启动
python cyber_live.py
```

### 4️⃣ OBS 配置

1. **B区面板**: 添加**图像源** → 选择 `data/panel.png`
2. **自动刷新**: 工具 → 脚本 → 加载 `scripts/obs/panel_refresh.lua`
3. 完成！面板每 1 秒自动更新

详见 [屏幕布局与 ABC 区域配置](doc/singll-live-guide.md#二屏幕布局与-abc-区域)

## 项目结构

```
SingllLive/
├── cyber_live.py              # 主入口 (asyncio 事件循环)
├── config.ini.example         # 配置模板
├── requirements.txt           # Python 依赖
│
├── modules/                   # Python 模块
│   ├── songs.py              # 歌曲管理 + 队列
│   ├── vlc_control.py        # VLC 控制 + 看门狗
│   ├── panel.py              # Pillow 面板渲染
│   ├── modes.py              # 模式管理系统
│   ├── danmaku.py            # 弹幕机器人
│   └── brotli_patch.py       # Python 3.14 兼容性补丁
│
├── assets/                    # 静态资源
│   ├── fonts/
│   │   ├── JetBrainsMono-Regular.ttf
│   │   └── NotoSansCJKsc-Regular.otf
│   └── designs/
│       ├── background.svg    # 赛博背景
│       └── frame-overlay.svg # 边框装饰
│
├── scripts/                   # OBS 脚本
│   └── obs/panel_refresh.lua # OBS 自动刷新脚本
│
├── data/                      # 运行时数据 (自动生成)
│   ├── panel.png            # B区面板
│   ├── now_playing.txt      # 当前歌名
│   └── ticker.txt           # 底部字幕
│
└── doc/                       # 文档
    └── singll-live-guide.md  # 完整技术指南
```

## 弹幕命令

```
点歌 歌名      - 搜索并播放歌曲
切歌          - 跳过当前歌曲
当前          - 显示当前播放歌曲
歌单          - 显示歌曲库列表
帮助/命令     - 显示支持的命令

直播模式      - 切换到直播模式（优先级 1）
PK模式        - 切换到 PK 模式（优先级 2）
点歌模式      - 切换到点歌模式（优先级 2）
轮播模式      - 切换到轮播模式（优先级 3）
其他模式      - 切换到空闲模式（优先级 4）
查看模式      - 显示当前模式和优先级
```

## 技术栈

- **Python 3.8+** (推荐 3.10+)
- **asyncio** - 异步并发
- **Pillow** - 图像渲染
- **aiohttp** - HTTP 客户端
- **blivedm** - B站弹幕接收
- **bilibili-api-python** - B站 API

## 性能指标

| 指标 | 原方案 (HTML) | SingllLive |
|------|---------------|-----------|
| GPU 负担 | Chromium + CSS 动画 | **零** (静态 PNG) |
| 运行进程 | ~8 个 | **3 个** (VLC+OBS+Python) |
| 内存占用 (B区) | ~150MB | **~30MB** |
| 启动时间 | 30+ 秒 | **5-10 秒** |

## 故障排查

遇到问题？请查阅：

- **配置问题** → [配置详解](doc/singll-live-guide.md#四配置详解)
- **VLC 不播放** → [故障排查](doc/singll-live-guide.md#六故障排查)
- **面板不更新** → [故障排查](doc/singll-live-guide.md#六故障排查)
- **弹幕命令无响应** → [故障排查](doc/singll-live-guide.md#六故障排查)
- **依赖安装错误** → [安装步骤](doc/singll-live-guide.md#三快速开始)

## 环境要求

- Windows 10/11 或 Linux
- Python 3.8+
- Git (用于安装 blivedm)
- VLC 播放器
- OBS Studio

## 完整文档

更多详细信息请参考：**[完整使用指南](doc/singll-live-guide.md)**

包含内容：
- 系统概述和技术栈
- ABC 区域详细配置
- 快速开始步骤
- 配置详解
- 工作流程
- 故障排查指南

## 许可证

MIT

---

**问题反馈**: 遇到 bug 或有功能建议？欢迎提交 Issue 或 Pull Request！

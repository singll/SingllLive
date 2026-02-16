# SingllLive - 程序员深夜电台

> 全自动多模式 B站直播控制系统

## 核心特性

- **OBS WebSocket v5 控制** — 通过 WebSocket 直接控制 VLC 源播放列表和源可见性
- **多模式系统** — 直播/PK/点歌/轮播/空闲 5 种模式，自由切换
- **弹幕机器人** — 实时点歌、切歌、模式切换
- **终端风格面板** — Pillow PNG 渲染，零 GPU 开销
- **歌曲管理** — 自动索引、模糊搜索、队列管理

## 屏幕布局

```
1920×1080 OBS 画布

┌────────────────────────────────────┬──────────────┐
│                                    │  B区 520×435  │
│  A区 1344×756                      │  信息面板     │
│  VLC 视频/音乐                     ├──────────────┤
│                                    │  C区 532×488  │
│                                    │  VTuber/房间   │
└────────────────────────────────────┴──────────────┘
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置
copy config\config.ini.example config.ini
# 编辑 config.ini，填入 B站凭证、OBS WebSocket 密码、歌曲目录

# 3. 启动
python cyber_live.py
```

详细配置步骤见 [快速配置指南](doc/QUICK_START.md)

## 项目结构

```
SingllLive/
├── cyber_live.py              # 主入口
├── config/config.ini.example  # 配置模板
├── requirements.txt           # 依赖
├── modules/
│   ├── obs_control.py         # OBS WebSocket v5 控制器
│   ├── vlc_control.py         # VLC 源播放控制
│   ├── modes.py               # 模式管理系统
│   ├── danmaku.py             # 弹幕机器人
│   ├── panel.py               # 面板渲染
│   ├── songs.py               # 歌曲管理
│   └── brotli_patch.py        # Python 3.14 兼容
├── assets/fonts/              # 字体
└── doc/                       # 文档
```

## 弹幕命令

| 命令 | 功能 |
|------|------|
| `点歌 歌名` | 搜索并播放 |
| `切歌` | 下一首 |
| `当前` | 当前播放 |
| `歌单` | 歌曲库 |
| `直播模式` / `轮播模式` / `PK模式` / `点歌模式` / `其他模式` | 切换模式 |
| `查看模式` | 当前模式 |
| `帮助` | 命令列表 |

## 模式切换

所有模式之间可以自由切换，通过弹幕命令即可。
点歌行为：直播模式下点歌加入队列，其他模式立即播放。

## 环境要求

- Windows 10/11 或 Linux
- Python 3.8+
- OBS Studio 28+ (内置 WebSocket v5)
- Git (安装 blivedm)

## 技术栈

Python asyncio / obsws-python / blivedm / bilibili-api-python / Pillow / aiohttp

---

MIT License

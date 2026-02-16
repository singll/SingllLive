# 快速配置指南

> 5 分钟快速上手

---

## 架构概览

```
弹幕命令 / 自动检测
    │
    ▼
Python 模式管理器
    │
    ├── OBS WebSocket → VLC 源播放列表 / 源可见性
    ├── 面板渲染 → panel.png → OBS 图像源刷新
    └── 弹幕回复 → B站直播间
```

**核心改进**: 通过 OBS WebSocket v5 直接控制 OBS，无需 Lua 脚本和文件监听。

---

## 第一步：安装依赖

```bash
pip install -r requirements.txt
```

关键依赖：
- `obsws-python` — OBS WebSocket v5 控制
- `blivedm` — B站弹幕接收
- `bilibili-api-python` — B站弹幕发送
- `Pillow` — 面板渲染

---

## 第二步：配置文件

```bash
copy config\config.ini.example config.ini
```

编辑 `config.ini`，填入：

### [bilibili] B站凭证
```ini
room_id = 你的直播间号
uid = 你的B站UID
sessdata = (浏览器 F12 → Application → Cookies)
bili_jct = (同上)
buvid3 = (同上)
```

### [obs] OBS WebSocket
```ini
host = localhost
port = 4455
password = (OBS WebSocket 设置中的密码)
scene_name = AScreen
vlc_source = vlc_player
broadcast_source = broadcast_screen
panel_source = B区-终端面板
```

### [paths] 路径
```ini
song_dir = D:\live\songs\queue
playback_dir = D:\live\songs\playback
data_dir = D:\live\data
```

---

## 第三步：配置 OBS

### 3.1 开启 WebSocket 服务器

```
OBS → 工具 → WebSocket服务器设置
  ☑ 启用 WebSocket 服务器
  端口: 4455
  密码: (设置一个密码，填入 config.ini)
```

### 3.2 创建场景和源

创建 **AScreen** 场景，添加以下源：

| 源名称 | 类型 | 说明 |
|--------|------|------|
| `vlc_player` | VLC 视频源 | 播放视频/音乐 (☑循环 ☑随机) |
| `broadcast_screen` | 窗口捕获/采集卡 | 直播画面 |
| `B区-终端面板` | 图像 | 指向 `data\panel.png` |

源名称必须与 config.ini 中的配置一致。

### 3.3 面板图像源

面板 PNG 由程序生成，通过 OBS WebSocket 自动刷新（每秒）。

---

## 第四步：启动

```bash
python cyber_live.py
```

正常输出：
```
[14:24:08] main     歌曲库: 50 首
[14:24:08] main     模式管理器已初始化
[14:24:08] obs      OBS WebSocket 已连接: localhost:4455
[14:24:08] vlc      VLC 控制器已初始化 (OBS WebSocket 模式)
[14:24:08] danmaku  弹幕机器人启动 (直播间 12345)
[14:24:08] main     程序员深夜电台 - 所有服务已启动
```

---

## 弹幕命令

| 命令 | 功能 |
|------|------|
| `点歌 歌名` | 搜索并播放歌曲 |
| `切歌` | 跳到下一首 |
| `当前` | 查看当前播放 |
| `歌单` | 查看歌曲库 |
| `查看模式` | 查看当前模式 |
| `直播模式` | 切换到直播模式 (最高优先级) |
| `PK模式` | 切换到PK模式 |
| `轮播模式` | 切换到轮播模式 |
| `点歌模式` | 切换到点歌模式 |
| `其他模式` | 切换到空闲模式 |
| `帮助` | 显示命令列表 |

---

## 模式优先级

```
直播模式 (1) > PK模式 (2) > 轮播/点歌/其他 (3)
```

- 高优先级模式运行时，低优先级模式无法切入
- 同优先级模式之间可以自由切换
- 直播模式下点歌会添加到队列，轮播时自动播放

---

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| OBS 连接失败 | 确保 OBS 已启动并开启 WebSocket (工具 → WebSocket服务器设置) |
| VLC 无画面 | 检查歌曲目录不为空，源名称与配置一致 |
| 面板不刷新 | 检查 panel.png 路径正确，确认 OBS WebSocket 已连接 |
| 弹幕不回复 | 检查 B站凭证 (sessdata/bili_jct)，可能已过期 |
| 模式切换失败 | 检查是否被高优先级模式阻止 (发"查看模式"确认) |

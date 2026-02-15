# Plan A 实现：文件系统模式播放列表管理

> **版本**: 1.0 - Plan A 文件系统实现
> **日期**: 2026-02-15
> **核心改进**: 删除外挂 VLC 进程，改用 .m3u 播放列表文件控制 OBS 内置 libvlc

---

## 📋 Overview

**Plan A** 是 SingllLive 直播系统的最终优化方案，核心特点：

| 方面 | Plan A+ (已弃用) | Plan A (当前) |
|------|----------|---------|
| **VLC 实例** | 1 个外挂进程（HTTP API 控制） | 0 个外挂进程 |
| **播放列表管理** | VLC HTTP API 动态切换 | 生成 .m3u 文件 |
| **OBS 集成** | OBS VLC 源连接外挂 VLC | OBS VLC 源直接读取 .m3u 文件 |
| **启动流程** | start.bat 启动外挂 VLC | start.bat 仅启动 Python 后端 |
| **依赖** | VLC 安装、HTTP 接口启用 | 无额外依赖 |
| **系统复杂度** | 中等（多进程通信） | 简单（文件系统） |
| **用户体验** | ✅ 无缝切换 | ✅ 无缝切换（资源占用更低） |

---

## 🎯 工作原理

### Plan A 架构流程

```
模式变化 (mode.txt)
    ↓
cyber_live.py 检测模式变化
    ↓
VLCController.write_playlist_file() 方法
    ↓
扫描目录，生成 .m3u 播放列表内容
    ↓
轮转播放列表文件 (.0.m3u → .1.m3u → .2.m3u → .0.m3u)
    ↓
更新 current_playlist_status.txt（供OBS脚本读取）
    ↓
OBS 脚本检测到文件路径变化
    ↓
更新 VLC 源的 playlist 属性
    ↓
OBS VLC 源重新加载新的 .m3u 文件
    ↓
直播画面无缝切换 ✓
```

### 关键组件

**1. VLCController** (`modules/vlc_control.py`)
```python
# 核心方法
def _get_m3u_content(directory: str) -> str
    # 扫描目录，生成 M3U 格式内容

def _rotate_playlist_file() -> None
    # 轮转文件指针 (0 → 1 → 2 → 0)
    # OBS VLC源只有在文件路径改变时才会重新加载
    # 通过轮转文件名强制重新加载

def write_playlist_file(mode: str, directory: str) -> bool
    # 1. 轮转文件指针
    # 2. 将 M3U 内容写入 current_playlist.{rotation}.m3u
    # 3. 更新 current_playlist_status.txt
    # 返回成功/失败

async def play(filepath: str) -> bool
    # 点歌即时播放
    # 1. 轮转文件指针
    # 2. 生成单文件列表
    # 3. 写入旋转的 .m3u 文件
```

**2. 模式管理循环** (`cyber_live.py`)
```python
async def _vlc_mode_manager_loop(vlc, mode_manager, interval=3.0)
    # PLAYBACK → write_playlist_file("playback", playback_dir)
    # SONG_REQUEST → write_playlist_file("song_request", song_dir)
    # BROADCAST/PK → write_playlist_file("paused", "")
    # OTHER → write_playlist_file("other", "")
```

**3. OBS 配置**
```
AScreen 场景
  ├── vlc_player 源（指向 current_playlist.0.m3u）
  │   - 位置: (18, 18), 大小: 1344×756
  │   - ☑ 循环，☑ 随机
  │   - NOTE: 初始设置为 .0.m3u，路径会由脚本自动更新
  ├── lyrics_display 源
  ├── broadcast_screen 源
  └── pk_background 源

ascreen_source_switcher.lua (OBS 脚本)
  - 监听 mode.txt（模式变化）
  - 监听 current_playlist_status.txt（文件轮转）
  - 根据模式切换源可见性
  - 根据status文件更新VLC源playlist属性
```

---

## 📂 目录结构

```
SingllLive/
├── songs/                          # 歌曲库根目录
│   ├── playback/                   # 轮播歌曲库
│   │   ├── 歌手A/
│   │   │   ├── 歌曲1.mp3
│   │   │   └── 歌曲2.mp3
│   │   └── 歌手B/
│   │       └── ...
│   │
│   └── queue/                      # 点歌队列（动态）
│       ├── 歌曲A.mp3
│       ├── 歌曲B.mp4
│       └── ...
│
├── data/                           # 运行时数据
│   ├── current_playlist.0.m3u     # ✨ 轮转的播放列表文件 1
│   ├── current_playlist.1.m3u     # ✨ 轮转的播放列表文件 2
│   ├── current_playlist.2.m3u     # ✨ 轮转的播放列表文件 3
│   ├── current_playlist_status.txt # 当前活跃的.m3u文件路径（OBS脚本读取）
│   ├── mode.txt                    # 当前模式
│   ├── panel.png                   # 动态面板
│   └── now_playing.txt             # 当前歌名
│
├── cyber_live.py                   # 主程序
├── start.bat                       # 启动脚本（仅启动 Python，不启动 VLC）
├── config.ini                      # 配置文件
└── modules/
    └── vlc_control.py              # VLC 控制器（Plan A 版）
```

---

## ⚙️ 配置指南

### config.ini 配置

```ini
[paths]
; 点歌队列目录
song_dir = D:\live\songs\queue

; 轮播目录
playback_dir = D:\live\songs\playback

; 运行时数据目录（生成的 .m3u 文件会存放这里）
data_dir = D:\live\data

[vlc]
; 以下配置在 Plan A 中不再使用，仅保留用于向后兼容
path = C:\Program Files\VideoLAN\VLC\vlc.exe
http_port = 9090
http_password = 123456
```

### OBS VLC 源配置

**步骤 1**: 在 AScreen 场景中添加 VLC 视频源
```
OBS → AScreen 场景 → 源 → [+] → VLC 视频源
名称: vlc_player
```

**步骤 2**: 配置播放列表

```
VLC 视频源属性 → 播放列表

添加文件：
  选择 SingllLive/data/current_playlist.0.m3u
  (OBS脚本会自动轮转路径，所以初始配置 .0.m3u 即可)

选项：
  ☑ 循环播放
  ☑ 随机播放
  ☑ 暂停后自动播放
```

**重要说明**: OBS VLC源的playlist属性会由 `ascreen_source_switcher.lua` 脚本自动更新，
当 `current_playlist_status.txt` 文件改变时，脚本会更新VLC源指向新的文件路径，
强制OBS VLC重新加载播放列表内容。

**步骤 3**: 配置位置和大小
```
位置: (18, 18)
大小: 1344 × 756
缩放类型: 缩放以适应窗口
```

---

## 🔄 模式切换工作流

### 轮播 → 点歌 切换示例

```timeline
T0: 轮播模式运行中
    cyber_live.py 定期检查模式
    current_playlist.m3u 包含轮播目录的歌曲

T1: 用户弹幕 "点歌 三体"
    danmaku.py 处理命令
    将歌曲添加到 songs/queue/
    更新 mode.txt: "song_request"

T2: VLC 模式管理循环检测到模式变化
    current_mode = SONG_REQUEST
    调用: vlc.write_playlist_file("song_request", "songs/queue")

    动作:
    1. 扫描 songs/queue/ 目录
    2. 找到所有媒体文件
    3. 生成 .m3u 格式内容
    4. 写入 data/current_playlist.m3u

T3: OBS VLC 源监听到文件更新
    自动重新加载 current_playlist.m3u
    VLC 读取新的播放列表
    开始播放点歌队列

T4: OBS 脚本检测到模式变化
    检测 mode.txt = "song_request"
    vlc_player 源保持显示 ✓
    lyrics_display 更新为点歌界面

用户体验:
    直播画面从轮播歌曲平滑切换到点歌歌曲 ✓
    无黑屏，无卡顿 ✓
```

---

## 📊 .m3u 播放列表格式

Plan A 生成的 `current_playlist.m3u` 文件示例：

```m3u
#EXTM3U
#EXTINF:-1,歌曲1.mp3
file:///D:/live/songs/playback/歌手A/歌曲1.mp3
#EXTINF:-1,歌曲2.mp3
file:///D:/live/songs/playback/歌手B/歌曲2.mp3
#EXTINF:-1,歌曲3.mp4
file:///D:/live/songs/playback/歌手A/MV/歌曲3.mp4
```

**格式说明**:
- `#EXTM3U` - M3U 文件头（必需）
- `#EXTINF:-1,标题` - 媒体条目信息
- `file:///路径` - 文件 URI（支持 Windows 路径）

---

## 🎬 启动步骤

### 1. 准备目录结构

```bash
# 创建必要的目录
mkdir SingllLive\songs\playback
mkdir SingllLive\songs\queue
mkdir SingllLive\data

# 将轮播歌曲放入 playback 目录
# 将初始点歌队列放入 queue 目录（可为空）
```

### 2. 配置文件

编辑 `config.ini`，配置正确的目录路径：
```ini
song_dir = D:\live\songs\queue
playback_dir = D:\live\songs\playback
data_dir = D:\live\data
```

### 3. 启动后端

```bash
# 双击 start.bat 或在 PowerShell 中运行
python cyber_live.py

# 观察日志输出
# [vlc] VLC 播放列表管理器已初始化 (Plan A - 无外挂进程)
# [vlc]   - 轮播目录: D:\live\songs\playback
# [vlc]   - 点歌目录: D:\live\songs\queue
# [vlc]   - 播放列表文件: D:\live\data/current_playlist.m3u
```

### 4. OBS 配置

- 在 OBS 的 AScreen 场景中添加 VLC 视频源
- 配置 VLC 源指向 `current_playlist.m3u`
- 启用循环和随机播放选项
- 设置正确的位置和大小 (18, 18, 1344×756)

### 5. 验证工作

```
启动后端 →（等待日志提示初始化完成）→

弹幕: "轮播模式"
→ 检查 OBS vlc_player 源是否显示轮播歌曲 ✓

弹幕: "点歌 歌名"
→ 检查 songs/queue 目录是否有歌曲
→ 检查 OBS vlc_player 源是否切换到点歌歌曲 ✓

弹幕: "直播模式"
→ 检查 OBS vlc_player 源是否隐藏 ✓
→ 检查 broadcast_screen 源是否显示 ✓
```

---

## 🔄 VLC 播放列表轮转机制（2026-02-15 更新）

### 问题背景

OBS 内置 libvlc 有一个架构限制：
- ✗ 只有当 `.m3u` **文件路径改变** 时才会重新加载
- ✗ 不会监听 `.m3u` 文件的 **内容变化**
- 结果：直接修改 `current_playlist.m3u` 内容无法让 VLC 切换新歌曲

### 解决方案：三文件轮转

采用**轮流使用三个播放列表文件**的策略强制 OBS 重新加载：

```
轮转序列: .0.m3u → .1.m3u → .2.m3u → .0.m3u → ...

每次切换时：
1. 轮转文件指针 (0 → 1 → 2 → 0)
2. 写入新内容到新文件路径
3. 更新 status 文件（告诉 OBS 脚本当前文件）
4. OBS 脚本检测文件变化
5. 更新 VLC 源的 playlist 属性
6. OBS VLC 重新加载新路径的文件
```

### 实现细节

**Python 后端 (vlc_control.py)**:
```python
# 轮转计数器（初始值0）
self._playlist_rotation = 0  # 0, 1, 2

# 轮转文件指针
def _rotate_playlist_file(self) -> None:
    self._playlist_rotation = (self._playlist_rotation + 1) % 3
    self._write_playlist_status_file()

# 获取当前文件名
def _get_rotated_playlist_file(self) -> str:
    return f"{base_name}.{self._playlist_rotation}.m3u"
    # 返回: current_playlist.0.m3u 或 .1.m3u 或 .2.m3u

# 写入状态文件
def _write_playlist_status_file(self) -> None:
    # 写入当前文件路径到 current_playlist_status.txt
    # 供 OBS 脚本读取
```

**OBS 脚本 (ascreen_source_switcher.lua)**:
```lua
-- 读取 status 文件
function read_playlist_status_file()
    local file = io.open(playlist_status_file, "r")
    if file == nil then return nil end
    local content = file:read("*a")
    file:close()
    return content:match("^%s*(.-)%s*$")
end

-- 刷新 VLC 源
function refresh_vlc_source()
    local current_file = read_playlist_status_file()
    if current_file == last_playlist_file then
        return  -- 文件未改变，跳过
    end

    -- 文件已改变，更新 VLC 源的 playlist 属性
    local settings = obs.obs_source_get_settings(vlc_source)
    obs.obs_data_set_string(settings, "playlist", current_file)
    obs.obs_source_update(vlc_source, settings)
    obs.obs_data_release(settings)
    last_playlist_file = current_file
end

-- 定时检查（每 1000ms）
function check_mode_change()
    -- ... 检查 mode.txt ...
    refresh_vlc_source()  -- 同时检查 status 文件
end
```

### 时间流程示例

```timeline
用户弹幕: "点歌 稻香"
    ↓ T0
danmaku.py 将歌曲下载到 songs/queue/
mode_manager 切换到 SONG_REQUEST
    ↓ T1
cyber_live.py 检测到模式变化
vlc.write_playlist_file("song_request", "songs/queue")
    ├─ 轮转: _playlist_rotation = 1 (从0变成1)
    ├─ 生成 M3U 内容（只含 稻香.mp3）
    ├─ 写入 current_playlist.1.m3u
    └─ 更新 current_playlist_status.txt = "current_playlist.1.m3u"
    ↓ T2 (~1000ms)
OBS 脚本定时检查:
ascreen_source_switcher.lua
    ├─ 读取 current_playlist_status.txt
    ├─ 发现文件从 .0.m3u 变成 .1.m3u
    └─ 更新 VLC 源的 playlist 属性为 .1.m3u
    ↓ T3
OBS VLC 源检测到路径改变
    ├─ 停止播放旧文件
    ├─ 加载 current_playlist.1.m3u
    ├─ 播放 稻香.mp3
    └─ 用户听到点歌 ✓
```

### 配置清单

**Python 配置 (config.ini)**:
```ini
[paths]
song_dir = D:\live\songs\queue
playback_dir = D:\live\songs\playback
data_dir = D:\live\data
```

**OBS 脚本配置 (ascreen_source_switcher.lua 属性)**:
```
Mode文件路径: D:/live/data/mode.txt
播放列表状态文件: D:/live/data/current_playlist_status.txt  ← 新增
AScreen场景名称: AScreen
检查间隔(ms): 1000
```

**OBS VLC 源初始配置**:
- 选择 `D:\live\data\current_playlist.0.m3u` 作为初始路径
- 脚本会自动轮转路径，无需手动更改

---

### 问题 1: OBS VLC 源显示黑屏

**原因**: 播放列表为空或目录不存在

**解决方案**:
1. 检查 songs/playback 或 songs/queue 目录中是否有媒体文件
2. 检查 data/current_playlist.m3u 文件是否存在
3. 检查文件路径是否正确（避免空格和特殊字符）
4. 在 OBS 中右键 VLC 源 → 刷新

### 问题 2: 切换模式时 VLC 不更新

**原因**: OBS VLC 源没有检测到文件更新（文件内容变化但路径不变）

**解决方案**:
1. 确认 `current_playlist.0/1/2.m3u` 文件都存在
2. 确认 `current_playlist_status.txt` 存在且可读
3. 检查 cyber_live.py 日志，搜索关键词 "播放列表轮转"
4. 检查 OBS 脚本日志，搜索关键词 "VLC源播放列表已更新"
5. 在 OBS 脚本属性中启用 "调试模式" 查看详细日志
6. 如果 status 文件未更新，检查 data_dir 路径权限

### 问题 3: songs/queue 目录中的歌曲没有播放

**原因**: 点歌模式下播放列表未正确生成

**解决方案**:
1. 确认点歌系统正确将歌曲添加到 songs/queue
2. 检查 cyber_live.py 日志中的 "切换到点歌模式" 消息
3. 手动检查 data/current_playlist.m3u 文件内容
4. 确认 songs/queue 目录中文件路径有效

### 问题 4: Windows 路径显示为 forward slashes

**说明**: 这是正常的！
```
# VLC 在 Windows 上既支持反斜杠也支持正斜杠
file:///D:/live/songs/playback/song.mp3  ✓
file:///D:\live\songs\playback\song.mp3  ✗ (VLC 不推荐)
```

---

## 📝 关键文件说明

### modules/vlc_control.py (Plan A 版)

```python
class VLCController:
    """OBS VLC 源的播放列表管理器 (Plan A - 无外挂 VLC 进程)"""

    def __init__(self, vlc_path, http_port, http_password,
                 song_dir, song_manager, playback_dir=None,
                 playlist_file="current_playlist.m3u"):
        # 注意：vlc_path, http_port, http_password 参数仅保留向后兼容
        # 在 Plan A 中不再使用

        self.song_dir = song_dir              # 点歌队列目录
        self.playback_dir = playback_dir      # 轮播目录
        self.playlist_file = playlist_file    # .m3u 文件路径
        self._current_playlist_mode = None    # 模式追踪

    def _get_m3u_content(self, directory: str) -> str:
        """生成 .m3u 播放列表内容"""
        # 1. 扫描目录中的媒体文件
        # 2. 支持子目录递归扫描
        # 3. 返回 M3U 格式内容

    def write_playlist_file(self, mode: str, directory: str) -> bool:
        """将播放列表写入 .m3u 文件"""
        # 1. 避免重复切换（检查 _current_playlist_mode）
        # 2. 生成播放列表内容
        # 3. 写入文件（UTF-8 编码）
        # 4. 返回成功/失败
```

### cyber_live.py 改进

```python
async def _vlc_mode_manager_loop(vlc, mode_manager, interval=3.0):
    """VLC 播放列表管理循环 (Plan A - 文件系统模式)"""

    # 不再调用:
    # - vlc.start_vlc()          (删除)
    # - vlc.set_playlist_directory() (已迁移到 write_playlist_file)
    # - vlc._request()           (删除)
    # - vlc.watchdog_loop()      (删除)
    # - vlc.sync_loop()          (删除)

    # 改为调用:
    # - vlc.write_playlist_file(mode, directory)
```

---

## ✨ Plan A 优势总结

✅ **系统简洁**
- 无需额外的 VLC 进程
- 减少资源占用
- 启动更快

✅ **文件系统集成**
- 通过文件系统控制播放列表
- 天然支持文件监听
- 易于调试和监控

✅ **高可靠性**
- 无 HTTP 通信失败的风险
- 播放列表持久化存储
- 故障重启后自动恢复

✅ **易于扩展**
- 可轻松添加新的播放模式
- 支持任意数量的目录切换
- 逻辑清晰易维护

✅ **用户体验**
- 模式切换无缝
- 无黑屏或卡顿
- 与原 Plan A+ 相同的流畅体验

---

## 🔗 相关文档

- [OBS 嵌套场景架构](./OBS_NESTED_SCENE_FINAL.md) - 场景配置指南
- [快速开始指南](./QUICK_START.md) - 快速配置步骤

---

**文档版本**: 1.1
**最后更新**: 2026-02-15（添加VLC播放列表轮转机制）
**维护者**: SingllLive Team

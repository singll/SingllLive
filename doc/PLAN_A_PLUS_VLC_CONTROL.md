# Plan A+ 实现：VLC 动态播放列表切换

> **版本**: 2.0 - VLC 控制改进版
>
> 从 Plan A（单一 VLC 实例）进化到 Plan A+（动态播放列表切换）

---

## 核心问题与解决方案

### 问题分析

Plan A 存在的关键问题：
1. **播放列表固定** - VLC 启动时播放一个固定目录
2. **模式切换不完整** - 轮播和点歌需要不同的播放源
3. **OBS 源配置困境** - OBS VLC 视频源需要指向正确的目录

### Plan A+ 的解决方案

使用 **VLC HTTP API** 实现动态播放列表切换：

```
模式切换 (mode.txt)
    ↓
cyberlive.py 检测模式变化
    ↓
调用 vlc.set_playlist_directory(mode, directory)
    ↓
VLC HTTP API 清空并重新加载播放列表
    ↓
OBS VLC 视频源自动应用新列表
    ↓
直播画面无缝更新 ✓
```

---

## 技术实现详解

### 1. VLC 控制器改进 (vlc_control.py)

#### 新增属性

```python
class VLCController:
    def __init__(self, vlc_path, http_port, http_password,
                 song_dir, song_manager, playback_dir=None):
        # 轮播目录（歌曲库）
        self.playback_dir = playback_dir or song_dir

        # 点歌队列目录（点歌时的歌曲目录）
        self.song_dir = song_dir

        # 当前播放列表模式追踪
        self._current_playlist_mode = None
```

#### 新增方法

```python
async def set_playlist_directory(self, mode: str, directory: str) -> bool:
    """
    动态切换 VLC 播放列表目录

    Args:
        mode: 'playback' (轮播) 或 'song_request' (点歌)
        directory: 要播放的目录路径

    Returns:
        成功返回 True
    """
```

**工作流程**：
1. 检查是否已经是目标模式（避免重复切换）
2. 清空当前播放列表（`pl_empty`）
3. 将新目录加入播放列表（`in_enqueue`）
4. 更新内部状态追踪

### 2. 模式管理循环改进 (cyber_live.py)

#### 新逻辑流程

```python
async def _vlc_mode_manager_loop(vlc, mode_manager, interval=3.0):
    """
    Plan A+ 改进版：支持动态播放列表切换
    """

    # PLAYBACK (轮播)
    if current_mode == Mode.PLAYBACK:
        → 启动 VLC（如果未运行）
        → 切换到轮播目录 (vlc.playback_dir)
        → 播放

    # SONG_REQUEST (点歌)
    elif current_mode == Mode.SONG_REQUEST:
        → 启动 VLC（如果未运行）
        → 切换到点歌队列目录 (vlc.song_dir)
        → 播放

    # BROADCAST/PK (直播/PK)
    elif current_mode in (Mode.BROADCAST, Mode.PK):
        → 暂停 VLC（保持在后台）

    # OTHER (空闲)
    else:
        → 停止 VLC
```

---

## 目录结构配置

### 推荐的目录组织

```
SingllLive/
├── songs/                          # 歌曲库根目录
│   ├── playback/                   # 轮播歌曲
│   │   ├── 歌手A/
│   │   ├── 歌手B/
│   │   └── ...
│   │
│   └── queue/                      # 点歌队列（动态）
│       ├── 00_queue.txt            # 队列列表
│       └── [动态生成的歌曲链接或文件]
│
├── data/
│   ├── mode.txt                    # 当前模式
│   ├── panel.png                   # 动态面板
│   └── now_playing.txt             # 当前歌名
│
└── config.ini                      # 配置文件
```

### config.ini 配置

```ini
[paths]
song_dir = songs/queue             # 点歌队列目录
playback_dir = songs/playback      # 轮播目录

[vlc]
path = D:\\Program Files\\VideoLAN\\VLC\\vlc.exe
http_port = 9090
http_password = 123456
```

---

## OBS VLC 视频源配置

### 配置步骤

1. **创建 VLC 视频源**
   ```
   OBS → AScreen 场景 → 源 → [+] → VLC 视频源
   名称: vlc_player
   ```

2. **配置播放列表**
   ```
   VLC 视频源 → 属性 → 播放列表

   添加文件：选择轮播目录 (songs/playback)
   或添加文件夹直接（让 VLC 自动扫描）

   循环: ☑ 启用
   随机: ☑ 启用
   ```

3. **关键配置**
   ```
   位置: (18, 18)
   大小: 1344 × 756
   缩放类型: 缩放以适应窗口
   ```

### 工作原理

- OBS VLC 源通过 HTTP API 连接到 VLC 进程
- 当 `set_playlist_directory()` 修改 VLC 播放列表时
- VLC 自动应用新列表
- OBS 源自动显示更新的内容

---

## 模式切换工作流

### 轮播 → 点歌 切换

```
时间线:

T0: 轮播模式运行中
    - vlc_player 显示 ✓
    - 播放 songs/playback 目录
    - 循环随机播放

T1: 弹幕 "点歌 三体"
    - danmaku.py 处理命令
    - 添加歌曲到队列
    - 更新 mode.txt: "song_request"

T2: VLC 模式管理检测到模式变化
    - current_mode = SONG_REQUEST
    - 调用: vlc.set_playlist_directory("song_request", "songs/queue")
    - VLC HTTP API 清空旧播放列表
    - VLC HTTP API 加载 songs/queue 目录
    - VLC 开始播放点歌队列

T3: OBS 脚本检测 mode.txt 变化
    - 检测到 "song_request" 模式
    - vlc_player 源保持显示 ✓
    - BScreen 面板更新为点歌界面

T4: 用户看到无缝切换
    - 视频内容从轮播歌曲变为点歌歌曲
    - 无黑屏、无卡顿 ✓
```

### 点歌 → 直播 切换

```
T0: 点歌模式运行中
    - vlc_player 显示 ✓
    - 播放 songs/queue 目录

T1: 弹幕 "直播模式"
    - mode_manager 更新模式: "broadcast"

T2: VLC 模式管理检测到模式变化
    - current_mode = BROADCAST
    - 调用: vlc._request("pl_pause")
    - VLC 暂停播放（保持播放列表状态）

T3: OBS 脚本检测 mode.txt 变化
    - 检测到 "broadcast" 模式
    - vlc_player 隐藏 ✗
    - broadcast_screen 显示 ✓
    - BScreen 面板更新为直播界面

T4: 直播画面显示
    - OBS 显示直播源画面
    - VLC 在后台暂停
    - 随时可恢复
```

---

## 配置清单

### Python 后端

```
□ modules/vlc_control.py
  ✅ 添加 playback_dir 参数
  ✅ 添加 set_playlist_directory() 方法
  ✅ 添加 _current_playlist_mode 追踪

□ cyber_live.py
  ✅ 修改 _vlc_mode_manager_loop() 支持动态切换
  ✅ PLAYBACK 模式调用 set_playlist_directory("playback", vlc.playback_dir)
  ✅ SONG_REQUEST 模式调用 set_playlist_directory("song_request", vlc.song_dir)

□ config.ini
  ✅ 添加 playback_dir 配置项（轮播目录）
  ✅ song_dir 保持为点歌队列目录
```

### OBS 配置

```
□ AScreen 场景
  ✅ vlc_player 源（连接到 VLC HTTP API）
  ✅ 位置: (18, 18), 大小: 1344×756
  ✅ 循环: 启用，随机: 启用

□ BScreen 场景
  ✅ panel.png 源（自动刷新）

□ 脚本
  ✅ ascreen_source_switcher.lua (Plan A)
     - 根据模式显示/隐藏 vlc_player
     - 显示/隐藏 broadcast_screen
     - 显示/隐藏 pk_background
  ✅ panel_refresh.lua
     - 每秒刷新 panel.png
```

### 目录结构

```
□ songs/playback/          (轮播歌曲库)
  ✅ 包含所有轮播歌曲文件
  ✅ 支持子目录（歌手分类）
  ✅ VLC 会自动递归扫描

□ songs/queue/             (点歌队列)
  ✅ 由 songs.py 动态管理
  ✅ 包含当前点歌列表
  ✅ VLC 自动读取更新
```

---

## VLC HTTP API 参考

Plan A+ 使用的关键 API 命令：

```
pl_empty              清空播放列表
pl_play               播放（继续）
pl_pause              暂停
pl_stop               停止
pl_next               下一首
pl_previous           上一首

in_play <input>       播放指定文件/目录
in_enqueue <input>    加入播放列表
```

示例请求（HTTP GET）：
```
http://127.0.0.1:9090/requests/status.xml?command=pl_empty
http://127.0.0.1:9090/requests/status.xml?command=in_enqueue&input=D:/songs/queue
http://127.0.0.1:9090/requests/status.xml?command=pl_play
```

---

## 故障排除

### VLC 播放列表不更新

**症状**: 模式切换时，VLC 仍在播放旧目录

**排查**:
```
1. 检查 VLC HTTP API 是否可访问
   → 浏览器访问: http://127.0.0.1:9090/requests/status.xml
   → 输入密码（默认 123456）

2. 检查目录路径是否正确
   → songs/playback 必须存在
   → songs/queue 必须存在
   → 路径中不能有中文特殊字符

3. 查看 cyber_live.py 的日志
   → 搜索关键词: "VLC 播放列表已切换"
   → 确认模式切换是否被触发
```

### OBS VLC 源仍显示旧内容

**症状**: OBS 中 vlc_player 显示的仍是旧歌曲

**原因**: OBS VLC 源可能没有与 VLC 进程同步

**解决**:
```
1. 在 OBS 中刷新 VLC 源
   → 右键 vlc_player 源 → 刷新

2. 重启 VLC
   → 关闭后端
   → 手动关闭 VLC 进程
   → 重新启动后端

3. 检查 VLC 循环和随机设置
   → OBS VLC 源属性
   → 确保"循环"已启用
```

### VLC HTTP API 无法连接

**症状**: 日志显示 "VLC 请求失败"

**排查**:
```
1. 确认 VLC 已启动
   → 任务管理器查看 vlc.exe 进程
   → 或查看日志 "[vlc] VLC 已启动 (PID: ...)"

2. 确认 HTTP 接口已启用
   → config.ini 中的 http_port 和 http_password
   → VLC 启动命令中的 --extraintf=http 参数

3. 测试 HTTP 连接
   → PowerShell 或 curl：
     curl -u :123456 http://127.0.0.1:9090/requests/status.xml
```

---

## 与 Plan A 的对比

| 方面 | Plan A | Plan A+ |
|------|--------|---------|
| **VLC 实例数** | 1 个 | 1 个（改进管理） |
| **OBS 源数** | 4 个 | 4 个（不变） |
| **播放列表** | 固定 | 动态切换 |
| **轮播** | ✓ 支持 | ✓ 支持（独立目录） |
| **点歌** | ✓ 支持 | ✓ 支持（独立目录） |
| **模式间过渡** | 暂停/恢复 | 切换播放列表 |
| **用户体验** | ✓ 无黑屏 | ✓ 无黑屏（内容精准） |
| **系统复杂度** | 简单 | 中等（需配置两个目录） |

---

## 最佳实践

### 1. 目录管理

✅ **推荐做法**:
```
songs/playback/  - 存放所有轮播歌曲（来自歌曲库）
songs/queue/     - 由系统自动管理，包含当前点歌队列
```

❌ **避免做法**:
```
不要在轮播和点歌目录中存放相同的文件
→ VLC 可能加载重复的播放列表
→ 导致性能下降
```

### 2. 歌曲队列管理

在 `modules/songs.py` 中动态更新点歌队列：

```python
# 点歌时
def add_to_queue(self, song_name):
    song_file = self.search(song_name)
    # 将歌曲链接添加到 songs/queue/ 目录
    # 或生成 .m3u 播放列表文件
    self._update_queue_playlist()

# 实现 _update_queue_playlist()
def _update_queue_playlist(self):
    # 根据当前队列重新生成 songs/queue/.m3u 文件
    # VLC 会自动检测更新
```

### 3. 模式切换延迟优化

如果观察到切换延迟，调整参数：

```python
# cyber_live.py
tasks.append(asyncio.create_task(
    _vlc_mode_manager_loop(vlc, mode_manager, interval=1.0)  # 改为 1 秒
))
```

更小的 interval 会更快检测模式变化，但增加 CPU 占用。

---

## 总结

**Plan A+ 的优势**:

✅ **精准控制** - VLC 在轮播和点歌间无缝切换
✅ **内容分离** - 轮播和点歌使用不同的播放列表
✅ **自动管理** - 后端自动处理所有切换逻辑
✅ **用户透明** - 直播间观众无感知，画面平滑
✅ **易于扩展** - 可轻松添加新的播放列表模式

**需要注意的**:

⚠️ 确保两个目录（playback 和 queue）存在且有内容
⚠️ VLC HTTP API 必须可访问
⚠️ 避免在目录名中使用中文特殊字符
⚠️ 定期监控 VLC 进程健康状态（使用看门狗）

---

**文档版本**: 2.0 - Plan A+ VLC 控制改进
**最后更新**: 2026-02-15
**维护者**: SingllLive Team

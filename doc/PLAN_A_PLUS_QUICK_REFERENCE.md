# Plan A+ 快速参考 - VLC 动态播放列表切换

> **一页纸总结** - Plan A+ 实现指南

---

## 🎯 核心改进

| 方面 | 改变 |
|------|------|
| **问题** | VLC 播放列表固定，无法在轮播和点歌间切换 |
| **解决** | 使用 VLC HTTP API 动态修改播放列表目录 |
| **结果** | 轮播和点歌的内容分离，模式切换无缝 |

---

## 📂 目录结构（必须）

```
songs/
├── playback/          ← 轮播目录（所有轮播歌曲）
│   ├── 歌手A/
│   ├── 歌手B/
│   └── ...
└── queue/             ← 点歌队列目录（动态管理）
    └── [当前点歌列表]
```

---

## ⚙️ 配置更新（config.ini）

```ini
[paths]
song_dir = D:\live\songs\queue      # 点歌队列
playback_dir = D:\live\songs\playback  # 轮播歌曲库
```

---

## 🔧 代码修改（已完成）

### vlc_control.py
- ✅ `set_playlist_directory(mode, directory)` 新方法
- ✅ 支持动态切换播放列表

### cyber_live.py
- ✅ `_vlc_mode_manager_loop()` 支持 Plan A+
- ✅ PLAYBACK 模式 → 切换到 playback_dir
- ✅ SONG_REQUEST 模式 → 切换到 song_dir

---

## 📋 实施步骤

### Step 1: 准备目录
```bash
# 创建两个目录
mkdir songs\playback        # 轮播歌曲
mkdir songs\queue           # 点歌队列

# 将歌曲分类放入：
# - 轮播库歌曲 → songs/playback/
# - 点歌队列 → songs/queue/ (初始可为空)
```

### Step 2: 更新配置
```ini
# config.ini
[paths]
song_dir = D:\live\songs\queue
playback_dir = D:\live\songs\playback
```

### Step 3: 启动测试
```bash
python cyber_live.py
# 查看日志，应显示：
# [vlc] VLC 已启动 (PID: ...)
# [vlc] VLC 播放列表已切换到 playback 模式: D:\live\songs\playback
```

### Step 4: 测试模式切换
```
弹幕: "轮播模式"
→ VLC 切换到 playback 目录 ✓

弹幕: "点歌 歌名"
→ VLC 切换到 queue 目录 ✓

弹幕: "直播模式"
→ VLC 暂停（保持后台）✓
```

---

## 🔍 验证 Plan A+ 工作

### 日志检查
```
搜索关键词: "VLC 播放列表已切换"
如果看到此行，说明 Plan A+ 正常工作 ✓
```

### OBS 检查
```
1. AScreen 中的 vlc_player 源
2. 轮播时显示轮播歌曲 ✓
3. 点歌时显示点歌歌曲 ✓
4. 直播时 vlc_player 隐藏，broadcast_screen 显示 ✓
```

---

## ⚡ VLC HTTP API 命令

Plan A+ 使用的核心命令：

```
pl_empty              清空播放列表
in_enqueue <dir>     加入目录到播放列表
pl_play              播放
pl_pause             暂停
pl_stop              停止
```

手动测试（PowerShell）：
```powershell
# 清空列表
curl -u :123456 "http://127.0.0.1:9090/requests/status.xml?command=pl_empty"

# 加入轮播目录
curl -u :123456 "http://127.0.0.1:9090/requests/status.xml?command=in_enqueue&input=D:/songs/playback"

# 播放
curl -u :123456 "http://127.0.0.1:9090/requests/status.xml?command=pl_play"
```

---

## 🚨 常见问题

### Q: 点歌后 VLC 仍在播放轮播歌曲？
**A**: 检查日志是否有 "VLC 播放列表已切换"
- 如果没有：检查 mode.txt 是否正确更新
- 如果有：VLC 可能需要时间加载新列表，等待 2-3 秒

### Q: 两个目录的内容如何管理？
**A**:
- `playback/` - 手动管理，放入所有轮播歌曲
- `queue/` - 由系统自动管理，点歌时动态更新

### Q: 如何在点歌时动态更新 queue 目录？
**A**: 在 `modules/songs.py` 的 `add_to_queue()` 中：
```python
def add_to_queue(self, song):
    # 1. 添加到内存队列
    self.queue.append(song)

    # 2. 更新 queue 目录（复制或创建链接）
    self._sync_queue_to_disk()

    # 3. VLC 自动检测目录变化并更新播放列表
```

### Q: 轮播和点歌可以同时共存吗？
**A**: 不可以。当前设计是择一，不支持混合播放。
可以配置为：
- 轮播时，播放轮播目录（无点歌）
- 有点歌时，自动切换到点歌队列

---

## 📊 性能优化

### 1. 加快模式检测
```python
# cyber_live.py - 减少检查间隔
_vlc_mode_manager_loop(vlc, mode_manager, interval=1.0)  # 1秒检查一次
```

### 2. 避免重复切换
Plan A+ 已内置 `_current_playlist_mode` 追踪，避免重复调用 HTTP API

### 3. VLC 循环设置
确保 VLC 启动参数中有 `--loop` 和 `--random`：
```python
# vlc_control.py
cmd = [
    self.vlc_path, directory,
    "--loop",      # 循环播放
    "--random",    # 随机顺序
    ...
]
```

---

## 🧪 单元测试

测试 `set_playlist_directory()` 方法：

```python
import asyncio
from modules.vlc_control import VLCController
from modules.songs import SongManager

async def test_plan_a_plus():
    songs = SongManager("config.ini")
    vlc = VLCController(
        vlc_path="C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
        http_port=9090,
        http_password="123456",
        song_dir="D:\\songs\\queue",
        song_manager=songs,
        playback_dir="D:\\songs\\playback"
    )

    # 启动 VLC
    vlc.start_vlc()
    await asyncio.sleep(3)

    # 测试切换到轮播
    result1 = await vlc.set_playlist_directory("playback", "D:\\songs\\playback")
    print(f"切换到轮播: {'✓' if result1 else '✗'}")

    # 测试切换到点歌
    result2 = await vlc.set_playlist_directory("song_request", "D:\\songs\\queue")
    print(f"切换到点歌: {'✓' if result2 else '✗'}")

asyncio.run(test_plan_a_plus())
```

---

## 📞 支持

**出现问题？**

1. 查看日志：`[vlc]` 开头的行
2. 检查 VLC HTTP API：浏览器访问 `http://127.0.0.1:9090/requests/status.xml`
3. 确认目录存在：`songs/playback` 和 `songs/queue`
4. 查看完整文档：`doc/PLAN_A_PLUS_VLC_CONTROL.md`

---

## 总结

```
Plan A+ = Plan A + VLC 动态播放列表切换

✅ 单一 VLC 实例（资源效率）
✅ 轮播和点歌目录分离（内容清晰）
✅ 模式切换自动调整播放列表（无缝体验）
✅ 画面无黑屏无卡顿（用户满意）
```

---

**版本**: Plan A+ v1.0
**最后更新**: 2026-02-15

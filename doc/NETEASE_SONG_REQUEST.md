# 网易云音乐点歌系统集成指南

> 使用网易云 API 实现在线点歌和歌词显示

---

## 🎵 系统架构

```
用户弹幕 "点歌 歌曲名"
    ↓
DanmakuBot 处理
    ↓
NetEaseAPI.search_song() 搜索歌曲
    ↓
NetEaseAPI.get_lyrics() 获取歌词
    ↓
LyricsDisplay.render_lyrics() 渲染歌词图像
    ↓
OBS 显示 lyrics_display 源（实时歌词）
    ↓
VLC 播放歌曲（Plan A 文件系统或在线链接）
```

---

## 📦 核心模块

### `modules/music_api.py` - 网易云 API 客户端

```python
from modules.music_api import NetEaseAPI

api = NetEaseAPI()

# 搜索歌曲
songs = await api.search_song("三体")
# [
#   {
#     'id': 2014337720,
#     'name': 'THREE-BODY',
#     'artist': '重塑雕像的权利',
#     'duration': 336000  # 毫秒
#   },
#   ...
# ]

# 获取歌词
lyrics = await api.get_lyrics(2014337720)
# {
#   'content': '[00:10.00]歌词...',
#   'lines': [
#     {'time': 10.0, 'text': '歌词内容'},
#     ...
#   ]
# }
```

### `modules/lyrics_display.py` - 歌词显示

```python
from modules.lyrics_display import LyricsDisplay

display = LyricsDisplay()

# 渲染歌词
await display.render_lyrics(
    {
        'name': '歌曲名',
        'artist': '艺术家',
        'lyrics': lyrics['lines']
    },
    current_time=25.5,
    total_time=200
)
# 输出: data/current_lyrics.png
```

---

## 🔧 集成到弹幕点歌

### 修改 `modules/danmaku.py`

```python
from modules.music_api import NetEaseAPI
from modules.lyrics_display import LyricsDisplay

class DanmakuBot:
    def __init__(self, ...):
        self.api = NetEaseAPI()
        self.lyrics_display = LyricsDisplay()

    async def handle_request_song(self, user: str, song_name: str):
        """处理点歌命令"""
        try:
            # 1️⃣ 搜索歌曲
            songs = await self.api.search_song(song_name)

            if not songs:
                self.send_message(f"@{user} 未找到歌曲 '{song_name}'")
                return

            song = songs[0]

            # 2️⃣ 获取歌词
            lyrics = await self.api.get_lyrics(song['id'])

            # 3️⃣ 添加到队列
            queue_entry = {
                'id': song['id'],
                'name': song['name'],
                'artist': song['artist'],
                'duration': song['duration'],
                'user': user,
                'lyrics': lyrics['lines'] if lyrics else [],
            }
            self.songs.queue.append(queue_entry)

            # 4️⃣ 发送确认
            self.send_message(f"@{user} ✅ 已添加: {song['name']} - {song['artist']}")

            # 5️⃣ 立即渲染歌词
            if lyrics:
                await self.lyrics_display.render_lyrics(
                    {
                        'name': song['name'],
                        'artist': song['artist'],
                        'lyrics': lyrics['lines']
                    },
                    current_time=0,
                    total_time=song['duration'] / 1000  # 转换为秒
                )

        except Exception as e:
            log.error(f"点歌异常: {e}")
            self.send_message(f"@{user} 点歌失败")
```

---

## 🎬 OBS 配置

### 1. 修改 lyrics_display 源

```
OBS → AScene 场景
源列表 → 双击 "lyrics_display"

设置为：图像源
文件：<项目>/data/current_lyrics.png
位置：(18, 18)
大小：1344×756
```

### 2. 添加自动刷新脚本

创建 `scripts/obs/lyrics_refresh.lua`：

```lua
-- 自动刷新歌词显示

function on_event(event)
    if event == obs.OBS_FRONTEND_EVENT_SCRIPTING_SHUTDOWN then
        return
    end
end

function timer_callback()
    local source = obs.obs_get_source_by_name("lyrics_display")
    if source then
        obs.obs_source_update(source, nil)
        obs.obs_source_release(source)
    end
end

obs.timer_add(timer_callback, 100)  -- 100ms 刷新一次
```

在 OBS 中加载：
```
OBS → 工具 → 脚本 → [+] → 选择 lyrics_refresh.lua
```

---

## 🚀 快速测试

```bash
# 1. 测试 API
python modules/music_api.py

# 预期输出：
# ✅ 找到 N 首歌曲
# 显示歌曲列表和歌词预览
```

---

## 💡 工作流程

### 场景：用户点歌

```
Time T0: 用户发送弹幕
  "点歌 三体"

Time T1: 系统搜索歌曲 (~1秒)
  ✅ 搜索成功，找到 "THREE-BODY"

Time T2: 获取歌词 (~1秒)
  ✅ 获取 50 行歌词

Time T3: 渲染歌词图像 (~0.5秒)
  ✅ 生成 data/current_lyrics.png

Time T4: OBS 刷新显示 (~100ms)
  ✅ lyrics_display 源显示歌词图像

Time T5: 用户开始播放歌曲
  VLC 播放音频
  lyrics_display 实时显示对应歌词
```

---

## ⚙️ 配置参数

### `config.ini` 配置

```ini
[music]
# 音乐 API 配置
api_timeout = 10        # API 请求超时 (秒)
cache_enabled = true    # 启用搜索和歌词缓存

[lyrics]
# 歌词显示配置
output_path = data/current_lyrics.png
width = 1344
height = 756
refresh_interval = 100  # 毫秒
```

---

## 🔍 调试和监控

### 查看日志

```bash
# 运行系统并观察日志
python cyber_live.py 2>&1 | grep "music_api\|lyrics"

# 预期日志：
# [music_api] 网易云搜索 '三体' 找到 5 首歌曲
# [lyrics_display] 歌词已渲染: data/current_lyrics.png
```

### 检查缓存

```python
from modules.music_api import NetEaseAPI

api = NetEaseAPI()
# 查看缓存状态
print(f"缓存大小: {len(api._cache)}")

# 清空缓存
api.clear_cache()
```

---

## 📊 网易云 API 说明

### 搜索接口

- **URL**: `http://music.163.com/api/search/get`
- **方法**: POST
- **参数**:
  - `s`: 搜索关键词
  - `type`: 搜索类型 (1=歌曲)
  - `limit`: 返回结果数量
  - `offset`: 分页偏移

### 歌词接口

- **URL**: `http://music.163.com/api/song/lyricNew`
- **方法**: POST
- **参数**:
  - `id`: 歌曲 ID
  - `lv`: 日志级别 (-1)
  - `tv`: 时间值 (-1)

**返回**：LRC 格式歌词

---

## ✅ 完整检查清单

```
□ API 测试
  ✅ python modules/music_api.py 运行成功
  ✅ 搜索功能正常
  ✅ 歌词获取正常

□ 歌词显示
  ✅ LyricsDisplay 初始化
  ✅ 图像文件生成（data/current_lyrics.png）
  ✅ 中文显示正常

□ OBS 配置
  ✅ lyrics_display 源为图像
  ✅ 文件路径正确
  ✅ 自动刷新脚本已加载

□ 点歌系统
  ✅ danmaku.py 集成 NetEaseAPI
  ✅ 搜索到歌曲时自动添加队列
  ✅ 歌词自动渲染和显示

□ 端到端测试
  ✅ 启动系统：python cyber_live.py
  ✅ 发送弹幕：点歌 歌曲名
  ✅ 验证：歌词显示在 OBS
```

---

## 🎉 总结

✅ 使用网易云 API 实现完整的在线点歌系统
✅ 实时歌词搜索和获取
✅ 优雅的歌词显示效果
✅ 无需本地歌词库，完全网络驱动
✅ 即插即用，开箱即用

---

**最后更新**: 2026-02-15

# 歌词系统 - 完整解决方案（离线+在线）

> **方案对比**: 在线 API vs 本地离线 vs 混合方案

---

## 🎯 三种实现方案对比

### 方案 A: 本地离线方案 (✅ 推荐 - 无网络依赖)

**优点：**
- ✅ 无需网络连接
- ✅ 速度快（本地 JSON 查询）
- ✅ 完全掌控数据
- ✅ 无 API 限制
- ✅ 离线直播也能用

**缺点：**
- ❌ 需要手动添加歌词
- ❌ 库的大小取决于手动添加

**适用场景：**
- 固定歌单（轮播歌曲库）
- 网络不稳定
- 离线直播

**实现文件：**
- `modules/local_lyrics.py` - 本地歌词管理
- `modules/lyrics_display.py` - 歌词显示（已有）

---

### 方案 B: 在线 API 方案 (❌ 当前无法使用)

**原因：**
- 酷狗 API: `searpc.kugou.com` DNS 解析失败
- 网易云 API: 需要复杂加密认证
- 无法保证稳定性

**备选：** 如果网络恢复可尝试

---

### 方案 C: 混合方案 (✅ 最优 - 推荐)

**原理：**
```
┌─────────────────┐
│ 搜索点歌歌曲    │
├─────────────────┤
│  ↓              │
│ 优先查本地库    │ → 找到 → 直接使用 ✅
│  ↓              │
│ 本地库中没有 → 手动添加或使用演示歌词
│              │
│  ↓ (网络可用)│
│ 联网搜索 API → 找到 → 获取歌词 → 保存到本地 → 显示
│              │
└─────────────────┘
```

**优点：**
- ✅ 优先使用本地库（快速）
- ✅ 本地无货时可以网络获取
- ✅ 自动建立本地库
- ✅ 渐进式完善

---

## 🚀 快速开始：本地离线方案 (推荐)

### Step 1: 使用本地歌词管理

```python
from modules.local_lyrics import LocalLyricsManager

# 初始化本地歌词管理器
lyrics_manager = LocalLyricsManager("data/lyrics")

# 添加歌曲（手动）
lrc_content = """[00:10.00]第一行歌词
[00:20.00]第二行歌词
[00:30.00]第三行歌词
"""

lyrics_manager.add_song(
    song_name="歌曲名",
    artist="艺术家",
    lyrics=lrc_content,
    duration=180  # 歌曲时长(秒)
)

# 搜索歌曲
songs = lyrics_manager.search_song("歌曲名")
# [{'id': '歌曲名 - 艺术家', 'name': '歌曲名', 'artist': '艺术家', ...}]

# 获取歌词
lyrics = lyrics_manager.get_lyrics("歌曲名 - 艺术家")
# {'content': 'LRC内容', 'lines': [{'time': 10.0, 'text': '第一行歌词'}, ...]}
```

### Step 2: 批量导入 LRC 文件

**文件组织方式：**
```
data/lyrics/
├── input/                      # LRC 文件输入目录
│   ├── 三体 - 许嵩.lrc
│   ├── 晴天 - 周杰伦.lrc
│   ├── 浙江这一路 - 许嵩.lrc
│   └── ...
│
└── lyrics_db.json             # 自动生成的歌词数据库
```

**文件名格式：** `歌曲名 - 艺术家.lrc`

**导入代码：**
```python
from modules.local_lyrics import LocalLyricsManager

lyrics_manager = LocalLyricsManager()

# 批量导入整个目录
count = lyrics_manager.import_lrc_directory("data/lyrics/input")
print(f"✅ 导入 {count} 个 LRC 文件")

# 查看所有歌曲
all_songs = lyrics_manager.get_all_songs()
for song in all_songs:
    print(f"{song['name']} - {song['artist']}: {song['lyrics_lines']} 行歌词")
```

### Step 3: 修改 danmaku.py 使用本地歌词

```python
# modules/danmaku.py

from modules.local_lyrics import LocalLyricsManager
from modules.lyrics_display import LyricsDisplay

class DanmakuBot:
    def __init__(self, ...):
        self.lyrics_manager = LocalLyricsManager()
        self.lyrics_display = LyricsDisplay()

    async def handle_request_song(self, user: str, song_name: str):
        """处理点歌 - 使用本地离线歌词"""
        log.info(f"{user} 点歌: {song_name}")

        try:
            # 1️⃣ 从本地库搜索歌曲
            songs = self.lyrics_manager.search_song(song_name)

            if not songs:
                self.send_message(f"@{user} 本地库中没有 '{song_name}' 😕")
                self.send_message("💡 可以上传 LRC 文件到 data/lyrics/input 目录来扩充歌库")
                return

            song = songs[0]
            log.info(f"找到歌曲: {song['name']} - {song['artist']}")

            # 2️⃣ 获取歌词
            lyrics_info = self.lyrics_manager.get_lyrics(song['id'])

            if not lyrics_info:
                self.send_message(f"@{user} 无法获取 '{song['name']}' 的歌词")
                return

            # 3️⃣ 添加到队列
            queue_entry = {
                'id': song['id'],
                'name': song['name'],
                'artist': song['artist'],
                'duration': song.get('duration', 0),
                'user': user,
                'lyrics': lyrics_info['lines'],
            }

            self.songs.queue.append(queue_entry)

            # 4️⃣ 发送确认
            self.send_message(f"@{user} ✅ 已添加: {song['name']} - {song['artist']}")

            # 5️⃣ 立即渲染歌词
            await self.lyrics_display.render_lyrics(
                {
                    'name': song['name'],
                    'artist': song['artist'],
                    'lyrics': lyrics_info['lines'],
                },
                current_time=0,
                total_time=queue_entry['duration'],
            )

        except Exception as e:
            log.error(f"点歌异常: {e}")
            self.send_message(f"@{user} 点歌失败 😔")
```

### Step 4: OBS 配置（同前）

- 修改 `lyrics_display` 源为图像
- 指向 `data/current_lyrics.png`
- 加载刷新脚本

---

## 📚 获取 LRC 歌词文件

### 来源 1: 网络下载

**国内网站：**
- [Genius 中文](https://genius.com) - 英文歌词
- [LrcGet](http://www.lrcget.net/) - 中文歌词库
- [千千静听](http://music.baidu.com) - 歌词库
- [QQ 音乐](https://y.qq.com) - 歌词库

### 来源 2: 离线工具生成

如果你有某首歌的 mp3 文件，可以使用工具自动匹配歌词：

```python
# 使用 python-lyrics 库获取歌词
pip install python-lyrics

from lyrics import get_lyrics_from_file

# 对 mp3 文件识别并获取歌词
lyrics = get_lyrics_from_file("song.mp3")
if lyrics:
    with open("song_name - artist.lrc", "w") as f:
        f.write(lyrics)
```

### 来源 3: 手动编辑

如果找不到 LRC，可以手动创建：

```lrc
[00:10.00]第一行歌词
[00:20.00]第二行歌词
[00:30.00]第三行歌词
```

---

## 🔧 完整的点歌系统示例

### 配置文件更新

```ini
[paths]
song_dir = D:\live\songs\queue
playback_dir = D:\live\songs\playback
data_dir = D:\live\data
lyrics_dir = D:\live\data\lyrics

[lyrics]
# 歌词系统配置
use_local = true           # 优先使用本地库
use_api = false            # 当前 API 不可用
lyrics_output = data/current_lyrics.png
refresh_interval = 500     # 毫秒
```

### 点歌流程图

```
用户弹幕: "点歌 歌曲名"
    ↓
DanmakuBot 处理
    ↓
LocalLyricsManager 搜索
    ├─ 找到 → 获取歌词 → 添加队列 ✅
    └─ 没找到 → 提示用户上传 LRC ❌
    ↓
LyricsDisplay 渲染
    ↓
OBS 显示歌词图像
```

---

## 📋 常见问题

### Q1: 如何批量添加歌词？

**A:** 准备好所有 LRC 文件，放到 `data/lyrics/input/` 目录，然后运行：

```python
from modules.local_lyrics import LocalLyricsManager

manager = LocalLyricsManager()
count = manager.import_lrc_directory("data/lyrics/input")
print(f"导入 {count} 个文件")
```

### Q2: LRC 文件格式不对怎么办？

**A:** 确保文件名格式为 `歌曲名 - 艺术家.lrc`，文件内容为标准 LRC 格式：

```
[00:时分.毫秒]歌词内容
[00:00.00]歌词开始
[00:05.50]下一行歌词
```

### Q3: 如何修改已有歌词？

**A:** 编辑 `data/lyrics/lyrics_db.json`，或删除再重新导入：

```python
manager = LocalLyricsManager()
manager.delete_song("歌曲名 - 艺术家")
# 然后重新导入 LRC 文件
```

### Q4: 能否同时支持在线和离线？

**A:** 可以，使用混合方案。当本地库没有时，尝试从网络获取：

```python
# 混合搜索
def search_song_hybrid(self, keyword):
    # 先查本地
    local_results = self.local_lyrics.search_song(keyword)
    if local_results:
        return local_results

    # 再查网络 (如果可用)
    if self.api_available:
        api_results = await self.api.search_song(keyword)
        # 自动保存到本地
        for song in api_results:
            self.local_lyrics.add_song(...)
        return api_results

    return []
```

---

## ✅ 推荐配置清单

```
□ 本地歌词管理系统配置
  ✅ LocalLyricsManager 初始化
  ✅ 歌词输入目录: data/lyrics/input/
  ✅ 歌词数据库: data/lyrics/lyrics_db.json

□ LRC 文件准备
  ✅ 收集常用歌曲的 LRC 文件
  ✅ 文件名格式: 歌曲名 - 艺术家.lrc
  ✅ 批量导入到本地库

□ 歌词显示配置
  ✅ LyricsDisplay 初始化
  ✅ 输出路径: data/current_lyrics.png
  ✅ 字体支持: 中文显示正常

□ OBS 集成
  ✅ lyrics_display 源为图像
  ✅ 文件路径正确
  ✅ 自动刷新脚本启用

□ 弹幕点歌集成
  ✅ DanmakuBot 使用 LocalLyricsManager
  ✅ 搜索到歌词时自动渲染
  ✅ 未找到时给出提示
```

---

## 🎉 总结

**本地离线方案的优势：**
- ✨ 无网络依赖，完全离线工作
- ✨ 响应快（本地 JSON 查询）
- ✨ 完全掌控数据和隐私
- ✨ 适合固定歌单的轮播场景
- ✨ 易于管理和维护

**立即开始：**

```bash
# 1. 准备 LRC 文件到 data/lyrics/input/
# 2. 运行导入脚本
python -c "from modules.local_lyrics import LocalLyricsManager; \
  m = LocalLyricsManager(); \
  m.import_lrc_directory('data/lyrics/input')"

# 3. 修改 danmaku.py 使用本地歌词
# 4. 启动系统进行测试
python cyber_live.py
```

现在你的歌词系统已经完全独立工作，不依赖任何外部 API！🎵

---

**文档版本**: 1.0
**日期**: 2026-02-15
**方案**: 本地离线 + 混合可选

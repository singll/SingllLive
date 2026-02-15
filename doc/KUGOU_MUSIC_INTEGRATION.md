# 酷狗音乐集成方案：歌词显示与点歌

> **方案对比与可行性分析** - VLC vs 酷狗音乐的集成方法

---

## 📊 方案对比

### 当前方案（VLC）
- ✅ 开源、稳定、易控制
- ✅ Plan A 文件系统控制成熟
- ❌ 没有原生歌词显示能力
- ❌ 需要手动获取歌词（困难）
- ✅ 可完全自定义化

### 酷狗音乐方案
- ✅ 丰富的歌词库
- ✅ 开放的 API 接口
- ✅ 官方点歌功能
- ❌ 可控性不如 VLC
- ❌ 可能存在版权限制

---

## 🎯 推荐方案：混合架构

不建议完全替换 VLC，而是采用 **混合方案**：

```
┌─────────────────────────────────────────────────────────┐
│           SingllLive 混合音乐系统架构                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ① 音乐播放层 (双轨制)                                    │
│  ├─ VLC (继续用于本地文件播放)                           │
│  │  └─ 轮播模式：播放 songs/playback 中的 mp3            │
│  │                                                      │
│  └─ 酷狗 API (点歌和歌词获取)                            │
│     └─ 点歌模式：通过酷狗 API 搜索和获取歌曲              │
│                                                      │
│  ② 歌词层 (统一由酷狗提供)                                │
│  └─ 从酷狗 API 获取歌词                                  │
│     ├─ 显示到 OBS (lyrics_display)                      │
│     └─ 支持实时滚动/歌词同步                             │
│                                                      │
│  ③ 点歌层 (完全从酷狗迁移)                                │
│  ├─ 通过弹幕/网页调用酷狗搜索                            │
│  ├─ 获取歌曲信息和播放链接                              │
│  └─ 无缝整合到现有系统                                  │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🔌 实现方案 A：Python 集成方案 (推荐)

### 方案说明
- 使用 Python 调用酷狗 API
- 保留 VLC 用于本地文件播放
- 点歌时通过 API 获取歌曲
- 歌词由 Python 后端获取并显示到 OBS

### 核心模块架构

```python
# modules/kugou_api.py (新增)
class KugouAPI:
    """酷狗音乐 API 客户端"""

    async def search_song(self, keywords: str) -> list:
        """搜索歌曲

        Args:
            keywords: 搜索关键词

        Returns:
            [
                {
                    'id': '歌曲ID',
                    'name': '歌曲名',
                    'artist': '艺术家',
                    'lyrics_url': '歌词链接'
                },
                ...
            ]
        """

    async def get_lyrics(self, song_id: str) -> dict:
        """获取歌词

        Args:
            song_id: 酷狗歌曲 ID

        Returns:
            {
                'song_name': '歌曲名',
                'artist': '艺术家',
                'content': '歌词内容 (LRC 格式)',
                'lines': [
                    {'time': '00:10', 'text': '歌词行'},
                    ...
                ]
            }
        """

    async def get_download_url(self, song_id: str) -> str:
        """获取歌曲下载链接

        用于本地播放或流媒体
        """

# modules/lyrics_display.py (新增)
class LyricsDisplay:
    """歌词显示管理"""

    def __init__(self, output_path: str):
        """初始化

        Args:
            output_path: 输出图像路径 (供 OBS 显示)
        """

    async def render_lyrics(self, song_info: dict, current_time: float) -> str:
        """渲染歌词图像

        Args:
            song_info: 歌曲信息和歌词
            current_time: 当前播放时间 (秒)

        Returns:
            输出图像路径

        功能:
        - 根据时间显示对应歌词行
        - 突出显示当前演唱的歌词
        - 显示歌曲名和艺术家
        - 优雅的排版和动画
        """

# cyber_live.py (修改)
async def _lyrics_sync_loop(lyrics_display, vlc, kugou_api):
    """歌词同步循环

    定期:
    1. 获取当前播放时间 (从 VLC 或酷狗)
    2. 从缓存获取当前歌曲歌词
    3. 调用 lyrics_display.render_lyrics() 生成图像
    4. OBS 自动刷新显示
    """
```

### 优势
✅ 保留 VLC 的稳定性和本地播放能力
✅ 充分利用酷狗的歌词库
✅ 点歌功能原生支持
✅ 歌词显示实时同步
✅ 代码改动最小化

### 劣势
❌ 需要处理 API 调用延迟
❌ 依赖酷狗 API 可用性
❌ 可能存在版权限制

---

## 🔌 实现方案 B：完全替换 VLC (不推荐)

### 方案说明
- 完全用酷狗音乐替代 VLC
- 所有播放都通过酷狗
- 完整的酷狗生态

### 劣势（这是为什么不推荐）
❌ 酷狗 API 稳定性和版权限制未知
❌ 完全重构 Plan A 播放系统
❌ 失去对本地文件的控制
❌ 如果 API 失效，整个系统瘫痪
❌ 点歌功能强依赖酷狗

---

## ✅ 推荐方案详细实现

### 第一步：lyrics_display 源配置 (OBS)

**配置步骤：**

1. **在 AScreen 中修改 lyrics_display 源**
   ```
   OBS → AScreen → 源面板
   双击 lyrics_display 源 → 属性

   设置为 "图像" 或 "图像幻灯片"
   选择文件: data/current_lyrics.png
   ```

2. **配置自动刷新**
   ```lua
   -- scripts/obs/lyrics_refresh.lua (类似 panel_refresh.lua)

   local function on_event(event)
       if event == obs.OBS_FRONTEND_EVENT_SCRIPTING_SHUTDOWN then
           return
       end

       -- 每 100ms 刷新一次 lyrics 源
       -- 从 data/current_lyrics.png 读取最新的歌词图像
       obs.obs_source_list_release(sources)
   end
   ```

### 第二步：集成酷狗 API

**安装依赖：**

```bash
pip install kugou-api  # 或使用其他酷狗 API 库
# 或手动实现 HTTP 请求调用酷狗 API
```

**实现 modules/kugou_api.py：**

```python
import aiohttp
import logging
from typing import Optional, List, Dict

log = logging.getLogger("kugou")

class KugouAPI:
    """酷狗音乐 API 客户端"""

    BASE_URL = "http://searpc.kugou.com/v1/search/songs"
    LYRICS_URL = "http://lyrics.kugou.com/download"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取 HTTP 会话"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def search_song(self, keywords: str, page: int = 1) -> List[Dict]:
        """搜索歌曲

        Args:
            keywords: 搜索关键词
            page: 页码 (默认 1)

        Returns:
            歌曲列表
        """
        try:
            session = await self._get_session()

            params = {
                'keyword': keywords,
                'page': page,
                'pagesize': 10,
                'bitrate': 0
            }

            async with session.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout
            ) as resp:
                if resp.status != 200:
                    log.error(f"搜索失败: {resp.status}")
                    return []

                data = await resp.json()
                songs = []

                for item in data.get('data', {}).get('songs', []):
                    song = {
                        'id': item.get('ID'),
                        'name': item.get('SongName'),
                        'artist': ', '.join([
                            a.get('ArtistName', '')
                            for a in item.get('ArtistArray', [])
                        ]),
                        'album': item.get('AlbumName'),
                        'duration': item.get('Duration', 0),
                        'hash': item.get('FileHash'),
                    }
                    songs.append(song)

                log.info(f"搜索 '{keywords}' 找到 {len(songs)} 首歌曲")
                return songs

        except Exception as e:
            log.error(f"搜索歌曲异常: {e}")
            return []

    async def get_lyrics(self, song_hash: str, song_id: str) -> Optional[Dict]:
        """获取歌词

        Args:
            song_hash: 歌曲 hash
            song_id: 歌曲 ID

        Returns:
            歌词信息或 None
        """
        try:
            session = await self._get_session()

            params = {
                'hash': song_hash,
                'id': song_id,
                'client': 'pc',
                'ft': '0'
            }

            async with session.get(
                self.LYRICS_URL,
                params=params,
                timeout=self.timeout
            ) as resp:
                if resp.status != 200:
                    return None

                text = await resp.text()

                # 解析 LRC 格式歌词
                lines = self._parse_lrc(text)

                return {
                    'content': text,
                    'lines': lines,
                }

        except Exception as e:
            log.error(f"获取歌词异常: {e}")
            return None

    @staticmethod
    def _parse_lrc(lrc_content: str) -> List[Dict]:
        """解析 LRC 歌词格式

        LRC 格式:
        [00:10.00]第一行歌词
        [00:20.00]第二行歌词

        Returns:
            [
                {'time': 10.0, 'text': '第一行歌词'},
                {'time': 20.0, 'text': '第二行歌词'},
                ...
            ]
        """
        lines = []
        for line in lrc_content.split('\n'):
            line = line.strip()
            if line.startswith('[') and ']' in line:
                try:
                    time_str = line[1:line.index(']')]
                    text = line[line.index(']') + 1:]

                    # 转换时间格式 mm:ss.cc -> 秒
                    parts = time_str.split(':')
                    minutes = int(parts[0])
                    seconds = float(parts[1])
                    total_seconds = minutes * 60 + seconds

                    lines.append({
                        'time': total_seconds,
                        'text': text
                    })
                except (ValueError, IndexError):
                    continue

        return lines

    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
```

### 第三步：实现歌词显示

```python
# modules/lyrics_display.py (新增)

from PIL import Image, ImageDraw, ImageFont
import os
from typing import Dict, List
import logging

log = logging.getLogger("lyrics")

class LyricsDisplay:
    """歌词显示渲染"""

    def __init__(self, output_path: str = "data/current_lyrics.png"):
        self.output_path = output_path
        # 标准分辨率（与 OBS 中 lyrics_display 源大小一致）
        self.width = 1344
        self.height = 756
        self.bg_color = (0, 0, 0)  # 黑色背景
        self.text_color = (255, 255, 255)  # 白色文字
        self.current_color = (0, 255, 0)  # 绿色当前行

    async def render_lyrics(
        self,
        song_info: Dict,
        current_time: float = 0
    ) -> str:
        """渲染歌词并保存为图像

        Args:
            song_info: {
                'name': '歌曲名',
                'artist': '艺术家',
                'lyrics': [
                    {'time': 10.0, 'text': '歌词行'},
                    ...
                ]
            }
            current_time: 当前播放时间 (秒)

        Returns:
            输出图像路径
        """
        try:
            # 创建背景图像
            img = Image.new('RGB', (self.width, self.height), self.bg_color)
            draw = ImageDraw.Draw(img)

            # 加载字体 (使用系统字体)
            try:
                # Windows
                font = ImageFont.truetype("C:\\Windows\\Fonts\\msyh.ttc", 40)
                small_font = ImageFont.truetype("C:\\Windows\\Fonts\\msyh.ttc", 24)
            except:
                try:
                    # Linux
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
                    small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
                except:
                    # Fallback
                    font = ImageFont.load_default()
                    small_font = font

            # 绘制歌曲信息
            draw.text(
                (672, 50),
                f"{song_info.get('name', '未知歌曲')} - {song_info.get('artist', '未知艺术家')}",
                fill=self.text_color,
                font=font,
                anchor="mm"
            )

            # 绘制歌词
            lyrics = song_info.get('lyrics', [])
            if not lyrics:
                # 如果没有歌词，显示提示
                draw.text(
                    (672, 400),
                    "暂无歌词",
                    fill=self.text_color,
                    font=font,
                    anchor="mm"
                )
            else:
                # 找到当前和前后几行歌词
                current_idx = -1
                for i, line in enumerate(lyrics):
                    if line['time'] > current_time:
                        current_idx = i - 1
                        break
                else:
                    current_idx = len(lyrics) - 1

                # 显示前 3 行、当前行、后 3 行
                start_idx = max(0, current_idx - 3)
                end_idx = min(len(lyrics), current_idx + 4)

                y_pos = 200
                for i in range(start_idx, end_idx):
                    line = lyrics[i]
                    text = line['text']
                    color = self.current_color if i == current_idx else self.text_color

                    draw.text(
                        (672, y_pos),
                        text,
                        fill=color,
                        font=font if i == current_idx else small_font,
                        anchor="mm"
                    )
                    y_pos += 80

            # 保存图像
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            img.save(self.output_path)

            log.debug(f"歌词已渲染: {self.output_path}")
            return self.output_path

        except Exception as e:
            log.error(f"渲染歌词失败: {e}")
            return self.output_path
```

### 第四步：集成到主程序

```python
# cyber_live.py (修改)

async def _lyrics_sync_loop(
    lyrics_display: LyricsDisplay,
    current_song_info: Dict,
    interval: float = 0.5
):
    """歌词同步循环

    定期刷新歌词显示，保持与播放同步
    """
    log.info("歌词同步循环启动")
    last_rendered_time = -1

    try:
        while True:
            try:
                # 获取当前播放时间
                # 方式 1: 从 VLC 获取
                # current_time = await vlc.get_current_time()

                # 方式 2: 从文件读取 (如果有时间戳)
                # current_time = load_playback_time()

                # 为了演示，这里固定获取时间
                # 实际需要与 VLC 或播放器同步
                current_time = get_current_playback_time()

                # 避免频繁重新渲染
                if abs(current_time - last_rendered_time) > 0.1:
                    await lyrics_display.render_lyrics(
                        current_song_info,
                        current_time
                    )
                    last_rendered_time = current_time

            except Exception as e:
                log.debug(f"歌词同步异常: {e}")

            await asyncio.sleep(interval)

    except asyncio.CancelledError:
        log.info("歌词同步循环已取消")
```

---

## 📋 点歌集成方案

### 方案 1：直接通过酷狗 API 点歌 (推荐)

```python
# modules/danmaku.py (修改点歌处理)

async def handle_request_song(self, user: str, song_name: str):
    """处理点歌命令

    用户弹幕: "点歌 歌名"
    """
    log.info(f"{user} 点歌: {song_name}")

    # 1. 通过酷狗 API 搜索歌曲
    results = await self.kugou_api.search_song(song_name)

    if not results:
        self.send_message(f"@{user} 未找到歌曲 '{song_name}'")
        return

    # 2. 选择第一个结果
    song = results[0]
    log.info(f"找到歌曲: {song['name']} - {song['artist']}")

    # 3. 获取歌词
    lyrics_info = await self.kugou_api.get_lyrics(
        song['hash'],
        song['id']
    )

    # 4. 添加到队列
    queue_entry = {
        'id': song['id'],
        'name': song['name'],
        'artist': song['artist'],
        'duration': song['duration'],
        'user': user,
        'lyrics': lyrics_info,
        'url': f"http://www.kugou.com/song/{song['id']}.html"
    }

    self.songs.queue.append(queue_entry)
    self.send_message(f"@{user} 已添加到队列: {song['name']}")

    # 5. 更新点歌队列显示 (BScreen)
    await self.update_song_queue_display()
```

### 方案 2：网页点歌界面

```html
<!-- web/request_song.html -->

<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>点歌</title>
    <style>
        body { font-family: 微软雅黑; }
        #search-results { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .song-item { padding: 10px; border: 1px solid #ccc; cursor: pointer; }
        .song-item:hover { background: #f0f0f0; }
    </style>
</head>
<body>
    <h1>点歌系统</h1>
    <input id="search-box" type="text" placeholder="输入歌曲名或艺术家" />
    <button onclick="search()">搜索</button>

    <div id="search-results"></div>

    <script>
        async function search() {
            const keyword = document.getElementById('search-box').value;
            const response = await fetch(`/api/search_song?q=${keyword}`);
            const results = await response.json();

            const html = results.map(song => `
                <div class="song-item" onclick="requestSong('${song.id}', '${song.name}')">
                    <strong>${song.name}</strong><br>
                    ${song.artist}
                </div>
            `).join('');

            document.getElementById('search-results').innerHTML = html;
        }

        async function requestSong(id, name) {
            await fetch('/api/request_song', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ song_id: id })
            });
            alert(`已添加: ${name}`);
        }
    </script>
</body>
</html>
```

---

## 🎬 lyrics_display 显示方案对比

### 方案 A：纯文字显示 (简单)
```
歌曲: 《三体》- 许嵩

前一行歌词
当前行歌词 (高亮)
后一行歌词
```

### 方案 B：彩色渐进式 (优雅)
```
┌─────────────────────────────┐
│  三体 - 许嵩                   │
├─────────────────────────────┤
│                              │
│      已唱过的歌词 (灰色)       │
│      当前行歌词 (绿色)         │
│      待唱的歌词 (白色)         │
│                              │
│      ████████░░░░░░░░░░░░░░  │
│      1:23 / 3:45            │
└─────────────────────────────┘
```

### 方案 C：实时滚动 (炫彩)
- 歌词逐字显示
- 当前字高亮或变色
- 自动滚动效果

---

## 🚀 实现步骤

### Step 1: 安装酷狗 API 库
```bash
pip install aiohttp  # 酷狗 API 通过 HTTP 调用
```

### Step 2: 实现酷狗 API 模块
- 创建 `modules/kugou_api.py`
- 实现搜索、获取歌词、获取下载链接

### Step 3: 实现歌词显示模块
- 创建 `modules/lyrics_display.py`
- 使用 PIL 渲染歌词图像

### Step 4: 修改点歌逻辑
- 更新 `modules/danmaku.py` 的点歌处理
- 调用酷狗 API 搜索歌曲

### Step 5: 集成歌词同步
- 在 `cyber_live.py` 添加歌词同步循环
- 定期更新 `data/current_lyrics.png`

### Step 6: OBS 配置
- 修改 `lyrics_display` 源为图像
- 指向 `data/current_lyrics.png`
- 配置自动刷新脚本

---

## ⚠️ 注意事项

### 1. 版权问题
- ⚠️ 歌曲和歌词可能受版权保护
- ⚠️ 直播时可能涉及版权声明
- ✅ 建议: 仅用于个人/非商业直播

### 2. API 稳定性
- ⚠️ 第三方 API 可能变化或失效
- ✅ 建议: 添加错误处理和 fallback

### 3. 网络延迟
- ⚠️ 搜索和获取歌词可能有延迟
- ✅ 建议: 添加缓存机制

### 4. 本地文件处理
- ⚠️ 如何处理用户上传的本地歌曲?
- ✅ 建议: 使用 python-lyrics 库查询本地歌曲歌词

---

## 📚 参考资源

### 酷狗 API 文档
- [酷狗音乐搜索 API](http://search.kugou.com/)
- [酷狗歌词下载](http://lyrics.kugou.com/)

### Python 相关库
- [aiohttp](https://docs.aiohttp.org/) - 异步 HTTP 客户端
- [Pillow (PIL)](https://python-pillow.org/) - 图像处理
- [python-lyrics](https://github.com/wzk656/python-lyrics) - 歌词查询

### 替代方案
- [NetEase 网易云音乐 API](https://docs.python.org/zh-cn/3/library/)
- [Genius](https://genius.com/api-clients) - 英文歌词

---

## 📝 总结

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **A: 继续用 VLC + 酷狗歌词** | 稳定、最小改动 | 歌词获取困难 | ⭐⭐⭐⭐⭐ |
| **B: 替换为酷狗完全控制** | 完整、原生点歌 | 可控性差、依赖 API | ⭐⭐ |
| **C: 网易云/其他 API** | 可能更稳定 | 需要重新实现 | ⭐⭐⭐ |

**最终建议：采用方案 A（混合架构）**
- 保留 VLC 的稳定播放
- 使用酷狗 API 获取歌词和点歌
- 最小化代码改动
- 最大化系统稳定性

---

**文档版本**: 1.0
**日期**: 2026-02-15
**维护者**: SingllLive Team

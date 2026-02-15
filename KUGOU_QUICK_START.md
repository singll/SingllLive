# 酷狗音乐 + 歌词显示快速配置指南

> 5 分钟快速上手酷狗音乐 API 和歌词显示功能

---

## 🚀 快速开始

### 第一步：安装依赖

```bash
# 进入项目目录
cd /home/ubuntu/SingllLive

# 安装 Pillow (用于图像处理)
pip install Pillow

# 验证安装
python -c "from PIL import Image; print('✅ Pillow 安装成功')"
```

### 第二步：测试酷狗 API

```bash
# 运行 API 测试脚本
python modules/kugou_api.py

# 预期输出：
# [kugou] 正在搜索歌曲 '三体'...
# [kugou] 找到 10 首歌曲:
# 1. 三体
#    艺术家: 许嵩
#    时长: 220秒
# ...
# [kugou] 获取歌词成功，共 45 行:
# [00:10.00] 第一行歌词
# [00:20.00] 第二行歌词
```

### 第三步：测试歌词显示

```bash
# 运行歌词显示测试脚本
python modules/lyrics_display.py

# 预期输出：
# [lyrics_display] 字体加载完成
# [lyrics_display] 渲染 0s 时的歌词...
# [lyrics_display] 已保存到: data/current_lyrics.png
# [lyrics_display] 渲染 10s 时的歌词...
# ...

# 检查生成的图像
ls -lh data/current_lyrics.png
```

### 第四步：配置 OBS

1. **修改 lyrics_display 源**
   ```
   OBS → AScreen 场景
   源面板 → 双击 "lyrics_display"

   类型更改为：图像
   文件: <项目目录>/data/current_lyrics.png
   ```

2. **添加自动刷新脚本**

   创建 `scripts/obs/lyrics_refresh.lua`：
   ```lua
   -- 自动刷新 lyrics_display 源

   obs = obslua

   local REFRESH_INTERVAL = 100  -- 毫秒
   local last_refresh = 0

   function on_event(event)
       if event == obs.OBS_FRONTEND_EVENT_SCRIPTING_SHUTDOWN then
           return
       end
   end

   function timer_callback()
       local current_time = obs.os_gettime_ns() / 1000000  -- 转换为毫秒

       if current_time - last_refresh >= REFRESH_INTERVAL then
           -- 刷新 lyrics_display 源
           local scene = obs.obs_frontend_get_current_scene()
           if scene then
               local source = obs.obs_scene_find_source(scene, "lyrics_display")
               if source then
                   obs.obs_source_update(source, nil)
               end
               obs.obs_scene_release(scene)
           end

           last_refresh = current_time
       end
   end

   obs.timer_add(timer_callback, REFRESH_INTERVAL)
   ```

3. **在 OBS 中加载脚本**
   ```
   OBS → 工具 → 脚本 → Lua脚本 → [+]
   选择: scripts/obs/lyrics_refresh.lua
   ```

---

## 🎵 集成到弹幕点歌

### 修改 danmaku.py

在点歌处理函数中添加酷狗 API 调用：

```python
# modules/danmaku.py 中的点歌处理

from modules.kugou_api import KugouAPI
from modules.lyrics_display import LyricsDisplay

class DanmakuBot:
    def __init__(self, ...):
        # ... 现有初始化代码 ...
        self.kugou = KugouAPI()
        self.lyrics_display = LyricsDisplay()

    async def handle_request_song(self, user: str, song_name: str):
        """处理点歌命令 - 集成酷狗 API"""
        log.info(f"{user} 点歌: {song_name}")

        try:
            # 1️⃣ 搜索歌曲
            songs = await self.kugou.search_song(song_name, pagesize=5)

            if not songs:
                self.send_message(f"@{user} 未找到歌曲 '{song_name}' 😕")
                return

            # 选择第一个搜索结果
            song = songs[0]
            log.info(f"点歌结果: {song['name']} - {song['artist']}")

            # 2️⃣ 获取歌词
            lyrics_info = await self.kugou.get_lyrics(song['hash'], song['id'])

            # 3️⃣ 准备歌曲信息
            song_info = {
                'id': song['id'],
                'name': song['name'],
                'artist': song['artist'],
                'duration': song['duration'],
                'user': user,
                'request_time': datetime.now(),
            }

            # 如果获取到歌词，保存歌词信息
            if lyrics_info:
                song_info['lyrics'] = lyrics_info['lines']

            # 4️⃣ 添加到队列
            self.songs.queue.append(song_info)

            # 5️⃣ 发送确认消息
            self.send_message(
                f"@{user} 已添加到队列: 《{song['name']}》- {song['artist']}"
            )

            # 6️⃣ 立即渲染歌词显示
            if lyrics_info:
                await self.lyrics_display.render_lyrics(
                    {
                        'name': song['name'],
                        'artist': song['artist'],
                        'lyrics': song_info.get('lyrics', []),
                    },
                    current_time=0,
                    total_time=song['duration'],
                )

            # 7️⃣ 更新点歌队列显示面板
            await self.update_queue_display()

        except Exception as e:
            log.error(f"点歌异常: {e}")
            self.send_message(f"@{user} 点歌失败，请稍后重试 😔")
```

---

## 🎬 歌词同步循环

在 `cyber_live.py` 中添加歌词同步：

```python
# cyber_live.py 中添加

async def _lyrics_sync_loop(
    lyrics_display: LyricsDisplay,
    songs: SongManager,
    interval: float = 0.5
):
    """歌词同步循环 - 实时更新歌词显示"""
    log.info("歌词同步循环启动")
    last_render_time = -1

    try:
        while True:
            try:
                # 1️⃣ 获取当前播放歌曲
                current_song = songs.now_playing
                if not current_song:
                    # 没有正在播放的歌曲，显示等待界面
                    await lyrics_display.render_empty()
                else:
                    # 2️⃣ 获取当前播放时间
                    # 这里需要与 VLC 或播放器同步
                    # 暂时使用固定值用于测试
                    current_time = get_current_playback_time()

                    # 3️⃣ 避免频繁重新渲染
                    if abs(current_time - last_render_time) > 0.1:
                        # 4️⃣ 渲染歌词
                        await lyrics_display.render_lyrics(
                            current_song,
                            current_time=current_time,
                        )
                        last_render_time = current_time

            except Exception as e:
                log.debug(f"歌词同步异常: {e}")

            await asyncio.sleep(interval)

    except asyncio.CancelledError:
        log.info("歌词同步循环已取消")


# 在 run_all() 中启动歌词同步循环
async def run_all(config: configparser.ConfigParser):
    # ... 现有代码 ...

    # 初始化歌词显示
    lyrics_display = LyricsDisplay()

    # 启动歌词同步循环
    tasks.append(asyncio.create_task(
        _lyrics_sync_loop(lyrics_display, songs, interval=0.5)
    ))

    # ... 其他初始化代码 ...
```

---

## 🧪 测试检查清单

### 酷狗 API 测试
- [ ] 可以搜索歌曲 (运行 `modules/kugou_api.py`)
- [ ] 可以获取歌词 (查看测试输出)
- [ ] 缓存功能正常 (重复搜索应该很快)

### 歌词显示测试
- [ ] 图像文件生成成功 (检查 `data/current_lyrics.png`)
- [ ] 图像内容正确 (打开图像查看)
- [ ] 支持中文显示 (歌词中的中文应该正确显示)

### OBS 集成测试
- [ ] lyrics_display 源配置为图像源
- [ ] 图像路径指向正确的文件
- [ ] OBS 脚本正常加载
- [ ] 图像每秒自动刷新

### 端到端测试
- [ ] 发送弹幕点歌 (例如: "点歌 三体")
- [ ] 歌曲被添加到队列
- [ ] 歌词图像被渲染和显示
- [ ] OBS 中 lyrics_display 源显示歌词

---

## 📊 配置示例

### config.ini 配置

```ini
[paths]
# ... 现有配置 ...
song_dir = D:\live\songs\queue
playback_dir = D:\live\songs\playback
data_dir = D:\live\data

[lyrics]
# 歌词显示配置
output_path = data/current_lyrics.png
width = 1344
height = 756
# 刷新间隔 (毫秒)
refresh_interval = 500
```

---

## 🐛 故障排除

### 问题 1：搜索歌曲很慢或超时

**原因**: 酷狗 API 响应慢或网络问题

**解决方案**:
```python
# 增加超时时间
api = KugouAPI(timeout=20)  # 改为 20 秒

# 或者添加重试逻辑
import asyncio
for retry in range(3):
    try:
        songs = await api.search_song(keyword)
        break
    except asyncio.TimeoutError:
        if retry < 2:
            await asyncio.sleep(2)
        else:
            raise
```

### 问题 2：获取歌词失败 (返回 None)

**原因**: 某些歌曲可能没有歌词

**解决方案**:
```python
if not lyrics:
    log.warning(f"歌曲 {song_id} 没有歌词")
    # 使用备选方案：显示等待歌词界面
    await lyrics_display.render_empty()
```

### 问题 3：OBS 中歌词显示不更新

**原因**: 图像源没有配置自动刷新

**解决方案**:
```lua
-- 在 lyrics_refresh.lua 中增加强制刷新
obs.obs_source_list_release(sources)
obs.obs_scene_release(scene)

-- 或者在 OBS 中手动刷新
-- 右键 lyrics_display 源 → 刷新
```

### 问题 4：中文显示乱码

**原因**: 字体不支持中文

**解决方案**:
```python
# 指定支持中文的字体路径
display = LyricsDisplay(
    font_path="C:\\Windows\\Fonts\\msyh.ttc"  # Windows
    # 或 "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"  # Linux
)
```

---

## 📚 后续扩展

### 1. 歌词翻译
```python
# 支持显示英文歌词的中文翻译
song_info = {
    'name': '歌曲名',
    'artist': '艺术家',
    'lyrics': [...],
    'translation': [...],  # 添加翻译
}
```

### 2. 歌词特效
```python
# 支持不同的显示效果
display.render_lyrics_with_effect(
    song_info,
    effect='scroll',  # 滚动效果
    effect='fade',    # 淡入淡出
    effect='bounce',  # 弹跳效果
)
```

### 3. 歌词导出
```python
# 导出歌词为 SRT 或 VTT 格式
lyrics_display.export_lyrics(
    song_info,
    format='srt'  # 或 'vtt'
)
```

---

## ✅ 总结

现在你已经具备了：
- ✅ 酷狗音乐 API 集成 (搜索、获取歌词)
- ✅ 歌词图像实时渲染 (Pillow 实现)
- ✅ OBS 集成显示 (通过图像源)
- ✅ 点歌系统增强 (API 驱动的搜索)

**下一步**：测试系统，监控日志，根据实际情况调整！

---

**文档版本**: 1.0
**日期**: 2026-02-15
**维护者**: SingllLive Team

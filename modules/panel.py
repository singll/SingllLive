"""
B区终端风格信息面板 - Pillow PNG 渲染器
替代 terminal-panel.html + OBS Browser Source (Chromium)

生成 520x435 PNG 图片, 视觉风格复刻原 HTML 终端面板:
- 深色背景 + 绿色提示符 + 青色状态块 + 品红色队列
- OBS 使用 Image Source 加载, 配合 panel_refresh.lua 自动刷新
- GPU 开销: 零 (静态图片)
- CPU 开销: ~5-10ms/帧 (纯文字绘制)
"""

import asyncio
import logging
import os
import sys
import time
from datetime import timedelta as td, datetime, timezone
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from .songs import SongManager

log = logging.getLogger("panel")

# --- 颜色常量 (与 HTML 版一致) ---
C_BG = "#0d0d0d"
C_TEXT = "#c0c0c0"
C_DIM = "#666666"
C_DARK = "#555555"
C_DARKER = "#333333"
C_PROMPT_USER = "#27ca3f"
C_PROMPT_PATH = "#5c9eff"
C_PROMPT_SYM = "#888888"
C_CMD = "#ffffff"
C_CYAN = "#00ffff"
C_MAGENTA = "#ff00ff"
C_YELLOW = "#ffff00"
C_LIVE_GREEN = "#27ca3f"
C_BORDER_STATUS = "#27ca3f"
C_BORDER_PLAYING = "#00ffff"
C_BORDER_QUEUE = "#ff00ff"
C_STATUS_BG = "#0f120f"
C_PLAYING_BG = "#0d1114"
C_QUEUE_BG = "#110d11"
C_HINT_BG = "#1a1a00"

# CJK 字体搜索路径 (Windows + Linux)
_CJK_FONT_CANDIDATES = [
    # Windows
    "C:/Windows/Fonts/msyh.ttc",     # 微软雅黑
    "C:/Windows/Fonts/msyhbd.ttc",   # 微软雅黑 Bold
    "C:/Windows/Fonts/simhei.ttf",   # 黑体
    "C:/Windows/Fonts/simsun.ttc",   # 宋体
    # Linux
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/wenquanyi/wqy-zenhei/wqy-zenhei.ttc",
]


def _hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _find_cjk_font() -> Optional[str]:
    """查找 CJK 字体: 优先同目录下的 Noto Sans CJK, 然后系统字体"""
    # 先检查 assets/fonts/ 下的捆绑字体
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bundled = os.path.join(script_dir, "..", "assets", "fonts", "NotoSansCJKsc-Regular.otf")
    if os.path.exists(bundled):
        return bundled
    for path in _CJK_FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


class PanelRenderer:
    """终端风格面板 PNG 渲染器"""

    def __init__(self, width: int, height: int, output_path: str,
                 song_manager: SongManager, font_path: Optional[str] = None):
        self.width = width
        self.height = height
        self.output_path = output_path
        self.songs = song_manager
        self._start_time = time.time()

        # CJK 字体 (歌名、中文提示等)
        cjk_path = _find_cjk_font()
        if cjk_path:
            log.info(f"CJK 字体: {cjk_path}")

        # 加载字体: 英文用 JetBrains Mono, 中文用 CJK 字体
        # 字体大小: xs(12) sm(13) md(14) lg(18) - 比原来增大, 直播易于看清
        self._font_sm = self._load_font(font_path, 13)
        self._font_md = self._load_font(font_path, 14)
        self._font_lg = self._load_font(font_path, 18)
        self._font_xs = self._load_font(font_path, 12)

        # CJK 字体 (用于包含中文的文本)
        self._cjk_md = self._load_font(cjk_path, 14) if cjk_path else self._font_md
        self._cjk_lg = self._load_font(cjk_path, 18) if cjk_path else self._font_lg
        self._cjk_sm = self._load_font(cjk_path, 13) if cjk_path else self._font_sm

    def _load_font(self, font_path: Optional[str], size: int) -> ImageFont.FreeTypeFont:
        """加载字体, 优先使用指定路径, 回退到系统默认"""
        if font_path and os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
        # 尝试常见等宽字体
        for name in ["JetBrainsMono-Regular.ttf", "Consolas", "consola.ttf",
                      "DejaVuSansMono.ttf", "LiberationMono-Regular.ttf"]:
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                continue
        return ImageFont.load_default()

    def _has_cjk(self, text: str) -> bool:
        """检测文本是否包含 CJK 字符"""
        for ch in text:
            cp = ord(ch)
            if (0x4E00 <= cp <= 0x9FFF or   # CJK Unified Ideographs
                0x3400 <= cp <= 0x4DBF or   # CJK Extension A
                0x3000 <= cp <= 0x303F or   # CJK Symbols
                0xFF00 <= cp <= 0xFFEF):    # Fullwidth Forms
                return True
        return False

    def _pick_font(self, text: str, size: str = "md"):
        """根据文本内容选择字体: CJK 文本用 CJK 字体, ASCII 用等宽字体"""
        if self._has_cjk(text):
            return {"xs": self._cjk_sm, "sm": self._cjk_sm,
                    "md": self._cjk_md, "lg": self._cjk_lg}[size]
        return {"xs": self._font_xs, "sm": self._font_sm,
                "md": self._font_md, "lg": self._font_lg}[size]

    def _get_uptime(self) -> str:
        elapsed = int(time.time() - self._start_time)
        return str(td(seconds=elapsed))

    def _get_beijing_time(self) -> str:
        """获取北京时间 (UTC+8), 格式: 2025-02-15 01:23:45"""
        # 北京时间是 UTC+8
        beijing_tz = timezone(td(hours=8))
        now = datetime.now(beijing_tz)
        return now.strftime("%Y-%m-%d %H:%M:%S")

    def _text_width(self, text: str, font) -> int:
        # font.getbbox() 在 Pillow 8.0+ 可用
        # 对于旧版本使用 getsize() (已弃用但仍可用) 或直接估算
        try:
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0]
        except AttributeError:
            # Pillow < 8.0 fallback: 使用 getsize()
            try:
                return font.getsize(text)[0]
            except Exception:
                # 最后的备选: 粗略估算字宽
                return len(text) * 7

    def render(self):
        """渲染面板并保存为 PNG"""
        img = Image.new("RGB", (self.width, self.height), _hex_to_rgb(C_BG))
        draw = ImageDraw.Draw(img)
        y = 10  # 当前绘制 y 坐标

        # === 1. 命令提示符行 (纯 ASCII) ===
        x = 10
        parts = [
            ("stream@cyber-station", C_PROMPT_USER, self._font_md),
            (":", C_PROMPT_SYM, self._font_md),
            ("~/live", C_PROMPT_PATH, self._font_md),
            ("$ ", C_PROMPT_SYM, self._font_md),
            ("./status.sh --live", C_CMD, self._font_md),
        ]
        for text, color, font in parts:
            draw.text((x, y), text, fill=_hex_to_rgb(color), font=font)
            x += self._text_width(text, font)
        y += 22

        # === 2. 系统状态块 ===
        block_y = y + 4
        block_h = 90
        # 背景
        draw.rectangle(
            [(10, block_y), (self.width - 10, block_y + block_h)],
            fill=_hex_to_rgb(C_STATUS_BG)
        )
        # 左边框线
        draw.rectangle(
            [(10, block_y), (12, block_y + block_h)],
            fill=_hex_to_rgb(C_BORDER_STATUS)
        )

        # 标题
        inner_x = 18
        inner_y = block_y + 8
        draw.text((inner_x, inner_y), "[SYSTEM_STATUS]",
                  fill=_hex_to_rgb(C_PROMPT_USER), font=self._font_xs)
        inner_y += 18

        # 状态行 (纯 ASCII)
        status_rows = [
            ("STREAM", "● LIVE", C_LIVE_GREEN),
            ("UPTIME", self._get_uptime(), C_CYAN),
            ("MODE", "MUSIC_PLAYBACK", C_TEXT),
            ("QUEUE", f"{self.songs.queue_count}", C_CYAN),
        ]
        for key, value, color in status_rows:
            draw.text((inner_x, inner_y), key,
                      fill=_hex_to_rgb(C_PROMPT_SYM), font=self._font_md)
            draw.text((inner_x + 100, inner_y), value,
                      fill=_hex_to_rgb(color), font=self._font_md)
            if key == "QUEUE":
                vw = self._text_width(value, self._font_md)
                draw.text((inner_x + 100 + vw + 5, inner_y), "tracks",
                          fill=_hex_to_rgb(C_DARK), font=self._font_md)
            inner_y += 16

        y = block_y + block_h + 6

        # === 3. 当前播放块 ===
        playing_y = y
        playing_h = 60
        # 背景
        draw.rectangle(
            [(10, playing_y), (self.width - 10, playing_y + playing_h)],
            fill=_hex_to_rgb(C_PLAYING_BG)
        )
        # 左边框线 (粗)
        draw.rectangle(
            [(10, playing_y), (13, playing_y + playing_h)],
            fill=_hex_to_rgb(C_BORDER_PLAYING)
        )

        # 标签 (ASCII)
        draw.text((18, playing_y + 8), ">> NOW_PLAYING",
                  fill=_hex_to_rgb(C_CYAN), font=self._font_xs)

        # 歌名 (可能包含中文 -> 用 CJK 字体)
        song_name = self.songs.now_playing
        song_font = self._pick_font(song_name, "lg")
        # 按像素宽度截断
        max_w = self.width - 40
        display_name = song_name
        while self._text_width(display_name, song_font) > max_w and len(display_name) > 1:
            display_name = display_name[:-1]
        if display_name != song_name:
            display_name = display_name[:-1] + "..."
        draw.text((18, playing_y + 26), display_name,
                  fill=_hex_to_rgb(C_CMD), font=song_font)

        # 进度条
        bar_y = playing_y + playing_h - 8
        bar_w = self.width - 40
        # 背景条
        draw.rectangle(
            [(18, bar_y), (18 + bar_w, bar_y + 4)],
            fill=_hex_to_rgb("#1a1a1a")
        )
        # 渐变进度 (30秒一个周期, 从青色到品红)
        progress = (time.time() % 30) / 30
        fill_w = int(bar_w * progress)
        if fill_w > 1:
            # 按段绘制渐变, 每 4px 一段以提高性能
            step = max(4, fill_w // 60)
            for px in range(0, fill_w, step):
                ratio = px / max(bar_w, 1)
                r = int(255 * ratio)
                g = int(255 * (1 - ratio))
                b = 255
                w = min(step, fill_w - px)
                draw.rectangle(
                    [(18 + px, bar_y), (18 + px + w, bar_y + 4)],
                    fill=(r, g, b)
                )

        y = playing_y + playing_h + 6

        # === 3.5 北京时间显示（显示器支架处） ===
        time_y = y
        time_text = self._get_beijing_time()
        time_font = self._pick_font(time_text, "xs")
        # 时间居中显示
        time_width = self._text_width(time_text, time_font)
        time_x = (self.width - time_width) // 2
        draw.text((time_x, time_y), time_text,
                  fill=_hex_to_rgb(C_DARK), font=time_font)

        y = time_y + 20
        queue_list = self.songs.queue_list()
        queue_display = queue_list[:5]
        remaining = len(queue_list) - 5 if len(queue_list) > 5 else 0

        queue_h = 18 + max(len(queue_display), 1) * 18 + (18 if remaining > 0 else 0) + 10
        queue_y = y

        # 背景
        draw.rectangle(
            [(10, queue_y), (self.width - 10, queue_y + queue_h)],
            fill=_hex_to_rgb(C_QUEUE_BG)
        )
        # 左边框线
        draw.rectangle(
            [(10, queue_y), (12, queue_y + queue_h)],
            fill=_hex_to_rgb(C_BORDER_QUEUE)
        )

        # 标题
        qx = 18
        qy = queue_y + 8
        draw.text((qx, qy), "[QUEUE_LIST]",
                  fill=_hex_to_rgb(C_MAGENTA), font=self._font_xs)
        qy += 18

        if queue_display:
            for i, name in enumerate(queue_display):
                draw.text((qx, qy), f"[{i+1}]",
                          fill=_hex_to_rgb(C_MAGENTA), font=self._font_md)
                name_font = self._pick_font(name, "md")
                draw.text((qx + 35, qy), name,
                          fill=_hex_to_rgb(C_TEXT), font=name_font)
                qy += 18
            if remaining > 0:
                hint = f"... 还有 {remaining} 首"
                draw.text((qx, qy), hint,
                          fill=_hex_to_rgb(C_DARK), font=self._pick_font(hint, "md"))
        else:
            empty_text = "// 队列为空"
            draw.text((qx, qy), empty_text,
                      fill=_hex_to_rgb(C_DARK), font=self._pick_font(empty_text, "md"))

        y = queue_y + queue_h + 6

        # === 5. 底部命令提示 ===
        # 分隔线
        draw.line([(10, y), (self.width - 10, y)],
                  fill=_hex_to_rgb(C_DARKER), width=1)
        y += 8

        # 提示文字
        hint_send = "发送"
        hint_join = "加入队列"
        cmd_text = "点歌 歌名"
        hint_font = self._pick_font(hint_send, "md")
        cmd_font = self._pick_font(cmd_text, "md")
        join_font = self._pick_font(hint_join, "md")

        draw.text((10, y), "$", fill=_hex_to_rgb(C_PROMPT_SYM), font=self._font_md)

        sx = 24
        draw.text((sx, y), hint_send,
                  fill=_hex_to_rgb(C_DARK), font=hint_font)
        sx += self._text_width(hint_send, hint_font) + 6

        # 命令高亮框
        cmd_w = self._text_width(cmd_text, cmd_font)
        draw.rectangle(
            [(sx - 3, y - 1), (sx + cmd_w + 3, y + 15)],
            fill=_hex_to_rgb(C_HINT_BG)
        )
        draw.text((sx, y), cmd_text,
                  fill=_hex_to_rgb(C_YELLOW), font=cmd_font)
        sx += cmd_w + 8

        draw.text((sx, y), hint_join,
                  fill=_hex_to_rgb(C_DARK), font=join_font)
        sx += self._text_width(hint_join, join_font) + 6

        # 闪烁光标 (交替显示)
        if int(time.time() * 2) % 2 == 0:
            draw.rectangle(
                [(sx, y + 1), (sx + 8, y + 14)],
                fill=_hex_to_rgb(C_PROMPT_USER)
            )

        # === 保存 ===
        # 先写临时文件再替换, 防止 OBS 读取到半写文件
        tmp_path = self.output_path + ".tmp"
        img.save(tmp_path, "PNG", optimize=False)
        os.replace(tmp_path, self.output_path)

    async def render_loop(self, interval: float = 3.0):
        """异步循环渲染面板"""
        log.info(f"面板渲染服务启动 ({self.width}x{self.height}, 间隔 {interval}s)")
        while True:
            try:
                self.render()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"面板渲染异常: {e}")
            await asyncio.sleep(interval)

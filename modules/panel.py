"""
B区终端风格信息面板 - 多模式 Pillow PNG 渲染器

支持 5 种播放模式，动态调整面板布局和字体大小：
1. BROADCAST (直播模式) - 显示直播间信息
2. PK (PK模式) - 显示PK对战信息
3. SONG_REQUEST (点歌模式) - 显示点歌队列
4. PLAYBACK (轮播模式) - 显示当前播放和队列预览
5. OTHER (其他模式) - 显示欢迎信息

520×435 PNG 图片，视觉风格：
- 深色背景 + 绿色提示符 + 青色状态块 + 品红色队列
- 模式优先级越高，信息展示越详细
- 字体大小根据模式自动调整，充分利用B区空间
"""

import asyncio
import logging
import os
import time
from datetime import timedelta as td, datetime, timezone
from typing import Optional, Dict, Any

from PIL import Image, ImageDraw, ImageFont

from .songs import SongManager
from .modes import Mode, ModeManager

log = logging.getLogger("panel")

# --- 颜色常量 ---
C_BG = "#0d0d0d"
C_TEXT = "#c0c0c0"
C_DIM = "#666666"
C_CYAN = "#00ffff"
C_MAGENTA = "#ff00ff"
C_YELLOW = "#ffff00"
C_RED = "#ff5555"

# CJK 字体搜索路径
_CJK_FONT_CANDIDATES = [
    # Windows
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
    # Linux
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
]


def _hex_to_rgb(hex_color: str) -> tuple:
    """转换十六进制颜色为 RGB 元组"""
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _find_cjk_font() -> Optional[str]:
    """查找 CJK 字体"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bundled = os.path.join(script_dir, "..", "assets", "fonts", "NotoSansCJKsc-Regular.otf")
    if os.path.exists(bundled):
        return bundled
    for path in _CJK_FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


class PanelRenderer:
    """多模式终端风格面板 PNG 渲染器"""

    def __init__(self, width: int, height: int, output_path: str,
                 song_manager: SongManager, mode_manager: Optional[ModeManager] = None,
                 font_path: Optional[str] = None, obs_controller=None):
        self.width = width
        self.height = height
        self.output_path = output_path
        self.songs = song_manager
        self.mode_manager = mode_manager
        self.obs = obs_controller
        self._start_time = time.time()

        # 加载字体 - 适配 520×435 面板在 1080p 直播中的可读性
        # 观众在全屏 1080p 观看时，B区仅占 ~27% 屏幕宽度
        self._font_xs = self._load_font(font_path, 14)
        self._font_sm = self._load_font(font_path, 17)
        self._font_md = self._load_font(font_path, 20)
        self._font_lg = self._load_font(font_path, 26)
        self._font_xl = self._load_font(font_path, 32)

        # CJK 字体
        cjk_path = _find_cjk_font()
        if cjk_path:
            log.info(f"CJK 字体: {cjk_path}")
        self._cjk_xs = self._load_font(cjk_path, 14) if cjk_path else self._font_xs
        self._cjk_sm = self._load_font(cjk_path, 17) if cjk_path else self._font_sm
        self._cjk_md = self._load_font(cjk_path, 20) if cjk_path else self._font_md
        self._cjk_lg = self._load_font(cjk_path, 26) if cjk_path else self._font_lg
        self._cjk_xl = self._load_font(cjk_path, 32) if cjk_path else self._font_xl

    def _load_font(self, font_path: Optional[str], size: int) -> ImageFont.FreeTypeFont:
        """加载字体，优先使用指定路径，回退到系统默认"""
        if font_path and os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
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
        """根据文本内容选择字体"""
        if self._has_cjk(text):
            return {
                "xs": self._cjk_xs, "sm": self._cjk_sm,
                "md": self._cjk_md, "lg": self._cjk_lg,
                "xl": self._cjk_xl
            }[size]
        return {
            "xs": self._font_xs, "sm": self._font_sm,
            "md": self._font_md, "lg": self._font_lg,
            "xl": self._font_xl
        }[size]

    def _text_width(self, text: str, font) -> int:
        """计算文本宽度"""
        try:
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0]
        except AttributeError:
            try:
                return font.getsize(text)[0]
            except Exception:
                return len(text) * 8

    def _get_uptime(self) -> str:
        """获取运行时间"""
        elapsed = int(time.time() - self._start_time)
        return str(td(seconds=elapsed))

    def _get_beijing_time(self) -> str:
        """获取北京时间"""
        beijing_tz = timezone(td(hours=8))
        now = datetime.now(beijing_tz)
        return now.strftime("%H:%M:%S")

    def render(self):
        """根据当前模式渲染面板"""
        # 创建图像
        img = Image.new("RGB", (self.width, self.height), _hex_to_rgb(C_BG))
        draw = ImageDraw.Draw(img)

        # 获取当前模式
        if self.mode_manager:
            mode = self.mode_manager.current_mode
            mode_state = self.mode_manager.get_mode_state(mode)
        else:
            mode = Mode.PLAYBACK
            mode_state = {}

        # 根据模式调用不同的渲染方法
        if mode == Mode.BROADCAST:
            self._render_broadcast_mode(img, draw, mode_state)
        elif mode == Mode.PK:
            self._render_pk_mode(img, draw, mode_state)
        elif mode == Mode.SONG_REQUEST:
            self._render_song_request_mode(img, draw, mode_state)
        elif mode == Mode.PLAYBACK:
            self._render_playback_mode(img, draw, mode_state)
        else:  # Mode.OTHER
            self._render_other_mode(img, draw, mode_state)

        # 保存为 PNG
        try:
            img.save(self.output_path, "PNG")
        except Exception as e:
            log.error(f"保存 PNG 失败: {e}")

    def _render_broadcast_mode(self, img: Image.Image, draw: ImageDraw.ImageDraw, state: Dict[str, Any]):
        """直播模式 - 显示直播间信息和在线人数"""
        y = 15

        # 标题
        title_font = self._pick_font("直播中", "xl")
        draw.text((15, y), "● 直播中", fill=_hex_to_rgb(C_RED), font=title_font)
        y += 46

        # 在线人数
        viewer_count = state.get("viewer_count", 0)
        info_font = self._pick_font(f"在线: {viewer_count}", "lg")
        draw.text((15, y), f"在线: {viewer_count:,}", fill=_hex_to_rgb(C_CYAN), font=info_font)
        y += 38

        # 运行时间
        uptime_font = self._pick_font(self._get_uptime(), "md")
        draw.text((15, y), f"时长: {self._get_uptime()}", fill=_hex_to_rgb(C_YELLOW), font=uptime_font)
        y += 30

        # 当前歌曲
        current_song = self.songs.now_playing or "等待播放..."
        song_font = self._pick_font(current_song, "md")
        draw.text((15, y), "♫ " + current_song[:22], fill=_hex_to_rgb(C_TEXT), font=song_font)
        y += 30

        # 北京时间
        time_font = self._pick_font(self._get_beijing_time(), "md")
        draw.text((15, y), "时间: " + self._get_beijing_time(), fill=_hex_to_rgb(C_DIM), font=time_font)

        # 提示
        hint_font = self._pick_font("发送「点歌 歌名」即可点歌", "xs")
        draw.text((15, self.height - 25), "发送「点歌 歌名」即可点歌",
                  fill=_hex_to_rgb(C_DIM), font=hint_font)

    def _render_pk_mode(self, img: Image.Image, draw: ImageDraw.ImageDraw, state: Dict[str, Any]):
        """PK模式 - 显示PK对战信息"""
        y = 15

        # 标题
        title_font = self._pick_font("PK模式", "xl")
        draw.text((15, y), "⚔ PK对战", fill=_hex_to_rgb(C_MAGENTA), font=title_font)
        y += 46

        # 对手信息
        opponent_name = state.get("opponent_name", "未知")
        our_score = state.get("our_score", 0)
        opponent_score = state.get("opponent_score", 0)

        score_font = self._pick_font("我方: 0000", "lg")
        draw.text((15, y), f"我方: {our_score:>4}", fill=_hex_to_rgb(C_CYAN), font=score_font)
        y += 38

        draw.text((15, y), f"对手: {opponent_score:>4}", fill=_hex_to_rgb(C_YELLOW), font=score_font)
        y += 38

        opponent_font = self._pick_font(opponent_name[:15], "md")
        draw.text((15, y), f"VS {opponent_name[:15]}", fill=_hex_to_rgb(C_RED), font=opponent_font)
        y += 30

        # 当前歌曲
        current_song = self.songs.now_playing or "等待播放..."
        song_font = self._pick_font(current_song, "md")
        draw.text((15, y), "♫ " + current_song[:22], fill=_hex_to_rgb(C_TEXT), font=song_font)

        # 时间
        time_font = self._pick_font(self._get_beijing_time(), "xs")
        draw.text((15, self.height - 25), self._get_beijing_time(),
                  fill=_hex_to_rgb(C_DIM), font=time_font)

    def _render_song_request_mode(self, img: Image.Image, draw: ImageDraw.ImageDraw, state: Dict[str, Any]):
        """点歌模式 - 显示点歌队列"""
        y = 15

        # 标题
        title_font = self._pick_font("点歌队列", "xl")
        queue_count = state.get("queue_count", 0)
        draw.text((15, y), f"♫ 队列 {queue_count}首", fill=_hex_to_rgb(C_MAGENTA), font=title_font)
        y += 46

        # 当前播放
        current_song = self.songs.now_playing or "等待播放..."
        song_font = self._pick_font(current_song, "lg")
        draw.text((15, y), "▶ " + current_song[:18], fill=_hex_to_rgb(C_CYAN), font=song_font)
        y += 38

        # 队列列表 (最多显示4首) - 使用实际点歌队列
        queue_songs = self.songs.queue_list()[:4]
        if not queue_songs:
            empty_font = self._pick_font("暂无排队", "md")
            draw.text((15, y), "暂无排队", fill=_hex_to_rgb(C_DIM), font=empty_font)
            y += 28
        else:
            for i, song in enumerate(queue_songs, 1):
                song_line = f"{i}. {song[:20]}"
                q_font = self._pick_font(song_line, "sm")
                draw.text((15, y), song_line, fill=_hex_to_rgb(C_TEXT), font=q_font)
                y += 26

        # 提示
        hint_font = self._pick_font("发送「点歌 歌名」加入队列", "xs")
        draw.text((15, self.height - 45), "发送「点歌 歌名」加入队列",
                  fill=_hex_to_rgb(C_MAGENTA), font=hint_font)

        # 时间
        time_font = self._pick_font(self._get_beijing_time(), "xs")
        draw.text((15, self.height - 22), self._get_beijing_time(),
                  fill=_hex_to_rgb(C_DIM), font=time_font)

    def _render_playback_mode(self, img: Image.Image, draw: ImageDraw.ImageDraw, state: Dict[str, Any]):
        """轮播模式 - 显示当前播放和队列预览"""
        y = 15

        # 标题
        title_font = self._pick_font("轮播模式", "lg")
        draw.text((15, y), "[轮播模式]", fill=_hex_to_rgb(C_CYAN), font=title_font)
        y += 36

        # 当前播放（大字）
        current_song = self.songs.now_playing or "等待播放..."
        song_font = self._pick_font(current_song, "lg")
        draw.text((15, y), "▶ " + current_song[:18], fill=_hex_to_rgb(C_CYAN), font=song_font)
        y += 38

        # 下一首 (显示歌曲库的前几首)
        all_songs = self.songs.list_songs(limit=2)
        if all_songs:
            next_font = self._pick_font(all_songs[0], "md")
            draw.text((15, y), "> " + all_songs[0][:22], fill=_hex_to_rgb(C_TEXT), font=next_font)
            y += 30

        # 点歌队列预览
        queue_songs = self.songs.queue_list()[:3]
        if queue_songs:
            draw.text((15, y), "点歌队列:", fill=_hex_to_rgb(C_MAGENTA), font=self._pick_font("点歌队列:", "md"))
            y += 28
            for i, song in enumerate(queue_songs, 1):
                song_line = f"{i}. {song[:20]}"
                q_font = self._pick_font(song_line, "sm")
                draw.text((20, y), song_line, fill=_hex_to_rgb(C_DIM), font=q_font)
                y += 26
        else:
            draw.text((15, y), "发送「点歌 歌名」即可点歌",
                      fill=_hex_to_rgb(C_DIM), font=self._pick_font("发送「点歌 歌名」即可点歌", "xs"))
            y += 22

        # 统计
        total_font = self._pick_font(f"共 {self.songs.total} 首", "xs")
        draw.text((15, self.height - 45), f"共 {self.songs.total} 首",
                  fill=_hex_to_rgb(C_DIM), font=total_font)

        # 时间
        time_font = self._pick_font(self._get_beijing_time(), "xs")
        draw.text((15, self.height - 22), self._get_beijing_time(),
                  fill=_hex_to_rgb(C_DIM), font=time_font)

    def _render_other_mode(self, img: Image.Image, draw: ImageDraw.ImageDraw, state: Dict[str, Any]):
        """其他模式 - 显示欢迎信息和帮助"""
        y = 40

        # 欢迎
        welcome_font = self._pick_font("程序员深夜电台", "xl")
        draw.text((15, y), "程序员深夜电台", fill=_hex_to_rgb(C_CYAN), font=welcome_font)
        y += 50

        # 说明
        info1_font = self._pick_font("发送「点歌 歌名」点歌", "md")
        draw.text((15, y), "发送「点歌 歌名」点歌",
                  fill=_hex_to_rgb(C_TEXT), font=info1_font)
        y += 32

        info2_font = self._pick_font("发送「切歌」切换歌曲", "md")
        draw.text((15, y), "发送「切歌」切换歌曲",
                  fill=_hex_to_rgb(C_TEXT), font=info2_font)
        y += 32

        info3_font = self._pick_font("发送「歌单」查看全部", "md")
        draw.text((15, y), "发送「歌单」查看全部",
                  fill=_hex_to_rgb(C_TEXT), font=info3_font)
        y += 55

        # 提示
        hint_font = self._pick_font("感谢关注~", "lg")
        draw.text((15, y), "感谢关注~", fill=_hex_to_rgb(C_MAGENTA), font=hint_font)

        # 时间
        time_font = self._pick_font(self._get_beijing_time(), "xs")
        draw.text((15, self.height - 22), self._get_beijing_time(),
                  fill=_hex_to_rgb(C_DIM), font=time_font)

    async def render_loop(self, interval: float = 1.0):
        """异步循环渲染面板"""
        log.info(f"面板渲染器启动 (间隔 {interval}s)")
        try:
            while True:
                self.render()
                # 通过 OBS WebSocket 刷新图像源
                if self.obs:
                    await self.obs.refresh_image_source()
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            log.info("面板渲染器停止")
            raise

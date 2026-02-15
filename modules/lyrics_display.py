"""
歌词显示渲染模块

将歌词信息渲染为图像，供 OBS 显示
"""

from PIL import Image, ImageDraw, ImageFont
import os
from typing import Dict, List, Optional
import logging
from datetime import datetime

log = logging.getLogger("lyrics_display")


class LyricsDisplay:
    """歌词图像渲染和显示

    将歌词信息实时渲染为 PNG 图像，供 OBS 的 lyrics_display 源显示
    """

    def __init__(
        self,
        output_path: str = "data/current_lyrics.png",
        width: int = 1344,
        height: int = 756,
        font_path: Optional[str] = None,
    ):
        """初始化歌词显示

        Args:
            output_path: 输出图像路径
            width: 图像宽度 (像素)
            height: 图像高度 (像素)
            font_path: 自定义字体路径 (可选)
        """
        self.output_path = output_path
        self.width = width
        self.height = height
        self.font_path = font_path

        # 颜色配置 (RGB)
        self.colors = {
            'bg': (15, 15, 15),           # 深灰黑背景
            'title': (255, 255, 255),     # 白色标题
            'current': (0, 255, 100),     # 绿色当前行
            'next': (200, 200, 200),      # 浅灰后续行
            'prev': (100, 100, 100),      # 深灰前面行
            'progress_bar': (0, 200, 100), # 绿色进度条
        }

        # 加载字体
        self._load_fonts()

    def _load_fonts(self):
        """加载系统字体"""
        self.fonts = {}

        # 大字体 (标题)
        try:
            # Windows
            self.fonts['title'] = ImageFont.truetype(
                "C:\\Windows\\Fonts\\msyh.ttc", 48
            )
        except:
            try:
                # Linux (Noto Sans CJK)
                self.fonts['title'] = ImageFont.truetype(
                    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 48
                )
            except:
                try:
                    # Linux fallback
                    self.fonts['title'] = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48
                    )
                except:
                    self.fonts['title'] = ImageFont.load_default()

        # 中字体 (歌词行)
        try:
            # Windows
            self.fonts['lyrics'] = ImageFont.truetype(
                "C:\\Windows\\Fonts\\msyh.ttc", 36
            )
        except:
            try:
                # Linux
                self.fonts['lyrics'] = ImageFont.truetype(
                    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 36
                )
            except:
                try:
                    self.fonts['lyrics'] = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36
                    )
                except:
                    self.fonts['lyrics'] = ImageFont.load_default()

        # 小字体 (时间/其他信息)
        try:
            # Windows
            self.fonts['small'] = ImageFont.truetype(
                "C:\\Windows\\Fonts\\msyh.ttc", 24
            )
        except:
            try:
                # Linux
                self.fonts['small'] = ImageFont.truetype(
                    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 24
                )
            except:
                try:
                    self.fonts['small'] = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24
                    )
                except:
                    self.fonts['small'] = ImageFont.load_default()

        log.info("字体加载完成")

    async def render_lyrics(
        self,
        song_info: Dict,
        current_time: float = 0.0,
        total_time: float = 0.0,
    ) -> str:
        """渲染歌词并保存为图像

        Args:
            song_info: 歌曲信息
            {
                'name': '歌曲名',
                'artist': '艺术家',
                'lyrics': [
                    {'time': 10.0, 'text': '歌词行'},
                    ...
                ]
            }
            current_time: 当前播放时间 (秒)
            total_time: 歌曲总时长 (秒)

        Returns:
            输出图像路径
        """
        try:
            # 创建背景图像
            img = Image.new('RGB', (self.width, self.height), self.colors['bg'])
            draw = ImageDraw.Draw(img)

            # 绘制内容
            self._draw_title(draw, song_info)
            self._draw_lyrics(draw, song_info, current_time)
            self._draw_progress_bar(draw, current_time, total_time)
            self._draw_time_display(draw, current_time, total_time)

            # 保存图像
            os.makedirs(os.path.dirname(self.output_path) or '.', exist_ok=True)
            img.save(self.output_path)

            return self.output_path

        except Exception as e:
            log.error(f"渲染歌词失败: {e}")
            # 返回输出路径即使失败，避免中断播放
            return self.output_path

    def _draw_title(self, draw: ImageDraw.ImageDraw, song_info: Dict):
        """绘制歌曲标题和艺术家

        Args:
            draw: ImageDraw 对象
            song_info: 歌曲信息
        """
        song_name = song_info.get('name', '未知歌曲')
        artist = song_info.get('artist', '未知艺术家')
        title_text = f"{song_name} - {artist}"

        # 计算文本位置 (水平居中，顶部)
        title_font = self.fonts.get('title', ImageFont.load_default())
        bbox = draw.textbbox((0, 0), title_text, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        y = 40

        # 绘制文本
        draw.text(
            (x, y),
            title_text,
            fill=self.colors['title'],
            font=title_font,
        )

    def _draw_lyrics(
        self,
        draw: ImageDraw.ImageDraw,
        song_info: Dict,
        current_time: float,
    ):
        """绘制歌词行

        显示：前两行、当前行(高亮)、后两行

        Args:
            draw: ImageDraw 对象
            song_info: 歌曲信息
            current_time: 当前播放时间
        """
        lyrics = song_info.get('lyrics', [])

        if not lyrics:
            # 如果没有歌词，显示提示
            no_lyrics_text = "暂无歌词"
            lyrics_font = self.fonts.get('lyrics', ImageFont.load_default())
            bbox = draw.textbbox((0, 0), no_lyrics_text, font=lyrics_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            y = self.height // 2

            draw.text(
                (x, y),
                no_lyrics_text,
                fill=self.colors['next'],
                font=lyrics_font,
            )
            return

        # 找到当前歌词行索引
        current_idx = -1
        for i, line in enumerate(lyrics):
            if line['time'] > current_time:
                current_idx = i - 1
                break
        else:
            current_idx = len(lyrics) - 1

        current_idx = max(0, min(current_idx, len(lyrics) - 1))

        # 计算要显示的行范围
        lines_to_show = 5  # 显示当前行前后各 2 行
        start_idx = max(0, current_idx - 2)
        end_idx = min(len(lyrics), current_idx + 3)

        # 计算起始 y 位置 (垂直居中)
        total_lines = end_idx - start_idx
        line_height = 70
        total_height = total_lines * line_height
        start_y = (self.height - 180 - total_height) // 2 + 120

        lyrics_font = self.fonts.get('lyrics', ImageFont.load_default())
        small_font = self.fonts.get('small', ImageFont.load_default())

        # 绘制歌词行
        for i in range(start_idx, end_idx):
            line = lyrics[i]
            text = line['text']

            # 确定颜色和字体大小
            if i == current_idx:
                color = self.colors['current']
                font = lyrics_font
                bold_offset = 2
            elif i < current_idx:
                color = self.colors['prev']
                font = small_font
                bold_offset = 0
            else:
                color = self.colors['next']
                font = small_font
                bold_offset = 0

            # 计算 y 位置
            y = start_y + (i - start_idx) * line_height

            # 水平居中绘制
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2

            # 绘制文本
            draw.text((x, y), text, fill=color, font=font)

    def _draw_progress_bar(
        self,
        draw: ImageDraw.ImageDraw,
        current_time: float,
        total_time: float,
    ):
        """绘制播放进度条

        Args:
            draw: ImageDraw 对象
            current_time: 当前播放时间 (秒)
            total_time: 歌曲总时长 (秒)
        """
        if total_time <= 0:
            return

        # 进度条位置和大小
        bar_width = self.width - 80
        bar_height = 4
        bar_x = 40
        bar_y = self.height - 80

        # 计算进度
        progress = min(current_time / total_time, 1.0)
        filled_width = int(bar_width * progress)

        # 绘制背景
        draw.rectangle(
            [(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)],
            fill=(50, 50, 50),
        )

        # 绘制进度条
        if filled_width > 0:
            draw.rectangle(
                [(bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height)],
                fill=self.colors['progress_bar'],
            )

    def _draw_time_display(
        self,
        draw: ImageDraw.ImageDraw,
        current_time: float,
        total_time: float,
    ):
        """绘制时间显示

        Args:
            draw: ImageDraw 对象
            current_time: 当前播放时间 (秒)
            total_time: 歌曲总时长 (秒)
        """
        # 格式化时间 mm:ss
        def format_time(seconds: float) -> str:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02d}:{secs:02d}"

        time_text = f"{format_time(current_time)} / {format_time(total_time)}"

        # 绘制时间
        small_font = self.fonts.get('small', ImageFont.load_default())
        bbox = draw.textbbox((0, 0), time_text, font=small_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        y = self.height - 45

        draw.text(
            (x, y),
            time_text,
            fill=self.colors['next'],
            font=small_font,
        )

    async def render_empty(self) -> str:
        """渲染空白歌词 (当没有正在播放的歌曲时)

        Returns:
            输出图像路径
        """
        img = Image.new('RGB', (self.width, self.height), self.colors['bg'])
        draw = ImageDraw.Draw(img)

        # 绘制 "等待播放..." 文本
        text = "等待播放中..."
        font = self.fonts.get('title', ImageFont.load_default())
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        y = self.height // 2

        draw.text((x, y), text, fill=self.colors['next'], font=font)

        # 保存图像
        os.makedirs(os.path.dirname(self.output_path) or '.', exist_ok=True)
        img.save(self.output_path)

        return self.output_path


# 使用示例
async def main():
    """使用示例"""
    from kugou_api import KugouAPI

    api = KugouAPI()
    display = LyricsDisplay()

    try:
        # 搜索歌曲
        print("🔍 正在搜索歌曲 '三体'...")
        songs = await api.search_song("三体", pagesize=1)

        if not songs:
            print("❌ 未找到歌曲")
            return

        song = songs[0]
        print(f"✅ 找到: {song['name']} - {song['artist']}")

        # 获取歌词
        print("📝 正在获取歌词...")
        lyrics = await api.get_lyrics(song['hash'], song['id'])

        if not lyrics:
            print("❌ 获取歌词失败")
            return

        print(f"✅ 获取歌词成功，共 {len(lyrics['lines'])} 行")

        # 渲染歌词图像
        song_info = {
            'name': song['name'],
            'artist': song['artist'],
            'lyrics': lyrics['lines'],
        }

        # 模拟不同时间点的渲染
        for current_time in [0, 10, 20, 30, 40]:
            print(f"\n⏱️  渲染 {current_time}s 时的歌词...")
            output_path = await display.render_lyrics(
                song_info,
                current_time=current_time,
                total_time=200,
            )
            print(f"✅ 已保存到: {output_path}")

    finally:
        await api.close()


if __name__ == '__main__':
    import asyncio
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format='[%(name)s] %(message)s'
    )

    asyncio.run(main())

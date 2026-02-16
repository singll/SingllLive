"""
VLC 源播放控制器 - 通过 OBS WebSocket 管理 VLC 视频源

替代之前的 .m3u 文件轮转方案，直接通过 OBS WebSocket API 设置 VLC 源的播放列表。

功能:
  - play(filepath): 点歌即时播放单个文件
  - play_directory(directory): 轮播模式播放整个目录
  - next_song(): 切歌 (跳到下一首)
  - stop(): 停止播放
  - clear_song_request(): 清除点歌，恢复轮播
"""

import logging
import os
from typing import Optional

from .songs import SongManager
from .obs_control import OBSController, MEDIA_NEXT, MEDIA_STOP, MEDIA_RESTART

log = logging.getLogger("vlc")

# 支持的媒体文件扩展名
MEDIA_EXTENSIONS = {'.mp3', '.mp4', '.mkv', '.avi', '.flv', '.m4a', '.aac', '.ogg', '.wav'}


class VLCController:
    """OBS VLC 源播放控制器

    通过 OBS WebSocket 直接控制 VLC 源的播放列表和媒体状态。
    不再生成 .m3u 文件，不再依赖 Lua 脚本。
    """

    def __init__(self, obs: OBSController, song_manager: SongManager,
                 playback_dir: str, song_dir: str, data_dir: str):
        """
        Args:
            obs: OBS WebSocket 控制器
            song_manager: 歌曲管理器
            playback_dir: 轮播目录 (本地歌曲库)
            song_dir: 点歌队列目录
            data_dir: 运行时数据目录
        """
        self.obs = obs
        self.songs = song_manager
        self.playback_dir = playback_dir
        self.song_dir = song_dir
        self.data_dir = data_dir

        self._current_song_request: Optional[str] = None
        self._current_mode: Optional[str] = None
        self._playback_files: list[str] = []  # 缓存轮播文件列表

        log.info("VLC 控制器已初始化 (OBS WebSocket 模式)")
        log.info(f"  轮播目录: {self.playback_dir}")
        log.info(f"  点歌目录: {self.song_dir}")

    def close(self):
        """清理资源"""
        pass

    def _scan_directory(self, directory: str) -> list[str]:
        """扫描目录中的媒体文件

        Args:
            directory: 要扫描的目录

        Returns:
            排序后的文件路径列表
        """
        files = []
        if not directory or not os.path.isdir(directory):
            log.warning(f"目录不存在: {directory}")
            return files

        try:
            for root, _dirs, filenames in os.walk(directory):
                for filename in filenames:
                    if os.path.splitext(filename)[1].lower() in MEDIA_EXTENSIONS:
                        full_path = os.path.join(root, filename)
                        files.append(full_path)
            files.sort()
            log.debug(f"扫描完成: {directory} - {len(files)} 个媒体文件")
        except Exception as e:
            log.error(f"扫描目录失败 {directory}: {e}")

        return files

    async def play(self, filepath: str) -> bool:
        """播放单个文件 (点歌即时播放)

        设置 VLC 源的播放列表为单个文件，立即开始播放。

        Args:
            filepath: 要播放的文件绝对路径
        """
        if not os.path.exists(filepath):
            log.error(f"文件不存在: {filepath}")
            return False

        self._current_song_request = filepath
        song_name = os.path.splitext(os.path.basename(filepath))[0]

        # 设置 VLC 源播放列表为单个文件
        success = await self.obs.set_vlc_playlist([filepath])
        if success:
            self.songs.now_playing = song_name
            self._current_mode = "song_request"
            log.info(f"即时播放: {song_name}")
            self._write_now_playing(song_name)
        else:
            log.error(f"设置 VLC 播放列表失败: {filepath}")

        return success

    async def play_directory(self, directory: str) -> bool:
        """播放目录中的所有文件 (轮播模式)

        Args:
            directory: 要播放的目录
        """
        files = self._scan_directory(directory)
        if not files:
            log.warning(f"目录为空: {directory}")
            return False

        self._playback_files = files
        self._current_song_request = None

        success = await self.obs.set_vlc_playlist(files)
        if success:
            self._current_mode = "playback"
            first_song = os.path.splitext(os.path.basename(files[0]))[0]
            self.songs.now_playing = first_song
            log.info(f"轮播已启动: {len(files)} 个文件 (来自: {directory})")
            self._write_now_playing(first_song)
        return success

    async def next_song(self) -> bool:
        """切歌 - 跳到下一首"""
        # 如果当前是点歌，清除并恢复轮播
        if self._current_song_request:
            log.info("点歌已切歌，恢复轮播")
            return await self.clear_song_request()

        # 否则跳到轮播的下一首
        success = await self.obs.media_action(MEDIA_NEXT)
        if success:
            log.info("已切歌 (下一首)")
        return success

    async def stop(self) -> bool:
        """停止播放"""
        success = await self.obs.media_action(MEDIA_STOP)
        if success:
            log.info("播放已停止")
        return success

    async def clear_song_request(self) -> bool:
        """清除当前点歌请求，恢复轮播列表

        Returns:
            是否成功恢复轮播
        """
        if not self._current_song_request:
            return True

        log.info("清除点歌请求，恢复轮播")
        self._current_song_request = None
        return await self.play_directory(self.playback_dir)

    def _write_now_playing(self, song_name: str):
        """写入 now_playing.txt (供 OBS 底部字幕使用)"""
        try:
            np_file = os.path.join(self.data_dir, "now_playing.txt")
            with open(np_file, "w", encoding="utf-8") as f:
                f.write(song_name)
        except OSError:
            pass

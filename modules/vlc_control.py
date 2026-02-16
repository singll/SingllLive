"""
VLC 源播放控制器 - 通过 OBS WebSocket 管理 VLC 视频源

功能:
  - play(filepath): 点歌即时播放单个文件
  - play_directory(directory): 播放整个目录
  - next_song(): 切歌 (模式感知)
  - stop(): 停止播放
  - transition_to_mode(old_key, new_key): 模式切换，保存/恢复状态
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

from .songs import SongManager
from .replay import ReplayManager
from .obs_control import OBSController, MEDIA_NEXT, MEDIA_STOP, MEDIA_RESTART

log = logging.getLogger("vlc")

# 支持的媒体文件扩展名
MEDIA_EXTENSIONS = {'.mp3', '.mp4', '.mkv', '.avi', '.flv', '.m4a', '.aac', '.ogg', '.wav'}


@dataclass
class ModeVLCState:
    """某个模式的 VLC 播放状态快照"""
    playlist: list[str] = field(default_factory=list)
    current_file: Optional[str] = None


class VLCController:
    """OBS VLC 源播放控制器

    通过 OBS WebSocket 直接控制 VLC 源的播放列表和媒体状态。
    支持模式切换时保存/恢复播放状态。
    """

    def __init__(self, obs: OBSController, song_manager: SongManager,
                 replay_manager: ReplayManager,
                 playback_dir: str, song_dir: str, replay_dir: str,
                 data_dir: str):
        """
        Args:
            obs: OBS WebSocket 控制器
            song_manager: 歌曲管理器
            replay_manager: 回放管理器
            playback_dir: 录像目录 (录像模式循环播放)
            song_dir: 歌曲目录
            replay_dir: 录播目录 (回放模式)
            data_dir: 运行时数据目录
        """
        self.obs = obs
        self.songs = song_manager
        self.replays = replay_manager
        self.playback_dir = playback_dir
        self.song_dir = song_dir
        self.replay_dir = replay_dir
        self.data_dir = data_dir

        self._current_song_request: Optional[str] = None
        self._current_replay_request: Optional[str] = None
        self._current_mode: Optional[str] = None
        self._playback_files: list[str] = []

        # 各模式的播放状态快照
        self._mode_states: dict[str, ModeVLCState] = {}

        log.info("VLC 控制器已初始化 (OBS WebSocket 模式)")
        log.info(f"  录像目录: {self.playback_dir}")
        log.info(f"  歌曲目录: {self.song_dir}")
        log.info(f"  录播目录: {self.replay_dir}")

    def close(self):
        """清理资源"""
        pass

    def _scan_directory(self, directory: str) -> list[str]:
        """扫描目录中的媒体文件"""
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

    def _save_mode_state(self, mode_key: str):
        """保存当前模式的播放状态"""
        if not mode_key:
            return
        # 只为有播放列表的模式保存状态
        if mode_key in ("video", "music", "replay"):
            current_file = None
            if mode_key == "video":
                # 录像模式：当前播放的是 now_playing 对应的文件
                current_file = self._current_song_request or self._get_current_file_from_now_playing()
            elif mode_key == "music":
                current_file = self._current_song_request
            elif mode_key == "replay":
                current_file = self._current_replay_request

            state = ModeVLCState(
                playlist=list(self._playback_files),
                current_file=current_file,
            )
            self._mode_states[mode_key] = state
            log.debug(f"已保存模式状态: {mode_key} (播放列表: {len(state.playlist)} 个文件)")

    def _get_current_file_from_now_playing(self) -> Optional[str]:
        """根据 now_playing 名称在播放列表中查找文件路径"""
        now = self.songs.now_playing
        if not now or now == "等待播放...":
            return None
        for fp in self._playback_files:
            name = os.path.splitext(os.path.basename(fp))[0]
            if name == now:
                return fp
        return None

    async def _restore_mode_state(self, mode_key: str) -> bool:
        """恢复已保存的模式播放状态

        将播放列表旋转，使保存时的文件排第一位。
        Returns:
            是否成功恢复 (False 表示无保存状态)
        """
        state = self._mode_states.get(mode_key)
        if not state or not state.playlist:
            return False

        playlist = list(state.playlist)

        # 如果有保存的当前文件，旋转列表使其排第一
        if state.current_file and state.current_file in playlist:
            idx = playlist.index(state.current_file)
            playlist = playlist[idx:] + playlist[:idx]

        self._playback_files = playlist
        success = await self.obs.set_vlc_playlist(playlist)
        if success:
            first_name = os.path.splitext(os.path.basename(playlist[0]))[0]
            self.songs.now_playing = first_name
            self._write_now_playing(first_name)
            log.info(f"已恢复模式状态: {mode_key} (从 {first_name} 继续)")
        return success

    async def transition_to_mode(self, old_key: str, new_key: str):
        """模式切换：保存旧模式状态，进入新模式

        Args:
            old_key: 旧模式键 (如 "video", "music", "replay")
            new_key: 新模式键
        """
        # 1. 保存旧模式状态
        self._save_mode_state(old_key)

        # 2. 进入新模式
        if new_key == "video":
            restored = await self._restore_mode_state("video")
            if not restored:
                await self.play_directory(self.playback_dir)
            self._current_mode = "video"
            self._current_song_request = None
            self._current_replay_request = None

        elif new_key == "music":
            restored = await self._restore_mode_state("music")
            if not restored:
                # 歌曲模式无保存状态时，等待点歌（不主动播放）
                pass
            self._current_mode = "music"
            self._current_replay_request = None

        elif new_key == "replay":
            restored = await self._restore_mode_state("replay")
            if not restored:
                await self.play_directory(self.replay_dir)
            self._current_mode = "replay"
            self._current_song_request = None

        elif new_key in ("broadcast", "pk"):
            await self.stop()
            self._current_mode = new_key

        elif new_key == "other":
            await self.stop()
            self._current_mode = "other"

    async def play(self, filepath: str) -> bool:
        """播放单个文件 (点歌即时播放)"""
        if not os.path.exists(filepath):
            log.error(f"文件不存在: {filepath}")
            return False

        self._current_song_request = filepath
        song_name = os.path.splitext(os.path.basename(filepath))[0]

        success = await self.obs.set_vlc_playlist([filepath])
        if success:
            self._playback_files = [filepath]
            self.songs.now_playing = song_name
            self._current_mode = "music"
            log.info(f"即时播放: {song_name}")
            self._write_now_playing(song_name)
        else:
            log.error(f"设置 VLC 播放列表失败: {filepath}")

        return success

    async def play_replay(self, filepath: str, code: str) -> bool:
        """播放单个录播文件 (点播即时播放)"""
        if not os.path.exists(filepath):
            log.error(f"文件不存在: {filepath}")
            return False

        self._current_replay_request = filepath

        success = await self.obs.set_vlc_playlist([filepath])
        if success:
            self._playback_files = [filepath]
            self.replays.now_playing = code
            self.songs.now_playing = f"回放 {code}"
            self._current_mode = "replay"
            log.info(f"即时播放录播: {code}")
            self._write_now_playing(f"回放 {code}")
        else:
            log.error(f"设置 VLC 播放列表失败: {filepath}")

        return success

    async def play_directory(self, directory: str) -> bool:
        """播放目录中的所有文件"""
        files = self._scan_directory(directory)
        if not files:
            log.warning(f"目录为空: {directory}")
            return False

        self._playback_files = files
        self._current_song_request = None
        self._current_replay_request = None

        success = await self.obs.set_vlc_playlist(files)
        if success:
            first_song = os.path.splitext(os.path.basename(files[0]))[0]
            self.songs.now_playing = first_song
            log.info(f"目录播放已启动: {len(files)} 个文件 (来自: {directory})")
            self._write_now_playing(first_song)
        return success

    async def next_song(self) -> bool:
        """切歌 - 模式感知

        video: MEDIA_NEXT
        music: 弹出歌曲队列，队列空则恢复录像模式
        replay: 弹出点播队列，队列空则 MEDIA_NEXT
        """
        if self._current_mode == "music":
            # 歌曲模式：弹出队列下一首
            next_item = self.songs.queue_pop()
            if next_item:
                name, filepath = next_item
                return await self.play(filepath)
            else:
                # 队列空，恢复录像模式（通过返回 False 让调用者处理）
                log.info("歌曲队列已空，等待切换到录像模式")
                self._current_song_request = None
                return False

        elif self._current_mode == "replay":
            # 回放模式：弹出点播队列下一个
            if self._current_replay_request:
                next_item = self.replays.queue_pop()
                if next_item:
                    code, filepath = next_item
                    return await self.play_replay(filepath, code)
                else:
                    # 点播队列空，恢复正常回放序列
                    log.info("点播已切歌，恢复回放序列")
                    self._current_replay_request = None
                    return await self.play_directory(self.replay_dir)
            else:
                success = await self.obs.media_action(MEDIA_NEXT)
                if success:
                    log.info("已切歌 (下一首)")
                return success

        else:
            # 录像模式及其他：直接 MEDIA_NEXT
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
        """清除当前点歌请求，恢复录像列表"""
        if not self._current_song_request:
            return True

        log.info("清除点歌请求，恢复录像")
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

"""
VLC 播放列表管理 - 为 OBS 内置 libvlc 生成 .m3u 播放列表文件 (Plan A - 无外挂 VLC)

说明：
- 方案 A 不再启动外挂 VLC 进程
- 改为生成 .m3u 播放列表文件
- OBS VLC 视频源通过 libvlc 播放本地文件
- Python 后端通过修改文件系统控制播放内容
"""

import logging
import os
from typing import Optional

from .songs import SongManager

log = logging.getLogger("vlc")


class VLCController:
    """OBS VLC 源的播放列表管理器 (Plan A - 无外挂 VLC 进程)

    生成 .m3u 播放列表文件供 OBS 内置 libvlc 使用
    """

    def __init__(self, vlc_path: str, http_port: int, http_password: str,
                 song_dir: str, song_manager: SongManager,
                 playback_dir: Optional[str] = None,
                 playlist_file: str = "current_playlist.m3u"):
        # 注意：vlc_path, http_port, http_password 参数保留以兼容现有代码
        # 但在 Plan A 中不再使用（OBS 使用内置 libvlc，不连接外部 VLC 进程）

        # 播放列表管理
        self.song_dir = song_dir  # 点歌队列目录
        self.playback_dir = playback_dir or song_dir  # 轮播目录
        self.playlist_file = playlist_file  # .m3u 文件路径
        self.songs = song_manager

        # 状态追踪
        self._current_playlist_mode: Optional[str] = None

        log.info(f"VLC 播放列表管理器已初始化 (Plan A - 无外挂进程)")
        log.info(f"  - 轮播目录: {self.playback_dir}")
        log.info(f"  - 点歌目录: {self.song_dir}")
        log.info(f"  - 播放列表文件: {self.playlist_file}")

    def close(self):
        """清理资源（兼容接口）"""
        pass  # Plan A 不需要清理（无外挂进程）

    # --- 播放列表管理 (Plan A) ---

    def _get_m3u_content(self, directory: str) -> str:
        """生成 .m3u 播放列表内容

        Args:
            directory: 要扫描的目录

        Returns:
            .m3u 文件内容 (UTF-8 编码)
        """
        m3u_lines = ["#EXTM3U"]

        try:
            if not os.path.isdir(directory):
                log.warning(f"目录不存在: {directory}")
                return "#EXTM3U\n"

            # 扫描目录中的媒体文件
            media_extensions = {'.mp3', '.mp4', '.mkv', '.avi', '.flv', '.m4a', '.aac', '.ogg', '.wav'}
            files = []

            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    if os.path.splitext(filename)[1].lower() in media_extensions:
                        full_path = os.path.join(root, filename)
                        files.append(full_path)

            # 排序文件
            files.sort()

            # 添加文件到 m3u
            for file_path in files:
                # 转换为 file:// 形式的 URI
                uri = "file:///" + file_path.replace("\\", "/").lstrip("/")
                m3u_lines.append(f"#EXTINF:-1,{os.path.basename(file_path)}")
                m3u_lines.append(uri)

            log.debug(f"扫描完成: {directory} - 找到 {len(files)} 个媒体文件")

        except Exception as e:
            log.error(f"扫描目录失败 {directory}: {e}")

        return "\n".join(m3u_lines) + "\n"

    def write_playlist_file(self, mode: str, directory: str) -> bool:
        """将播放列表写入 .m3u 文件

        Args:
            mode: 'playback' (轮播) 或 'song_request' (点歌)
            directory: 要播放的目录

        Returns:
            成功返回 True
        """
        # 跳过重复切换
        if self._current_playlist_mode == mode and mode in ['playback', 'song_request']:
            log.debug(f"播放列表已是 {mode} 模式，跳过写入")
            return True

        try:
            m3u_content = self._get_m3u_content(directory)

            # 写入文件
            with open(self.playlist_file, 'w', encoding='utf-8') as f:
                f.write(m3u_content)

            self._current_playlist_mode = mode
            log.info(f"播放列表已更新 ({mode} 模式): {self.playlist_file}")
            log.info(f"  - 播放目录: {directory}")

            return True

        except Exception as e:
            log.error(f"写入播放列表失败: {e}")
            return False

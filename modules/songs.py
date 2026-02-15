"""
歌曲搜索与队列管理
"""

import os
import glob
import threading
from typing import Optional


class SongManager:
    """歌曲库索引 + 队列管理"""

    EXTENSIONS = ("*.mp4", "*.mp3", "*.flv", "*.mkv", "*.wav")

    def __init__(self, song_dir: str, data_dir: str):
        self.song_dir = song_dir
        self.data_dir = data_dir
        self._index: list[tuple[str, str]] = []  # [(name, filepath), ...]
        self._queue: list[str] = []  # [filepath, ...]
        self._now_playing: str = "等待播放..."
        self._lock = threading.Lock()
        self.build_index()

    def build_index(self):
        """扫描歌曲目录, 构建索引"""
        index = []
        for ext in self.EXTENSIONS:
            for f in glob.glob(os.path.join(self.song_dir, ext)):
                name = os.path.splitext(os.path.basename(f))[0]
                index.append((name, f))
        with self._lock:
            self._index = sorted(index, key=lambda x: x[0])

    def search(self, keyword: str) -> Optional[tuple[str, str]]:
        """模糊搜索歌曲, 返回 (歌名, 文件路径) 或 None"""
        keyword_lower = keyword.lower()
        with self._lock:
            for name, path in self._index:
                if keyword_lower in name.lower():
                    return name, path
        return None

    def list_songs(self, limit: int = 0) -> list[str]:
        """返回所有歌曲名列表"""
        with self._lock:
            names = [name for name, _ in self._index]
        return names[:limit] if limit > 0 else names

    @property
    def total(self) -> int:
        with self._lock:
            return len(self._index)

    # --- 队列管理 ---

    def queue_add(self, filepath: str, name: str):
        with self._lock:
            self._queue.append((name, filepath))

    def queue_pop(self) -> Optional[tuple[str, str]]:
        with self._lock:
            return self._queue.pop(0) if self._queue else None

    def queue_list(self) -> list[str]:
        """返回队列中的歌名列表"""
        with self._lock:
            return [name for name, _ in self._queue]

    def queue_clear(self):
        with self._lock:
            self._queue.clear()

    @property
    def queue_count(self) -> int:
        with self._lock:
            return len(self._queue)

    # --- 当前播放 ---

    @property
    def now_playing(self) -> str:
        with self._lock:
            return self._now_playing

    @now_playing.setter
    def now_playing(self, value: str):
        with self._lock:
            self._now_playing = value
        # 同时写入文件, 供 OBS 底部字幕等使用
        try:
            np_file = os.path.join(self.data_dir, "now_playing.txt")
            with open(np_file, "w", encoding="utf-8") as f:
                f.write(value)
        except OSError:
            pass

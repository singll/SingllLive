"""
回放文件管理器 - 管理录播文件索引和点播队列

文件名格式: YYYYMMDDNN.ext (例如 2026013101.mp4)
  YYYYMMDD = 日期
  NN = 场次编号 (01-99)

支持的格式: .mp4, .mkv, .avi, .flv
"""

import os
import re
import threading
import logging
from typing import Optional

log = logging.getLogger("replay")

# 文件名匹配: 10位数字 + 视频扩展名
_REPLAY_PATTERN = re.compile(r"^(\d{10})\.(mp4|mkv|avi|flv)$", re.IGNORECASE)

# 支持的扩展名
REPLAY_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.flv'}


class ReplayManager:
    """录播文件索引 + 点播队列管理"""

    def __init__(self, replay_dir: str, data_dir: str):
        self.replay_dir = replay_dir
        self.data_dir = data_dir
        self._index: dict[str, str] = {}  # {code: filepath}
        self._queue: list[tuple[str, str]] = []  # [(code, filepath), ...]
        self._now_playing: str = "等待播放..."
        self._lock = threading.Lock()
        self.build_index()

    def build_index(self):
        """扫描录播目录，构建日期编号索引"""
        index = {}
        if not self.replay_dir or not os.path.isdir(self.replay_dir):
            log.warning(f"录播目录不存在: {self.replay_dir}")
            with self._lock:
                self._index = index
            return

        try:
            for filename in os.listdir(self.replay_dir):
                match = _REPLAY_PATTERN.match(filename)
                if match:
                    code = match.group(1)
                    filepath = os.path.join(self.replay_dir, filename)
                    index[code] = filepath
        except Exception as e:
            log.error(f"扫描录播目录失败: {e}")

        with self._lock:
            self._index = index

        log.info(f"录播索引: {len(index)} 个文件 (来自: {self.replay_dir})")

    def search(self, code: str) -> Optional[tuple[str, str]]:
        """按编号查找录播文件

        Args:
            code: 10位日期编号 (如 "2026013101")

        Returns:
            (code, filepath) 或 None
        """
        with self._lock:
            filepath = self._index.get(code)
            if filepath:
                return code, filepath
        return None

    def get_all_files(self) -> list[str]:
        """返回按日期编号排序的全部文件路径列表"""
        with self._lock:
            sorted_codes = sorted(self._index.keys())
            return [self._index[code] for code in sorted_codes]

    @property
    def total(self) -> int:
        with self._lock:
            return len(self._index)

    # --- 点播队列 ---

    def queue_add(self, code: str, filepath: str):
        """添加到点播队列"""
        with self._lock:
            self._queue.append((code, filepath))

    def queue_pop(self) -> Optional[tuple[str, str]]:
        """弹出队列头部"""
        with self._lock:
            return self._queue.pop(0) if self._queue else None

    def queue_list(self) -> list[str]:
        """返回队列中的编号列表"""
        with self._lock:
            return [code for code, _ in self._queue]

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

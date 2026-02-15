"""
VLC 播放器控制 - HTTP 接口 + 看门狗 + 歌名同步
"""

import asyncio
import logging
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from typing import Optional

import aiohttp
from aiohttp import hdrs

from .songs import SongManager

log = logging.getLogger("vlc")


class VLCController:
    """通过 HTTP 接口控制 VLC, 附带看门狗和歌名同步"""

    def __init__(self, vlc_path: str, http_port: int, http_password: str,
                 song_dir: str, song_manager: SongManager,
                 playback_dir: Optional[str] = None):
        self.vlc_path = vlc_path
        self.http_port = http_port
        self.http_password = http_password
        self.song_dir = song_dir  # 默认轮播目录
        self.playback_dir = playback_dir or song_dir  # 轮播目录（明确指定）
        self.songs = song_manager
        self._base_url = f"http://127.0.0.1:{http_port}"
        self._auth = aiohttp.BasicAuth("", http_password)
        self._process: Optional[subprocess.Popen] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._current_playlist_mode: Optional[str] = None  # 跟踪当前播放列表模式

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            # 创建 connector，禁用 brotli 支持以避免 Python 3.14+ 兼容性问题
            # 问题: aiohttp + brotli 版本不兼容导致 TypeError: process() takes exactly 1 argument
            connector = aiohttp.TCPConnector(use_dns_cache=True)

            # 创建会话并禁用 Accept-Encoding header，防止服务器返回 brotli 压缩内容
            headers = {hdrs.ACCEPT_ENCODING: "gzip, deflate"}

            self._session = aiohttp.ClientSession(
                connector=connector,
                auth=self._auth,
                timeout=aiohttp.ClientTimeout(total=5),
                headers=headers
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    # --- VLC 进程管理 ---

    def start_vlc(self):
        """启动 VLC 并开启 HTTP 接口"""
        if sys.platform != "win32":
            log.warning("VLC 自动启动仅支持 Windows, 请手动启动 VLC")
            return

        cmd = [
            self.vlc_path, self.song_dir,
            "--loop", "--random",
            "--one-instance",
            "--no-video-title-show",
            "--extraintf=http",
            f"--http-host=127.0.0.1",
            f"--http-port={self.http_port}",
            f"--http-password={self.http_password}",
        ]
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "DETACHED_PROCESS", 0),
            )
            log.info(f"VLC 已启动 (PID: {self._process.pid})")
        except FileNotFoundError:
            log.error(f"找不到 VLC: {self.vlc_path}")
        except Exception as e:
            log.error(f"VLC 启动失败: {e}")

    async def is_alive(self) -> bool:
        """通过 HTTP 心跳检测 VLC 是否存活"""
        try:
            session = await self._get_session()
            url = f"{self._base_url}/requests/status.xml"
            async with session.get(url) as resp:
                return resp.status == 200
        except Exception:
            return False

    # --- HTTP API 命令 ---

    async def _request(self, command: str, extra: str = "") -> Optional[str]:
        """发送 VLC HTTP API 请求, 返回响应文本"""
        url = f"{self._base_url}/requests/status.xml?command={command}{extra}"
        try:
            session = await self._get_session()
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.text()
        except Exception as e:
            log.debug(f"VLC 请求失败 ({command}): {e}")
        return None

    async def play(self, filepath: str) -> bool:
        """播放指定文件"""
        encoded = filepath.replace("\\", "/")
        result = await self._request("in_play", f"&input={encoded}")
        return result is not None

    async def enqueue(self, filepath: str) -> bool:
        """加入播放队列"""
        encoded = filepath.replace("\\", "/")
        result = await self._request("in_enqueue", f"&input={encoded}")
        return result is not None

    async def next_song(self) -> bool:
        result = await self._request("pl_next")
        return result is not None

    async def pause(self) -> bool:
        result = await self._request("pl_pause")
        return result is not None

    async def set_playlist_directory(self, mode: str, directory: str) -> bool:
        """动态切换 VLC 播放列表目录 (Plan A+ 特性)

        Args:
            mode: 'playback' (轮播) 或 'song_request' (点歌)
            directory: 要播放的目录路径

        Returns:
            成功返回 True
        """
        if self._current_playlist_mode == mode and mode in ['playback', 'song_request']:
            log.debug(f"播放列表已是 {mode} 模式，跳过切换")
            return True

        try:
            # 清空当前播放列表
            await self._request("pl_empty")
            await asyncio.sleep(0.5)

            # 添加新目录到播放列表
            encoded_dir = directory.replace("\\", "/")
            result = await self._request("in_enqueue", f"&input={encoded_dir}")

            if result:
                self._current_playlist_mode = mode
                log.info(f"VLC 播放列表已切换到 {mode} 模式: {directory}")
                return True
            else:
                log.warning(f"VLC 切换播放列表失败: {mode} -> {directory}")
                return False

        except Exception as e:
            log.error(f"VLC 切换播放列表异常: {e}")
            return False

    async def get_current_song(self) -> Optional[str]:
        """从 VLC status.xml 解析当前播放文件名"""
        try:
            session = await self._get_session()
            url = f"{self._base_url}/requests/status.xml"
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                text = await resp.text()
        except Exception:
            return None

        try:
            root = ET.fromstring(text)
            # 查找 <information><category name="meta"><info name="filename">
            for cat in root.iter("category"):
                if cat.get("name") == "meta":
                    for info in cat.iter("info"):
                        if info.get("name") == "filename":
                            filename = info.text or ""
                            return os.path.splitext(filename)[0]
        except ET.ParseError:
            pass
        return None

    # --- 异步服务循环 ---

    async def sync_loop(self, interval: float = 5.0):
        """每隔 interval 秒从 VLC 获取当前歌名并更新 SongManager"""
        log.info(f"歌名同步服务启动 (间隔 {interval}s)")
        while True:
            try:
                song = await self.get_current_song()
                if song:
                    self.songs.now_playing = song
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.debug(f"歌名同步异常: {e}")
            await asyncio.sleep(interval)

    async def watchdog_loop(self, interval: float = 30.0):
        """每隔 interval 秒检测 VLC, 崩溃则自动重启"""
        log.info(f"VLC 看门狗启动 (间隔 {interval}s)")
        # 首次等待, 给 VLC 启动时间
        await asyncio.sleep(10)
        while True:
            try:
                alive = await self.is_alive()
                if not alive:
                    log.warning("VLC 无响应, 正在重启...")
                    self.start_vlc()
                    await asyncio.sleep(5)  # 等待 VLC 启动
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.debug(f"看门狗异常: {e}")
            await asyncio.sleep(interval)

"""
OBS WebSocket v5 控制器
通过 obsws-python 直接控制 OBS Studio，替代 Lua 脚本 + 文件监听方案

功能:
  - VLC 源播放列表管理 (直接设置 playlist 数组)
  - 源可见性控制 (显示/隐藏)
  - 媒体播放控制 (play/pause/next/stop)
  - 图像源刷新 (面板 PNG)
  - 自动重连机制

依赖: pip install obsws-python>=1.7.0
前提: OBS Studio 28+ 内置 WebSocket v5 服务器
     OBS → 工具 → WebSocket服务器设置 → 启用
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

log = logging.getLogger("obs")

# OBS WebSocket 媒体控制动作常量
MEDIA_PLAY = "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY"
MEDIA_PAUSE = "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PAUSE"
MEDIA_STOP = "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_STOP"
MEDIA_RESTART = "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
MEDIA_NEXT = "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_NEXT"
MEDIA_PREVIOUS = "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PREVIOUS"


class OBSController:
    """OBS WebSocket v5 控制器

    所有 OBS 操作通过 WebSocket 完成，消除了对 Lua 脚本和文件监听的依赖。
    obsws-python 是同步库，所有调用通过 ThreadPoolExecutor 包装为异步。
    """

    def __init__(self, host: str = "localhost", port: int = 4455,
                 password: str = "", scene_name: str = "AScreen",
                 vlc_source_name: str = "vlc_player",
                 broadcast_source_name: str = "broadcast_screen",
                 panel_source_name: str = "B区-终端面板"):
        self.host = host
        self.port = port
        self.password = password
        self.scene_name = scene_name
        self.vlc_source_name = vlc_source_name
        self.broadcast_source_name = broadcast_source_name
        self.panel_source_name = panel_source_name

        self._client = None
        self._connected = False
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="obs")
        self._reconnect_interval = 5
        self._reconnecting = False

    @property
    def connected(self) -> bool:
        return self._connected

    async def connect(self) -> bool:
        """连接到 OBS WebSocket 服务器"""
        try:
            import obsws_python as obsws
        except ImportError:
            log.warning("obsws-python 未安装，OBS 控制不可用")
            log.warning("请运行: pip install obsws-python")
            return False

        try:
            loop = asyncio.get_event_loop()
            self._client = await loop.run_in_executor(
                self._executor,
                lambda: obsws.ReqClient(
                    host=self.host, port=self.port,
                    password=self.password, timeout=5
                )
            )
            self._connected = True
            log.info(f"OBS WebSocket 已连接: {self.host}:{self.port}")
            return True
        except Exception as e:
            log.warning(f"OBS WebSocket 连接失败: {e}")
            log.warning("请确保 OBS 已启动并开启 WebSocket 服务器")
            self._connected = False
            return False

    async def disconnect(self):
        """断开连接"""
        if self._client:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self._executor, self._client.disconnect)
            except Exception:
                pass
            self._client = None
            self._connected = False
            log.info("OBS WebSocket 已断开")

    async def _run_sync(self, func):
        """在线程池中运行同步 OBS 调用，失败时触发重连"""
        if not self._connected or not self._client:
            return None
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self._executor, func)
        except Exception as e:
            error_msg = str(e).lower()
            if "closed" in error_msg or "connection" in error_msg or "eof" in error_msg:
                self._connected = False
                log.warning(f"OBS 连接断开: {e}")
                if not self._reconnecting:
                    asyncio.create_task(self._auto_reconnect())
            else:
                log.error(f"OBS 操作失败: {e}")
            return None

    async def _auto_reconnect(self):
        """后台自动重连"""
        if self._reconnecting:
            return
        self._reconnecting = True
        log.info("OBS 自动重连已启动...")
        try:
            while not self._connected:
                await asyncio.sleep(self._reconnect_interval)
                if await self.connect():
                    log.info("OBS 重连成功")
                    break
        finally:
            self._reconnecting = False

    # --- VLC 源播放列表管理 ---

    async def set_vlc_playlist(self, files: list, source_name: Optional[str] = None) -> bool:
        """设置 VLC 源的播放列表

        Args:
            files: 文件路径列表 (本地绝对路径)
            source_name: VLC 源名称，默认使用配置的名称
        """
        source = source_name or self.vlc_source_name
        playlist = [{"value": f, "hidden": False, "selected": False} for f in files]

        def _do():
            self._client.set_input_settings(source, {
                "playlist": playlist
            }, overlay=True)

        result = await self._run_sync(_do)
        if result is not None or self._connected:
            log.debug(f"VLC 播放列表已更新: {len(files)} 个文件 → {source}")
            return True
        return False

    async def media_action(self, action: str, source_name: Optional[str] = None) -> bool:
        """触发 VLC 源的媒体控制动作

        Args:
            action: 媒体动作常量 (MEDIA_PLAY, MEDIA_NEXT 等)
            source_name: 源名称
        """
        source = source_name or self.vlc_source_name

        def _do():
            self._client.trigger_media_input_action(source, action)

        result = await self._run_sync(_do)
        if result is not None or self._connected:
            log.debug(f"VLC 媒体控制: {action} → {source}")
            return True
        return False

    # --- 源可见性控制 ---

    async def set_source_visible(self, source_name: str, visible: bool,
                                  scene_name: Optional[str] = None) -> bool:
        """设置场景中源的可见性

        Args:
            source_name: 源名称
            visible: True=显示, False=隐藏
            scene_name: 场景名称，默认 AScreen
        """
        scene = scene_name or self.scene_name

        def _do():
            item = self._client.get_scene_item_id(scene, source_name)
            self._client.set_scene_item_enabled(scene, item.scene_item_id, visible)

        result = await self._run_sync(_do)
        if result is not None or self._connected:
            status = "显示" if visible else "隐藏"
            log.debug(f"源 {source_name} → {status} (场景: {scene})")
            return True
        return False

    async def apply_mode_sources(self, mode_key: str) -> bool:
        """根据模式设置 AScreen 内源的可见性

        Args:
            mode_key: 模式键 ('playback', 'broadcast', 'pk', 'song_request', 'other')
        """
        configs = {
            "playback": {self.vlc_source_name: True, self.broadcast_source_name: False},
            "song_request": {self.vlc_source_name: True, self.broadcast_source_name: False},
            "broadcast": {self.vlc_source_name: False, self.broadcast_source_name: True},
            "pk": {self.vlc_source_name: False, self.broadcast_source_name: True},
            "other": {self.vlc_source_name: False, self.broadcast_source_name: False},
        }

        config = configs.get(mode_key)
        if not config:
            log.warning(f"未知模式: {mode_key}")
            return False

        log.info(f"OBS 源切换: 模式={mode_key}")
        for source, visible in config.items():
            await self.set_source_visible(source, visible)
        return True

    # --- 图像源刷新 ---

    async def refresh_image_source(self, source_name: Optional[str] = None) -> bool:
        """强制刷新图像源 (重新加载文件)"""
        source = source_name or self.panel_source_name

        def _do():
            resp = self._client.get_input_settings(source)
            self._client.set_input_settings(source, resp.input_settings, overlay=True)

        result = await self._run_sync(_do)
        return result is not None or self._connected

    # --- 信息查询 ---

    async def get_scene_list(self) -> list:
        """获取所有场景名称列表"""
        def _do():
            resp = self._client.get_scene_list()
            return [s["sceneName"] for s in resp.scenes]

        result = await self._run_sync(_do)
        return result if result else []

    async def get_version(self) -> Optional[str]:
        """获取 OBS 版本信息"""
        def _do():
            resp = self._client.get_version()
            return f"OBS {resp.obs_version} / WebSocket {resp.obs_web_socket_version}"

        return await self._run_sync(_do)

"""
OBS WebSocket 场景控制模块
用途: 通过 OBS WebSocket API 实现模式切换时的场景自动切换

依赖: pip install obs-websocket-py
      或 pip install obswebsocket

工作流程:
1. 连接到 OBS WebSocket 服务器
2. 监听模式变化回调
3. 根据新模式自动切换对应的 OBS 场景
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from enum import Enum

log = logging.getLogger("obs_control")


class ObsMode(Enum):
    """OBS 模式与场景的映射"""
    BROADCAST = "Scene_Broadcast"      # 直播模式
    PK = "Scene_PK"                    # PK模式
    SONG_REQUEST = "Scene_SongRequest" # 点歌模式
    PLAYBACK = "Scene_Playback"        # 轮播模式
    OTHER = "Scene_Other"              # 其他模式


class ObsController:
    """OBS WebSocket 控制器"""

    def __init__(self, host: str = "localhost", port: int = 4455, password: str = ""):
        """
        初始化 OBS 控制器

        Args:
            host: OBS WebSocket 服务器地址
            port: OBS WebSocket 服务器端口
            password: OBS WebSocket 密码（如果有的话）
        """
        self.host = host
        self.port = port
        self.password = password
        self.connected = False
        self.ws = None
        self.current_scene = None

        # 延迟导入，允许在没有 obswebsocket 时仍能导入此模块
        try:
            from obswebsocket import obsws
            self.obsws = obsws
            self.available = True
        except ImportError:
            log.warning("obswebsocket 未安装，OBS 控制功能不可用")
            log.warning("请运行: pip install obs-websocket-py 或 pip install obswebsocket")
            self.available = False

    async def connect(self) -> bool:
        """
        连接到 OBS WebSocket 服务器

        Returns:
            是否连接成功
        """
        if not self.available:
            log.warning("OBS WebSocket 不可用，跳过连接")
            return False

        try:
            # 同步连接（在线程池中运行以避免阻塞）
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._connect_sync
            )
            self.connected = True
            log.info(f"OBS WebSocket 已连接: {self.host}:{self.port}")
            return True
        except Exception as e:
            log.error(f"OBS WebSocket 连接失败: {e}")
            self.connected = False
            return False

    def _connect_sync(self):
        """同步连接（内部使用）"""
        self.ws = self.obsws(self.host, self.port, self.password)
        self.ws.connect()

    async def disconnect(self):
        """断开连接"""
        if self.ws:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.ws.disconnect)
                self.connected = False
                log.info("OBS WebSocket 已断开连接")
            except Exception as e:
                log.error(f"OBS WebSocket 断开失败: {e}")

    async def switch_scene(self, scene_name: str) -> bool:
        """
        切换到指定场景

        Args:
            scene_name: 场景名称

        Returns:
            是否切换成功
        """
        if not self.connected or not self.ws:
            log.warning(f"OBS 未连接，无法切换场景: {scene_name}")
            return False

        try:
            # 获取可用场景列表（验证场景是否存在）
            loop = asyncio.get_event_loop()

            # 切换场景
            def _switch():
                self.ws.call("SetCurrentProgramScene", {"sceneName": scene_name})

            await loop.run_in_executor(None, _switch)

            self.current_scene = scene_name
            log.info(f"OBS 场景已切换: {scene_name}")
            return True

        except Exception as e:
            log.error(f"OBS 场景切换失败 ({scene_name}): {e}")
            return False

    async def get_scene_list(self) -> list:
        """
        获取所有可用场景列表

        Returns:
            场景名称列表
        """
        if not self.connected or not self.ws:
            log.warning("OBS 未连接，无法获取场景列表")
            return []

        try:
            loop = asyncio.get_event_loop()

            def _get_scenes():
                response = self.ws.call("GetSceneList")
                return [s["sceneName"] for s in response.getScenes()]

            scenes = await loop.run_in_executor(None, _get_scenes)
            return scenes

        except Exception as e:
            log.error(f"获取 OBS 场景列表失败: {e}")
            return []

    async def validate_scenes(self) -> bool:
        """
        验证所有必需的场景是否存在

        Returns:
            所有必需的场景是否都存在
        """
        scenes = await self.get_scene_list()
        required_scenes = [mode.value for mode in ObsMode]

        missing = [s for s in required_scenes if s not in scenes]

        if missing:
            log.warning(f"缺少以下 OBS 场景: {missing}")
            log.info(f"当前可用场景: {scenes}")
            return False

        log.info(f"所有必需场景都存在: {required_scenes}")
        return True


class ObsModeController:
    """OBS 模式控制 - 与 ModeManager 集成"""

    def __init__(self, obs_controller: Optional[ObsController] = None):
        """
        初始化 OBS 模式控制器

        Args:
            obs_controller: OBS 控制器实例
        """
        self.obs = obs_controller or ObsController()
        self.mode_to_scene = {
            "BROADCAST": ObsMode.BROADCAST.value,
            "PK": ObsMode.PK.value,
            "SONG_REQUEST": ObsMode.SONG_REQUEST.value,
            "PLAYBACK": ObsMode.PLAYBACK.value,
            "OTHER": ObsMode.OTHER.value,
        }

    async def on_mode_changed(self, old_mode, new_mode, reason: str = ""):
        """
        模式变化回调 - 用于注册到 ModeManager

        Args:
            old_mode: 旧模式
            new_mode: 新模式
            reason: 变化原因
        """
        mode_name = new_mode.name if hasattr(new_mode, 'name') else str(new_mode)
        scene_name = self.mode_to_scene.get(mode_name)

        if scene_name:
            log.info(f"模式已变更: {old_mode} → {new_mode}, 准备切换场景...")
            success = await self.obs.switch_scene(scene_name)
            if success:
                log.info(f"场景切换成功: {scene_name}")
            else:
                log.error(f"场景切换失败: {scene_name}")
        else:
            log.warning(f"未找到模式对应的场景: {mode_name}")


# 使用示例
if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)

    async def demo():
        # 创建 OBS 控制器
        obs = ObsController("localhost", 4455, "your_password")

        # 连接到 OBS
        if await obs.connect():
            # 验证场景
            await obs.validate_scenes()

            # 获取场景列表
            scenes = await obs.get_scene_list()
            print(f"可用场景: {scenes}")

            # 切换场景
            await obs.switch_scene("Scene_Playback")

            # 断开连接
            await obs.disconnect()
        else:
            print("连接失败")

    asyncio.run(demo())

"""
模式管理系统 - 支持多种播放模式

支持的模式：
1. BROADCAST - 直播模式
2. PK - PK对战模式
3. PLAYBACK - 轮播模式 (循环播放直播画面/视频)
4. SONG_REQUEST - 点歌模式
5. OTHER - 其他模式

所有模式之间可以自由切换，无优先级限制。
"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio
import logging

log = logging.getLogger("mode")


class Mode(Enum):
    """播放模式枚举，所有模式可自由切换"""
    BROADCAST = ("直播模式", "broadcast")
    PK = ("PK模式", "pk")
    PLAYBACK = ("轮播模式", "playback")
    SONG_REQUEST = ("点歌模式", "song_request")
    OTHER = ("其他模式", "other")

    def __init__(self, chinese_name: str, key: str):
        self.chinese_name = chinese_name
        self.key = key

    def __str__(self):
        return self.chinese_name

    def __repr__(self):
        return f"Mode.{self.name}"


class ModeManager:
    """模式管理器 - 管理当前播放模式和模式切换逻辑"""

    def __init__(self):
        self.current_mode = Mode.PLAYBACK
        self.previous_mode = Mode.OTHER
        self.mode_changed_at = datetime.now()

        self.mode_state: Dict[Mode, Dict[str, Any]] = {
            Mode.BROADCAST: {
                "is_active": False,
                "viewer_count": 0,
                "uptime_seconds": 0,
            },
            Mode.PK: {
                "is_active": False,
                "opponent_name": "",
                "our_score": 0,
                "opponent_score": 0,
            },
            Mode.SONG_REQUEST: {
                "queue_count": 0,
                "requester": "",
            },
            Mode.PLAYBACK: {
                "current_song": "",
                "next_song": "",
            },
            Mode.OTHER: {
                "message": "空闲状态",
            },
        }

        self._mode_lock = asyncio.Lock()
        self._mode_change_callbacks = []

    async def set_mode(self, mode: Mode, reason: str = "") -> bool:
        """设置当前模式，所有模式之间可自由切换

        Args:
            mode: 要切换到的模式
            reason: 切换原因

        Returns:
            是否成功切换
        """
        async with self._mode_lock:
            if mode == self.current_mode:
                return True

            self.previous_mode = self.current_mode
            self.current_mode = mode
            self.mode_changed_at = datetime.now()

            log.info(f"模式切换: {self.previous_mode} → {mode} (原因: {reason})")
            await self._call_mode_change_callbacks(self.previous_mode, mode, reason)
            return True

    async def update_mode_state(self, mode: Mode, **kwargs) -> None:
        """更新指定模式的状态信息"""
        async with self._mode_lock:
            if mode in self.mode_state:
                self.mode_state[mode].update(kwargs)

    def get_mode_state(self, mode: Optional[Mode] = None) -> Dict[str, Any]:
        """获取模式状态"""
        if mode is None:
            mode = self.current_mode
        return self.mode_state.get(mode, {})

    async def auto_switch_for_song_request(self, queue_count: int) -> None:
        """有点歌时自动切换到点歌模式，队列清空时回到轮播"""
        if queue_count > 0:
            await self.set_mode(Mode.SONG_REQUEST, f"队列有 {queue_count} 首歌")
            await self.update_mode_state(Mode.SONG_REQUEST, queue_count=queue_count)
        elif self.current_mode == Mode.SONG_REQUEST:
            await self.set_mode(Mode.PLAYBACK, "点歌队列已清空")

    async def auto_switch_for_pk(self, is_pk_active: bool, opponent_name: str = "") -> None:
        """PK开始时切换到PK模式，结束时回到轮播"""
        if is_pk_active:
            await self.set_mode(Mode.PK, f"PK 对手: {opponent_name}")
            await self.update_mode_state(Mode.PK, is_active=True, opponent_name=opponent_name)
        else:
            if self.current_mode == Mode.PK:
                await self.set_mode(Mode.PLAYBACK, "PK已结束")
            await self.update_mode_state(Mode.PK, is_active=False)

    async def auto_switch_for_broadcast(self, is_live: bool, viewer_count: int = 0, uptime_seconds: int = 0) -> None:
        """开播时切换到直播模式，下播时回到轮播"""
        if is_live:
            await self.set_mode(Mode.BROADCAST, f"直播中，在线人数: {viewer_count}")
            await self.update_mode_state(Mode.BROADCAST, is_active=True,
                                          viewer_count=viewer_count, uptime_seconds=uptime_seconds)
        else:
            if self.current_mode == Mode.BROADCAST:
                await self.set_mode(Mode.PLAYBACK, "直播已结束")
            await self.update_mode_state(Mode.BROADCAST, is_active=False)

    def get_mode_info(self) -> Dict[str, Any]:
        """获取当前模式的完整信息"""
        return {
            "mode": self.current_mode.name,
            "chinese_name": self.current_mode.chinese_name,
            "changed_at": self.mode_changed_at.isoformat(),
            "state": self.get_mode_state(),
        }

    def register_mode_change_callback(self, callback):
        """注册模式变更回调"""
        self._mode_change_callbacks.append(callback)

    async def _call_mode_change_callbacks(self, old_mode: Mode, new_mode: Mode, reason: str) -> None:
        """调用所有已注册的模式变更回调"""
        for callback in self._mode_change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(old_mode, new_mode, reason)
                else:
                    callback(old_mode, new_mode, reason)
            except Exception as e:
                log.error(f"模式回调执行出错: {e}")

    def get_all_modes(self) -> list:
        """获取所有可用的模式"""
        return list(Mode)

    def get_mode_by_key(self, key: str) -> Optional[Mode]:
        """通过键获取模式"""
        for mode in Mode:
            if mode.key == key:
                return mode
        return None

    def get_mode_by_command(self, command: str) -> Optional[Mode]:
        """通过弹幕命令获取模式

        支持命令: "直播模式", "PK模式", "点歌模式", "轮播模式", "其他模式"
        """
        command = command.strip()
        for mode in Mode:
            if command == mode.chinese_name:
                return mode
        return None

"""
模式管理系统 - 支持多种播放模式和优先级控制

支持的模式：
1. BROADCAST (优先级1) - 直播模式，最高优先级
2. PK (优先级2) - PK对战模式
3. PLAYBACK (优先级3) - 轮播模式
4. SONG_REQUEST (优先级3) - 点歌模式
5. OTHER (优先级3) - 其他模式，最低优先级

优先级规则：
- 数字越小优先级越高
- 高优先级模式会阻止低优先级模式切入
- 同优先级模式之间可以自由切换 (轮播↔点歌↔其他)
- 高优先级模式可以打断任何低优先级模式
"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio
import logging

log = logging.getLogger("mode")


class Mode(Enum):
    """播放模式枚举

    优先级规则（数字越小优先级越高）：
    - 直播模式 (1): 最高优先级，打断所有其他模式
    - PK模式 (2): 次高优先级，打断轮播/点歌/其他
    - 轮播模式 (3): 普通优先级，与点歌/其他自由切换
    - 点歌模式 (3): 普通优先级，与轮播/其他自由切换
    - 其他模式 (3): 普通优先级，与轮播/点歌自由切换
    """
    BROADCAST = (1, "直播模式", "broadcast")
    PK = (2, "PK模式", "pk")
    PLAYBACK = (3, "轮播模式", "playback")
    SONG_REQUEST = (3, "点歌模式", "song_request")
    OTHER = (3, "其他模式", "other")

    def __init__(self, priority: int, chinese_name: str, key: str):
        self.priority = priority
        self.chinese_name = chinese_name
        self.key = key

    def __str__(self):
        return self.chinese_name

    def __repr__(self):
        return f"Mode.{self.name}(priority={self.priority})"


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
        """设置当前模式

        Args:
            mode: 要切换到的模式
            reason: 切换原因

        Returns:
            是否成功切换
        """
        async with self._mode_lock:
            if self._is_blocked(mode):
                log.warning(f"模式 {mode} 被阻止 (当前: {self.current_mode})")
                return False

            if mode == self.current_mode:
                return True

            self.previous_mode = self.current_mode
            self.current_mode = mode
            self.mode_changed_at = datetime.now()

            log.info(f"模式切换: {self.previous_mode} → {mode} (原因: {reason})")
            await self._call_mode_change_callbacks(self.previous_mode, mode, reason)
            return True

    def _is_blocked(self, mode: Mode) -> bool:
        """检查切换是否被阻止

        规则:
        - 同优先级或更高优先级 → 允许切换
        - 低优先级想切入高优先级正在运行 → 阻止

        Args:
            mode: 要切换到的目标模式

        Returns:
            True = 被阻止
        """
        # 目标模式优先级 <= 当前模式优先级 (数字小=优先级高) → 允许
        if mode.priority <= self.current_mode.priority:
            return False
        # 目标模式优先级更低 → 被阻止
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
        """自动切换到点歌模式"""
        if queue_count > 0:
            success = await self.set_mode(Mode.SONG_REQUEST, f"队列有 {queue_count} 首歌")
            await self.update_mode_state(Mode.SONG_REQUEST, queue_count=queue_count)
        else:
            if self.current_mode == Mode.SONG_REQUEST:
                await self.set_mode(Mode.PLAYBACK, "点歌队列已清空")

    async def auto_switch_for_pk(self, is_pk_active: bool, opponent_name: str = "") -> None:
        """自动切换到PK模式"""
        if is_pk_active:
            await self.set_mode(Mode.PK, f"PK 对手: {opponent_name}")
            await self.update_mode_state(Mode.PK, is_active=True, opponent_name=opponent_name)
        else:
            if self.current_mode == Mode.PK:
                await self.set_mode(Mode.PLAYBACK, "PK已结束")
            await self.update_mode_state(Mode.PK, is_active=False)

    async def auto_switch_for_broadcast(self, is_live: bool, viewer_count: int = 0, uptime_seconds: int = 0) -> None:
        """自动切换到直播模式"""
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
            "priority": self.current_mode.priority,
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

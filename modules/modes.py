"""
模式管理系统 - 支持多种播放模式和优先级控制

支持的模式：
1. BROADCAST (优先级1) - 直播模式，最高优先级
2. PK (优先级2) - PK对战模式
3. SONG_REQUEST (优先级2) - 点歌模式
4. PLAYBACK (优先级3) - 轮播模式
5. OTHER (优先级4) - 其他模式，最低优先级

优先级规则：
- 高优先级模式会阻止低优先级模式
- 自动检测高优先级状态并切换
- 支持手动命令切换模式
"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio


class Mode(Enum):
    """播放模式枚举，包含优先级和中文名称

    优先级规则（数字越小优先级越高）：
    - 直播模式 (1): 最高优先级，会打断所有其他模式
    - PK模式 (2): 次高优先级
    - 轮播模式 (2): 中等优先级，可被直播/PK打断，可与点歌相互打断
    - 点歌模式 (2): 中等优先级，可被直播/PK打断，可与轮播相互打断
    - 其他模式 (3): 最低优先级，会被所有其他模式打断
    """
    BROADCAST = (1, "直播模式", "broadcast")
    PK = (2, "PK模式", "pk")
    PLAYBACK = (2, "轮播模式", "playback")
    SONG_REQUEST = (2, "点歌模式", "song_request")
    OTHER = (3, "其他模式", "other")

    def __init__(self, priority: int, name: str, key: str):
        self.priority = priority
        self.chinese_name = name
        self.key = key

    def __str__(self):
        return self.chinese_name

    def __repr__(self):
        return f"Mode.{self.name}(priority={self.priority})"


class ModeManager:
    """模式管理器 - 管理当前播放模式和模式切换逻辑"""

    def __init__(self):
        """初始化模式管理器"""
        self.current_mode = Mode.PLAYBACK  # 默认轮播模式
        self.previous_mode = Mode.OTHER
        self.mode_changed_at = datetime.now()

        # 模式状态信息
        self.mode_state: Dict[str, Any] = {
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
                "is_blocked": False,  # 是否被高优先级模式阻止
            },
            Mode.PLAYBACK: {
                "current_song": "",
                "next_song": "",
            },
            Mode.OTHER: {
                "message": "空闲状态",
            },
        }

        # 模式锁，防止并发修改
        self._mode_lock = asyncio.Lock()

        # 模式变更回调
        self._mode_change_callbacks = []

    async def set_mode(self, mode: Mode, reason: str = "") -> bool:
        """
        设置当前模式

        Args:
            mode: 要切换到的模式
            reason: 切换原因（用于日志）

        Returns:
            是否成功切换（如果低优先级模式被高优先级阻止，返回False）
        """
        async with self._mode_lock:
            # 检查是否被高优先级模式阻止
            if self._is_blocked(mode):
                print(f"[ModeManager] 模式 {mode} 被高优先级模式阻止, 当前: {self.current_mode}")
                return False

            # 如果是同一模式，不切换
            if mode == self.current_mode:
                return True

            # 记录模式变更
            self.previous_mode = self.current_mode
            self.current_mode = mode
            self.mode_changed_at = datetime.now()

            print(f"[ModeManager] 模式切换: {self.previous_mode} → {mode} (原因: {reason})")

            # 触发回调
            await self._call_mode_change_callbacks(self.previous_mode, mode, reason)

            return True

    async def update_mode_state(self, mode: Mode, **kwargs) -> None:
        """
        更新指定模式的状态信息

        Args:
            mode: 要更新的模式
            **kwargs: 状态字段及其值
        """
        async with self._mode_lock:
            if mode in self.mode_state:
                self.mode_state[mode].update(kwargs)

    def get_mode_state(self, mode: Optional[Mode] = None) -> Dict[str, Any]:
        """
        获取模式状态

        Args:
            mode: 要获取的模式，None 表示当前模式

        Returns:
            模式状态字典
        """
        if mode is None:
            mode = self.current_mode
        return self.mode_state.get(mode, {})

    def _is_blocked(self, mode: Mode) -> bool:
        """
        检查一个模式是否被更高优先级的模式阻止

        Args:
            mode: 要检查的模式

        Returns:
            是否被阻止
        """
        if mode.priority >= self.current_mode.priority:
            return False
        return True

    async def auto_switch_for_song_request(self, queue_count: int) -> None:
        """
        自动切换到点歌模式（如果有队列且不被高优先级模式阻止）

        Args:
            queue_count: 队列中的歌曲数
        """
        if queue_count > 0:
            # 尝试切换到点歌模式
            success = await self.set_mode(Mode.SONG_REQUEST, f"队列有 {queue_count} 首歌")
            await self.update_mode_state(Mode.SONG_REQUEST, queue_count=queue_count, is_blocked=not success)
        else:
            # 如果队列为空，尝试回到轮播模式
            if self.current_mode == Mode.SONG_REQUEST:
                await self.set_mode(Mode.PLAYBACK, "点歌队列已清空")

    async def auto_switch_for_pk(self, is_pk_active: bool, opponent_name: str = "") -> None:
        """
        自动切换到PK模式

        Args:
            is_pk_active: PK 是否进行中
            opponent_name: 对手名称
        """
        if is_pk_active:
            await self.set_mode(Mode.PK, f"PK 对手: {opponent_name}")
            await self.update_mode_state(Mode.PK, is_active=True, opponent_name=opponent_name)
        else:
            if self.current_mode == Mode.PK:
                await self.set_mode(Mode.PLAYBACK, "PK已结束")
            await self.update_mode_state(Mode.PK, is_active=False)

    async def auto_switch_for_broadcast(self, is_live: bool, viewer_count: int = 0, uptime_seconds: int = 0) -> None:
        """
        自动切换到直播模式

        Args:
            is_live: 直播是否进行中
            viewer_count: 在线人数
            uptime_seconds: 直播已进行的秒数
        """
        if is_live:
            await self.set_mode(Mode.BROADCAST, f"直播中，在线人数: {viewer_count}")
            await self.update_mode_state(Mode.BROADCAST, is_active=True, viewer_count=viewer_count, uptime_seconds=uptime_seconds)
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
        """
        注册模式变更回调

        Args:
            callback: 异步回调函数，签名为 async def callback(old_mode: Mode, new_mode: Mode, reason: str)
        """
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
                print(f"[ModeManager] 回调执行出错: {e}")

    def get_all_modes(self) -> list:
        """获取所有可用的模式"""
        return list(Mode)

    def get_mode_by_key(self, key: str) -> Optional[Mode]:
        """通过键获取模式"""
        for mode in Mode:
            if mode.key == key:
                return mode
        return None

    def get_mode_by_name(self, name: str) -> Optional[Mode]:
        """通过中文名称获取模式"""
        for mode in Mode:
            if mode.chinese_name == name or name in mode.chinese_name:
                return mode
        return None

    def get_mode_by_command(self, command: str) -> Optional[Mode]:
        """
        通过弹幕命令获取模式

        支持的命令格式：
        - "直播模式"
        - "PK模式"
        - "点歌模式"
        - "轮播模式"
        - "其他模式"
        """
        command = command.strip()
        for mode in Mode:
            if command == mode.chinese_name:
                return mode
        return None

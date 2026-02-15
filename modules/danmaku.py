"""
B站直播弹幕机器人
基于 blivedm (接收弹幕) + bilibili-api-python (发送弹幕/API调用)
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Optional

import aiohttp
from aiohttp import hdrs
import blivedm
# 兼容不同版本的 blivedm
try:
    import blivedm.models.web as web_models
except (ImportError, AttributeError):
    # 如果上面的导入失败，使用备选方案
    try:
        from blivedm import models as web_models
    except ImportError:
        # 最后的备选：不使用类型提示
        web_models = None

from bilibili_api import live as bili_live, Credential, Danmaku

from .songs import SongManager
from .vlc_control import VLCController
from .modes import ModeManager, Mode

log = logging.getLogger("danmaku")

# 命令冷却时间 (秒)
COOLDOWNS = {
    "点歌": 5,
    "切歌": 10,
    "歌单": 30,
    "当前": 10,
    "PK": 60,
    "模式切换": 3,
    "查看模式": 2,
}


class DanmakuBot:
    """B站直播弹幕命令机器人"""

    def __init__(self, room_id: int, uid: int,
                 sessdata: str, bili_jct: str, buvid3: str,
                 vlc: VLCController, songs: SongManager,
                 mode_manager: ModeManager = None,
                 pk_target_room_id: int = 0):
        self.room_id = room_id
        self.uid = uid
        self.vlc = vlc
        self.songs = songs
        self.mode_manager = mode_manager
        self.pk_target_room_id = pk_target_room_id

        self._sessdata = sessdata
        self._bili_jct = bili_jct
        self._credential = Credential(
            sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3
        )
        self._last_cmd_time: dict[str, float] = {}

    def _check_cooldown(self, cmd: str) -> bool:
        now = datetime.now().timestamp()
        cd = COOLDOWNS.get(cmd, 5)
        if cmd in self._last_cmd_time and now - self._last_cmd_time[cmd] < cd:
            return False
        self._last_cmd_time[cmd] = now
        return True

    async def _send_reply(self, text: str):
        """发送弹幕到直播间"""
        try:
            room = bili_live.LiveRoom(self.room_id, credential=self._credential)
            await room.send_danmaku(Danmaku(text[:30]))
        except Exception as e:
            log.error(f"弹幕发送失败: {e}")

    async def _handle_danmaku(self, text: str, uid: int, uname: str):
        """处理弹幕命令"""

        # --- 点歌 ---
        match = re.match(r"^点歌\s+(.+)$", text)
        if match:
            if not self._check_cooldown("点歌"):
                return
            keyword = match.group(1).strip()
            result = self.songs.search(keyword)
            if result:
                songname, filepath = result
                await self.vlc.play(filepath)
                self.songs.now_playing = songname
                await self._send_reply(f">_ 正在播放：{songname}")
                log.info(f"[点歌] {uname}: {keyword} -> {songname}")
            else:
                await self._send_reply(f">_ 未找到「{keyword}」")
                log.info(f"[点歌] {uname}: {keyword} -> 未找到")
            return

        # --- 切歌 ---
        if text.strip() == "切歌":
            if not self._check_cooldown("切歌"):
                return
            await self.vlc.next_song()
            await self._send_reply(">_ 已切歌~")
            log.info(f"[切歌] {uname}")
            return

        # --- 当前播放 ---
        if text.strip() == "当前":
            if not self._check_cooldown("当前"):
                return
            song = self.songs.now_playing
            await self._send_reply(f">_ 当前：{song}")
            return

        # --- 歌单 ---
        if text.strip() == "歌单":
            if not self._check_cooldown("歌单"):
                return
            total = self.songs.total
            preview = "、".join(self.songs.list_songs(limit=5))
            await self._send_reply(f">_ 共{total}首：{preview}...")
            return

        # --- PK ---
        if text.strip() == "PK":
            if uid != self.uid:
                await self._send_reply(">_ PK仅限主播发起")
                return
            if self.pk_target_room_id <= 0:
                await self._send_reply(">_ PK目标未配置")
                return
            if not self._check_cooldown("PK"):
                return
            success = await self._send_pk_request()
            if success:
                await self._send_reply(">_ PK请求已发送~")
            else:
                await self._send_reply(">_ PK失败，请手动操作")
            return

        # --- 模式切换 ---
        if self.mode_manager:
            # 查看当前模式
            if text.strip() == "查看模式":
                if not self._check_cooldown("查看模式"):
                    return
                mode_info = self.mode_manager.get_mode_info()
                mode_name = mode_info["chinese_name"]
                priority = mode_info["priority"]
                await self._send_reply(f">_ 当前模式: {mode_name} (优先级{priority})")
                return

            # 模式切换命令
            mode = self.mode_manager.get_mode_by_command(text.strip())
            if mode:
                if not self._check_cooldown("模式切换"):
                    return
                success = await self.mode_manager.set_mode(mode, f"弹幕命令 ({uname})")
                if success:
                    await self._send_reply(f">_ 已切换到 {mode.chinese_name}")
                    log.info(f"[模式切换] {uname} 切换到 {mode.chinese_name}")
                else:
                    await self._send_reply(f">_ 无法切换到 {mode.chinese_name} (被高优先级模式阻止)")
                    log.warning(f"[模式切换] {uname} 尝试切换到 {mode.chinese_name} 但被阻止")
                return

    async def _send_pk_request(self) -> bool:
        """通过B站API发起PK请求"""
        url = "https://api.live.bilibili.com/xlive/web-room/v1/index/pkInvite"
        headers = {
            "Cookie": f"SESSDATA={self._sessdata}; bili_jct={self._bili_jct}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0",
            "Referer": f"https://live.bilibili.com/{self.room_id}",
            # 禁用 brotli，仅请求 gzip/deflate 以避免 Python 3.14+ 兼容性问题
            hdrs.ACCEPT_ENCODING: "gzip, deflate",
        }
        data = {
            "room_id": self.room_id,
            "invite_room_id": self.pk_target_room_id,
            "csrf_token": self._bili_jct,
            "csrf": self._bili_jct,
        }
        try:
            # 创建 connector，禁用 DNS 缓存以支持更多环境
            connector = aiohttp.TCPConnector(use_dns_cache=True)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, headers=headers, data=data) as resp:
                    result = await resp.json()
                    if result.get("code") == 0:
                        log.info(f"PK 请求已发送到房间 {self.pk_target_room_id}")
                        return True
                    else:
                        log.warning(f"PK 请求失败: {result.get('message')}")
                        return False
        except Exception as e:
            log.error(f"PK 请求异常: {e}")
            return False

    async def run(self):
        """启动弹幕监听"""
        log.info(f"弹幕机器人启动 (直播间 {self.room_id})")
        log.info("支持命令: 点歌/切歌/当前/歌单/PK")
        if self.mode_manager:
            log.info("支持模式切换: 直播模式/PK模式/点歌模式/轮播模式/其他模式/查看模式")

        # 创建 blivedm 事件处理器
        bot = self

        class Handler(blivedm.BaseHandler):
            async def _on_danmaku(self, client, message):
                # message 类型为 DanmakuMessage，但为了兼容不同 blivedm 版本，不用类型提示
                await bot._handle_danmaku(message.msg, message.uid, message.uname)

            async def _on_gift(self, client, message):
                uname = getattr(message, "uname", "")
                gift_name = getattr(message, "gift_name", "")
                if uname and gift_name:
                    await bot._send_reply(f"感谢{uname}的{gift_name}!")

        client = blivedm.BLiveClient(self.room_id, session=None)

        # 兼容不同版本的 blivedm
        handler = Handler()
        try:
            # 新版本（>= 0.7）
            client.add_handler(handler)
        except AttributeError:
            # 旧版本（< 0.7）
            client.set_handler(handler)

        client.start()

        try:
            await asyncio.Future()  # 永久运行
        except asyncio.CancelledError:
            pass
        finally:
            client.stop()
            await client.join()

#!/usr/bin/env python3
"""
程序员深夜电台 - 统一直播控制系统

功能:
  1. OBS WebSocket 控制 (VLC 源播放列表、源可见性、面板刷新)
  2. B区终端面板渲染 (Pillow -> panel.png)
  3. 弹幕机器人 (blivedm + bilibili-api)
  4. 歌曲搜索 + 队列管理
  5. 模式管理 + 自动切换

用法:
  python cyber_live.py                  # 使用 config.ini
  python cyber_live.py --config my.ini  # 指定配置文件
  python cyber_live.py --panel-only     # 仅运行面板渲染 (测试用)
"""

import argparse
import asyncio
import configparser
import logging
import os
import signal
import sys

# 在导入 aiohttp/blivedm 之前应用 brotli 补丁
from modules import brotli_patch  # noqa: F401

from modules.songs import SongManager
from modules.panel import PanelRenderer
from modules.modes import ModeManager, Mode

log = logging.getLogger("main")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(name)-8s %(message)s",
        datefmt="%H:%M:%S",
    )


def load_config(config_path: str) -> configparser.ConfigParser:
    """加载配置文件"""
    config = configparser.ConfigParser(interpolation=None)

    if config_path != "config.ini":
        if not os.path.exists(config_path):
            print(f"错误: 配置文件不存在 - {config_path}")
            sys.exit(1)
        config.read(config_path, encoding="utf-8")
        return config

    for path in ["config.ini", "config/config.ini"]:
        if os.path.exists(path):
            config.read(path, encoding="utf-8")
            log.info(f"已加载配置: {path}")
            return config

    print("错误: 找不到 config.ini")
    print("  1. 复制 config\\config.ini.example 为 config.ini")
    print("  2. 填入 B站凭证和路径配置")
    sys.exit(1)


def ensure_dirs(data_dir: str):
    os.makedirs(data_dir, exist_ok=True)


async def _song_request_cleanup_loop(vlc, mode_manager: ModeManager, interval: float = 5.0):
    """自动清除点歌请求，恢复轮播"""
    log.info("点歌自动清除循环启动")
    song_request_start_time = None
    TIMEOUT = 15 * 60  # 15分钟超时

    try:
        while True:
            has_request = vlc._current_song_request is not None

            if has_request:
                if song_request_start_time is None:
                    song_request_start_time = asyncio.get_event_loop().time()

                elapsed = asyncio.get_event_loop().time() - song_request_start_time
                if elapsed > TIMEOUT:
                    log.info(f"点歌已播放 {elapsed/60:.0f} 分钟，自动恢复轮播")
                    await vlc.clear_song_request()
                    song_request_start_time = None
            elif song_request_start_time is not None:
                song_request_start_time = None

            # 高优先级模式下清除点歌
            current = mode_manager.current_mode
            if current in (Mode.BROADCAST, Mode.PK) and has_request:
                log.info(f"切换到 {current.chinese_name}，清除点歌请求")
                await vlc.clear_song_request()
                song_request_start_time = None

            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        log.info("点歌自动清除循环停止")
        raise


async def _on_mode_change(old_mode, new_mode, reason, vlc, obs):
    """模式变更回调 - 统一处理 OBS 源切换和 VLC 播放控制"""
    log.info(f"模式回调: {old_mode} → {new_mode}")

    # 1. 通过 OBS WebSocket 切换源可见性
    if obs and obs.connected:
        await obs.apply_mode_sources(new_mode.key)

    # 2. 根据模式控制 VLC 播放
    if new_mode == Mode.PLAYBACK:
        await vlc.play_directory(vlc.playback_dir)
    elif new_mode in (Mode.BROADCAST, Mode.PK):
        await vlc.stop()
        await vlc.clear_song_request()
    elif new_mode == Mode.OTHER:
        await vlc.stop()


async def run_all(config: configparser.ConfigParser, panel_only: bool = False):
    """启动所有服务"""
    # 读取路径配置
    song_dir = config.get("paths", "song_dir")
    playback_dir = config.get("paths", "playback_dir", fallback=None)
    data_dir = config.get("paths", "data_dir")
    ensure_dirs(data_dir)

    song_library_dir = playback_dir or song_dir
    if not playback_dir:
        log.warning(f"未配置 playback_dir, 使用 song_dir: {song_library_dir}")

    panel_width = config.getint("panel", "width", fallback=520)
    panel_height = config.getint("panel", "height", fallback=435)
    panel_interval = config.getfloat("panel", "refresh_interval", fallback=1.0)
    panel_output = os.path.join(data_dir, "panel.png")

    # 字体路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(script_dir, "assets", "fonts", "JetBrainsMono-Regular.ttf")
    if not os.path.exists(font_path):
        font_path = None

    # 初始化歌曲管理器
    songs = SongManager(song_library_dir, data_dir)
    log.info(f"歌曲库: {songs.total} 首 (来自: {song_library_dir})")

    # 初始化模式管理器
    mode_manager = ModeManager()
    log.info("模式管理器已初始化 (默认轮播模式)")

    if panel_only:
        panel = PanelRenderer(panel_width, panel_height, panel_output, songs, mode_manager, font_path)
        panel.render()
        log.info(f"面板已生成: {panel_output}")
        return

    # 延迟导入 (panel-only 模式不需要这些)
    from modules.obs_control import OBSController
    from modules.vlc_control import VLCController
    from modules.danmaku import DanmakuBot

    # 初始化 OBS 控制器
    obs_host = config.get("obs", "host", fallback="localhost")
    obs_port = config.getint("obs", "port", fallback=4455)
    obs_password = config.get("obs", "password", fallback="")
    obs_scene = config.get("obs", "scene_name", fallback="AScreen")
    obs_vlc_source = config.get("obs", "vlc_source", fallback="vlc_player")
    obs_broadcast_source = config.get("obs", "broadcast_source", fallback="broadcast_screen")
    obs_panel_source = config.get("obs", "panel_source", fallback="B区-终端面板")

    obs = OBSController(
        host=obs_host, port=obs_port, password=obs_password,
        scene_name=obs_scene, vlc_source_name=obs_vlc_source,
        broadcast_source_name=obs_broadcast_source,
        panel_source_name=obs_panel_source,
    )

    # 连接 OBS (非阻塞，后台自动重连)
    obs_connected = await obs.connect()
    if obs_connected:
        version = await obs.get_version()
        if version:
            log.info(f"OBS 版本: {version}")
    else:
        log.warning("OBS 未连接，将在后台持续重连")

    # 初始化 VLC 控制器 (通过 OBS WebSocket)
    vlc = VLCController(
        obs=obs,
        song_manager=songs,
        playback_dir=playback_dir or song_dir,
        song_dir=song_dir,
        data_dir=data_dir,
    )

    # 注册模式变更回调
    async def mode_change_callback(old_mode, new_mode, reason):
        await _on_mode_change(old_mode, new_mode, reason, vlc, obs)

    mode_manager.register_mode_change_callback(mode_change_callback)

    # 初始化面板
    panel = PanelRenderer(
        panel_width, panel_height, panel_output,
        songs, mode_manager, font_path, obs_controller=obs,
    )

    # 写入 ticker.txt
    ticker_text = config.get("paths", "ticker_text",
                             fallback="欢迎来到程序员的深夜电台 ~ 发「点歌 歌名」即可点歌")
    ticker_file = os.path.join(data_dir, "ticker.txt")
    if not os.path.exists(ticker_file):
        with open(ticker_file, "w", encoding="utf-8") as f:
            f.write(ticker_text)

    tasks = []

    # 启动面板渲染
    tasks.append(asyncio.create_task(panel.render_loop(panel_interval)))

    # 启动点歌自动清除
    tasks.append(asyncio.create_task(_song_request_cleanup_loop(vlc, mode_manager, 5)))

    # 触发初始模式 (启动轮播)
    await mode_manager.set_mode(Mode.PLAYBACK, "系统启动")

    # 启动弹幕机器人
    room_id = config.getint("bilibili", "room_id", fallback=0)
    if room_id > 0:
        sessdata = config.get("bilibili", "sessdata", fallback="")
        bili_jct = config.get("bilibili", "bili_jct", fallback="")
        buvid3 = config.get("bilibili", "buvid3", fallback="")

        if sessdata and bili_jct:
            bot = DanmakuBot(
                room_id=room_id,
                uid=config.getint("bilibili", "uid", fallback=0),
                sessdata=sessdata,
                bili_jct=bili_jct,
                buvid3=buvid3,
                vlc=vlc,
                songs=songs,
                mode_manager=mode_manager,
                pk_target_room_id=config.getint("pk", "target_room_id", fallback=0),
            )
            tasks.append(asyncio.create_task(bot.run()))
        else:
            log.warning("B站凭证未配置, 弹幕机器人未启动")
    else:
        log.warning("直播间号未配置, 弹幕机器人未启动")

    log.info("=" * 45)
    log.info("  程序员深夜电台 - 所有服务已启动")
    log.info(f"  OBS WebSocket: {obs_host}:{obs_port} ({'已连接' if obs_connected else '等待连接'})")
    log.info(f"  面板输出:  {panel_output}")
    log.info(f"  歌曲数量:  {songs.total}")
    log.info("  按 Ctrl+C 优雅退出")
    log.info("=" * 45)

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    finally:
        vlc.close()
        await obs.disconnect()


def main():
    parser = argparse.ArgumentParser(description="程序员深夜电台 - 直播控制系统")
    parser.add_argument("--config", default="config.ini", help="配置文件路径")
    parser.add_argument("--panel-only", action="store_true", help="仅渲染一次面板")
    args = parser.parse_args()

    setup_logging()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    config = load_config(args.config)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 异常处理器
    def handle_exception(loop, context):
        exception = context.get('exception')
        message = str(context.get('message', ''))
        if exception and isinstance(exception, AssertionError):
            return
        if "Task exception was never retrieved" in message:
            return
        if exception:
            log.error(f"未处理的异常: {message} - {exception}")

    loop.set_exception_handler(handle_exception)

    def _shutdown(sig):
        log.info(f"收到退出信号 ({sig.name}), 正在关闭...")
        try:
            tasks = asyncio.all_tasks()
        except TypeError:
            tasks = asyncio.all_tasks(loop)
        for task in tasks:
            task.cancel()

    if sys.platform != "win32":
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, _shutdown, sig)

    try:
        loop.run_until_complete(run_all(config, args.panel_only))
    except KeyboardInterrupt:
        log.info("用户中断, 正在关闭...")
        try:
            tasks = asyncio.all_tasks()
        except TypeError:
            tasks = asyncio.all_tasks(loop)
        for task in tasks:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    finally:
        loop.close()
        log.info("已退出")


if __name__ == "__main__":
    main()

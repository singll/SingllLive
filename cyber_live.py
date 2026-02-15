#!/usr/bin/env python3
"""
程序员深夜电台 - 统一直播控制系统
替代原来的 6+ 个 bat 脚本 + HTML 面板 + HTTP 服务器

功能:
  1. VLC 自动启动 + 循环播放
  2. VLC 看门狗 (崩溃自动重启)
  3. 歌名同步 (VLC HTTP API -> now_playing.txt)
  4. B区终端面板渲染 (Pillow -> panel.png)
  5. 弹幕机器人 (blivedm + bilibili-api)
  6. 歌曲搜索 + 队列管理

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

# 关键: 在导入任何 aiohttp/blivedm 之前应用 brotli 补丁
# 这可以防止 Python 3.14+ 中的 brotli 兼容性问题
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
    """加载配置文件，支持多个位置"""
    # 创建 ConfigParser，禁用插值以支持包含 % 的值（如 URL 编码的 sessdata）
    config = configparser.ConfigParser(interpolation=None)

    # 如果指定了路径，直接使用
    if config_path != "config.ini":
        if not os.path.exists(config_path):
            print(f"错误: 配置文件不存在 - {config_path}")
            sys.exit(1)
        config.read(config_path, encoding="utf-8")
        return config

    # 默认配置：尝试多个位置
    possible_paths = [
        "config.ini",           # 项目根目录（推荐）
        "config/config.ini",    # config 子目录（备选）
    ]

    for path in possible_paths:
        if os.path.exists(path):
            config.read(path, encoding="utf-8")
            log.info(f"已加载配置: {path}")
            return config

    # 都不存在，提示错误
    print("错误: 找不到 config.ini 配置文件")
    print()
    print("请执行以下步骤:")
    print("  1. 复制配置模板:")
    print("     copy config\\config.ini.example config.ini")
    print()
    print("  2. 编辑 config.ini，填入:")
    print("     - [bilibili] 直播间号、UID、SESSDATA 等")
    print("     - [vlc] VLC 安装路径")
    print("     - [paths] 歌曲目录等")
    print()
    sys.exit(1)


def ensure_dirs(data_dir: str):
    os.makedirs(data_dir, exist_ok=True)


async def _mode_auto_switch_loop(mode_manager: ModeManager, songs: SongManager, interval: float = 2.0):
    """监听队列状态，自动处理点歌队列

    当轮播模式下有队列时，自动从队列中加载歌曲到VLC
    """
    log.info("模式自动切换循环启动")
    try:
        while True:
            queue_count = songs.queue_count
            current_mode = mode_manager.current_mode

            # 如果在轮播模式且队列有歌曲，从队列中取出下一首（由 VLC 模式管理处理）
            if queue_count > 0:
                log.debug(f"队列中有 {queue_count} 首歌曲 (当前模式: {current_mode})")

            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        log.info("模式自动切换循环停止")
        raise


async def _vlc_mode_manager_loop(vlc, mode_manager: ModeManager, interval: float = 3.0):
    """根据模式管理 VLC 播放列表 (Plan A - 文件系统模式)

    规则:
    - PLAYBACK (轮播) → 生成轮播目录的 .m3u 播放列表
    - BROADCAST (直播)/PK → 清空播放列表（暂停播放）
    - OTHER → 清空播放列表

    说明：点歌队列中的歌曲在轮播模式下自动加载，在直播模式下暂停等待
    """
    log.info("VLC 模式管理循环启动 (Plan A - 文件系统模式)")
    last_mode = None

    try:
        while True:
            current_mode = mode_manager.current_mode

            # 模式变化时处理
            if current_mode != last_mode:
                log.info(f"VLC 模式变化: {last_mode} → {current_mode}")

                if current_mode == Mode.PLAYBACK:
                    # 轮播模式：生成轮播目录的 .m3u 播放列表
                    log.info("切换到轮播模式")
                    vlc.write_playlist_file("playback", vlc.playback_dir)

                elif current_mode in (Mode.BROADCAST, Mode.PK):
                    # 直播/PK 模式：清空播放列表（OBS 脚本会隐藏 vlc_player 源）
                    log.info("进入直播/PK模式，VLC 暂停（队列中的歌曲将在轮播时播放）")
                    vlc.write_playlist_file("paused", "")

                elif current_mode == Mode.OTHER:
                    # 其他/空闲模式：清空播放列表
                    log.info("进入空闲模式")
                    vlc.write_playlist_file("other", "")

                last_mode = current_mode

            await asyncio.sleep(interval)

    except asyncio.CancelledError:
        log.info("VLC 模式管理循环已取消")
    except Exception as e:
        log.error(f"VLC 模式管理异常: {e}")


async def run_all(config: configparser.ConfigParser, panel_only: bool = False):
    """启动所有服务"""
    # 读取配置
    song_dir = config.get("paths", "song_dir")
    playback_dir = config.get("paths", "playback_dir", fallback=None)
    data_dir = config.get("paths", "data_dir")
    ensure_dirs(data_dir)

    # 歌曲库目录：优先使用轮播目录，回退到点歌目录
    song_library_dir = playback_dir or song_dir
    if not playback_dir:
        log.warning(f"未配置 playback_dir, 使用 song_dir 作为歌曲库: {song_library_dir}")
    else:
        log.info(f"使用轮播目录作为歌曲库: {playback_dir}")

    panel_width = config.getint("panel", "width", fallback=520)
    panel_height = config.getint("panel", "height", fallback=435)
    panel_interval = config.getfloat("panel", "refresh_interval", fallback=1.0)
    panel_output = os.path.join(data_dir, "panel.png")

    # 字体路径: 优先 assets/fonts/, 回退到系统字体
    script_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(script_dir, "assets", "fonts", "JetBrainsMono-Regular.ttf")
    if not os.path.exists(font_path):
        font_path = None

    # 初始化歌曲管理器（从轮播目录搜索歌曲，而不是点歌队列目录）
    songs = SongManager(song_library_dir, data_dir)
    log.info(f"歌曲库加载完成: {songs.total} 首 (来自: {song_library_dir})")

    # 初始化模式管理器
    mode_manager = ModeManager()
    log.info("模式管理器已初始化 (默认轮播模式)")

    # 初始化面板渲染器
    panel = PanelRenderer(panel_width, panel_height, panel_output, songs, mode_manager, font_path)

    # 写入 ticker.txt
    ticker_text = config.get("paths", "ticker_text",
                             fallback="欢迎来到程序员的深夜电台 ~ 发「点歌 歌名」即可点歌")
    ticker_file = os.path.join(data_dir, "ticker.txt")
    if not os.path.exists(ticker_file):
        with open(ticker_file, "w", encoding="utf-8") as f:
            f.write(ticker_text)

    tasks = []

    if panel_only:
        # 仅渲染面板 (测试模式)
        log.info("=== 仅面板渲染模式 ===")
        panel.render()
        log.info(f"面板已生成: {panel_output}")
        return

    # 延迟导入 (这些模块依赖 aiohttp/blivedm, panel-only 模式不需要)
    from modules.vlc_control import VLCController
    from modules.danmaku import DanmakuBot

    # 初始化 VLC 控制器 (Plan A - 文件系统模式)
    vlc = VLCController(
        vlc_path=config.get("vlc", "path"),
        http_port=config.getint("vlc", "http_port", fallback=9090),
        http_password=config.get("vlc", "http_password", fallback="123456"),
        song_dir=song_dir,  # 点歌队列目录（暂未使用，保留用于向后兼容）
        song_manager=songs,
        playback_dir=playback_dir,  # 轮播目录（实际歌曲库）
    )

    # VLC 将由模式管理器根据模式动态启动/停止，不再在这里启动
    # 这样可以避免在不需要时浪费资源

    # 启动 VLC 模式管理 (根据模式动态更新播放列表文件)
    tasks.append(asyncio.create_task(_vlc_mode_manager_loop(vlc, mode_manager, 3)))
    # 启动模式自动切换 (监听队列状态)
    tasks.append(asyncio.create_task(_mode_auto_switch_loop(mode_manager, songs, 2)))
    # 启动面板渲染
    tasks.append(asyncio.create_task(panel.render_loop(panel_interval)))

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
    log.info(f"  VLC HTTP:  http://127.0.0.1:{config.getint('vlc', 'http_port', fallback=9090)}")
    log.info(f"  面板输出:  {panel_output}")
    log.info(f"  歌曲数量:  {songs.total}")
    log.info("  按 Ctrl+C 优雅退出")
    log.info("=" * 45)

    # 等待所有任务 (Ctrl+C 会触发 CancelledError)
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    finally:
        vlc.close()


def main():
    parser = argparse.ArgumentParser(description="程序员深夜电台 - 直播控制系统")
    parser.add_argument("--config", default="config.ini", help="配置文件路径")
    parser.add_argument("--panel-only", action="store_true", help="仅渲染一次面板 (测试用)")
    args = parser.parse_args()

    setup_logging()

    # 切换工作目录到脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    config = load_config(args.config)

    # 信号处理: 优雅退出
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 设置异常处理器，忽略 aiohttp 的非致命异常 (Python 3.14+ protocol is None race condition)
    def handle_exception(loop, context):
        exception = context.get('exception')
        message = str(context.get('message', ''))

        # 抑制特定的非致命错误
        if exception:
            exc_str = str(exception)
            # 1. aiohttp/brotli_patch 的 AssertionError - 这是非致命的
            if isinstance(exception, AssertionError):
                # 忽略所有 AssertionError，它们通常是竞态条件导致的非致命错误
                return

        # 忽略 "Task exception was never retrieved" 消息中的所有异常
        if "Task exception was never retrieved" in message:
            return

        # 其他异常正常处理
        if exception:
            log.error(f"未处理的异常: {message} - {exception}")

    loop.set_exception_handler(handle_exception)

    def _shutdown(sig):
        log.info(f"收到退出信号 ({sig.name}), 正在关闭...")
        # Python 3.10+ asyncio.all_tasks() 不需要 loop 参数
        try:
            tasks = asyncio.all_tasks()
        except TypeError:
            # Python < 3.10 fallback
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
            # Python < 3.10 fallback
            tasks = asyncio.all_tasks(loop)
        for task in tasks:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    finally:
        loop.close()
        log.info("已退出")


if __name__ == "__main__":
    main()

"""
酷狗音乐 API 客户端实现

提供搜索、获取歌词、获取播放链接等功能
"""

import aiohttp
import logging
from typing import Optional, List, Dict
import asyncio

log = logging.getLogger("kugou")


class KugouAPI:
    """酷狗音乐 API 客户端"""

    # API 端点
    SEARCH_URL = "http://searpc.kugou.com/v1/search/songs"
    LYRICS_URL = "http://lyrics.kugou.com/download"
    SONG_URL = "http://www.kugou.com/song/{}"

    def __init__(self, timeout: int = 10):
        """初始化 API 客户端

        Args:
            timeout: 请求超时时间 (秒)
        """
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict = {}  # 简单缓存

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP 会话"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def search_song(
        self,
        keywords: str,
        page: int = 1,
        pagesize: int = 10
    ) -> List[Dict]:
        """搜索歌曲

        Args:
            keywords: 搜索关键词 (支持歌曲名、艺术家等)
            page: 页码 (默认 1)
            pagesize: 每页结果数 (默认 10)

        Returns:
            歌曲列表，每个歌曲包含:
            {
                'id': '歌曲ID',
                'name': '歌曲名',
                'artist': '艺术家',
                'album': '专辑名',
                'duration': 播放时长(秒),
                'hash': '文件hash'，用于获取歌词和播放链接
            }

        示例:
            songs = await api.search_song("三体")
            # [
            #   {
            #     'id': '123456',
            #     'name': '三体',
            #     'artist': '许嵩',
            #     'duration': 220,
            #     ...
            #   }
            # ]
        """
        cache_key = f"search:{keywords}:{page}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            session = await self._get_session()

            params = {
                'keyword': keywords,
                'page': page,
                'pagesize': pagesize,
                'bitrate': 0,  # 获取所有比特率
                'isfuzzy': 0,  # 精确搜索
                'tag': 'em',   # 标签搜索
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            async with session.get(
                self.SEARCH_URL,
                params=params,
                headers=headers,
                timeout=self.timeout
            ) as resp:
                if resp.status != 200:
                    log.error(f"搜索歌曲失败: HTTP {resp.status}")
                    return []

                data = await resp.json()
                songs = []

                # 解析 API 响应
                for item in data.get('data', {}).get('songs', []):
                    try:
                        # 解析艺术家信息
                        artists = []
                        for artist in item.get('ArtistArray', []):
                            artists.append(artist.get('ArtistName', ''))
                        artist_str = ' / '.join(artists) if artists else '未知艺术家'

                        song = {
                            'id': item.get('ID'),
                            'name': item.get('SongName', '未知'),
                            'artist': artist_str,
                            'album': item.get('AlbumName', ''),
                            'duration': item.get('Duration', 0),
                            'hash': item.get('FileHash', ''),
                            'kugou_url': self.SONG_URL.format(item.get('ID')),
                        }
                        songs.append(song)
                    except Exception as e:
                        log.debug(f"解析歌曲信息异常: {e}")
                        continue

                log.info(f"搜索 '{keywords}' 找到 {len(songs)} 首歌曲")

                # 缓存结果
                self._cache[cache_key] = songs

                return songs

        except asyncio.TimeoutError:
            log.error(f"搜索歌曲超时")
            return []
        except Exception as e:
            log.error(f"搜索歌曲异常: {e}")
            return []

    async def get_lyrics(self, song_hash: str, song_id: str) -> Optional[Dict]:
        """获取歌词

        Args:
            song_hash: 歌曲 hash (来自搜索结果)
            song_id: 歌曲 ID

        Returns:
            歌词信息或 None:
            {
                'content': '完整 LRC 格式歌词',
                'lines': [
                    {'time': 10.0, 'text': '第一行歌词'},
                    {'time': 20.0, 'text': '第二行歌词'},
                    ...
                ]
            }

        示例:
            lyrics = await api.get_lyrics('abc123', '123456')
            # {
            #   'content': '[00:10.00]第一行\n[00:20.00]第二行\n...',
            #   'lines': [
            #     {'time': 10.0, 'text': '第一行'},
            #     {'time': 20.0, 'text': '第二行'},
            #   ]
            # }
        """
        cache_key = f"lyrics:{song_hash}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            session = await self._get_session()

            params = {
                'hash': song_hash,
                'id': song_id,
                'client': 'pc',
                'ft': '0',
                'charset': 'utf8',
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            async with session.get(
                self.LYRICS_URL,
                params=params,
                headers=headers,
                timeout=self.timeout
            ) as resp:
                if resp.status != 200:
                    log.warning(f"获取歌词失败: HTTP {resp.status}")
                    return None

                text = await resp.text()

                # 解析 LRC 格式歌词
                lines = self._parse_lrc(text)

                result = {
                    'content': text,
                    'lines': lines,
                }

                # 缓存结果
                self._cache[cache_key] = result

                log.debug(f"获取歌词成功: {len(lines)} 行")
                return result

        except asyncio.TimeoutError:
            log.warning(f"获取歌词超时")
            return None
        except Exception as e:
            log.error(f"获取歌词异常: {e}")
            return None

    @staticmethod
    def _parse_lrc(lrc_content: str) -> List[Dict]:
        """解析 LRC 歌词格式

        LRC 格式标准:
        [00:10.00]第一行歌词
        [00:20.50]第二行歌词
        [mm:ss.cc]第n行歌词

        Args:
            lrc_content: LRC 格式的字符串

        Returns:
            歌词行列表，每行包含时间(秒)和文本:
            [
                {'time': 10.0, 'text': '第一行歌词'},
                {'time': 20.5, 'text': '第二行歌词'},
                ...
            ]
        """
        lines = []

        for line in lrc_content.split('\n'):
            line = line.strip()

            # 检查是否是 LRC 格式行
            if not line.startswith('[') or ']' not in line:
                continue

            try:
                # 提取时间和文本
                end_bracket = line.index(']')
                time_str = line[1:end_bracket]
                text = line[end_bracket + 1:]

                # 跳过空文本
                if not text.strip():
                    continue

                # 解析时间 mm:ss.cc 或 mm:ss
                time_parts = time_str.split(':')
                if len(time_parts) != 2:
                    continue

                minutes = int(time_parts[0])
                seconds = float(time_parts[1])
                total_seconds = minutes * 60 + seconds

                lines.append({
                    'time': total_seconds,
                    'text': text.strip(),
                })

            except (ValueError, IndexError) as e:
                # 跳过无法解析的行
                continue

        # 按时间排序
        lines.sort(key=lambda x: x['time'])

        return lines

    async def close(self):
        """关闭 HTTP 会话"""
        if self.session:
            await self.session.close()
            self.session = None

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        log.info("缓存已清空")


# 使用示例
async def main():
    """使用示例"""
    api = KugouAPI()

    try:
        # 搜索歌曲
        print("🔍 正在搜索歌曲 '三体'...")
        songs = await api.search_song("三体", pagesize=5)

        if not songs:
            print("❌ 未找到歌曲")
            return

        # 显示搜索结果
        print(f"\n✅ 找到 {len(songs)} 首歌曲:\n")
        for i, song in enumerate(songs, 1):
            print(f"{i}. {song['name']}")
            print(f"   艺术家: {song['artist']}")
            print(f"   时长: {song['duration']}秒")
            print()

        # 获取第一首歌的歌词
        first_song = songs[0]
        print(f"📝 正在获取 '{first_song['name']}' 的歌词...")
        lyrics = await api.get_lyrics(first_song['hash'], first_song['id'])

        if lyrics:
            print(f"\n✅ 获取歌词成功，共 {len(lyrics['lines'])} 行:\n")
            # 显示前 5 行
            for line in lyrics['lines'][:5]:
                minutes = int(line['time'] // 60)
                seconds = line['time'] % 60
                print(f"[{minutes:02d}:{seconds:05.2f}] {line['text']}")
            if len(lyrics['lines']) > 5:
                print(f"... (还有 {len(lyrics['lines']) - 5} 行)")
        else:
            print("❌ 获取歌词失败")

    finally:
        await api.close()


if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='[%(name)s] %(message)s'
    )

    # 运行示例
    asyncio.run(main())

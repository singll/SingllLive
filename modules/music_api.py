"""
网易云音乐 API 客户端

支持歌曲搜索和歌词获取
"""

import aiohttp
import logging
import json
from typing import Optional, List, Dict
import asyncio

log = logging.getLogger("music_api")


class NetEaseAPI:
    """网易云音乐 API 客户端

    用于点歌系统的搜索和歌词获取
    """

    SEARCH_URL = "http://music.163.com/api/search/get"
    LYRICS_URL = "http://music.163.com/api/song/lyricNew"

    def __init__(self, timeout: int = 10):
        """初始化 API 客户端

        Args:
            timeout: 请求超时时间 (秒)
        """
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP 会话"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def search_song(
        self,
        keywords: str,
        limit: int = 10
    ) -> List[Dict]:
        """搜索歌曲

        Args:
            keywords: 搜索关键词 (歌曲名、艺术家等)
            limit: 返回结果数量 (默认 10)

        Returns:
            歌曲列表，每个歌曲包含:
            {
                'id': '网易云歌曲ID',
                'name': '歌曲名',
                'artist': '艺术家',
                'album': '专辑名',
                'duration': 播放时长(毫秒),
            }

        示例:
            >>> songs = await api.search_song("三体")
            >>> # [
            >>> #   {'id': 2014337720, 'name': 'THREE-BODY', 'artist': '重塑雕像的权利', ...}
            >>> # ]
        """
        cache_key = f"search:{keywords}:{limit}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            session = await self._get_session()

            # 搜索参数
            data = {
                "s": keywords,      # 搜索词
                "type": 1,          # 1=歌曲, 10=专辑, 100=歌手
                "limit": limit,
                "offset": 0
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://music.163.com/',
            }

            async with session.post(
                self.SEARCH_URL,
                data=data,
                headers=headers,
                timeout=self.timeout
            ) as resp:
                if resp.status != 200:
                    log.error(f"搜索歌曲失败: HTTP {resp.status}")
                    return []

                # 网易云 API 返回 text/plain，需要手动 parse JSON
                text = await resp.text()
                api_result = json.loads(text)

                songs = []
                for item in api_result.get('result', {}).get('songs', []):
                    try:
                        # 解析艺术家
                        artists = item.get('artists', [])
                        artist_name = ', '.join([a.get('name', '') for a in artists])

                        song = {
                            'id': item.get('id'),
                            'name': item.get('name', '未知'),
                            'artist': artist_name or '未知艺术家',
                            'album': item.get('album', {}).get('name', ''),
                            'duration': item.get('duration', 0),  # 毫秒
                        }
                        songs.append(song)
                    except Exception as e:
                        log.debug(f"解析歌曲信息异常: {e}")

                log.info(f"网易云搜索 '{keywords}' 找到 {len(songs)} 首歌曲")

                # 缓存结果
                self._cache[cache_key] = songs

                return songs

        except asyncio.TimeoutError:
            log.error(f"搜索歌曲超时")
            return []
        except Exception as e:
            log.error(f"搜索歌曲异常: {e}")
            return []

    async def get_lyrics(self, song_id: int) -> Optional[Dict]:
        """获取歌词

        Args:
            song_id: 网易云歌曲 ID

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
            >>> lyrics = await api.get_lyrics(2014337720)
            >>> # {'content': '[00:10.00]歌词\n...', 'lines': [...]}
        """
        cache_key = f"lyrics:{song_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            session = await self._get_session()

            params = {
                'id': song_id,
                'lv': -1,
                'tv': -1,
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://music.163.com/',
            }

            async with session.post(
                self.LYRICS_URL,
                data=params,
                headers=headers,
                timeout=self.timeout
            ) as resp:
                if resp.status != 200:
                    log.warning(f"获取歌词失败: HTTP {resp.status}")
                    return None

                text = await resp.text()
                api_result = json.loads(text)

                # 尝试获取歌词
                lrc = api_result.get('lrc', {})
                lyric_text = lrc.get('lyric', '')

                if not lyric_text:
                    log.warning(f"歌曲 {song_id} 无歌词")
                    return None

                # 解析 LRC 格式
                lines = self._parse_lrc(lyric_text)

                result = {
                    'content': lyric_text,
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

        Args:
            lrc_content: LRC 格式的字符串

        Returns:
            歌词行列表，每行包含时间(秒)和文本
        """
        lines = []

        for line in lrc_content.split('\n'):
            line = line.strip()

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

                # 解析时间 mm:ss.cc
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

            except (ValueError, IndexError):
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


# 使用示例和测试
async def main():
    """使用示例"""
    api = NetEaseAPI()

    try:
        # 搜索歌曲
        print("🔍 搜索歌曲 '三体'...\n")
        songs = await api.search_song("三体", limit=5)

        if not songs:
            print("❌ 未找到歌曲")
            return

        print(f"✅ 找到 {len(songs)} 首歌曲:\n")
        for i, song in enumerate(songs, 1):
            print(f"{i}. {song['name']}")
            print(f"   艺术家: {song['artist']}")
            print(f"   时长: {song['duration']/1000:.0f} 秒")
            print()

        # 获取第一首歌的歌词
        first_song = songs[0]
        print(f"📝 正在获取 '{first_song['name']}' 的歌词...\n")
        lyrics = await api.get_lyrics(first_song['id'])

        if lyrics:
            print(f"✅ 获取歌词成功，共 {len(lyrics['lines'])} 行:\n")
            # 显示前 5 行
            for line in lyrics['lines'][:5]:
                minutes = int(line['time'] // 60)
                seconds = line['time'] % 60
                print(f"[{minutes:02d}:{seconds:05.2f}] {line['text']}")
            if len(lyrics['lines']) > 5:
                print(f"... (还有 {len(lyrics['lines']) - 5} 行)")
        else:
            print("⚠️  该歌曲暂无歌词")

    finally:
        await api.close()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='[%(name)s] %(message)s'
    )

    asyncio.run(main())

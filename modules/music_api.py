"""
增强版本：支持多个音乐 API 后端
支持酷狗、网易云等多个音乐平台

当某个 API 失败时自动切换到备用方案
"""

import aiohttp
import logging
from typing import Optional, List, Dict
import asyncio

log = logging.getLogger("music_api")


class NetEaseAPI:
    """网易云音乐 API 客户端 (备用方案)

    网易云 API 在国内更稳定，推荐作为主方案
    """

    SEARCH_URL = "https://music.163.com/api/search/get"
    LYRICS_URL = "https://music.163.com/api/song/lyricNew"

    def __init__(self, timeout: int = 10):
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
            keywords: 搜索关键词
            limit: 返回结果数量

        Returns:
            歌曲列表
        """
        cache_key = f"search:{keywords}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            session = await self._get_session()

            # 网易云 API 需要特定的请求格式
            params = {
                'type': 1,  # 1: 单曲, 10: 专辑, 100: 歌手, 1000: 歌单
                's': keywords,
                'limit': limit,
                'offset': 0,
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://music.163.com/',
            }

            async with session.post(
                self.SEARCH_URL,
                data=params,
                headers=headers,
                timeout=self.timeout
            ) as resp:
                if resp.status != 200:
                    log.error(f"网易云搜索失败: HTTP {resp.status}")
                    return []

                data = await resp.json()
                songs = []

                for item in data.get('result', {}).get('songs', []):
                    try:
                        artists = ', '.join([a.get('name', '') for a in item.get('artists', [])])
                        song = {
                            'id': item.get('id'),
                            'name': item.get('name', '未知'),
                            'artist': artists or '未知艺术家',
                            'album': item.get('album', {}).get('name', ''),
                            'duration': item.get('duration', 0) // 1000,  # 转换为秒
                        }
                        songs.append(song)
                    except Exception as e:
                        log.debug(f"解析歌曲异常: {e}")

                log.info(f"网易云搜索 '{keywords}' 找到 {len(songs)} 首歌曲")
                self._cache[cache_key] = songs
                return songs

        except Exception as e:
            log.error(f"网易云搜索异常: {e}")
            return []

    async def get_lyrics(self, song_id: str) -> Optional[Dict]:
        """获取歌词

        Args:
            song_id: 网易云歌曲 ID

        Returns:
            歌词信息或 None
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
                    return None

                data = await resp.json()

                # 解析歌词
                lrc_text = data.get('lrc', {}).get('lyric', '')
                if not lrc_text:
                    return None

                lines = self._parse_lrc(lrc_text)

                result = {
                    'content': lrc_text,
                    'lines': lines,
                }

                self._cache[cache_key] = result
                log.debug(f"获取网易云歌词成功: {len(lines)} 行")
                return result

        except Exception as e:
            log.error(f"获取网易云歌词异常: {e}")
            return None

    @staticmethod
    def _parse_lrc(lrc_content: str) -> List[Dict]:
        """解析 LRC 歌词格式"""
        lines = []

        for line in lrc_content.split('\n'):
            line = line.strip()

            if not line.startswith('[') or ']' not in line:
                continue

            try:
                end_bracket = line.index(']')
                time_str = line[1:end_bracket]
                text = line[end_bracket + 1:]

                if not text.strip():
                    continue

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

        lines.sort(key=lambda x: x['time'])
        return lines

    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
            self.session = None


class MusicAPIClient:
    """通用音乐 API 客户端 - 支持多个后端

    自动选择最佳可用的 API 后端
    """

    def __init__(self):
        """初始化多个 API 后端"""
        self.apis = {
            'netease': NetEaseAPI(),
            # 'kugou': KugouAPI(),  # 可选
        }
        self.preferred_api = 'netease'  # 优先使用网易云

    async def search_song(self, keywords: str) -> List[Dict]:
        """搜索歌曲 - 自动切换 API

        Args:
            keywords: 搜索关键词

        Returns:
            歌曲列表
        """
        # 首先尝试优先的 API
        if self.preferred_api in self.apis:
            api = self.apis[self.preferred_api]
            songs = await api.search_song(keywords)
            if songs:
                return songs
            log.warning(f"{self.preferred_api} API 搜索失败，尝试备用 API")

        # 尝试其他 API
        for api_name, api in self.apis.items():
            if api_name == self.preferred_api:
                continue
            try:
                log.info(f"尝试使用 {api_name} API 搜索...")
                songs = await api.search_song(keywords)
                if songs:
                    log.info(f"✅ {api_name} API 搜索成功")
                    return songs
            except Exception as e:
                log.warning(f"{api_name} API 搜索异常: {e}")

        log.error("所有 API 搜索都失败了")
        return []

    async def get_lyrics(self, song_id: str, api_name: str = None) -> Optional[Dict]:
        """获取歌词

        Args:
            song_id: 歌曲 ID
            api_name: 指定 API (可选，默认使用优先 API)

        Returns:
            歌词信息或 None
        """
        if api_name and api_name in self.apis:
            return await self.apis[api_name].get_lyrics(song_id)

        # 尝试优先的 API
        api = self.apis[self.preferred_api]
        return await api.get_lyrics(song_id)

    async def close(self):
        """关闭所有会话"""
        for api in self.apis.values():
            await api.close()


# 使用示例和测试
async def main():
    """测试多 API 客户端"""
    client = MusicAPIClient()

    try:
        # 搜索歌曲
        print("🔍 搜索歌曲 '三体'...\n")
        songs = await client.search_song("三体")

        if not songs:
            print("❌ 未找到歌曲")
            return

        print(f"✅ 找到 {len(songs)} 首歌曲:\n")
        for i, song in enumerate(songs[:5], 1):
            print(f"{i}. {song['name']}")
            print(f"   艺术家: {song['artist']}")
            print(f"   时长: {song['duration']}秒\n")

        # 获取第一首歌的歌词
        first_song = songs[0]
        print(f"📝 正在获取 '{first_song['name']}' 的歌词...\n")
        lyrics = await client.get_lyrics(first_song['id'])

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
            print("❌ 获取歌词失败")

    finally:
        await client.close()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='[%(name)s] %(message)s'
    )

    asyncio.run(main())

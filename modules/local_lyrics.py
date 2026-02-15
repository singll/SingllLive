"""
本地歌词管理系统 - 完全离线工作

当网络不可用时，使用本地歌词库
用户可以手动添加歌词文件
"""

import os
import json
import logging
from typing import Optional, List, Dict
from pathlib import Path

log = logging.getLogger("local_lyrics")


class LocalLyricsManager:
    """本地歌词管理系统

    支持：
    - LRC 文件导入
    - JSON 歌词存储
    - 搜索和匹配
    - 自动管理
    """

    def __init__(self, lyrics_dir: str = "data/lyrics"):
        """初始化本地歌词管理器

        Args:
            lyrics_dir: 歌词库目录
        """
        self.lyrics_dir = lyrics_dir
        self.db_file = os.path.join(lyrics_dir, "lyrics_db.json")
        self.lyrics_db: Dict = {}

        # 创建目录
        os.makedirs(lyrics_dir, exist_ok=True)

        # 加载现有歌词数据库
        self._load_db()

    def _load_db(self):
        """从文件加载歌词数据库"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    self.lyrics_db = json.load(f)
                log.info(f"加载歌词数据库: {len(self.lyrics_db)} 首歌曲")
            except Exception as e:
                log.error(f"加载歌词数据库失败: {e}")
        else:
            log.info("歌词数据库不存在，将创建新的")

    def _save_db(self):
        """保存歌词数据库到文件"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.lyrics_db, f, ensure_ascii=False, indent=2)
            log.debug(f"歌词数据库已保存: {len(self.lyrics_db)} 首歌曲")
        except Exception as e:
            log.error(f"保存歌词数据库失败: {e}")

    def add_song(
        self,
        song_name: str,
        artist: str,
        lyrics: str,
        duration: float = 0
    ) -> bool:
        """添加歌曲和歌词

        Args:
            song_name: 歌曲名
            artist: 艺术家
            lyrics: LRC 格式歌词
            duration: 歌曲时长 (秒)

        Returns:
            是否成功添加
        """
        try:
            # 生成唯一键
            key = self._generate_key(song_name, artist)

            # 解析歌词
            lines = self._parse_lrc(lyrics)

            self.lyrics_db[key] = {
                'name': song_name,
                'artist': artist,
                'duration': duration,
                'lyrics': lyrics,  # 原始 LRC
                'lines': lines,    # 解析后的行
                'added_time': str(__import__('datetime').datetime.now()),
            }

            self._save_db()
            log.info(f"添加歌曲: {song_name} - {artist} ({len(lines)} 行歌词)")
            return True

        except Exception as e:
            log.error(f"添加歌曲失败: {e}")
            return False

    def search_song(self, keywords: str) -> List[Dict]:
        """搜索歌曲

        Args:
            keywords: 搜索关键词

        Returns:
            匹配的歌曲列表
        """
        results = []

        for key, data in self.lyrics_db.items():
            # 检查是否匹配歌曲名或艺术家
            if (keywords.lower() in data['name'].lower() or
                keywords.lower() in data['artist'].lower()):
                results.append({
                    'id': key,
                    'name': data['name'],
                    'artist': data['artist'],
                    'duration': data.get('duration', 0),
                })

        log.info(f"本地搜索 '{keywords}' 找到 {len(results)} 首歌曲")
        return results

    def get_lyrics(self, song_id: str) -> Optional[Dict]:
        """获取歌词

        Args:
            song_id: 歌曲 ID (通常是 song_name-artist)

        Returns:
            歌词信息或 None
        """
        if song_id not in self.lyrics_db:
            return None

        data = self.lyrics_db[song_id]
        return {
            'content': data['lyrics'],
            'lines': data['lines'],
            'name': data['name'],
            'artist': data['artist'],
        }

    def import_lrc_file(self, filepath: str) -> bool:
        """从 LRC 文件导入歌词

        文件名格式: 歌曲名 - 艺术家.lrc
        例: 三体 - 许嵩.lrc

        Args:
            filepath: LRC 文件路径

        Returns:
            是否成功导入
        """
        try:
            filename = os.path.basename(filepath)
            name_parts = filename.replace('.lrc', '').split(' - ')

            if len(name_parts) != 2:
                log.error(f"文件名格式错误: {filename}")
                log.info("正确格式: 歌曲名 - 艺术家.lrc")
                return False

            song_name, artist = name_parts

            with open(filepath, 'r', encoding='utf-8') as f:
                lyrics_content = f.read()

            return self.add_song(song_name, artist, lyrics_content)

        except Exception as e:
            log.error(f"导入 LRC 文件失败: {e}")
            return False

    def import_lrc_directory(self, directory: str) -> int:
        """从目录导入所有 LRC 文件

        Args:
            directory: 包含 LRC 文件的目录

        Returns:
            成功导入的文件数量
        """
        count = 0

        if not os.path.isdir(directory):
            log.error(f"目录不存在: {directory}")
            return 0

        for filename in os.listdir(directory):
            if filename.endswith('.lrc'):
                filepath = os.path.join(directory, filename)
                if self.import_lrc_file(filepath):
                    count += 1

        log.info(f"导入完成: {count} 个 LRC 文件")
        return count

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

    @staticmethod
    def _generate_key(song_name: str, artist: str) -> str:
        """生成唯一键"""
        return f"{song_name.strip()} - {artist.strip()}".lower()

    def get_all_songs(self) -> List[Dict]:
        """获取所有歌曲"""
        songs = []
        for key, data in self.lyrics_db.items():
            songs.append({
                'id': key,
                'name': data['name'],
                'artist': data['artist'],
                'duration': data.get('duration', 0),
                'lyrics_lines': len(data.get('lines', [])),
            })
        return sorted(songs, key=lambda x: x['name'])

    def delete_song(self, song_id: str) -> bool:
        """删除歌曲"""
        if song_id in self.lyrics_db:
            del self.lyrics_db[song_id]
            self._save_db()
            log.info(f"删除歌曲: {song_id}")
            return True
        return False

    def clear_all(self) -> bool:
        """清空所有歌词 (危险操作)"""
        self.lyrics_db.clear()
        self._save_db()
        log.warning("已清空所有歌词")
        return True


# 使用示例
def main():
    """测试本地歌词管理"""
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format='[%(name)s] %(message)s'
    )

    manager = LocalLyricsManager()

    # 示例 1: 手动添加歌词
    print("\n📝 示例 1: 手动添加歌词\n")

    sample_lyrics = """[00:10.00]三体人早已到来
[00:20.00]在黑暗中
[00:30.00]他们不会失败
[00:40.00]因为真理在他们这一方
"""

    if manager.add_song("三体", "许嵩", sample_lyrics, duration=180):
        print("✅ 歌曲已添加\n")
    else:
        print("❌ 添加失败\n")

    # 示例 2: 搜索歌曲
    print("🔍 示例 2: 搜索歌曲\n")

    songs = manager.search_song("三体")
    print(f"找到 {len(songs)} 首歌曲:")
    for song in songs:
        print(f"  - {song['name']} - {song['artist']}")

    # 示例 3: 获取歌词
    print("\n📖 示例 3: 获取歌词\n")

    lyrics = manager.get_lyrics("三体 - 许嵩")
    if lyrics:
        print(f"歌曲: {lyrics['name']} - {lyrics['artist']}")
        print(f"歌词 ({len(lyrics['lines'])} 行):")
        for line in lyrics['lines']:
            minutes = int(line['time'] // 60)
            seconds = line['time'] % 60
            print(f"  [{minutes:02d}:{seconds:05.2f}] {line['text']}")

    # 示例 4: 列出所有歌曲
    print("\n📋 示例 4: 所有歌曲\n")

    all_songs = manager.get_all_songs()
    print(f"总共 {len(all_songs)} 首歌曲:")
    for song in all_songs:
        print(f"  - {song['name']} - {song['artist']} ({song['lyrics_lines']} 行歌词)")


if __name__ == '__main__':
    main()

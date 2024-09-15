import json
import os
import random
import re
import urllib.error
from urllib.parse import urlencode, urlparse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypeAlias
import argparse
from enum import Enum
import datetime
import asyncio

FormattedTime: TypeAlias = str

class IHttpClient:
    """處理 HTTP 請求的介面"""
    
    base_url: str = 'https://ani.gamer.com.tw'

    async def get_request(self, path: str, headers: Dict[str, str], base_url: Optional[str] = None) -> Optional[str]:
        """發送 GET 請求"""
        raise NotImplementedError

    async def post_request(self, path: str, data: str, headers: Dict[str, str], base_url: Optional[str] = None) -> Optional[str]:
        """發送 POST 請求"""
        raise NotImplementedError

    async def get_request_headers(self) -> Dict[str, str]:
        """取得請求標頭"""
        raise NotImplementedError

class HttpClient(IHttpClient):
    """處理 HTTP 請求的類別"""

    @staticmethod
    def hostname(url: str) -> str | None:
        """取得 URL 的主機名稱"""
        return urlparse(url).hostname

    async def get_request(self, path: str, headers: Dict[str, str], base_url: Optional[str] = None) -> Optional[str]:
        url = (base_url if base_url else self.base_url) + path
        request = urllib.request.Request(url, headers=headers, method='GET')

        try:
            with urllib.request.urlopen(request) as response:
                if response.status in [301, 302]:
                    new_location = response.getheader('Location')
                    return await self.get_request(new_location, headers=headers)
                return response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            print(f"HTTPError: {e.code} {e.reason}")
        except urllib.error.URLError as e:
            print(f"URLError: {e.reason}")
        
        return None

    async def post_request(self, path: str, data: str, headers: Dict[str, str], base_url: Optional[str] = None) -> Optional[str]:
        url = (base_url if base_url else self.base_url) + path
        data_encoded = data.encode('utf-8')
        request = urllib.request.Request(url, data=data_encoded, headers=headers, method='POST')

        try:
            with urllib.request.urlopen(request) as response:
                if response.status in [301, 302]:
                    new_location = response.getheader('Location')
                    return await self.post_request(new_location, data=data, headers=headers)
                return response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            print(f"HTTPError: {e.code} {e.reason}")
        except urllib.error.URLError as e:
            print(f"URLError: {e.reason}")
        
        return None

    async def get_request_headers(self) -> Dict[str, str]:
        """取得請求標頭"""
        return {
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
            'Origin': 'https://ani.gamer.com.tw',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
        }
    
@dataclass
class DanmuTimePosition:
    """彈幕的時間和位置資訊"""

    start_time: FormattedTime
    end_time: FormattedTime 
    position: Optional[int]

class DanmuPosition(Enum):
    """彈幕位置的 Enum 類別，表示固定位置彈幕的位置"""

    TOP = "Top"
    BOTTOM = "Bottom"

@dataclass
class RollChannelAssignment:
    """滾動彈幕頻道的分配結果"""

    height: int
    end_time: int

@dataclass
class AnimeInfo:
    """動畫資訊"""

    name: str
    episode: str

@dataclass
class RollDanmu:
    height: int
    color: str

    def to_str(self) -> str:
        """
        生成滾動彈幕的字符串，格式化為 .ass 文件所需的格式。

        1. `Default`: 代表使用的字幕樣式名稱，表示滾動彈幕。
        2. `,,0,0,0,,`: 固定格式的佔位符，表示字幕的層級、起始時間、結束時間、邊距等。
        3. `{{\\move(1920,{self.height},-1000,{self.height})`: 
            - `\\move(x1, y1, x2, y2)` 表示字幕從 `(x1, y1)` 移動到 `(x2, y2)`。
            - 在此例中，字幕從畫面右側的 `1920` 水平方向移動到畫面左側的 `-1000`，並且在垂直位置 `self.height` 保持不變。
        4. `\\1c&H4C{self.color}}`: 
            - 這部分表示字幕的顏色。
            - `&H4C` 是固定值，`{self.color}` 是顏色的十六進位值

        Returns:
            str: 格式化的滾動彈幕字符串
        """
        parts = [
            'Default', ',,0,0,0,,',
            f'{{\\move(1920,{self.height},-1000,{self.height})',
            f'\\1c&H4C{self.color}}}'
        ]
        return "".join(parts)

@dataclass
class FixedPositionDanmu:
    position: DanmuPosition
    y_coordinate: int
    color: str

    def to_str(self) -> str:
        """
        生成固定位置彈幕的字符串，格式化為 .ass 文件所需的格式。

        1. `Default`: 代表使用的字幕樣式名稱
        2. `,,0,0,{self.y_coordinate},,`: 固定格式的佔位符，表示字幕的層級、起始時間、結束時間、垂直位置等。
        3. `{{\\1c&H4C{self.color}}}`:
            - 這部分表示字幕的顏色。
            - `&H4C` 是固定值，`{self.color}` 是顏色的十六進位值

        Returns:
            str: 格式化的固定位置彈幕字符串
        """
        parts = [
            'Default', ',,0,0,',
            str(self.y_coordinate), ',,',
            f'{{\\1c&H4C{self.color}}}'
        ]
        return "".join(parts)
    
@dataclass
class Episode:
    cover: str
    episode: float
    state: int
    videoSn: int

    @classmethod
    def from_dict(cls, org: dict[str, Any]):
        return cls(
            cover = org["cover"],
            episode = org["episode"],
            state = org["state"],
            videoSn = org["videoSn"]
        )

@dataclass
class DanmuHandler:
    """處理彈幕資料和檔案生成的類別"""

    http_client: IHttpClient

    @staticmethod
    def get_ass_template(title="彈幕"):
        return f'''
[Script Info]
; Generated by lekoOwO/Baha-Danmu @ {datetime.datetime.now()}
Title: {title}
ScriptType: v4.00+
Collisions: Normal
PlayResX: 960
PlayResY: 540
Timer: 10.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Sarasa Gothic TC,24,&H66FFFFFF,&H66FFFFFF,&H66000000,&H66000000,1,0,0,0,100,100,0,0,1,2,0,2,20,20,2,136

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''.strip() + "\n"

    async def download_danmu(self, sn: int, output_filepath: str, anime_info: AnimeInfo) -> None:
        """下載彈幕並儲存為 .ass 檔案"""
        headers = await self.http_client.get_request_headers()
        data = urlencode({'sn': str(sn)})
        response = await self.http_client.post_request('/ajax/danmuGet.php', data, headers)

        if not response:
            raise Exception(f'[DanmuHandler] 彈幕下載失敗 (sn: {sn})')
        
        danmu_data: List[Dict[str, Any]] = json.loads(response)
        roll_channels: List[int] = []
        roll_times: List[int] = []

        with open(output_filepath, 'w', encoding='utf8') as output_file:
            output_file.write(self.get_ass_template(title=f"{anime_info.name} [{anime_info.episode}]"))

            for danmu in danmu_data:
                self.write_danmu_line(output_file, danmu, roll_channels, roll_times)

        print(f'彈幕下載完成，檔案: {output_filepath}')

    @classmethod
    def write_danmu_line(cls, output_file: Any, danmu: Dict[str, Any], roll_channels: List[int], roll_times: List[int]) -> None:
        """寫入單行彈幕資料到輸出檔案"""
        output_file.write('Dialogue: 0,')

        danmu_time_position = cls.calculate_time_and_position(danmu, roll_channels, roll_times)

        output_file.write(f'{danmu_time_position.start_time},{danmu_time_position.end_time},')

        if danmu['position'] == 0:  # 滾動彈幕
            assert(isinstance(danmu_time_position.position, int))
            cls.write_roll_danmu(output_file, danmu, danmu_time_position.position)
        elif danmu['position'] == 1:  # 上方彈幕
            cls.write_fixed_position_danmu(output_file, danmu, DanmuPosition.TOP, 800)
        else:  # 下方彈幕
            cls.write_fixed_position_danmu(output_file, danmu, DanmuPosition.BOTTOM, 200)

        output_file.write(danmu['text'].replace("\n", " ") + '\n')

    @classmethod
    def calculate_time_and_position(cls, danmu: Dict[str, Any], roll_channels: List[int], roll_times: List[int]) -> DanmuTimePosition:
        """計算彈幕顯示的起始時間、結束時間及位置"""
        start_time = int(danmu['time'] / 10)
        match danmu['position']:
            case 0:
                start_time -= 7 # 滾動彈幕提前 0.7 秒出現
                assignment = cls.assign_roll_channel(danmu, roll_channels, roll_times, start_time)
                position = assignment.height
                end_time = assignment.end_time
            case _: # 上方或下方彈幕
                end_time = start_time + 5
                position = None

        hundred_ms = danmu['time'] % 10
        formatted_start_time = cls.format_time(start_time, hundred_ms)
        formatted_end_time = cls.format_time(end_time, hundred_ms)

        return DanmuTimePosition(formatted_start_time, formatted_end_time, position)

    @staticmethod
    def assign_roll_channel(danmu: Dict[str, Any], roll_channels: List[int], roll_times: List[int], start_time: int) -> RollChannelAssignment:
        """為滾動彈幕分配可用的頻道位置"""
        height = 0
        end_time = 0

        for i, channel_time in enumerate(roll_channels):
            if channel_time <= danmu['time']:
                height = i * 54 + 27
                roll_channels[i] = danmu['time'] + (len(danmu['text']) * roll_times[i]) / 8 + 1
                end_time = start_time + roll_times[i]
                break

        if height == 0:
            roll_channels.append(0)
            roll_times.append(random.randint(30, 30))
            roll_channels[-1] = danmu['time'] + (len(danmu['text']) * roll_times[-1]) / 8 + 1
            height = len(roll_channels) * 54 - 27
            end_time = start_time + roll_times[-1]

        return RollChannelAssignment(height, end_time)

    @staticmethod
    def format_time(seconds: int, hundred_ms: int) -> FormattedTime:
        """將時間格式化為 hh:mm:ss.00 的格式"""
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f'{h:d}:{m:02d}:{s:02d}.{hundred_ms:d}0'
    
    @staticmethod
    def rgb_to_bgr(rgb: str) -> str:
        """將 RGB 顏色值轉換為 BGR 顏色值"""
        if len(rgb) == 6:
            return rgb[4:] + rgb[2:4] + rgb[:2]
        elif len(rgb) == 8:
            return rgb[6:] + rgb[4:6] + rgb[2:4] + rgb[:2]
        else:
            raise ValueError(f'無效的 RGB 顏色值: {rgb}')

    @classmethod
    def write_roll_danmu(cls, output_file: Any, danmu: Dict[str, Any], height: int) -> None:
        """寫入滾動彈幕"""
        danmu_roll = RollDanmu(height=height, color=cls.rgb_to_bgr(danmu["color"][1:])) # [1:] 用於去掉顏色值的前面的 # 號
        output_file.write(danmu_roll.to_str())

    @classmethod
    def write_fixed_position_danmu(cls, output_file: Any, danmu: Dict[str, Any], position: DanmuPosition, y_coordinate: int) -> None:
        """寫入固定位置彈幕（上方或下方）"""
        danmu_fixed = FixedPositionDanmu(position=position, y_coordinate=y_coordinate, color=cls.rgb_to_bgr(danmu["color"][1:])) # [1:] 用於去掉顏色值的前面的 # 號
        output_file.write(danmu_fixed.to_str())

@dataclass
class AnimeInfoFetcher:
    """處理動畫資訊擷取的類別"""

    http_client: IHttpClient

    async def get_anime_info(self, sn: int) -> AnimeInfo:
        """取得動畫名稱和集數資訊"""
        headers = await self.http_client.get_request_headers()
        response = await self.http_client.get_request(f'/animeVideo.php?sn={sn}', headers)

        if not response:
            raise Exception(f'[AnimeInfoFetcher] 獲取資訊失敗 (sn: {sn})')
        
        # Get title tag
        title_tag = re.search(r'<title>(.+)</title>', response)
        title = title_tag.group(1) if title_tag else None

        if not title:
            raise Exception(f'[AnimeInfoFetcher] 無法獲取動畫名稱和集數 (sn: {sn})')
        
        # Get anime name and episode
        m = re.search(r"^(.+?)\s\[(.+)\].+?$", title)
        anime_name = m.group(1) if m else None
        episode = m.group(2) if m else None

        if not anime_name or not episode:
            raise Exception(f'[AnimeInfoFetcher] 無法獲取動畫名稱和集數 (sn: {sn})')

        return AnimeInfo(name=anime_name, episode=episode)
    
    async def get_anime_episodes(self, sn: int) -> dict[str, list[Episode]]:
        """取得動畫的所有集數資訊"""
        headers = await self.http_client.get_request_headers()
        response = await self.http_client.get_request(f'/anime/v1/video.php?videoSn={sn}', headers, base_url='https://api.gamer.com.tw')

        if not response:
            raise Exception(f'[AnimeInfoFetcher] 獲取資訊失敗 (sn: {sn})')
        
        data = json.loads(response)
        episodes: dict[str, list[dict]] = data["data"]["anime"]["episodes"]
        return {key: [Episode.from_dict(e) for e in value] for key, value in episodes.items()}

class DanmuDownloader:
    """處理彈幕下載的類別，統籌管理 DanmuHandler 和 AnimeInfoFetcher"""
    _http_client: IHttpClient
    danmu_handler: DanmuHandler
    anime_info_fetcher: AnimeInfoFetcher

    def __init__(self, http_client: Optional[IHttpClient] = None):
        self._http_client = http_client if http_client else HttpClient()
        self.danmu_handler = DanmuHandler(self._http_client)
        self.anime_info_fetcher = AnimeInfoFetcher(self._http_client)

    async def download_comments(self, sn: int, output_dir: str, filename_format: str) -> None:
        """下載彈幕並儲存為檔案"""
        anime_info = await self.anime_info_fetcher.get_anime_info(sn)
        output_filepath = os.path.join(output_dir, filename_format.format(anime_name=anime_info.name, episode=anime_info.episode))
        await self.danmu_handler.download_danmu(sn, output_filepath, anime_info)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="下載彈幕並儲存為檔案")
    parser.add_argument("-n", '--sn', type=int, help="動畫 SN", required=True)
    parser.add_argument("-o", '--output_dir', type=str, help="輸出目錄", required=True)
    parser.add_argument("-f", '--filename_format', type=str, default="{anime_name}[{episode}].ass", help=r"檔案名稱格式 (預設: {anime_name}[{episode}].ass)")

    args = parser.parse_args()

    downloader = DanmuDownloader()
    asyncio.run(downloader.download_comments(args.sn, args.output_dir, args.filename_format))

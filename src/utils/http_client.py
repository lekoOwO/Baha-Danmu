from .danmu import IHttpClient
import httpx
from typing import Dict, Optional

class AsyncHttpClient(IHttpClient):
    """使用 httpx 的非同步 HTTP 客戶端實現"""

    async def get_request(self, path: str, headers: Dict[str, str], base_url: Optional[str] = None) -> Optional[str]:
        url = httpx.URL(base_url if base_url else self.base_url).join(path)

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if response.status_code in [301, 302]:
                new_location = response.headers.get('Location')
                return await self.get_request(new_location, headers=headers)

            if response.status_code != 200:
                return None

            return response.text

    async def post_request(self, path: str, data: str, headers: Dict[str, str], base_url: Optional[str] = None) -> Optional[str]:
        url = httpx.URL(base_url if base_url else self.base_url).join(path)

        async with httpx.AsyncClient() as client:
            response = await client.post(url, content=data, headers=headers)

            if response.status_code in [301, 302]:
                new_location = response.headers.get('Location')
                return await self.post_request(new_location, data=data, headers=headers)

            if response.status_code != 200:
                return None

            return response.text

    async def get_request_headers(self) -> Dict[str, str]:
        """取得請求標頭"""
        return {
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
            'Origin': 'https://ani.gamer.com.tw',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
        }

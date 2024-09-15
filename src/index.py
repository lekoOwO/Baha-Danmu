import asyncio
from dataclasses import dataclass
from typing import Any, Coroutine
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse 
import utils
import pathlib

app = FastAPI()
app.mount("/static", StaticFiles(directory=utils.env.STATIC_DIR), name="static")

router = APIRouter(prefix="/api")

@app.get("/")
async def GET_index():
    return FileResponse(utils.env.STATIC_DIR / "index.html")

@router.get("/lsInitialPath")
async def GET_ls_initial_path():
    return utils.env.VIDEO_BASE_DIR.as_posix()

@router.get("/ls")
async def GET_ls(path: str):
    if not utils.path.is_valid_video_path(path):
        raise HTTPException(status_code=404, detail="Invalid path")
    
    return utils.path.ls(path)  

@router.get("/episodes")
async def GET_episodes(sn: int):
    anime_info_fetcher = utils.danmu.AnimeInfoFetcher(
        utils.danmu.HttpClient(),
    )
    return anime_info_fetcher.get_anime_episodes(sn)

@dataclass
class DownloadBody:
    video_path: str
    sn: int

@router.post("/download")
async def POST_download(data: list[DownloadBody]):
    for item in data:
        if not utils.path.is_valid_video_path(item.video_path):
            raise HTTPException(status_code=404, detail="Invalid path")

    http_client = utils.http_client.AsyncHttpClient()
    downloader = utils.danmu.DanmuDownloader(http_client)

    async def download_item(item: DownloadBody) -> bool:
        try:
            subtitle_path = pathlib.Path(item.video_path).with_suffix(".danmu.ass").absolute()
            await downloader.download_comments(item.sn, subtitle_path.parent.as_posix(), subtitle_path.name)
            return True
        except:
            return False
        
    tasks = [download_item(item) for item in data]
    result = await asyncio.gather(*tasks)

    return result

@router.post("/episodeDetection")
async def POST_episodeDetection(filenames: list[str]):
    return await utils.episode_detection.episode_detection(filenames)

app.include_router(router)
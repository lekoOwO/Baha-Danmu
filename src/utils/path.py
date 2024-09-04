from dataclasses import dataclass
from typing import Optional
from .env import VIDEO_BASE_DIR
from pathlib import Path

@dataclass
class MyPath:
    path: str
    is_dir: bool
    size: Optional[int]

    @classmethod
    def from_path(cls, path: str | Path):
        path = Path(path).absolute()
        return cls(path.as_posix(), path.is_dir(), path.stat().st_size if path.is_file() else None)

def is_valid_video_path(video_path: str | Path) -> bool:
    video_path = Path(video_path).absolute()
    return video_path.exists() and \
        ((VIDEO_BASE_DIR in video_path.parents) or VIDEO_BASE_DIR == video_path)

def ls(path: str | Path) -> list[MyPath]:
    path = Path(path).absolute()
    return [MyPath.from_path(p) for p in path.iterdir()]
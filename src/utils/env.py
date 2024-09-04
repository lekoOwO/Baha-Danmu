import os
import pathlib

VIDEO_BASE_DIR = pathlib.Path(os.getenv('VIDEO_BASE_DIR', '/data/videos')).absolute()
assert(VIDEO_BASE_DIR.exists())

STATIC_DIR = pathlib.Path("src/static").absolute()
assert(STATIC_DIR.exists())

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
assert(GEMINI_API_KEY is not None)
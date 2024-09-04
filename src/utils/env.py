import os
import pathlib

VIDEO_BASE_DIR = pathlib.Path(os.getenv('VIDEO_BASE_DIR', '/data/videos')).absolute()
assert(VIDEO_BASE_DIR.exists())

# Get this file's parent directory
SRC_DIR = pathlib.Path(__file__).parent.parent.absolute()
STATIC_DIR = (SRC_DIR / "static").absolute()
assert(STATIC_DIR.exists())

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
assert(GEMINI_API_KEY is not None)
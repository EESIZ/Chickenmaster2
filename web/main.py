"""uvicorn 진입점"""

import sys
import os

# src를 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from web.app import create_app
from web.config import HOST, PORT

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web.main:app", host=HOST, port=PORT, reload=True)

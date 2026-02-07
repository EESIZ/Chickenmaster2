"""웹 서버 설정"""

import os


# 서버
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# 데이터
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
EVENTS_CSV = os.path.join(DATA_DIR, "events.csv")
DB_PATH = os.path.join(DATA_DIR, "chickenmaster.db")

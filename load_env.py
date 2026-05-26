"""
.env 파일에서 환경변수를 로드하는 유틸리티.
외부 패키지(dotenv) 없이 표준 라이브러리만 사용.
"""

import os
from pathlib import Path


def load_dotenv(env_path=None):
    """Load .env file into os.environ (skip if already set)."""
    if env_path is None:
        env_path = Path(__file__).parent / ".env"
    else:
        env_path = Path(env_path)

    if not env_path.exists():
        return

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key and not os.environ.get(key):
                os.environ[key] = value

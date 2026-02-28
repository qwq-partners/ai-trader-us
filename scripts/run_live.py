#!/usr/bin/env python3
"""
AI Trader US - Live Trading Entry Point

Usage:
    python scripts/run_live.py --config config/default.yml --log-level DEBUG
    python scripts/run_live.py  # 기본 설정
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from src.utils.logger import setup_logger
from src.core.config import AppConfig
from src.core.live_engine import LiveEngine
from src.api.server import APIServer


PID_FILE = Path("/tmp/ai_trader_us_live.pid")


def write_pid():
    PID_FILE.write_text(str(os.getpid()))


def remove_pid():
    if PID_FILE.exists():
        PID_FILE.unlink()


async def main(config_path: str, log_level: str):
    """라이브 트레이딩 실행"""
    setup_logger(level=log_level, log_file=str(project_root / "data" / "logs" / "live.log"))

    config = AppConfig.load(config_path)
    engine = LiveEngine(config)
    api_server = APIServer(engine, port=8081)

    try:
        write_pid()
        await engine.initialize()
        await asyncio.gather(
            engine.run(),
            api_server.run(),
        )
    except KeyboardInterrupt:
        pass
    except Exception as e:
        from loguru import logger
        logger.exception(f"라이브 엔진 치명적 오류: {e}")
    finally:
        await engine.shutdown()
        await api_server.stop()
        remove_pid()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Trader US - Live Trading")
    parser.add_argument(
        "--config", "-c",
        default=str(project_root / "config" / "default.yml"),
        help="설정 파일 경로 (default: config/default.yml)",
    )
    parser.add_argument(
        "--log-level", "-l",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="로그 레벨 (default: INFO)",
    )

    args = parser.parse_args()

    # logs 디렉토리 생성
    (project_root / "data" / "logs").mkdir(parents=True, exist_ok=True)

    asyncio.run(main(args.config, args.log_level))

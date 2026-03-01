"""
AI Trader US - KIS API Token Manager

KIS OAuth2 Access Token 발급/캐싱/자동갱신.
v2 kis_token_manager.py 기반, WebSocket Approval Key 제거 (불필요).

토큰:
- Access Token (REST API용) - 24시간 유효
- 파일 캐싱으로 재시작 시에도 토큰 유지
- 만료 5분 전 자동 갱신
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import aiohttp
from loguru import logger


class KISTokenManager:
    """
    KIS API 토큰 매니저 (싱글톤)

    환경변수:
        KIS_APPKEY / KIS_APP_KEY
        KIS_APPSECRET / KIS_SECRET_KEY
        KIS_ENV: prod (실전) / dev (모의투자)
    """

    _instance: Optional["KISTokenManager"] = None
    _lock: Optional[asyncio.Lock] = None

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        return cls._lock

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        self._initialized = True

        # API 설정
        self._app_key = os.getenv("KIS_APPKEY", "") or os.getenv("KIS_APP_KEY", "")
        self._app_secret = os.getenv("KIS_APPSECRET", "") or os.getenv("KIS_SECRET_KEY", "")
        self._env = os.getenv("KIS_ENV", "prod")

        # 토큰
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

        # HTTP 세션 (lazy init)
        self._session: Optional[aiohttp.ClientSession] = None

        # 캐시 경로
        cache_dir = Path(os.path.expanduser("~/.cache/ai_trader"))
        cache_dir.mkdir(parents=True, exist_ok=True)
        self._token_cache_path = cache_dir / f"kis_token_{self._env}.json"

        # API URL
        if self._env == "prod":
            self._base_url = "https://openapi.koreainvestment.com:9443"
        else:
            self._base_url = "https://openapivts.koreainvestment.com:29443"

        # 캐시된 토큰 로드
        self._load_cached_token()

        logger.debug(f"KISTokenManager 초기화: env={self._env}")

    # ============================================================
    # 공개 인터페이스
    # ============================================================

    async def get_access_token(self) -> Optional[str]:
        """REST API용 Access Token 반환 (자동 갱신)"""
        async with self._get_lock():
            if self._is_token_valid():
                return self._access_token

            success = await self._issue_access_token()
            return self._access_token if success else None

    async def refresh(self) -> bool:
        """토큰 강제 갱신"""
        async with self._get_lock():
            return await self._issue_access_token()

    def invalidate(self):
        """토큰 무효화"""
        self._access_token = None
        self._token_expires_at = None
        logger.info("KIS 토큰 무효화됨")

    @property
    def app_key(self) -> str:
        return self._app_key

    @property
    def app_secret(self) -> str:
        return self._app_secret

    @property
    def env(self) -> str:
        return self._env

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def token_info(self) -> dict:
        return {
            "access_token_valid": self._is_token_valid(),
            "token_expires_at": self._token_expires_at.isoformat() if self._token_expires_at else None,
            "env": self._env,
        }

    # ============================================================
    # 토큰 유효성 검사
    # ============================================================

    def _is_token_valid(self) -> bool:
        if not self._access_token or not self._token_expires_at:
            return False
        return datetime.now() < self._token_expires_at - timedelta(minutes=5)

    # ============================================================
    # 토큰 발급
    # ============================================================

    async def _ensure_session(self):
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)

    async def _issue_access_token(self) -> bool:
        try:
            await self._ensure_session()

            url = f"{self._base_url}/oauth2/tokenP"
            body = {
                "grant_type": "client_credentials",
                "appkey": self._app_key,
                "appsecret": self._app_secret,
            }

            async with self._session.post(url, json=body) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"[TokenManager] Access Token 발급 실패: {resp.status} - {text}")
                    return False

                data = await resp.json()

                self._access_token = data.get("access_token")
                expires_in = int(data.get("expires_in", 86400))
                self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

                await self._save_token_cache()

                logger.info(
                    f"[TokenManager] Access Token 발급 완료 "
                    f"(만료: {self._token_expires_at.strftime('%Y-%m-%d %H:%M:%S')})"
                )
                return True

        except Exception as e:
            logger.exception(f"[TokenManager] Access Token 발급 오류: {e}")
            return False

    # ============================================================
    # 캐시 관리
    # ============================================================

    def _load_cached_token(self):
        try:
            if self._token_cache_path.exists():
                with open(self._token_cache_path, 'r') as f:
                    cache = json.load(f)

                expires_at_str = cache.get("expires_at")
                if expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str)
                    if datetime.now() < expires_at - timedelta(minutes=5):
                        self._access_token = cache.get("token")
                        self._token_expires_at = expires_at
                        logger.debug("[TokenManager] 캐시된 Access Token 로드 완료")
        except Exception as e:
            logger.debug(f"[TokenManager] Access Token 캐시 로드 실패: {e}")

    async def _save_token_cache(self):
        try:
            cache = {
                "token": self._access_token,
                "expires_at": self._token_expires_at.isoformat() if self._token_expires_at else None,
                "updated_at": datetime.now().isoformat(),
            }
            await asyncio.to_thread(self._write_json, self._token_cache_path, cache)
        except Exception as e:
            logger.debug(f"[TokenManager] Access Token 캐시 저장 실패: {e}")

    @staticmethod
    def _write_json(path, data):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    # ============================================================
    # 정리
    # ============================================================

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None


# ============================================================
# 전역 인스턴스 접근
# ============================================================

_token_manager: Optional[KISTokenManager] = None


def get_token_manager() -> KISTokenManager:
    """전역 토큰 매니저 인스턴스"""
    global _token_manager
    if _token_manager is None:
        _token_manager = KISTokenManager()
    return _token_manager


async def get_access_token() -> Optional[str]:
    """Access Token 획득 (편의 함수)"""
    return await get_token_manager().get_access_token()

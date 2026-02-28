"""
AI Trader US - 텔레그램 알림 유틸리티

KR 봇과 동일 토큰 사용, [US] 접두사로 구분.
"""

import os
import asyncio
from typing import Optional, List
import aiohttp
from loguru import logger


class TelegramNotifier:
    """텔레그램 알림 발송기"""

    MAX_MESSAGE_LENGTH = 4096

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self._session: Optional[aiohttp.ClientSession] = None

        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다")
        if not self.chat_id:
            logger.warning("TELEGRAM_CHAT_ID가 설정되지 않았습니다")

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def send_message(
        self,
        text: str,
        parse_mode: str = "HTML",
        disable_notification: bool = False,
    ) -> bool:
        """텔레그램 메시지 발송"""
        if not self.is_configured:
            return False

        # 긴 메시지 분할
        if len(text) > self.MAX_MESSAGE_LENGTH:
            return await self._send_chunks(text, parse_mode, disable_notification)

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification,
        }

        try:
            session = await self._get_session()
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    return True
                data = await resp.json()
                logger.error(f"텔레그램 발송 실패: {data}")
                return False
        except Exception as e:
            logger.error(f"텔레그램 발송 오류: {e}")
            return False

    async def send_alert(
        self,
        text: str,
        parse_mode: str = "HTML",
        max_retries: int = 2,
    ) -> bool:
        """알림 발송 (재시도 포함)"""
        for attempt in range(1 + max_retries):
            if await self.send_message(text, parse_mode):
                return True
            if attempt < max_retries:
                await asyncio.sleep(1)
        logger.error(f"텔레그램 알림 {1 + max_retries}회 시도 모두 실패")
        return False

    async def _send_chunks(
        self, text: str, parse_mode: str, disable_notification: bool,
    ) -> bool:
        """긴 메시지 분할 발송"""
        max_len = self.MAX_MESSAGE_LENGTH - 100
        chunks: List[str] = []
        current = ""

        for line in text.split("\n"):
            if len(line) > max_len:
                if current:
                    chunks.append(current.strip())
                    current = ""
                for i in range(0, len(line), max_len):
                    chunks.append(line[i:i + max_len])
                continue
            if len(current) + len(line) + 1 > max_len:
                if current:
                    chunks.append(current.strip())
                current = line + "\n"
            else:
                current += line + "\n"

        if current.strip():
            chunks.append(current.strip())

        success = True
        for chunk in chunks:
            if not await self.send_message(chunk, parse_mode, disable_notification):
                success = False
            await asyncio.sleep(0.5)
        return success

    async def close(self):
        """세션 종료"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None


# ── 모듈 레벨 편의 함수 ──────────────────────────────────────────────────────

_notifier: Optional[TelegramNotifier] = None


def get_notifier() -> TelegramNotifier:
    """전역 TelegramNotifier 인스턴스"""
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier()
    return _notifier


async def send_alert(text: str, **kwargs) -> bool:
    """모듈 레벨 알림 발송"""
    return await get_notifier().send_alert(text, **kwargs)

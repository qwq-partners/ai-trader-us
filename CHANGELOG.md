# Changelog

## 2026-02-28 — Live Trading 테스트 셋업

**신규 파일:**
- `src/core/live_engine.py` — 라이브 트레이딩 엔진 (6개 비동기 태스크: 스크리닝/청산/동기화/주문체크/EOD/하트비트)
- `src/execution/broker/kis_us_broker.py` — KIS 해외주식 브로커 (aiohttp, rate limiter, 토큰 자동갱신)
- `src/execution/broker/alpaca_async_broker.py` — AsyncAlpacaBroker (동기 AlpacaBroker를 asyncio.to_thread로 래핑, yfinance 시세 fallback)
- `src/utils/kis_auth.py` — KIS OAuth2 토큰 매니저 (싱글톤, 파일 캐싱, 자동갱신)
- `src/utils/trade_journal.py` — CSV 기반 거래/주문 저널
- `scripts/run_live.py` — 라이브 트레이딩 엔트리포인트
- `scripts/test_live.py` — 라이브 엔진 1사이클 테스트 (--dry-run 기본, --symbols 지정 가능)

**변경:**
- `src/core/live_engine.py` — 하드코딩된 KISUSBroker() → `_create_broker()` 팩토리 (alpaca_paper | kis)
- `config/default.yml` — live 섹션 추가 (broker=alpaca_paper, 테스트용 단축 간격)

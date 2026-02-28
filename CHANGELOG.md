# Changelog

## 2026-02-28 — HTTP API 서버 추가 (Phase 1)

**API 서버 (포트 8081):**
- `src/api/server.py`: aiohttp 기반 HTTP API 서버 신규 추가
  - `GET /health` — 헬스체크
  - `GET /api/us/status` — 엔진 상태 (running, session, version)
  - `GET /api/us/portfolio` — 포트폴리오 요약 (cash, total_value, daily_pnl)
  - `GET /api/us/positions` — 보유 포지션 목록 (Decimal→float 변환)
  - `GET /api/us/signals` — 최근 50건 시그널 (in-memory deque)
  - `GET /api/us/orders` — 미체결 주문 목록
  - CORS 미들웨어 (`Access-Control-Allow-Origin: *`)
- `src/core/live_engine.py`: `recent_signals: deque(maxlen=50)` 추가, `_process_signal()` 성공 시 시그널 기록
- `scripts/run_live.py`: APIServer를 `asyncio.gather`로 LiveEngine과 병렬 실행

## 2026-02-28 — US 장 독립 운영 + 코드리뷰 + 서비스 등록 + 버그 수정

**US 장 독립 운영 정합성 (commit `f84c18d`):**
- config: screening_interval_min 5→30분, max_screen_symbols 20→100 (운영값)
- live_engine: 유니버스 랜덤 셔플 추가 (매 사이클, 전 903종목 순환 커버)
- session.py: next_trading_day(), prev_trading_day() 위임 메서드 추가
- 검증: NYSE 캘린더(XNYS) 기반 — 3/2(한국 대체공휴일)도 US 거래일 ✅

**버그 수정 (commit `3884055`):**
- P1: 빈 `order_no` 충돌 — KIS ODNO="" 시 `local-{uuid}` 폴백 키 사용 (매수/매도)
- P2: `pending` 상태 주문 타임아웃 미작동 — 폴백키 5분 / 정상 pending 10분 경고

**인프라 (commit `b8275fd`):**
- S&P 500/400 Wikipedia 403 차단 수정 — requests User-Agent + 로컬 캐시(7일 만료)
- `data/universe/sp500.txt` (503종목), `sp400.txt` (400종목)
- `.gitignore`: `/data/` 루트 전용으로 수정 (src/data/ 오배제 수정)
- `requirements.txt`: lxml 추가

**서비스 (외부):**
- `ai-trader-us.service` systemd 서비스 등록 + enabled (부팅 자동 시작)
- 테스트 결과: Alpaca Paper 브로커 연결 ✅, 5전략 로드 ✅, 유니버스 903종목 ✅

---

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

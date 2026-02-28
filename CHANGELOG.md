# Changelog

## 2026-02-28 — 2차 코드리뷰 수정 (5건)

- `live_engine.py`: 전량 매도 체결 시 `positions.pop()` 누락 → 반복 매도 방지
- `live_engine.py`: 일일 손실 경고 `-2.0%` 하드코딩 → `daily_max_loss_pct * 0.67` 동적 계산
- `live_engine.py`: `_ws_last_exit_check` 포지션 청산 시 정리 로직 추가 (메모리 누수 방지)
- `live_engine.py`: `_eod_close_loop` `date.today()` → `self.session.now_et().date()` (KST/ET 불일치 수정)
- `live_engine.py`: `_heartbeat_loop` `date.today()` → `self.session.now_et().date()` (동일)

---

## 2026-02-28 — P0-P1 종합 버그 수정 (코드리뷰 19건)

**P0 (치명적) 8건:**
- `live_engine.py`: 매도 체결 시 `daily_pnl` 미갱신 + `reset_daily()` 미호출 → 일일 손실 한도 무력화 수정
- `live_engine.py`: `_sync_portfolio`에서 pending 종목 무시 없이 포지션 제거 → pending 체크 추가
- `live_engine.py`: 주문 취소 실패 시 pending 영구 블로킹 → 강제 해제 추가
- `live_engine.py`: `asyncio.gather(return_exceptions=True)` → 태스크 모니터링 루프 (크래시 감지 + 재시작)
- `live_engine.py`: 1주 포지션 분할매도 시 전량 청산 → ratio < 1.0이면 스킵
- `base.py`: `Decimal(str(price)) if price else None` falsy 패턴 → `is not None` 수정
- `health_monitor.py`: `daily_loss_limit_pct` → `daily_max_loss_pct` 속성명 수정
- `live_engine.py`: 히스토리 다운로드 365일 → 500일 (SEPA MA200 충분한 마진)

**P1 (중요) 8건:**
- `live_engine.py`: 매수 체결/sync 시 `highest_price` 미초기화 → 트레일링 스탑 활성화
- `live_engine.py`: 기존 포지션 exchange 캐시 미갱신 수정
- `live_engine.py`: EOD 청산 지정가 → 시장가 전환 (미체결 위험 제거)
- `live_engine.py`: `_execute_exit` pending 체크 추가 (레이스 컨디션 방지)
- `live_engine.py`: `_check_orders` KST/ET 날짜 불일치 → ET 날짜로 조회
- `live_engine.py`: `_indicator_cache.clear()` → 보유 종목 캐시 보존
- `live_engine.py`: 시장가 폴백 실패 시 텔레그램 긴급 알림 추가
- `live_engine.py` + `config/default.yml`: `max_price: 200.0` 고가 종목 필터 추가

**P1 (기타) 3건:**
- `types.py`: RiskConfig 기본값을 실제 config에 맞게 조정 (max_positions=4, base_position_pct=25.0 등)
- `exit_manager.py`: 분할매도 85% 설계 의도 주석 추가
- P1-11 (SEPA RS Rating): sepa.py에서 미사용 확인 → 코드 변경 불필요

**수정 파일**: `live_engine.py`, `types.py`, `base.py`, `health_monitor.py`, `exit_manager.py`, `config/default.yml`

---

## 2026-02-28 — 손절 매도 시장가 폴백 + 시세 폴링 강화

**매도 타임아웃 분리 + 시장가 폴백 (`src/core/live_engine.py`):**
- 매수 미체결: 10분 → 자동 취소 (기존과 동일)
- 매도 미체결: **2분 → 취소 → 시장가 폴백 재주문** (손절 지연 방지)
- 시장가 폴백 주문도 pending 추적에 등록

**WS/REST 이중화 강화:**
- `_exit_check_loop`: WS 연결 시 60초, **WS 미연결 시 30초**로 폴링 단축
- Heartbeat에 `ws=connected/disconnected` 상태 표시 추가

---

## 2026-02-28 — 코드리뷰 P0/P1/P2 수정

**P0 (치명적):**
- `live_engine.py`: 매도 체결 시 `pos` 미초기화 → NameError 크래시 수정 (else 분기 최상단으로 이동)
- `live_engine.py`: 매도 주문가 0일 때 시장가 오발주 방지 가드 추가
- `live_engine.py`: `_sync_portfolio`에서 pending 종목 수량 업데이트 스킵 (부분매도 경쟁 방지)

**P1 (중요):**
- `exit_manager.py`: `highest_price` falsy 패턴 수정 (`and` → `is not None and`)
- `live_engine.py`: 지정가 산출 `float` → `Decimal` 정밀 계산으로 전환
- `live_engine.py`: `cancel_order` qty=0 → 원주문 수량 전달로 수정
- `finnhub_ws.py`: `_connect_and_listen` finally에서 `_cleanup` 중복 호출 제거 (인라인 정리)

**P2 (경미):**
- `live_engine.py`: `import time` 함수 내부 → 최상단으로 이동
- `finnhub_ws.py`: 재연결 성공 후 백오프 기본값 리셋 추가

---

## 2026-02-28 — KIS 실전 전환 + Finnhub WS + 지정가 주문 + 엔진 강화

**KIS 실전 브로커 전환:**
- `config/default.yml`: broker `alpaca_paper` → `kis`, env `dev` → `prod`
- `.env`: `KIS_ENV=dev` → `KIS_ENV=prod`
- 포지션 사이징: base 10→25%, max 15→35%, max_positions 10→4 ($700 자본 기준)
- 전략: ORB/VWAP 비활성화, Momentum/SEPA/EarningsDrift 유지
- 스크리닝 주기: 30분→15분, initial_capital: $100K→$700, min_position_value: $1000→$50

**지정가 주문 로직 (`src/core/live_engine.py`):**
- 매수: `price=0` (시장가) → `price=round(price*1.002, 2)` (현재가+0.2% 지정가)
- 매도: `price=0` → `price=round(position.current_price, 2)` (현재가 지정가)
- 주문 기록 order_type: `market` → `limit`

**미체결 주문 자동 취소 + 부분매도 수량 동기화:**
- `_check_orders()`: 미체결 10분 경과 시 `broker.cancel_order()` 자동 호출
  - 취소 성공 시 `_pending_orders`, `_pending_symbols` 정리
  - local-xxx 폴백 주문은 기존 5분 타임아웃 유지
- `_on_order_filled()`: sell 체결 시 `filled_qty < pos.quantity`면 수량 차감 (부분매도)

**Finnhub WebSocket 실시간 시세:**
- 신규 `src/data/feeds/finnhub_ws.py`: FinnhubWSFeed 클래스
  - aiohttp ws_connect, 지수 백오프 재연결 (5s→120s)
  - 종목당 마지막 체결가만 사용 (중복 콜백 방지)
  - subscribe/unsubscribe 동적 관리
- `live_engine.py` 통합:
  - `_on_ws_price()`: 실시간 가격 갱신 + 즉시 exit 체크 (종목당 10초 스로틀)
  - `_check_exits()`: WS 연결 시 REST 가격 조회 스킵, 미연결 시 폴백
  - 매수 체결 시 subscribe, 포지션 청산 시 unsubscribe
  - 7번째 태스크로 Finnhub WS 추가

**ExitManager falsy 패턴 수정 (`src/strategies/exit_manager.py`):**
- L97: `if atr and avg_price > 0` → `if atr is not None and atr > 0 and avg_price > 0`
- atr=0.0일 때 False 처리 방지

---

## 2026-03-03 — 대시보드 TEST 배지용 상태 API 확장

**commit `f74c1aa`**

- `src/api/server.py`: `GET /api/us/status` 응답에 필드 3개 추가
  - `"broker"`: 현재 브로커명 (e.g. `"alpaca_paper"`)
  - `"env"`: 운영 환경 (`"dev"` | `"prod"`)
  - `"paper_trading"`: 모의거래 여부 (`true` | `false`)
- 이 필드를 기반으로 ai-trader-v2 대시보드가 TEST/모의 배지 자동 표시
- KIS 실계좌 전환 시 `env: "prod"` → 배지 자동 제거 (코드 변경 불필요)

```json
// 현재 응답 예시
{
  "running": true,
  "session": "closed",
  "broker": "alpaca_paper",
  "env": "dev",
  "paper_trading": true
}
```

---

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

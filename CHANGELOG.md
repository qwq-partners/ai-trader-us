# Changelog

## [2026-03-01] 포트폴리오 동기화 버그 수정 — commit `9e89d58`

### Bug 1: avg_price KRW 오계산 (kis_us_broker.py)
- **원인**: `WCRC_FRCR_DVSN_CD=02`(원화 모드) → `PCH_AMT`가 KRW 총매입금액으로 반환됨
  - 예: NVDA 1주 $180 구매 → `PCH_AMT` ≈ 252,000(원) → avg_price=252,000로 오입력
- **수정**: `EVLU_PFLS_RT1`(손익률%) + `OVRS_NOW_PRIC1`(현재가 USD)로 역산
  - `avg_price = current_price / (1 + pnl_pct/100)` — 통화 설정 무관, 항상 USD 주당가
  - `get_positions()` + `get_balance()` 양쪽 모두 수정

### Bug 2: highest_price 재시작 시 trailing stop 고점 리셋
- **원인**: 재시작 후 `highest_price = current_price`로 초기화 → 기존 고점 유실
- **수정**: `~/.cache/ai_trader_us/highest_prices.json` 영속화
  - `_save_highest_prices()`: `_sync_portfolio()` 매 30초 호출 시 자동 저장
  - `_load_highest_prices()`: 재시작 시 로드 → `max(cached, current_price)` 복원
  - 포지션 청산 시 다음 save 사이클에서 자동 제거

---

## [2026-03-01] _watchlist_loop — 상위 25 + 보유 포지션 Finviz 실시간 모니터링 — commit `d62aeab`

### 배경
- `_screener_loop(60분)` / `_screening_loop(15분)` 갭이 너무 커서 강한 모멘텀 기회를 놓침
- 보유 포지션의 장중 모멘텀 급락을 즉시 감지하지 못함

### 구현
- 새 태스크: `_watchlist_loop(5분 주기)`, 총 태스크 9개 → **10개**
  - 대상: StockScreener 상위 25 + 보유 포지션 (배치 호출)
  - Finviz `get_intraday_scan()` TTL=5분 캐시 재사용
- **보유 포지션 모니터링**: `ms < 25 AND perf_1h ≤ -2.5%` → `_check_exits()` 즉시
- **상위 후보 즉시 평가**: `ms ≥ 75 AND perf_1h ≥ 0.5%` → `_evaluate_watchlist_candidate()`
  - 기존 스크리닝과 동일 파이프라인: `_get_history → compute_indicators → strategy.evaluate → Finviz 필터 → _process_signal()`
  - 워치리스트 쿨다운 15분 (스크리닝 쿨다운과 독립)

### 설계 원칙
- Finviz 게이트(매수 차단) ↔ 워치리스트(매수 가속) 상호 보완
- Fall-through 안전: 오류 시 해당 종목 스킵, 루프 계속
- [Finviz 장중 최종 게이트] commit `3921277`: `_process_signal()` 매수 직전 heuristic check

---

## 2026-03-01 — Finviz Elite API 전면 통합 v2 — commits `9e598ea`, `701e1f3`, `e895d0a`

### FinvizProvider v2 (`src/data/providers/finviz_provider.py`)
- **DAILY_COLUMNS 확장**: 15 → 24개 (FwdPE/EPS3개/영업이익률/Gross마진/Beta/ATR/목표가/EPS NextQ 추가)
- **보너스 체계 재설계 (최대 ~90pt, 페널티 ~-25pt)**:
  - [A] 기관/내부자 수급 +30pt (inst_trans ≥5%: +25pt 최강 신호)
  - [B] 실적 성장 +25pt (EPS QQ + Next Year + 시너지 +5pt)
  - [C] 비즈니스 품질 +20pt (영업이익률/ROE/Gross마진 3중)
  - [D] 애널리스트 +15pt (목표가 괴리율 ≥40%: +10pt 신규)
  - [E] 밸류에이션 페널티: FwdPE>100: -10pt, FwdPE>60: -5pt
- **EPS QQ 급락 보정**: `eps_qq ≤ -30%` → 내년 전망 신뢰도 50% 할인
  - TSLA 수정: +2pt → -2pt (FwdPE 153.7x + 실적 -64%)
  - CRWD 수정: +23pt → +20pt (어닝 충격 -98% 반영)
- **신규 메서드**:
  - `get_strategy_signals(sym, strategy)`: SEPA/Momentum/EarningsDrift 전략별 Finviz 필터
  - `get_intraday_scan(symbols)`: 5/15/30분/1시간 실시간 퍼포먼스 + 장중 모멘텀 점수(0~100), TTL 5분
  - `get_risk_multiplier(sym)`: Beta 기반 포지션 보정 (Beta>2.5: 0.7x / >2.0: 0.8x / >1.5: 0.9x)
  - `get_atr(sym)`, `get_target_upside(sym)` 헬퍼 메서드

### live_engine.py 통합
- `strategy.evaluate()` 후 `get_strategy_signals()` 적용:
  - `pass=False` → 시그널 폐기 + 경고 로그
  - `score_adjustment` → signal.score 반영
  - `reasons` → signal.reason에 추가 (ex: "기관 매집 2.73%, 목표가 상승여지 45.6%")
- `_process_signal()`: `get_risk_multiplier()` 적용 → Beta 고위험 종목 자동 축소
  - ARM(4.17): 30% / NVDA(2.32): 20% / AMD(1.97): 10%

### 대시보드 (ai-trader-v2)
- US 스크리닝 테이블 9열로 확장 (themes.js v5):
  - 기관거래% (inst_trans): +2%↑ 초록
  - 목표가↑ (target_upside): +30%↑ 초록
  - 점수: total_score(기술+Finviz) + bonus 작은 글씨

---

## 2026-03-01 — US 전략 전면 개선 (P1/P2/P3) — commit `b03eca1`

**P1-A: StockScreener → 전략 스캔 연동**
- `live_engine.py`: `_run_screening()`에서 `_last_screen_result` 점수순 상위 150개를 후보 pool로 사용
- 기존 랜덤 샘플 → 스크리너 결과 없을 때만 폴백

**P1-B: EarningsDrift 어닝 캘린더 연동**
- `src/data/providers/earnings_provider.py` 신규
  - Finnhub `GET /calendar/earnings` 어제~내일 조회
  - 1일 로컬 캐시 (`~/.cache/ai_trader_us/earnings_YYYY-MM-DD.json`)
- `live_engine.py`: `_earnings_today` Set 관리, 장 시작 시 1일 1회 갱신
- EarningsDrift는 `_earnings_today` 종목에만 적용 (API 키 없으면 전체 적용 유지)

**P2: 파라미터 조정 (config/default.yml)**
- `trailing_stop_pct`: 2.0 → 3.0 (US 일중 ATR 2~3% 기준)
- `stop_loss_pct`: 3.0 → 4.0 (일중 노이즈 필터)
- `momentum.volume_surge_ratio`: 1.2 → 1.8 (기관 주도 돌파 기준)

**P3: 동적 max_price + 금액 기준 최소 1주**
- `_run_screening()`: `effective_max_price = cash × max_position_pct%` 동적 계산
- `RiskManager.calculate_position_size(allow_min_one=True)`: qty=0이어도 주가 ≤ max_position_value이고 현금 ≥ 주가이면 1주 강제
  - KIS 소수주 불가 → 금액 기준 최소 단위 보장 (정수 주문)
- `_process_signal()`: `allow_min_one=True` 전달

**KIS 소수주 주문 불가 결론**
- `ORD_QTY` 정수 전용 → 소수주/금액 기준 주문 API 레벨 불가
- 엔진 레벨에서 `floor(목표금액/주가)` + `allow_min_one` 방식으로 대응

---

## 2026-03-01 — 대시보드 테마 탭 개선 — commits `1ea8365`, `6c0a34e`

- 뉴스 건수 불일치 수정: `news_count` → `newsItems.length` (KR/US 모두)
- KR 스크리닝 종목명만 표시 (심볼 코드 제거)
- themes.js v4

---

## 2026-03-01 — US 테마 탐지 + 스크리닝 통합

**신규 파일**:
- `src/data/providers/us_theme_detector.py` — US 테마 탐지기 (Finnhub 뉴스 키워드 매칭, 11개 테마, 30분 주기)

**수정 파일**:
- `src/data/providers/news_provider.py` — FinnhubNewsProvider, CompositeNewsProvider에 async 래퍼 추가 (`get_news_async`, `get_sentiment_async`)
- `src/core/live_engine.py` — 테마 탐지/스크리너 루프 2개 추가 (태스크 7,8), SentimentScorer 전략 주입, restart_map 갱신
- `src/api/server.py` — `/api/us/themes`, `/api/us/screening` 엔드포인트 추가

### 상세
- `USThemeDetector`: Finnhub general_news(30건) + 대형주 5개 company_news(각 5건) 수집 → 11개 테마 키워드 매칭
- 활성 테마 조건: news_count >= 2, score = min(100, count * 15 + 20)
- 스크리너: 기존 `StockScreener.scan()` 60분 주기 장중 실행 (유니버스 300개)
- 센티멘트: `SentimentScorer`를 전략에 `_sentiment_scorer` 속성으로 주입
- KR 대시보드 프록시 경유 확인 완료 (`/api/us-proxy/api/us/themes`)

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

# Finviz 동적 스크리닝 + 필터 개선 구현 플랜

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Finviz Elite API의 `f=` 필터로 동적 종목 발견 + Dollar Volume/ATR% 필터 추가로 스크리닝 품질 개선

**Architecture:** 기존 SP500+400 정적 유니버스 유지 + Finviz 동적 발견 종목을 보강. screener.py의 필터를 거래대금/변동성 기반으로 강화. 3개 파일만 수정.

**Tech Stack:** aiohttp (Finviz Elite API), pandas (dollar volume 계산)

---

### Task 1: FinvizProvider에 `discover_dynamic()` 메서드 추가

**Files:**
- Modify: `src/data/providers/finviz_provider.py:236` (refresh 메서드 뒤)

**Step 1: `discover_dynamic()` 메서드 구현**

`refresh()` 메서드 아래(라인 236 뒤)에 추가:

```python
    async def discover_dynamic(self) -> List[str]:
        """
        Finviz f= 필터로 오늘의 핫 종목 동적 발견.

        3가지 필터 셋:
          A. 거래량 급증 + 상승: 장중 핫 종목
          B. 신고가 근접 + 4주 모멘텀: SEPA/추세 후보
          C. 어닝 주간 + 큰 갭: EarningsDrift 후보

        Returns:
            중복 제거된 티커 리스트 (기존 유니버스에 추가용)
        """
        if not self._token:
            return []

        filters = [
            # A: 거래량 급증 + 상승 (프리마켓/장중 핫 종목)
            "sh_avgvol_o500,sh_price_o10,ta_relvol_o2,ta_change_u3",
            # B: 신고가 근접 + 4주 모멘텀 (추세 추종 후보)
            "sh_avgvol_o500,sh_price_o10,ta_highlow52w_nh,ta_perf4w_o10",
            # C: 어닝 주간 + 큰 갭 (EarningsDrift 후보)
            "sh_avgvol_o500,sh_price_o10,ta_change_u5,earningsdate_thisweek",
        ]
        filter_names = ["거래량급증", "신고가모멘텀", "어닝갭"]

        discovered: set = set()
        for f_str, f_name in zip(filters, filter_names):
            try:
                rows = await self._fetch_rows("1,65", filter_str=f_str)
                syms = {
                    row.get("Ticker", "").strip()
                    for row in rows
                    if row.get("Ticker", "").strip()
                }
                discovered |= syms
                logger.info(f"[Finviz 동적] {f_name}: {len(syms)}종목")
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.warning(f"[Finviz 동적] {f_name} 실패: {e}")

        logger.info(f"[Finviz 동적] 총 {len(discovered)}종목 발견 (중복 제거)")
        return sorted(discovered)
```

**Step 2: 컴파일 확인**

Run: `cd /home/user/projects/ai-trader-us && source venv/bin/activate && python3 -m py_compile src/data/providers/finviz_provider.py`
Expected: 에러 없음

**Step 3: 커밋**

```bash
git add src/data/providers/finviz_provider.py
git commit -m "feat(finviz): discover_dynamic() — Finviz f= 필터로 동적 종목 발견"
```

---

### Task 2: screener.py에 Dollar Volume + ATR% 필터 추가

**Files:**
- Modify: `src/data/screener.py:149-244`

**Step 1: `scan()` 파라미터 추가**

`scan()` 시그니처를 변경 (라인 149-156):

```python
    def scan(
        self,
        symbols: List[str],
        min_price: float = 5.0,
        min_avg_volume: int = 500_000,
        vol_surge_threshold: float = 2.0,
        lookback_days: int = 252,
        min_dollar_volume: float = 5_000_000,
        min_atr_pct: float = 2.0,
    ) -> ScreenerResult:
```

`_analyze_symbol()` 호출부도 변경 (라인 178-181):

```python
            result = self._analyze_symbol(
                symbol, start, today, min_price, min_avg_volume,
                vol_surge_threshold, min_dollar_volume, min_atr_pct,
            )
```

**Step 2: `_analyze_symbol()` 시그니처 + 필터 로직 변경**

시그니처 변경 (라인 213-220):

```python
    def _analyze_symbol(
        self,
        symbol: str,
        start: date,
        end: date,
        min_price: float,
        min_avg_volume: int,
        vol_surge_threshold: float,
        min_dollar_volume: float = 5_000_000,
        min_atr_pct: float = 2.0,
    ) -> Optional[ScreenResult]:
```

Volume filter 부분 변경 (라인 241-244):

```python
        # Volume filter (shares + dollar volume)
        avg_vol_20 = int(df['volume'].tail(20).mean())
        if avg_vol_20 < min_avg_volume:
            return None
        avg_dollar_vol = float((df['volume'] * df['close']).tail(20).mean())
        if avg_dollar_vol < min_dollar_volume:
            return None
```

ATR% 계산 직후 (라인 278 뒤) 하한 필터 추가:

```python
        atr_pct = (atr / close * 100) if close > 0 else 0

        # ATR% 하한 필터 (변동성 부족 종목 제외)
        if atr_pct < min_atr_pct:
            return None
```

**Step 3: 컴파일 확인**

Run: `cd /home/user/projects/ai-trader-us && python3 -m py_compile src/data/screener.py`
Expected: 에러 없음

**Step 4: 커밋**

```bash
git add src/data/screener.py
git commit -m "feat(screener): dollar volume 필터 + ATR% 하한 추가"
```

---

### Task 3: live_engine.py에 동적 유니버스 연동

**Files:**
- Modify: `src/core/live_engine.py:129,373-439`

**Step 1: 상태 변수 추가**

`__init__`에서 `_last_screen_time` 뒤(라인 130 근처)에 추가:

```python
        self._dynamic_symbols: Set[str] = set()  # Finviz 동적 발견 종목
        self._dynamic_last_refresh: Optional[date] = None
```

**Step 2: `_screening_loop`에 동적 유니버스 갱신 추가**

Finviz daily refresh 직후 (라인 385 뒤, `await self._run_screening()` 전)에 추가:

```python
                # Finviz 동적 유니버스 갱신 (1일 1회, daily refresh 후)
                if self._dynamic_last_refresh != today:
                    try:
                        dynamic = await self.finviz_provider.discover_dynamic()
                        if dynamic:
                            new_syms = set(dynamic) - set(self._universe)
                            self._dynamic_symbols = new_syms
                            self._dynamic_last_refresh = today
                            if new_syms:
                                logger.info(
                                    f"[Finviz 동적] 신규 {len(new_syms)}종목 보강 "
                                    f"(기존 유니버스 외)"
                                )
                    except Exception as e:
                        logger.warning(f"[Finviz 동적] 갱신 실패: {e}")
```

**Step 3: `_run_screening`의 후보 선정에 동적 종목 우선 삽입**

StockScreener 후보 선정 부분 (라인 418-439) 변경:

```python
        # ── P1-A: StockScreener 결과 기반 후보 우선 사용 ──────────────────
        held = set(self.portfolio.positions.keys())
        screen_candidates: List[str] = []

        if self._last_screen_result and self._last_screen_result.results:
            # StockScreener 점수 순 상위 150개 (보유 종목 제외)
            screen_candidates = [
                r.symbol for r in self._last_screen_result.results
                if r.symbol not in held
            ][:150]
            logger.debug(
                f"[스크리닝] StockScreener 상위 {len(screen_candidates)}개 후보 사용"
            )

        # Finviz 동적 발견 종목을 후보 상위에 삽입
        if self._dynamic_symbols:
            dynamic_candidates = [
                s for s in self._dynamic_symbols
                if s not in held and s not in self._signal_cooldown
            ]
            if dynamic_candidates:
                existing = set(screen_candidates)
                new_dynamic = [s for s in dynamic_candidates if s not in existing]
                screen_candidates = new_dynamic + screen_candidates
                logger.debug(
                    f"[스크리닝] 동적 {len(new_dynamic)}종목 삽입 → "
                    f"총 {len(screen_candidates)}개 후보"
                )

        if screen_candidates:
            candidates = screen_candidates[:self._max_screen_symbols]
        else:
            # 폴백: 랜덤 셔플 (StockScreener 결과 없을 때)
            logger.debug("[스크리닝] StockScreener 결과 없음 — 랜덤 샘플 폴백")
            candidates = [s for s in self._universe if s not in held]
            random.shuffle(candidates)
            candidates = candidates[:self._max_screen_symbols]
```

**Step 4: 컴파일 확인**

Run: `cd /home/user/projects/ai-trader-us && python3 -m py_compile src/core/live_engine.py`
Expected: 에러 없음

**Step 5: 커밋**

```bash
git add src/core/live_engine.py
git commit -m "feat(engine): Finviz 동적 유니버스 보강 + 스크리닝 후보 우선삽입"
```

---

### Task 4: 검증 및 배포

**Step 1: 전체 py_compile**

```bash
cd /home/user/projects/ai-trader-us && source venv/bin/activate
python3 -m py_compile src/data/providers/finviz_provider.py
python3 -m py_compile src/data/screener.py
python3 -m py_compile src/core/live_engine.py
```

**Step 2: 봇 재시작**

```bash
echo 'user123!' | sudo -S -k systemctl restart ai-trader-us
systemctl is-active ai-trader-us
journalctl -u ai-trader-us -n 30 --no-pager
```

Expected 로그:
- `AI Trader US - Live Engine 시작`
- `[스크리너] 캐시 로드: N종목` (이전 캐시 존재 시)
- 장중이면: `[Finviz] 갱신 완료`, `[Finviz 동적] 신규 N종목 보강`

**Step 3: CHANGELOG 업데이트**

CHANGELOG.md 상단에 변경 이력 추가.

**Step 4: 최종 커밋 + 푸시**

```bash
git add CHANGELOG.md
git commit -m "docs: CHANGELOG 업데이트 — Finviz 동적 스크리닝 + 필터 개선"
git push
```

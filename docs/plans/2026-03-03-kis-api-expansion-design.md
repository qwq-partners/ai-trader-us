# KIS API 5종 확장 설계

> 날짜: 2026-03-03
> 상태: 승인됨

## 목표

KIS 해외주식 API 레퍼런스(`docs/KIS_OVERSEAS_API.md`) 기반으로 미사용 유용 API 5종을 구현하여 US 엔진의 주문 안전성, 장중 현금 정합성, 거래 시간 확장을 달성한다.

## 구현 범위

### 브로커 레이어 (kis_us_broker.py) — 5개 메서드 추가

| # | 메서드 | TR_ID | API 경로 | 용도 |
|---|--------|-------|----------|------|
| 1 | `get_pending_orders()` | TTTS3018R | `/trading/inquire-nccs` | 미체결 주문 조회 |
| 2 | `get_buying_power()` | TTTS3007R/VTTS3007R | `/trading/inquire-psamount` | 장중 매수가능금액 |
| 3 | `submit_daytime_order()` | TTTS6036U/37U | `/trading/daytime-order` | 주간거래 (10~18 KST) |
| 4 | `get_period_profit()` | TTTS3039R | `/trading/inquire-period-profit` | 기간 실현손익 |
| 5 | `get_quote_detail()` | HHDFS76200200 | `/quotations/price-detail` | 펀더멘탈 (PER/EPS/PBR) |

### 엔진 레이어 (live_engine.py) — 핵심 2곳 통합

1. **`_execute_entry` 매수 직전**: `get_buying_power()` → 실시간 가용현금 검증
2. **`submit_buy/sell_order` 내부**: KST 시각 감지 → 주간거래 TR_ID 자동 분기

## 상세 설계

### 1. get_pending_orders() — TTTS3018R

```
GET /uapi/overseas-stock/v1/trading/inquire-nccs
tr_id: TTTS3018R (실전만, 모의투자 미지원)
```

**파라미터**:
- `OVRS_EXCG_CD`: "NASD" (미국 전체)
- `SORT_SQN`: "" (공란 = 역순)
- `CTX_AREA_FK200/NK200`: 페이지네이션

**반환**: `[{order_no, symbol, side, ord_qty, filled_qty, unfilled_qty, price, exchange, time}]`

**제약**: 모의투자 미지원 → `config.env != "prod"`이면 빈 리스트 반환

### 2. get_buying_power() — TTTS3007R

```
GET /uapi/overseas-stock/v1/trading/inquire-psamount
tr_id: TTTS3007R (실전) / VTTS3007R (모의)
```

**파라미터**:
- `OVRS_EXCG_CD`: 거래소 코드
- `OVRS_ORD_UNPR`: 주문 단가 (문자열)
- `ITEM_CD`: 종목 코드

**반환**: `{available_cash, max_qty, exchange_rate}`
- `ord_psbl_frcr_amt` → available_cash (외화 주문가능금액)
- `max_ord_psbl_qty` → max_qty (최대 주문가능수량)
- `exrt` → exchange_rate

### 3. submit_daytime_order() — TTTS6036U/37U

```
POST /uapi/overseas-stock/v1/trading/daytime-order
tr_id: TTTS6036U (매수) / TTTS6037U (매도)
```

**제약**:
- 지정가(ORD_DVSN="00")만 가능 (시장가 불가)
- 모의투자 미지원
- 일부 종목만 지원
- 10:00~18:00 KST만

**엔진 통합**: `submit_buy/sell_order()` 내부에서 KST 시각 감지 → 자동 분기
- 주간거래 시간이면 `daytime-order` URL + TTTS6036U/37U 사용
- 아닌 경우 기존 `order` URL + TTTT1002U/1006U 사용

### 4. get_period_profit() — TTTS3039R

```
GET /uapi/overseas-stock/v1/trading/inquire-period-profit
tr_id: TTTS3039R (실전만)
```

**파라미터**:
- `OVRS_EXCG_CD`: "" (전체) 또는 "NASD"
- `INQR_STRT_DT/INQR_END_DT`: YYYYMMDD
- `WCRC_FRCR_DVSN_CD`: "01" (외화=USD)
- `CRCY_CD`: "USD"
- `PDNO`: "" (전체)

**반환**:
```
{
  trades: [{date, symbol, sell_qty, avg_buy, avg_sell, pnl, pnl_pct, exchange}],
  summary: {total_sell_amt, total_buy_amt, total_fee, total_pnl, total_pnl_pct}
}
```

**페이지네이션**: Output1(거래 목록) 연속조회, Output2(합계) 첫 페이지만

### 5. get_quote_detail() — HHDFS76200200

```
GET /uapi/overseas-price/v1/quotations/price-detail
tr_id: HHDFS76200200
```

**파라미터**:
- `AUTH`: ""
- `EXCD`: 거래소 코드 (NAS/NYS/AMS)
- `SYMB`: 종목 코드

**반환**: `{symbol, price, per, pbr, eps, bps, market_cap, week52_high, week52_low, dividend_yield, ...}`

## 엔진 통합 상세

### _execute_entry 매수가능금액 검증

```python
# 기존 흐름 유지하되, KIS 직접 확인 추가
buying_power = await self.broker.get_buying_power(symbol, exchange, price)
if buying_power:
    kis_max_qty = buying_power.get("max_qty", 0)
    if kis_max_qty < qty:
        logger.warning(f"[매수] KIS 매수가능수량 {kis_max_qty} < 계획 {qty}, 조정")
        qty = kis_max_qty
    if qty <= 0:
        logger.warning(f"[매수거부] {symbol} KIS 매수가능금액 부족")
        return
```

- 실패 시 기존 로직(portfolio.available_cash) 폴백 — 안전장치
- API 호출 1건 추가 (rate limit 내)

### 주간거래 자동 분기

`_submit_order` 내부에서 분기:

```python
from zoneinfo import ZoneInfo
kst = datetime.now(ZoneInfo("Asia/Seoul"))
is_daytime = 10 <= kst.hour < 18

if is_daytime and self.config.env == "prod":
    # 주간거래: 지정가만, 별도 URL/TR_ID
    url = f"{base_url}/uapi/overseas-stock/v1/trading/daytime-order"
    tr_id = "TTTS6036U" if side == "buy" else "TTTS6037U"
    body["ORD_DVSN"] = "00"  # 지정가 강제
    if price <= 0:
        logger.warning("주간거래는 지정가만 가능, 시장가 요청 거부")
        return {"success": False, "message": "주간거래 시장가 미지원"}
else:
    url = f"{base_url}/uapi/overseas-stock/v1/trading/order"
    tr_id = self._tr_buy if side == "buy" else self._tr_sell
```

## 미구현 (다음 단계)

- 미체결내역(TTTS3018R) 기반 EOD orphan 주문 자동취소
- 기간손익(TTTS3039R) 기반 daily report 개선
- 현재가상세(HHDFS76200200) 기반 스크리닝 펀더멘탈 필터

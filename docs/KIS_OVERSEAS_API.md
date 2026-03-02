# KIS 해외주식 오픈 API 레퍼런스

> **출처**: 한국투자증권 오픈 API 공식 문서 (xlsx 4종)  
> **정리일**: 2026-03-03  
> **대상 프로젝트**: `ai-trader-us`  
> **공식 문서**: https://apiportal.koreainvestment.com  
> **샘플 코드**: https://github.com/koreainvestment/open-trading-api

---

## 목차

1. [공통 사항](#1-공통-사항)
2. [주문/계좌 API (REST)](#2-주문계좌-api-rest)
3. [기본시세 API (REST)](#3-기본시세-api-rest)
4. [시세분석/랭킹 API (REST)](#4-시세분석랭킹-api-rest)
5. [실시간시세 API (WebSocket)](#5-실시간시세-api-websocket)
6. [개발 가이드 & 주의사항](#6-개발-가이드--주의사항)
7. [ai-trader-us 활용 전략](#7-ai-trader-us-활용-전략)

---

## 1. 공통 사항

### 도메인

| 환경 | 도메인 |
|------|--------|
| **실전투자** | `https://openapi.koreainvestment.com:9443` |
| **모의투자** | `https://openapivts.koreainvestment.com:29443` |
| **WebSocket 실전** | `ws://ops.koreainvestment.com:21000` |
| **WebSocket 모의** | `ws://ops.koreainvestment.com:31000` |

### 공통 Request Header

| Element | 설명 | 필수 |
|---------|------|------|
| `content-type` | `application/json; charset=utf-8` | Y |
| `authorization` | `Bearer {access_token}` (유효기간: 개인 1일, 법인 3개월) | Y |
| `appkey` | 앱키 (노출 금지) | Y |
| `appsecret` | 앱시크릿 (노출 금지) | Y |
| `tr_id` | 거래 ID (API마다 상이) | Y |
| `custtype` | `P` (개인) / `B` (법인) | Y |
| `tr_cont` | 연속조회 여부: 공백(초기) / `N`(다음) | N |

### 공통 Response Body

| Element | 설명 |
|---------|------|
| `rt_cd` | `0` = 성공, 이외 = 실패 |
| `msg_cd` | 응답코드 |
| `msg1` | 응답메시지 |
| `output` / `output1` / `output2` | 응답 데이터 (API마다 상이) |

### 미국 거래소 코드

| 코드 | 거래소 | 비고 |
|------|--------|------|
| `NASD` | 나스닥 | 정규장 주문 |
| `NYSE` | 뉴욕증권거래소 | 정규장 주문 |
| `AMEX` | 아멕스 | 정규장 주문 |
| `BAQ` | 나스닥 (주간거래) | 10:00~18:00 KST |
| `BAY` | 뉴욕 (주간거래) | 10:00~18:00 KST |
| `BAA` | 아멕스 (주간거래) | 10:00~18:00 KST |

### 미국 거래시간 (KST 기준)

| 세션 | 시간 | Summer Time |
|------|------|-------------|
| 프리마켓 | 18:00 ~ 23:30 | 17:00 ~ 22:30 |
| **정규장** | **23:30 ~ 06:00** | **22:30 ~ 05:00** |
| 애프터마켓 | 06:00 ~ 07:00 | 05:00 ~ 07:00 |
| 주간거래 | 10:00 ~ 18:00 | 동일 |

> ⚠️ **주간거래**는 별도 TR_ID 사용 (`TTTS6036U` 매수 / `TTTS6037U` 매도), 모든 종목 지원 안 됨

### POST API 주의사항

```
POST Body의 key는 반드시 대문자로 작성
{"CANO": "12345678", "ACNT_PRDT_CD": "01", ...}
```

---

## 2. 주문/계좌 API (REST)

### 해외주식 주문

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-001` |
| 통신방식 | REST / POST |
| 실전 TR_ID | `(미국매수) TTTT1002U  (미국매도) TTTT1006U (아시아 국가 하단 규격서 참고)` |
| 모의 TR_ID | `(미국매수) VTTT1002U  (미국매도) VTTT1001U  (아시아 국가 하단 규격서 참고)` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| 모의 Domain | `https://openapivts.koreainvestment.com:29443` |
| URL | `/uapi/overseas-stock/v1/trading/order` |

> 해외주식 주문 API입니다.  * 모의투자의 경우, 모든 해외 종목 매매가 지원되지 않습니다. 일부 종목만 매매 가능한 점 유의 부탁드립니다.  * 해외주식 서비스 신청 후 이용 가능합니다. (아래 링크 3번 해외증권 거래신청 참고) https://securities.koreainvestment.com/main/bond/research/_static/TF03ca010001.jsp  * 해외 거래소 운영시간 외 API 호출 시 에러가 발생하오니 운영시간을 확인해주세요. (미국주식 주간주문은 "해외주식 미국주간주문"을 이용

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | N | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token 일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용) 법인(Access t |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appsecret (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | [실전투자] TTTT1002U : 미국 매수 주문 TTTT1006U : 미국 매도 주문 TTTS0308U : 일본 매수 주문 TTTS0307U : 일본 매도 주문  TTTS0202U : 상해 매수 주문 TTTS100 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객타입 | string | N | 1 | B : 법인 P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호 ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `CANO` | 종합계좌번호 | string | Y | 8 | 계좌번호 체계(8-2)의 앞 8자리 |
| `ACNT_PRDT_CD` | 계좌상품코드 | string | Y | 2 | 계좌번호 체계(8-2)의 뒤 2자리 |
| `OVRS_EXCG_CD` | 해외거래소코드 | string | Y | 4 | NASD : 나스닥 NYSE : 뉴욕 AMEX : 아멕스 SEHK : 홍콩 SHAA : 중국상해 SZAA : 중국심천 TKSE : 일본 HASE : 베트남 하노이 VNSE : 베트남 호치민 |
| `PDNO` | 상품번호 | string | Y | 12 | 종목코드 |
| `ORD_QTY` | 주문수량 | string | Y | 10 | 주문수량 (해외거래소 별 최소 주문수량 및 주문단위 확인 필요) |
| `OVRS_ORD_UNPR` | 해외주문단가 | string | Y | 31 | 1주당 가격 * 시장가의 경우 1주당 가격을 공란으로 비우지 않음 "0"으로 입력 |
| `CTAC_TLNO` | 연락전화번호 | string | N | 20 |  |
| `MGCO_APTM_ODNO` | 운용사지정주문번호 | string | N | 12 |  |
| `SLL_TYPE` | 판매유형 | string | N | 2 | 제거 : 매수 00 : 매도 |
| `ORD_SVR_DVSN_CD` | 주문서버구분코드 | string | Y | 1 | "0"(Default) |
| `ORD_DVSN` | 주문구분 | string | Y | 2 | [Header tr_id TTTT1002U(미국 매수 주문)] 00 : 지정가 32 : LOO(장개시지정가) 34 : LOC(장마감지정가) 35 : TWAP (시간가중평균) 36 : VWAP (거래량가중평균) * 모 |
| `START_TIME` | 시작시간 | string | N | 6 | ※ TWAP, VWAP 주문유형이고 알고리즘주문시간구분코드가 00일때 사용 ※ YYMMDD 형태로 입력 ※ 시간 입력 시 정규장 종료 5분전까지 입력 가능 |
| `END_TIME` | 종료시간 | string | N | 6 | ※ TWAP, VWAP 주문유형이고 알고리즘주문시간구분코드가 00일때 사용 ※ YYMMDD 형태로 입력 ※ 시간 입력 시 정규장 종료 5분전까지 입력 가능 |
| `ALGO_ORD_TMD_DVSN_CD` | 알고리즘주문시간구분코드 | string | N | 2 | 00 : 분할주문 시간 직접입력 , 02 : 정규장 종료시까지 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 | 0 : 성공  0 이외의 값 : 실패 |
| `msg_cd` | 응답코드 | string | Y | 8 | 응답코드 |
| `msg1` | 응답메세지 | string | Y | 80 | 응답메세지 |
| `output` | 응답상세 | object | Y |  |  |
| `KRX_FWDG_ORD_ORGNO` | 한국거래소전송주문조직번호 | string | Y | 5 | 주문시 한국투자증권 시스템에서 지정된 영업점코드 |
| `ODNO` | 주문번호 | string | Y | 10 | 주문시 한국투자증권 시스템에서 채번된 주문번호 |
| `ORD_TMD` | 주문시각 | string | Y | 6 | 주문시각(시분초HHMMSS) |

**Request 예시**
```
{ "CANO": "810XXXXX", "ACNT_PRDT_CD": "01", "OVRS_EXCG_CD": "NASD", "PDNO": "AAPL", "ORD_QTY": "1", "OVRS_ORD_UNPR": "145.00", "CTAC_TLNO": "", "MGCO_APTM_ODNO": "", "ORD_SVR_DVSN_CD": "0", "ORD_DVSN": "00" }
```

**Response 예시**
```json
{   "rt_cd": "0",   "msg_cd": "APBK0013",   "msg1": "주문 전송 완료 되었습니다.",   "output": {     "KRX_FWDG_ORD_ORGNO": "01790",     "ODNO": "0000004336",     "ORD_TMD": "160524"   } }
```

---

### 해외주식 정정취소주문

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-003` |
| 통신방식 | REST / POST |
| 실전 TR_ID | `(미국 정정·취소) TTTT1004U (아시아 국가 하단 규격서 참고)` |
| 모의 TR_ID | `(미국 정정·취소) VTTT1004U (아시아 국가 하단 규격서 참고)` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| 모의 Domain | `https://openapivts.koreainvestment.com:29443` |
| URL | `/uapi/overseas-stock/v1/trading/order-rvsecncl` |

> 접수된 해외주식 주문을 정정하거나 취소하기 위한 API입니다. (해외주식주문 시 Return 받은 ODNO를 참고하여 API를 호출하세요.)  * 해외주식 서비스 신청 후 이용 가능합니다. (아래 링크 3번 해외증권 거래신청 참고) https://securities.koreainvestment.com/main/bond/research/_static/TF03ca010001.jsp  * 해외 거래소 운영시간 외 API 호출 시 에러가 발생하오니 운영시간을 확인해주세요. * 해외 거래소 운영시간(한국시간 기준) 1) 미국

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | N | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token 일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용) 법인(Access t |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appsecret (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | [실전투자] TTTT1004U : 미국 정정 취소 주문 TTTS1003U : 홍콩 정정 취소 주문 TTTS0309U : 일본 정정 취소 주문 TTTS0302U : 상해 취소 주문 TTTS0306U : 심천 취소 주문 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객타입 | string | N | 1 | B : 법인 P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호 ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `CANO` | 종합계좌번호 | string | Y | 8 | 계좌번호 체계(8-2)의 앞 8자리 |
| `ACNT_PRDT_CD` | 계좌상품코드 | string | Y | 2 | 계좌번호 체계(8-2)의 뒤 2자리 |
| `OVRS_EXCG_CD` | 해외거래소코드 | string | Y | 4 | NASD : 나스닥  NYSE : 뉴욕  AMEX : 아멕스 SEHK : 홍콩 SHAA : 중국상해 SZAA : 중국심천 TKSE : 일본 HASE : 베트남 하노이 VNSE : 베트남 호치민 |
| `PDNO` | 상품번호 | string | Y | 12 |  |
| `ORGN_ODNO` | 원주문번호 | string | Y | 10 | 정정 또는 취소할 원주문번호 (해외주식_주문 API ouput ODNO  or 해외주식 미체결내역 API output ODNO 참고) |
| `RVSE_CNCL_DVSN_CD` | 정정취소구분코드 | string | Y | 2 | 01 : 정정  02 : 취소 |
| `ORD_QTY` | 주문수량 | string | Y | 10 |  |
| `OVRS_ORD_UNPR` | 해외주문단가 | string | Y | 32 | 취소주문 시, "0" 입력 |
| `MGCO_APTM_ODNO` | 운용사지정주문번호 | string | N | 12 |  |
| `ORD_SVR_DVSN_CD` | 주문서버구분코드 | string | N | 1 | "0"(Default) |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 | 0 : 성공  0 이외의 값 : 실패 |
| `msg_cd` | 응답코드 | string | Y | 8 | 응답코드 |
| `msg1` | 응답메세지 | string | Y | 80 | 응답메세지 |
| `output` | 응답상세 | object | Y |  |  |
| `KRX_FWDG_ORD_ORGNO` | 한국거래소전송주문조직번호 | string | Y | 5 | 주문시 한국투자증권 시스템에서 지정된 영업점코드 |
| `ODNO` | 주문번호 | string | Y | 10 | 주문시 한국투자증권 시스템에서 채번된 주문번호 |
| `ORD_TMD` | 주문시각 | string | Y | 6 | 주문시각(시분초HHMMSS) |

**Request 예시**
```
{ "CANO": "810XXXXX", "ACNT_PRDT_CD": "01", "OVRS_EXCG_CD": "NYSE", "PDNO": "BA", "ORGN_ODNO": "30135009", "RVSE_CNCL_DVSN_CD": "01", "ORD_QTY": "1", "OVRS_ORD_UNPR": "226.00", "CTAC_TLNO": "", "MGCO_APTM_ODNO": "", "ORD_SVR_DVSN_CD": "0" }
```

**Response 예시**
```json
{   "rt_cd": "0",   "msg_cd": "APBK0013",   "msg1": "주문 전송 완료 되었습니다.",   "output": {     "KRX_FWDG_ORD_ORGNO": "01790",     "ODNO": "0000004338",     "ORD_TMD": "160710"   } }
```

---

### 해외주식 미국주간주문

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-026` |
| 통신방식 | REST / POST |
| 실전 TR_ID | `(주간매수) TTTS6036U (주간매도) TTTS6037U` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/trading/daytime-order` |

> 해외주식 미국주간주문 API입니다.  * 미국주식 주간거래 시 아래 참고 부탁드립니다. . 포럼 &gt; FAQ &gt; 미국주식 주간거래 시 어떤 API를 사용해야 하나요?  * 미국주간거래의 경우, 모든 미국 종목 매매가 지원되지 않습니다. 일부 종목만 매매 가능한 점 유의 부탁드립니다.  * 해외주식 서비스 신청 후 이용 가능합니다. (아래 링크 3번 해외증권 거래신청 참고) https://securities.koreainvestment.com/main/bond/research/_static/TF03ca01000

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | [실전투자] 미국주간매수 : TTTS6036U 미국주간매도 : TTTS6037U |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `CANO` | 종합계좌번호 | string | Y | 8 | 계좌번호 체계(8-2)의 앞 8자리 |
| `ACNT_PRDT_CD` | 계좌상품코드 | string | Y | 2 | 계좌번호 체계(8-2)의 뒤 2자리 |
| `OVRS_EXCG_CD` | 해외거래소코드 | string | Y | 4 | NASD:나스닥 / NYSE:뉴욕 / AMEX:아멕스 |
| `PDNO` | 상품번호 | string | Y | 12 | 종목코드 |
| `ORD_QTY` | 주문수량 | string | Y | 10 | 해외거래소 별 최소 주문수량 및 주문단위 확인 필요 |
| `OVRS_ORD_UNPR` | 해외주문단가 | string | Y | 32 | 소수점 포함, 1주당 가격 * 시장가의 경우 1주당 가격을 공란으로 비우지 않음 "0"으로 입력 |
| `CTAC_TLNO` | 연락전화번호 | string | N | 20 | " " |
| `MGCO_APTM_ODNO` | 운용사지정주문번호 | string | N | 12 | " " |
| `ORD_SVR_DVSN_CD` | 주문서버구분코드 | string | Y | 1 | "0" |
| `ORD_DVSN` | 주문구분 | string | Y | 2 | [미국 매수/매도 주문]  00 : 지정가  * 주간거래는 지정가만 가능 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output` | 응답상세 | object | N |  |  |
| `KRX_FWDG_ORD_ORGNO` | 한국거래소전송주문조직번호 | string | Y | 5 | 주문시 한국투자증권 시스템에서 지정된 영업점코드 |
| `ODNO` | 주문번호 | string | Y | 10 | 주문시 한국투자증권 시스템에서 채번된 주문번호 |
| `ORD_TMD` | 주문시각 | string | Y | 6 | 주문시각(시분초HHMMSS) |

---

### 해외주식 잔고

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-006` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `TTTS3012R` |
| 모의 TR_ID | `VTTS3012R` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| 모의 Domain | `https://openapivts.koreainvestment.com:29443` |
| URL | `/uapi/overseas-stock/v1/trading/inquire-balance` |

> 해외주식 잔고를 조회하는 API 입니다. 한국투자 HTS(eFriend Plus) &gt; [7600] 해외주식 종합주문 화면의 좌측 하단 '실시간잔고' 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.  다만 미국주간거래 가능종목에 대해서는 frcr_evlu_pfls_amt(외화평가손익금액), evlu_pfls_rt(평가손익율), ovrs_stck_evlu_amt(해외주식평가금액), now_pric2(현재가격2) 값이 HTS와는 상이하게 표출될 수 있습니다. (주간시간 시간대에 HTS는 주간

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | N | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token 일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용) 법인(Access t |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appsecret (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | [실전투자] TTTS3012R  [모의투자] VTTS3012R |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우) |
| `custtype` | 고객타입 | string | N | 1 | B : 법인 P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호 ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `CANO` | 종합계좌번호 | string | Y | 8 | 계좌번호 체계(8-2)의 앞 8자리 |
| `ACNT_PRDT_CD` | 계좌상품코드 | string | Y | 2 | 계좌번호 체계(8-2)의 뒤 2자리 |
| `OVRS_EXCG_CD` | 해외거래소코드 | string | Y | 4 | [모의] NASD : 나스닥 NYSE : 뉴욕  AMEX : 아멕스  [실전] NASD : 미국전체 NAS : 나스닥 NYSE : 뉴욕  AMEX : 아멕스  [모의/실전 공통] SEHK : 홍콩 SHAA : 중국상 |
| `TR_CRCY_CD` | 거래통화코드 | string | Y | 3 | USD : 미국달러 HKD : 홍콩달러 CNY : 중국위안화 JPY : 일본엔화 VND : 베트남동 |
| `CTX_AREA_FK200` | 연속조회검색조건200 | string | N | 200 | 공란 : 최초 조회시 이전 조회 Output CTX_AREA_FK200값 : 다음페이지 조회시(2번째부터) |
| `CTX_AREA_NK200` | 연속조회키200 | string | N | 200 | 공란 : 최초 조회시 이전 조회 Output CTX_AREA_NK200값 : 다음페이지 조회시(2번째부터) |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | Y | 1 | F or M : 다음 데이터 있음 D or E : 마지막 데이터 |
| `gt_uid` | Global UID | string | Y | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 | 0 : 성공  0 이외의 값 : 실패 |
| `msg_cd` | 응답코드 | string | Y | 8 | 응답코드 |
| `msg1` | 응답메세지 | string | Y | 80 | 응답메세지 |
| `ctx_area_fk200` | 연속조회검색조건200 | string | Y | 200 |  |
| `ctx_area_nk200` | 연속조회키200 | string | Y | 200 |  |
| `output1` | 응답상세1 | array | Y |  |  |
| `cano` | 종합계좌번호 | string | Y | 8 | 계좌번호 체계(8-2)의 앞 8자리 |
| `acnt_prdt_cd` | 계좌상품코드 | string | Y | 2 | 계좌상품코드 |
| `prdt_type_cd` | 상품유형코드 | string | Y | 3 |  |
| `ovrs_pdno` | 해외상품번호 | string | Y | 12 |  |
| `ovrs_item_name` | 해외종목명 | string | Y | 60 |  |
| `frcr_evlu_pfls_amt` | 외화평가손익금액 | string | Y | 30 | 해당 종목의 매입금액과 평가금액의 외회기준 비교 손익 |
| `evlu_pfls_rt` | 평가손익율 | string | Y | 10 | 해당 종목의 평가손익을 기준으로 한 수익률 |
| `pchs_avg_pric` | 매입평균가격 | string | Y | 23 | 해당 종목의 매수 평균 단가 |
| `ovrs_cblc_qty` | 해외잔고수량 | string | Y | 19 |  |
| `ord_psbl_qty` | 주문가능수량 | string | Y | 10 | 매도 가능한 주문 수량 |
| `frcr_pchs_amt1` | 외화매입금액1 | string | Y | 23 | 해당 종목의 외화 기준 매입금액 |
| `ovrs_stck_evlu_amt` | 해외주식평가금액 | string | Y | 32 | 해당 종목의 외화 기준 평가금액 |
| `now_pric2` | 현재가격2 | string | Y | 25 | 해당 종목의 현재가 |
| `tr_crcy_cd` | 거래통화코드 | string | Y | 3 | USD : 미국달러 HKD : 홍콩달러 CNY : 중국위안화 JPY : 일본엔화 VND : 베트남동 |
| `ovrs_excg_cd` | 해외거래소코드 | string | Y | 4 | NASD : 나스닥 NYSE : 뉴욕 AMEX : 아멕스 SEHK : 홍콩 SHAA : 중국상해 SZAA : 중국심천 TKSE : 일본 HASE : 하노이거래소 VNSE : 호치민거래소 |
| `loan_type_cd` | 대출유형코드 | string | Y | 2 | 00 : 해당사항없음 01 : 자기융자일반형 03 : 자기융자투자형 05 : 유통융자일반형 06 : 유통융자투자형 07 : 자기대주 09 : 유통대주 10 : 현금 11 : 주식담보대출 12 : 수익증권담보대출 13 |
| `loan_dt` | 대출일자 | string | Y | 8 | 대출 실행일자 |
| `expd_dt` | 만기일자 | string | Y | 8 | 대출 만기일자 |
| `output2` | 응답상세2 | object | Y |  |  |
| `frcr_pchs_amt1` | 외화매입금액1 | string | Y | 24 |  |
| `ovrs_rlzt_pfls_amt` | 해외실현손익금액 | string | Y | 20 |  |
| `ovrs_tot_pfls` | 해외총손익 | string | Y | 24 |  |
| `rlzt_erng_rt` | 실현수익율 | string | Y | 32 |  |
| `tot_evlu_pfls_amt` | 총평가손익금액 | string | Y | 32 |  |
| `tot_pftrt` | 총수익률 | string | Y | 32 |  |
| `frcr_buy_amt_smtl1` | 외화매수금액합계1 | string | Y | 25 |  |
| `ovrs_rlzt_pfls_amt2` | 해외실현손익금액2 | string | Y | 24 |  |
| `frcr_buy_amt_smtl2` | 외화매수금액합계2 | string | Y | 25 |  |

**Request 예시**
```
{ "CANO": "810XXXXX", "ACNT_PRDT_CD":"01", "OVRS_EXCG_CD": "NASD", "TR_CRCY_CD": "USD", "CTX_AREA_FK200": "", "CTX_AREA_NK200": "" }
```

**Response 예시**
```json
{   "ctx_area_fk200": "                                                                                                                                                                                                        ",   "ctx_area_nk200": "                                                                                                                                                         
```

---

### 해외주식 체결기준현재잔고

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-008` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `CTRP6504R` |
| 모의 TR_ID | `VTRP6504R` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| 모의 Domain | `https://openapivts.koreainvestment.com:29443    (output3만 이용 가능)` |
| URL | `/uapi/overseas-stock/v1/trading/inquire-present-balance` |

> 해외주식 잔고를 체결 기준으로 확인하는 API 입니다.   HTS(eFriend Plus) [0839] 해외 체결기준잔고 화면을 API로 구현한 사항으로 화면을 함께 보시면 기능 이해가 쉽습니다.  (※모의계좌의 경우 output3(외화평가총액 등 확인 가능)만 정상 출력됩니다.  잔고 확인을 원하실 경우에는 해외주식 잔고[v1_해외주식-006] API 사용을 부탁드립니다.)  * 해외주식 서비스 신청 후 이용 가능합니다. (아래 링크 3번 해외증권 거래신청 참고) https://securities.koreainves

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | N | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token 일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용) 법인(Access t |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appsecret (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | [실전투자] CTRP6504R  [모의투자] VTRP6504R |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우) |
| `custtype` | 고객타입 | string | N | 1 | B : 법인 P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호 ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `CANO` | 종합계좌번호 | string | Y | 8 | 계좌번호 체계(8-2)의 앞 8자리 |
| `ACNT_PRDT_CD` | 계좌상품코드 | string | Y | 2 | 계좌번호 체계(8-2)의 뒤 2자리 |
| `WCRC_FRCR_DVSN_CD` | 원화외화구분코드 | string | Y | 2 | 01 : 원화  02 : 외화 |
| `NATN_CD` | 국가코드 | string | Y | 3 | 000 전체 840 미국 344 홍콩 156 중국 392 일본 704 베트남 |
| `TR_MKET_CD` | 거래시장코드 | string | Y | 2 | [Request body NATN_CD 000 설정] 00 : 전체  [Request body NATN_CD 840 설정] 00 : 전체 01 : 나스닥(NASD) 02 : 뉴욕거래소(NYSE) 03 : 미국(PIN |
| `INQR_DVSN_CD` | 조회구분코드 | string | Y | 2 | 00 : 전체  01 : 일반해외주식  02 : 미니스탁 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | Y | 1 | F or M : 다음 데이터 있음 D or E : 마지막 데이터 |
| `gt_uid` | Global UID | string | Y | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 | 0 : 성공  0 이외의 값 : 실패 |
| `msg_cd` | 응답코드 | string | Y | 8 | 응답코드 |
| `msg1` | 응답메세지 | string | Y | 80 | 응답메세지 |
| `output1` | 응답상세1 (체결기준 잔고) | array | Y |  | 체결기준현재잔고 없으면 빈값으로 출력 |
| `prdt_name` | 상품명 | string | Y | 60 | 종목명 |
| `cblc_qty13` | 잔고수량13 | string | Y | 32 | 결제보유수량 |
| `thdt_buy_ccld_qty1` | 당일매수체결수량1 | string | Y | 32 | 당일 매수 체결 완료 수량 |
| `thdt_sll_ccld_qty1` | 당일매도체결수량1 | string | Y | 32 | 당일 매도 체결 완료 수량 |
| `ccld_qty_smtl1` | 체결수량합계1 | string | Y | 32 | 체결기준 현재 보유수량 |
| `ord_psbl_qty1` | 주문가능수량1 | string | Y | 32 | 주문 가능한 주문 수량 |
| `frcr_pchs_amt` | 외화매입금액 | string | Y | 29 | 해당 종목의 외화 기준 매입금액 |
| `frcr_evlu_amt2` | 외화평가금액2 | string | Y | 30 | 해당 종목의 외화 기준 평가금액 |
| `evlu_pfls_amt2` | 평가손익금액2 | string | Y | 31 | 해당 종목의 매입금액과 평가금액의 외회기준 비교 손익 |
| `evlu_pfls_rt1` | 평가손익율1 | string | Y | 32 | 해당 종목의 평가손익을 기준으로 한 수익률 |
| `pdno` | 상품번호 | string | Y | 12 | 종목코드 |
| `bass_exrt` | 기준환율 | string | Y | 31 | 원화 평가 시 적용 환율 |
| `buy_crcy_cd` | 매수통화코드 | string | Y | 3 | USD : 미국달러 HKD : 홍콩달러 CNY : 중국위안화 JPY : 일본엔화 VND : 베트남동 |
| `ovrs_now_pric1` | 해외현재가격1 | string | Y | 29 | 해당 종목의 현재가 |
| `avg_unpr3` | 평균단가3 | string | Y | 29 | 해당 종목의 매수 평균 단가 |
| `tr_mket_name` | 거래시장명 | string | Y | 60 | 해당 종목의 거래시장명 |
| `natn_kor_name` | 국가한글명 | string | Y | 60 | 거래 국가명 |
| `pchs_rmnd_wcrc_amt` | 매입잔액원화금액 | string | Y | 19 |  |
| `thdt_buy_ccld_frcr_amt` | 당일매수체결외화금액 | object | Y | 30 | 당일 매수 외화금액 (Type: Object X String O) |
| `thdt_sll_ccld_frcr_amt` | 당일매도체결외화금액 | string | Y | 30 | 당일 매도 외화금액 |
| `unit_amt` | 단위금액 | string | Y | 19 |  |
| `std_pdno` | 표준상품번호 | string | Y | 12 |  |
| `prdt_type_cd` | 상품유형코드 | string | Y | 3 |  |
| `scts_dvsn_name` | 유가증권구분명 | string | Y | 60 |  |
| `loan_rmnd` | 대출잔액 | string | Y | 19 | 대출 미상환 금액 |
| `loan_dt` | 대출일자 | string | Y | 8 | 대출 실행일자 |
| `loan_expd_dt` | 대출만기일자 | string | Y | 8 | 대출 만기일자 |
| `ovrs_excg_cd` | 해외거래소코드 | string | Y | 4 | NASD : 나스닥 NYSE : 뉴욕 AMEX : 아멕스 SEHK : 홍콩 SHAA : 중국상해 SZAA : 중국심천 TKSE : 일본 HASE : 하노이거래소 VNSE : 호치민거래소 |
| `item_lnkg_excg_cd` | 종목연동거래소코드 | string | Y | 4 | prdt_dvsn(상품구분) : 직원용 데이터(Type: String, Length:2) |
| `output2` | 응답상세2 | array | Y |  |  |
| `crcy_cd` | 통화코드 | string | Y | 3 |  |
| `crcy_cd_name` | 통화코드명 | string | Y | 60 |  |
| `frcr_buy_amt_smtl` | 외화매수금액합계 | string | Y | 29 | 해당 통화로 매수한 종목 전체의 매수금액 |
| `frcr_sll_amt_smtl` | 외화매도금액합계 | string | Y | 29 | 해당 통화로 매도한 종목 전체의 매수금액 |
| `frcr_dncl_amt_2` | 외화예수금액2 | string | Y | 29 | 외화로 표시된 외화사용가능금액 |
| `frst_bltn_exrt` | 최초고시환율 | string | Y | 31 |  |
| `frcr_buy_mgn_amt` | 외화매수증거금액 | string | Y | 31 | 매수증거금으로 사용된 외화금액 |
| `frcr_etc_mgna` | 외화기타증거금 | string | Y | 31 |  |
| `frcr_drwg_psbl_amt_1` | 외화출금가능금액1 | string | Y | 29 | 출금가능한 외화금액 |
| `frcr_evlu_amt2` | 출금가능원화금액 | string | Y | 29 | 출금가능한 원화금액 |
| `acpl_cstd_crcy_yn` | 현지보관통화여부 | string | Y | 1 |  |
| `nxdy_frcr_drwg_psbl_amt` | 익일외화출금가능금액 | string | Y | 31 |  |
| `output3` | 응답상세3 | object | Y |  |  |
| `pchs_amt_smtl` | 매입금액합계 | string | Y | 19 | 해외유가증권 매수금액의 원화 환산 금액 |
| `evlu_amt_smtl` | 평가금액합계 | string | Y | 19 | 해외유가증권 평가금액의 원화 환산 금액 |
| `evlu_pfls_amt_smtl` | 평가손익금액합계 | string | Y | 19 | 해외유가증권 평가손익의 원화 환산 금액 |
| `dncl_amt` | 예수금액 | string | Y | 19 |  |
| `cma_evlu_amt` | CMA평가금액 | string | Y | 19 |  |
| `tot_dncl_amt` | 총예수금액 | string | Y | 19 |  |
| `etc_mgna` | 기타증거금 | string | Y | 19 |  |
| `wdrw_psbl_tot_amt` | 인출가능총금액 | string | Y | 19 |  |
| `frcr_evlu_tota` | 외화평가총액 | string | Y | 19 |  |
| `evlu_erng_rt1` | 평가수익율1 | string | Y | 31 |  |
| `pchs_amt_smtl_amt` | 매입금액합계금액 | string | Y | 19 |  |
| `evlu_amt_smtl_amt` | 평가금액합계금액 | string | Y | 19 |  |
| `tot_evlu_pfls_amt` | 총평가손익금액 | string | Y | 31 |  |
| `tot_asst_amt` | 총자산금액 | string | Y | 19 |  |
| `buy_mgn_amt` | 매수증거금액 | string | Y | 19 |  |
| `mgna_tota` | 증거금총액 | string | Y | 19 |  |
| `frcr_use_psbl_amt` | 외화사용가능금액 | string | Y | 20 |  |
| `ustl_sll_amt_smtl` | 미결제매도금액합계 | string | Y | 19 |  |
| `ustl_buy_amt_smtl` | 미결제매수금액합계 | string | Y | 19 |  |
| `tot_frcr_cblc_smtl` | 총외화잔고합계 | string | Y | 29 |  |
| `tot_loan_amt` | 총대출금액 | string | Y | 19 |  |

**Request 예시**
```
{ "CANO": "810XXXXX", "ACNT_PRDT_CD":"01", "WCRC_FRCR_DVSN_CD": "01", "TR_MKET_CD": "00", "NATN_CD": "000", "INQR_DVSN_CD": "00" }
```

**Response 예시**
```json
{   "output1": [     {       "prdt_name": "애플",       "cblc_qty13": "40.00000000",       "thdt_buy_ccld_qty1": "0.00000000",       "thdt_sll_ccld_qty1": "0.00000000",       "ccld_qty_smtl1": "40.00000000",       "ord_psbl_qty1": "40.00000000",       "frcr_pchs_amt": "6411629.00000",       "frcr_evlu_amt2": "8491110.000000",       "evlu_pfls_amt2": "2079481.00000",       "evlu_pfls_rt1": "32.430000
```

---

### 해외주식 주문체결내역

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-007` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `TTTS3035R` |
| 모의 TR_ID | `VTTS3035R` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| 모의 Domain | `https://openapivts.koreainvestment.com:29443` |
| URL | `/uapi/overseas-stock/v1/trading/inquire-ccnl` |

> 일정 기간의 해외주식 주문 체결 내역을 확인하는 API입니다. 실전계좌의 경우, 한 번의 호출에 최대 20건까지 확인 가능하며, 이후의 값은 연속조회를 통해 확인하실 수 있습니다.  모의계좌의 경우, 한 번의 호출에 최대 15건까지 확인 가능하며, 이후의 값은 연속조회를 통해 확인하실 수 있습니다.   * 해외주식 서비스 신청 후 이용 가능합니다. (아래 링크 3번 해외증권 거래신청 참고) https://securities.koreainvestment.com/main/bond/research/_static/TF03ca010

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | N | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token 일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용) 법인(Access t |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appsecret (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | [실전투자] TTTS3035R  [모의투자] VTTS3035R |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우) |
| `custtype` | 고객타입 | string | N | 1 | B : 법인 P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호 ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `CANO` | 종합계좌번호 | string | Y | 8 | 계좌번호 체계(8-2)의 앞 8자리 |
| `ACNT_PRDT_CD` | 계좌상품코드 | string | Y | 2 | 계좌번호 체계(8-2)의 뒤 2자리 |
| `PDNO` | 상품번호 | string | Y | 12 | 전종목일 경우 "%" 입력 ※ 모의투자계좌의 경우 ""(전체 조회)만 가능 |
| `ORD_STRT_DT` | 주문시작일자 | string | Y | 8 | YYYYMMDD 형식 (현지시각 기준) |
| `ORD_END_DT` | 주문종료일자 | string | Y | 8 | YYYYMMDD 형식 (현지시각 기준) |
| `SLL_BUY_DVSN` | 매도매수구분 | string | Y | 2 | 00 : 전체  01 : 매도  02 : 매수 ※ 모의투자계좌의 경우 "00"(전체 조회)만 가능 |
| `CCLD_NCCS_DVSN` | 체결미체결구분 | string | Y | 2 | 00 : 전체  01 : 체결  02 : 미체결 ※ 모의투자계좌의 경우 "00"(전체 조회)만 가능 |
| `OVRS_EXCG_CD` | 해외거래소코드 | string | Y | 4 | 전종목일 경우 "%" 입력 NASD : 미국시장 전체(나스닥, 뉴욕, 아멕스) NYSE : 뉴욕 AMEX : 아멕스 SEHK : 홍콩  SHAA : 중국상해 SZAA : 중국심천 TKSE : 일본 HASE : 베트남 |
| `SORT_SQN` | 정렬순서 | string | Y | 2 | DS : 정순 AS : 역순  ※ 모의투자계좌의 경우 정렬순서 사용불가(Default : DS(정순)) |
| `ORD_DT` | 주문일자 | string | Y | 8 | "" (Null 값 설정) |
| `ORD_GNO_BRNO` | 주문채번지점번호 | string | Y | 5 | "" (Null 값 설정) |
| `ODNO` | 주문번호 | string | Y | 10 | "" (Null 값 설정) ※ 주문번호로 검색 불가능합니다. 반드시 ""(Null 값 설정) 바랍니다. |
| `CTX_AREA_NK200` | 연속조회키200 | string | Y | 200 | 공란 : 최초 조회시 이전 조회 Output CTX_AREA_NK200값 : 다음페이지 조회시(2번째부터) |
| `CTX_AREA_FK200` | 연속조회검색조건200 | string | Y | 200 | 공란 : 최초 조회시 이전 조회 Output CTX_AREA_FK200값 : 다음페이지 조회시(2번째부터) |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | Y | 1 | F or M : 다음 데이터 있음 D or E : 마지막 데이터 |
| `gt_uid` | Global UID | string | Y | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 | 0 : 성공  0 이외의 값 : 실패 |
| `msg_cd` | 응답코드 | string | Y | 8 | 응답코드 |
| `msg1` | 응답메세지 | string | Y | 80 | 응답메세지 |
| `ctx_area_fk200` | 연속조회검색조건200 | string | Y | 200 |  |
| `ctx_area_nk200` | 연속조회키200 | string | Y | 200 |  |
| `output` | 응답상세 | array | Y |  |  |
| `ord_dt` | 주문일자 | string | Y | 8 | 주문접수 일자 (현지시각 기준) |
| `ord_gno_brno` | 주문채번지점번호 | string | Y | 5 | 계좌 개설 시 관리점으로 선택한 영업점의 고유번호 |
| `odno` | 주문번호 | string | Y | 10 | 접수한 주문의 일련번호 ※ 정정취소주문 시, 해당 값 odno(주문번호) 넣어서 사용 |
| `orgn_odno` | 원주문번호 | string | Y | 10 | 정정 또는 취소 대상 주문의 일련번호 |
| `sll_buy_dvsn_cd` | 매도매수구분코드 | string | Y | 2 | 01 : 매도  02 : 매수 |
| `sll_buy_dvsn_cd_name` | 매도매수구분코드명 | string | Y | 60 |  |
| `rvse_cncl_dvsn` | 정정취소구분 | string | Y | 2 | 01 : 정정  02 : 취소 |
| `rvse_cncl_dvsn_name` | 정정취소구분명 | string | Y | 60 |  |
| `pdno` | 상품번호 | string | Y | 12 |  |
| `prdt_name` | 상품명 | string | Y | 60 |  |
| `ft_ord_qty` | FT주문수량 | string | Y | 10 | 주문수량 |
| `ft_ord_unpr3` | FT주문단가3 | string | Y | 26 | 주문가격 |
| `ft_ccld_qty` | FT체결수량 | string | Y | 10 | 체결된 수량 |
| `ft_ccld_unpr3` | FT체결단가3 | string | Y | 26 | 체결된 가격 |
| `ft_ccld_amt3` | FT체결금액3 | string | Y | 23 | 체결된 금액 |
| `nccs_qty` | 미체결수량 | string | Y | 10 | 미체결수량 |
| `prcs_stat_name` | 처리상태명 | string | Y | 60 | 완료, 거부, 전송 |
| `rjct_rson` | 거부사유 | string | Y | 60 | 정상 처리되지 못하고 거부된 주문의 사유 |
| `rjct_rson_name` | 거부사유명 | string | Y | 60 |  |
| `ord_tmd` | 주문시각 | string | Y | 6 | 주문 접수 시간 |
| `tr_mket_name` | 거래시장명 | string | Y | 60 |  |
| `tr_natn` | 거래국가 | string | Y | 3 |  |
| `tr_natn_name` | 거래국가명 | string | Y | 3 |  |
| `ovrs_excg_cd` | 해외거래소코드 | string | Y | 4 | NASD : 나스닥 NYSE : 뉴욕 AMEX : 아멕스 SEHK : 홍콩  SHAA : 중국상해 SZAA : 중국심천 TKSE : 일본 HASE : 베트남 하노이 VNSE : 베트남 호치민 |
| `tr_crcy_cd` | 거래통화코드 | string | Y | 60 |  |
| `dmst_ord_dt` | 국내주문일자 | string | Y | 8 |  |
| `thco_ord_tmd` | 당사주문시각 | string | Y | 6 |  |
| `loan_type_cd` | 대출유형코드 | string | Y | 2 | 00 : 해당사항없음 01 : 자기융자일반형 03 : 자기융자투자형 05 : 유통융자일반형 06 : 유통융자투자형 07 : 자기대주 09 : 유통대주 10 : 현금 11 : 주식담보대출 12 : 수익증권담보대출 13 |
| `loan_dt` | 대출일자 | string | Y | 8 |  |
| `mdia_dvsn_name` | 매체구분명 | string | Y | 60 | ex) OpenAPI, 모바일 |
| `usa_amk_exts_rqst_yn` | 미국애프터마켓연장신청여부 | string | Y | 1 | Y/N |
| `splt_buy_attr_name` | 분할매수/매도속성명 | string | Y | 60 | 정규장 종료 주문 시에는 '정규장 종료', 시간 입력 시에는 from ~ to 시간 표시 |

**Request 예시**
```
{ 	"CANO": "810XXXXX", 	"ACNT_PRDT_CD":"01", 	"PDNO": ""%, 	"ORD_STRT_DT": "20211027", 	"ORD_END_DT": "20211027", 	"SLL_BUY_DVSN": "00", 	"CCLD_NCCS_DVSN": "00", 	"OVRS_EXCG_CD": "%", 	"SORT_SQN": "DS", 	"ORD_DT": "", 	"ORD_GNO_BRNO":"02111", 	"ODNO": "", 	"CTX_AREA_NK200": "", 	"CTX_AREA_FK200": "" }
```

**Response 예시**
```json
{   "ctx_area_nk200": "                                                                                                                                                                                                        ",   "ctx_area_fk200": "12345678^01^^20211027^20211027^00^00^NASD^^                                                                                                              
```

---

### 해외주식 미체결내역

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-005` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `TTTS3018R` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/trading/inquire-nccs` |

> 접수된 해외주식 주문 중 체결되지 않은 미체결 내역을 조회하는 API입니다. 실전계좌의 경우, 한 번의 호출에 최대 40건까지 확인 가능하며, 이후의 값은 연속조회를 통해 확인하실 수 있습니다.   ※ 해외주식 미체결내역 API 모의투자에서는 사용이 불가합니다.     모의투자로 해외주식 미체결내역 확인시에는 해외주식 주문체결내역[v1_해외주식-007] API 조회하셔서 nccs_qty(미체결수량)으로 해외주식 미체결수량을 조회하실 수 있습니다.   * 해외주식 서비스 신청 후 이용 가능합니다. (아래 링크 3번 해외증

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | N | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token 일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용) 법인(Access t |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appsecret (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | [실전투자] TTTS3018R |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객타입 | string | N | 1 | B : 법인 P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호 ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `CANO` | 종합계좌번호 | string | Y | 8 | 계좌번호 체계(8-2)의 앞 8자리 |
| `ACNT_PRDT_CD` | 계좌상품코드 | string | Y | 2 | 계좌번호 체계(8-2)의 뒤 2자리 |
| `OVRS_EXCG_CD` | 해외거래소코드 | string | Y | 4 | NASD : 나스닥 NYSE : 뉴욕  AMEX : 아멕스 SEHK : 홍콩 SHAA : 중국상해 SZAA : 중국심천 TKSE : 일본 HASE : 베트남 하노이 VNSE : 베트남 호치민  * NASD 인 경우만 |
| `SORT_SQN` | 정렬순서 | string | Y | 2 | DS : 정순 그외 : 역순  [header tr_id: TTTS3018R] ""(공란) |
| `CTX_AREA_FK200` | 연속조회검색조건200 | string | Y | 200 | 공란 : 최초 조회시 이전 조회 Output CTX_AREA_FK200값 : 다음페이지 조회시(2번째부터) |
| `CTX_AREA_NK200` | 연속조회키200 | string | Y | 200 | 공란 : 최초 조회시 이전 조회 Output CTX_AREA_NK200값 : 다음페이지 조회시(2번째부터) |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | Y | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | Y | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 | 0 : 성공  0 이외의 값 : 실패 |
| `msg_cd` | 응답코드 | string | Y | 8 | 응답코드 |
| `msg1` | 응답메세지 | string | Y | 80 | 응답메세지 |
| `ctx_area_fk200` | 연속조회검색조건200 | string | Y | 200 |  |
| `ctx_area_nk200` | 연속조회키200 | string | Y | 200 |  |
| `output` | 응답상세 | array | Y |  |  |
| `ord_dt` | 주문일자 | string | Y | 8 | 주문접수 일자 |
| `ord_gno_brno` | 주문채번지점번호 | string | Y | 5 | 계좌 개설 시 관리점으로 선택한 영업점의 고유번호 |
| `odno` | 주문번호 | string | Y | 10 | 접수한 주문의 일련번호 |
| `orgn_odno` | 원주문번호 | string | Y | 10 | 정정 또는 취소 대상 주문의 일련번호 |
| `pdno` | 상품번호 | string | Y | 12 | 종목코드 |
| `prdt_name` | 상품명 | string | Y | 60 | 종목명 |
| `sll_buy_dvsn_cd` | 매도매수구분코드 | string | Y | 2 | 01 : 매도 02 : 매수 |
| `sll_buy_dvsn_cd_name` | 매도매수구분코드명 | string | Y | 60 | 매수매도구분명 |
| `rvse_cncl_dvsn_cd` | 정정취소구분코드 | string | Y | 2 | 01 : 정정 02 : 취소 |
| `rvse_cncl_dvsn_cd_name` | 정정취소구분코드명 | string | Y | 60 | 정정취소구분명 |
| `rjct_rson` | 거부사유 | string | Y | 60 | 정상 처리되지 못하고 거부된 주문의 사유 |
| `rjct_rson_name` | 거부사유명 | string | Y | 60 | 정상 처리되지 못하고 거부된 주문의 사유명 |
| `ord_tmd` | 주문시각 | string | Y | 6 | 주문 접수 시간 |
| `tr_mket_name` | 거래시장명 | string | Y | 60 |  |
| `tr_crcy_cd` | 거래통화코드 | string | Y | 3 | USD : 미국달러 HKD : 홍콩달러 CNY : 중국위안화 JPY : 일본엔화 VND : 베트남동 |
| `natn_cd` | 국가코드 | string | Y | 3 |  |
| `natn_kor_name` | 국가한글명 | string | Y | 60 |  |
| `ft_ord_qty` | FT주문수량 | string | Y | 10 | 주문수량 |
| `ft_ccld_qty` | FT체결수량 | string | Y | 10 | 체결된 수량 |
| `nccs_qty` | 미체결수량 | string | Y | 10 | 미체결수량 |
| `ft_ord_unpr3` | FT주문단가3 | string | Y | 26 | 주문가격 |
| `ft_ccld_unpr3` | FT체결단가3 | string | Y | 26 | 체결된 가격 |
| `ft_ccld_amt3` | FT체결금액3 | string | Y | 23 | 체결된 금액 |
| `ovrs_excg_cd` | 해외거래소코드 | string | Y | 4 | NASD : 나스닥 NYSE : 뉴욕 AMEX : 아멕스 SEHK : 홍콩 SHAA : 중국상해 SZAA : 중국심천 TKSE : 일본 HASE : 베트남 하노이 VNSE : 베트남 호치민 |
| `prcs_stat_name` | 처리상태명 | string | Y | 60 | "" |
| `loan_type_cd` | 대출유형코드 | string | Y | 2 | 00 해당사항없음 01 자기융자일반형 03 자기융자투자형 05 유통융자일반형 06 유통융자투자형 07 자기대주 09 유통대주 10 현금 11 주식담보대출 12 수익증권담보대출 13 ELS담보대출 14 채권담보대출 1 |
| `loan_dt` | 대출일자 | string | Y | 8 | 대출 실행일자 |
| `usa_amk_exts_rqst_yn` | 미국애프터마켓연장신청여부 | string | Y | 1 | Y/N |
| `splt_buy_attr_name` | 분할매수속성명 | string | Y | 60 | 정규장 종료 주문 시에는 '정규장 종료', 시간 입력 시에는 from ~ to 시간 표시됨 |

**Request 예시**
```
{ "CANO": "810XXXXX", "ACNT_PRDT_CD":"01", "OVRS_EXCG_CD": "NYSE", "SORT_SQN": "DS", "CTX_AREA_FK200": "", "CTX_AREA_NK200": "" }
```

**Response 예시**
```json
{   "ctx_area_fk200": "81055689^01^NYSE^DS^                                                                                                                                                                                    ",   "ctx_area_nk200": "                                                                                                                                                         
```

---

### 해외주식 매수가능금액조회

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-014` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `TTTS3007R` |
| 모의 TR_ID | `VTTS3007R` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| 모의 Domain | `https://openapivts.koreainvestment.com:29443` |
| URL | `/uapi/overseas-stock/v1/trading/inquire-psamount` |

> 해외주식 매수가능금액조회 API입니다.  * 해외주식 서비스 신청 후 이용 가능합니다. (아래 링크 3번 해외증권 거래신청 참고) https://securities.koreainvestment.com/main/bond/research/_static/TF03ca010001.jsp

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | N | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | [실전투자] TTTS3007R  [모의투자] VTTS3007R |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | N | 1 | B : 법인 / P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | 법인 : "001" / 개인: ""(Default) |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `CANO` | 종합계좌번호 | string | Y | 8 | 계좌번호 체계(8-2)의 앞 8자리 |
| `ACNT_PRDT_CD` | 계좌상품코드 | string | Y | 2 | 계좌번호 체계(8-2)의 뒤 2자리 |
| `OVRS_EXCG_CD` | 해외거래소코드 | string | Y | 4 | NASD : 나스닥 / NYSE : 뉴욕 / AMEX : 아멕스 SEHK : 홍콩 / SHAA : 중국상해 / SZAA : 중국심천 TKSE : 일본 / HASE : 하노이거래소 / VNSE : 호치민거래소 |
| `OVRS_ORD_UNPR` | 해외주문단가 | string | Y | 27 | 해외주문단가 (23.8) 정수부분 23자리, 소수부분 8자리 |
| `ITEM_CD` | 종목코드 | string | Y | 12 | 종목코드 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output` | 응답상세1 | object | N |  |  |
| `tr_crcy_cd` | 거래통화코드 | string | N | 3 | 18.2 |
| `ord_psbl_frcr_amt` | 주문가능외화금액 | string | N | 21 | 18.2 |
| `sll_ruse_psbl_amt` | 매도재사용가능금액 | string | N | 21 | 가능금액 산정 시 사용 |
| `ovrs_ord_psbl_amt` | 해외주문가능금액 | string | N | 21 | - 한국투자 앱 해외주식 주문화면내 "외화" 인경우 주문가능금액 |
| `max_ord_psbl_qty` | 최대주문가능수량 | string | N | 19 | - 한국투자 앱 해외주식 주문화면내 "외화" 인경우 주문가능수량 - 매수 시 수량단위 절사해서 사용     예 : (100주단위) 545 주 -> 500 주 / (10주단위) 545 주 -> 540 주 |
| `echm_af_ord_psbl_amt` | 환전이후주문가능금액 | string | N | 21 | 사용되지 않는 사항(0으로 출력) |
| `echm_af_ord_psbl_qty` | 환전이후주문가능수량 | string | N | 19 | 사용되지 않는 사항(0으로 출력) |
| `ord_psbl_qty` | 주문가능수량 | string | N | 10 | 22(20.1) |
| `exrt` | 환율 | string | N | 22 | 25(18.6) |
| `frcr_ord_psbl_amt1` | 외화주문가능금액1 | string | N | 25 | - 한국투자 앱 해외주식 주문화면내 "통합" 인경우 주문가능금액 |
| `ovrs_max_ord_psbl_qty` | 해외최대주문가능수량 | string | N | 19 | - 한국투자 앱 해외주식 주문화면내 "통합" 인경우 주문가능수량 - 매수 시 수량단위 절사해서 사용     예 : (100주단위) 545 주 -> 500 주 / (10주단위) 545 주 -> 540 주 |

**Request 예시**
```
"input": {             "ACNT_PRDT_CD": "01",             "CANO": "81019777",             "ITEM_CD": "00011",             "OVRS_EXCG_CD": "SEHK",             "OVRS_ORD_UNPR": "133.200"         }
```

**Response 예시**
```json
"output": {             "echm_af_ord_psbl_amt": "0.00",             "echm_af_ord_psbl_qty": "0",             "exrt": "165.5400000000",             "frcr_ord_psbl_amt1": "955**.12",             "max_ord_psbl_qty": "744**",             "ord_psbl_frcr_amt": "999**.52",             "ord_psbl_qty": "744**",             "ovrs_max_ord_psbl_qty": "717**",             "ovrs_ord_psbl_amt": "992**.35",      
```

---

### 해외주식 기간손익

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-032` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `TTTS3039R` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/trading/inquire-period-profit` |

> 해외주식 기간손익 API입니다. 한국투자 HTS(eFriend Plus) &gt; [7717] 해외 기간손익 화면의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.  * 해외주식 서비스 신청 후 이용 가능합니다. (아래 링크 3번 해외증권 거래신청 참고) https://securities.koreainvestment.com/main/bond/research/_static/TF03ca010001.jsp  [해외 기간손익 유의 사항] ■ 단순 매체결내역을 기초로 만든 화면으로 매도체결시점

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | [실전투자] TTTS3039R |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우) |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `CANO` | 종합계좌번호 | string | Y | 8 | 계좌번호 체계(8-2)의 앞 8자리 |
| `ACNT_PRDT_CD` | 계좌상품코드 | string | Y | 2 | 계좌번호 체계(8-2)의 뒤 2자리 |
| `OVRS_EXCG_CD` | 해외거래소코드 | string | Y | 2 | 공란 : 전체,  NASD : 미국, SEHK : 홍콩, SHAA : 중국, TKSE : 일본, HASE : 베트남 |
| `NATN_CD` | 국가코드 | string | Y | 2 | 공란(Default) |
| `CRCY_CD` | 통화코드 | string | Y | 2 | 공란 : 전체 USD : 미국달러, HKD : 홍콩달러, CNY : 중국위안화,  JPY : 일본엔화, VND : 베트남동 |
| `PDNO` | 상품번호 | string | Y | 2 | 공란 : 전체 |
| `INQR_STRT_DT` | 조회시작일자 | string | Y | 2 | YYYYMMDD |
| `INQR_END_DT` | 조회종료일자 | string | Y | 2 | YYYYMMDD |
| `WCRC_FRCR_DVSN_CD` | 원화외화구분코드 | string | Y | 2 | 01 : 외화, 02 : 원화 |
| `CTX_AREA_FK200` | 연속조회검색조건200 | string | Y | 2 |  |
| `CTX_AREA_NK200` | 연속조회키200 | string | Y | 2 |  |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | F or M : 다음 데이터 있음 D or E : 마지막 데이터 |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `Output1` | 응답상세 | object array | Y |  | array |
| `trad_day` | 매매일 | string | Y | 8 |  |
| `ovrs_pdno` | 해외상품번호 | string | Y | 12 |  |
| `ovrs_item_name` | 해외종목명 | string | Y | 60 |  |
| `slcl_qty` | 매도청산수량 | string | Y | 10 |  |
| `pchs_avg_pric` | 매입평균가격 | string | Y | 184 |  |
| `frcr_pchs_amt1` | 외화매입금액1 | string | Y | 185 |  |
| `avg_sll_unpr` | 평균매도단가 | string | Y | 238 |  |
| `frcr_sll_amt_smtl1` | 외화매도금액합계1 | string | Y | 186 |  |
| `stck_sll_tlex` | 주식매도제비용 | string | Y | 184 |  |
| `ovrs_rlzt_pfls_amt` | 해외실현손익금액 | string | Y | 145 |  |
| `pftrt` | 수익률 | string | Y | 238 |  |
| `exrt` | 환율 | string | Y | 201 |  |
| `ovrs_excg_cd` | 해외거래소코드 | string | Y | 4 |  |
| `frst_bltn_exrt` | 최초고시환율 | string | Y | 238 |  |
| `Output2` | 응답상세2 | object | Y |  |  |
| `stck_sll_amt_smtl` | 주식매도금액합계 | string | Y | 184 | WCRC_FRCR_DVSN_CD(원화외화구분코드)가 01(외화)이고 OVRS_EXCG_CD(해외거래소코드)가 공란(전체)인 경우 출력값 무시 |
| `stck_buy_amt_smtl` | 주식매수금액합계 | string | Y | 184 | WCRC_FRCR_DVSN_CD(원화외화구분코드)가 01(외화)이고 OVRS_EXCG_CD(해외거래소코드)가 공란(전체)인 경우 출력값 무시 |
| `smtl_fee1` | 합계수수료1 | string | Y | 138 | WCRC_FRCR_DVSN_CD(원화외화구분코드)가 01(외화)이고 OVRS_EXCG_CD(해외거래소코드)가 공란(전체)인 경우 출력값 무시 |
| `excc_dfrm_amt` | 정산지급금액 | string | Y | 205 | WCRC_FRCR_DVSN_CD(원화외화구분코드)가 01(외화)이고 OVRS_EXCG_CD(해외거래소코드)가 공란(전체)인 경우 출력값 무시 |
| `ovrs_rlzt_pfls_tot_amt` | 해외실현손익총금액 | string | Y | 145 | WCRC_FRCR_DVSN_CD(원화외화구분코드)가 01(외화)이고 OVRS_EXCG_CD(해외거래소코드)가 공란(전체)인 경우 출력값 무시 |
| `tot_pftrt` | 총수익률 | string | Y | 238 |  |
| `bass_dt` | 기준일자 | string | Y | 8 |  |
| `exrt` | 환율 | string | Y | 201 |  |

---

### 해외주식 일별거래내역

| 항목 | 값 |
|------|----|
| API ID | `해외주식-063` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `CTOS4001R` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/trading/inquire-period-trans` |

> 해외주식 일별거래내역 API입니다. 한국투자 HTS(eFriend Plus) &gt; [0828] 해외증권 일별거래내역 화면 의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.  ※ 체결가격, 매매금액, 정산금액, 수수료 원화금액은 국내 결제일까지는 예상환율로 적용되고, 국내 결제일 익일부터 확정환율로 적용됨으로 금액이 변경될 수 있습니다. ※ 해외증권 투자 및 업무문의 안내: 한국투자증권 해외투자지원부 02)3276-5300

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | CTOS4001R |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우) |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `CANO` | 종합계좌번호 | string | Y | 8 |  |
| `ACNT_PRDT_CD` | 계좌상품코드 | string | Y | 2 |  |
| `ERLM_STRT_DT` | 등록시작일자 | string | Y | 8 | 입력날짜 ~ (ex) 20240420) |
| `ERLM_END_DT` | 등록종료일자 | string | Y | 8 | ~입력날짜 (ex) 20240520) |
| `OVRS_EXCG_CD` | 해외거래소코드 | string | Y | 4 | 공백 |
| `PDNO` | 상품번호 | string | Y | 12 | 공백 (전체조회), 개별종목 조회는 상품번호입력 |
| `SLL_BUY_DVSN_CD` | 매도매수구분코드 | string | Y | 2 | 00(전체), 01(매도), 02(매수) |
| `LOAN_DVSN_CD` | 대출구분코드 | string | Y | 2 | 공백 |
| `CTX_AREA_FK100` | 연속조회검색조건100 | string | Y | 100 | 공백 |
| `CTX_AREA_NK100` | 연속조회키100 | string | Y | 100 | 공백 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | F or M : 다음 데이터 있음 D or E : 마지막 데이터 |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `ctx_area_fk100` | 연속조회검색조건100 | string | Y | 100 |  |
| `ctx_area_nk100` | 연속조회키100 | string | Y | 100 |  |
| `output1` | 응답상세 | object array | Y |  | array |
| `trad_dt` | 매매일자 | string | Y | 8 |  |
| `sttl_dt` | 결제일자 | string | Y | 8 |  |
| `sll_buy_dvsn_cd` | 매도매수구분코드 | string | Y | 2 |  |
| `sll_buy_dvsn_name` | 매도매수구분명 | string | Y | 4 |  |
| `pdno` | 상품번호 | string | Y | 12 |  |
| `ovrs_item_name` | 해외종목명 | string | Y | 60 |  |
| `ccld_qty` | 체결수량 | string | Y | 10 |  |
| `amt_unit_ccld_qty` | 금액단위체결수량 | string | Y | 188 |  |
| `ft_ccld_unpr2` | FT체결단가2 | string | Y | 238 |  |
| `ovrs_stck_ccld_unpr` | 해외주식체결단가 | string | Y | 238 |  |
| `tr_frcr_amt2` | 거래외화금액2 | string | Y | 236 |  |
| `tr_amt` | 거래금액 | string | Y | 19 |  |
| `frcr_excc_amt_1` | 외화정산금액1 | string | Y | 236 |  |
| `wcrc_excc_amt` | 원화정산금액 | string | Y | 19 |  |
| `dmst_frcr_fee1` | 국내외화수수료1 | string | Y | 235 |  |
| `frcr_fee1` | 외화수수료1 | string | Y | 236 |  |
| `dmst_wcrc_fee` | 국내원화수수료 | string | Y | 19 |  |
| `ovrs_wcrc_fee` | 해외원화수수료 | string | Y | 19 |  |
| `crcy_cd` | 통화코드 | string | Y | 3 |  |
| `std_pdno` | 표준상품번호 | string | Y | 12 |  |
| `erlm_exrt` | 등록환율 | string | Y | 238 |  |
| `loan_dvsn_cd` | 대출구분코드 | string | Y | 2 |  |
| `loan_dvsn_name` | 대출구분명 | string | Y | 60 |  |
| `output2` | 응답상세 | object | Y |  |  |
| `frcr_buy_amt_smtl` | 외화매수금액합계 | string | Y | 236 |  |
| `frcr_sll_amt_smtl` | 외화매도금액합계 | string | Y | 236 |  |
| `dmst_fee_smtl` | 국내수수료합계 | string | Y | 256 |  |
| `ovrs_fee_smtl` | 해외수수료합계 | string | Y | 236 |  |

**Request 예시**
```
CANO:12345678 ACNT_PRDT_CD:01 ERLM_STRT_DT:20240101 ERLM_END_DT:20240528 OVRS_EXCG_CD: PDNO: SLL_BUY_DVSN_CD:00 LOAN_DVSN_CD: CTX_AREA_FK100: CTX_AREA_NK100:
```

**Response 예시**
```json
{     "ctx_area_fk100": "12345678!^01!^20240101!^20240528!^!^                                                                ",     "ctx_area_nk100": "                                                                                                    ",     "output1": [         {             "trad_dt": "20240116",             "sttl_dt": "20240118",             "sll_buy_dvsn_cd": "01",             
```

---

### 해외주식 예약주문접수

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-002` |
| 통신방식 | REST / POST |
| 실전 TR_ID | `(미국예약매수) TTTT3014U  (미국예약매도) TTTT3016U   (중국/홍콩/일본/베트남 예약주문) TTTS3013U` |
| 모의 TR_ID | `(미국예약매수) VTTT3014U  (미국예약매도) VTTT3016U   (중국/홍콩/일본/베트남 예약주문) VTTS3013U` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| 모의 Domain | `https://openapivts.koreainvestment.com:29443` |
| URL | `/uapi/overseas-stock/v1/trading/order-resv` |

> 미국거래소 운영시간 외 미국주식을 예약 매매하기 위한 API입니다.  * 해외주식 서비스 신청 후 이용 가능합니다. (아래 링크 3번 해외증권 거래신청 참고) https://securities.koreainvestment.com/main/bond/research/_static/TF03ca010001.jsp  ※ POST API의 경우 BODY값의 key값들을 대문자로 작성하셔야 합니다.    (EX. "CANO" : "12345678", "ACNT_PRDT_CD": "01",...)  * 아래 각 국가의 시장별 예약주

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | N | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token 일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용) 법인(Access t |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appsecret (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | [실전투자] TTTT3016U : 미국 매도 예약 주문 TTTT3014U : 미국 매수 예약 주문 TTTS3013U : 중국/홍콩/일본/베트남 예약 매수/매도/취소 주문  [모의투자] VTTT3016U : 미국 매도 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객타입 | string | N | 1 | B : 법인 P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호 ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `CANO` | 종합계좌번호 | string | Y | 8 | 계좌번호 체계(8-2)의 앞 8자리 |
| `ACNT_PRDT_CD` | 계좌상품코드 | string | Y | 2 | 계좌번호 체계(8-2)의 뒤 2자리 |
| `SLL_BUY_DVSN_CD` | 매도매수구분코드 | string | N | 2 | tr_id가 TTTS3013U(중국/홍콩/일본/베트남 예약 주문)인 경우만 사용 01 : 매도 02 : 매수 |
| `RVSE_CNCL_DVSN_CD` | 정정취소구분코드 | string | Y | 2 | tr_id가 TTTS3013U(중국/홍콩/일본/베트남 예약 주문)인 경우만 사용 00 : "매도/매수 주문"시 필수 항목 02 : 취소 |
| `PDNO` | 상품번호 | string | Y | 12 |  |
| `PRDT_TYPE_CD` | 상품유형코드 | string | Y | 3 | tr_id가 TTTS3013U(중국/홍콩/일본/베트남 예약 주문)인 경우만 사용 515 : 일본 501 : 홍콩 / 543 : 홍콩CNY / 558 : 홍콩USD 507 : 베트남 하노이거래소 / 508 : 베트남  |
| `OVRS_EXCG_CD` | 해외거래소코드 | string | Y | 4 | NASD : 나스닥 NYSE : 뉴욕 AMEX : 아멕스 SEHK : 홍콩 SHAA : 중국상해 SZAA : 중국심천 TKSE : 일본 HASE : 베트남 하노이 VNSE : 베트남 호치민 |
| `FT_ORD_QTY` | FT주문수량 | string | Y | 10 |  |
| `FT_ORD_UNPR3` | FT주문단가3 | string | Y | 27 |  |
| `ORD_SVR_DVSN_CD` | 주문서버구분코드 | string | N | 1 | "0"(Default) |
| `RSVN_ORD_RCIT_DT` | 예약주문접수일자 | string | N | 8 | tr_id가 TTTS3013U(중국/홍콩/일본/베트남 예약 주문)인 경우만 사용 |
| `ORD_DVSN` | 주문구분 | string | N | 20 | tr_id가 TTTT3014U(미국 예약 매수 주문)인 경우만 사용 00 : 지정가 35 : TWAP 36 : VWAP  tr_id가 TTTT3016U(미국 예약 매도 주문)인 경우만 사용 00 : 지정가 31 :  |
| `OVRS_RSVN_ODNO` | 해외예약주문번호 | string | N | 10 | tr_id가 TTTS3013U(중국/홍콩/일본/베트남 예약 주문)인 경우만 사용 |
| `ALGO_ORD_TMD_DVSN_CD` | 알고리즘주문시간구분코드 | string | N | 2 | ※ TWAP, VWAP 주문에서만 사용. 예약주문은 시간입력 불가하여 02로 값 고정 ※ 정규장 종료 10분전까지 가능 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 | 0 : 성공  0 이외의 값 : 실패 |
| `msg_cd` | 응답코드 | string | Y | 8 | 응답코드 |
| `msg1` | 응답메세지 | string | Y | 80 | 응답메세지 |
| `output` | 응답상세 | object | Y |  |  |
| `ODNO` | 한국거래소전송주문조직번호 | string | Y | 10 | tr_id가 TTTT3016U(미국 예약 매도 주문) / TTTT3014U(미국 예약 매수 주문)인 경우만 출력 |
| `RSVN_ORD_RCIT_DT` | 예약주문접수일자 | string | Y | 8 | tr_id가 TTTS3013U(중국/홍콩/일본/베트남 예약 주문)인 경우만 출력 |
| `OVRS_RSVN_ODNO` | 해외예약주문번호 | string | Y | 10 | tr_id가 TTTS3013U(중국/홍콩/일본/베트남 예약 주문)인 경우만 출력 |

**Request 예시**
```
{ "CANO": "810XXXXX", "ACNT_PRDT_CD":"AAPL", "PDNO": "AAPL", "OVRS_EXCG_CD": "NASD", "FT_ORD_QTY": "1", "FT_ORD_UNPR3": "148.00" }
```

**Response 예시**
```json
{   "rt_cd": "0",   "msg_cd": "APBK0013",   "msg1": "주문 전송 완료 되었습니다.",   "output": {     "ODNO": "0030138295"   } }
```

---

### 해외주식 예약주문접수취소

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-004` |
| 통신방식 | REST / POST |
| 실전 TR_ID | `(미국 예약주문 취소접수) TTTT3017U (아시아국가 미제공)` |
| 모의 TR_ID | `(미국 예약주문 취소접수) VTTT3017U (아시아국가 미제공)` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| 모의 Domain | `https://openapivts.koreainvestment.com:29443` |
| URL | `/uapi/overseas-stock/v1/trading/order-resv-ccnl` |

> 접수된 미국주식 예약주문을 취소하기 위한 API입니다. (해외주식 예약주문접수 시 Return 받은 ODNO를 참고하여 API를 호출하세요.)  * 해외주식 서비스 신청 후 이용 가능합니다. (아래 링크 3번 해외증권 거래신청 참고) https://securities.koreainvestment.com/main/bond/research/_static/TF03ca010001.jsp  ※ POST API의 경우 BODY값의 key값들을 대문자로 작성하셔야 합니다.    (EX. "CANO" : "12345678", "ACN

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | N | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token 일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용) 법인(Access t |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appsecret (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | [실전투자] TTTT3017U : 미국예약주문접수 취소  [모의투자] VTTT3017U : 미국예약주문접수 취소 (일본, 홍콩 등 타국가 개발 진행 예정) |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객타입 | string | N | 1 | B : 법인 P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호 ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `CANO` | 종합계좌번호 | string | Y | 8 | 계좌번호 체계(8-2)의 앞 8자리 |
| `ACNT_PRDT_CD` | 계좌상품코드 | string | Y | 2 | 계좌번호 체계(8-2)의 뒤 2자리 |
| `RSYN_ORD_RCIT_DT` | 해외주문접수일자 | string | Y | 8 |  |
| `OVRS_RSVN_ODNO` | 해외예약주문번호 | string | Y | 10 | 해외주식_예약주문접수 API Output ODNO(주문번호) 참고 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | Y | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | Y | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 | 0 : 성공  0 이외의 값 : 실패 |
| `msg_cd` | 응답코드 | string | Y | 8 | 응답코드 |
| `msg1` | 응답메세지 | string | Y | 80 | 응답메세지 |
| `output` | 응답상세 | object | Y |  |  |
| `OVRS_RSVN_ODNO` | 해외예약주문번호 | string | Y | 10 |  |

**Request 예시**
```
{ "CANO": "810XXXXX", "ACNT_PRDT_CD": "01", "RSVN_ORD_RCIT_DT": "20211124", "OVRS_RSVN_ODNO": "30135682" }
```

**Response 예시**
```json
{   "rt_cd": "0",   "msg_cd": "APBK1711",   "msg1": "취소주문이 접수되었습니다.",   "output": {     "OVRS_RSVN_ODNO": "0030138295"   } }
```

---

### 해외주식 예약주문조회

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-013` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `(미국) TTTT3039R (일본/중국/홍콩/베트남) TTTS3014R` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/trading/order-resv-list` |

> 해외주식 예약주문 조회 API입니다. ※ 모의투자는 사용 불가합니다.  * 해외주식 서비스 신청 후 이용 가능합니다. (아래 링크 3번 해외증권 거래신청 참고) https://securities.koreainvestment.com/main/bond/research/_static/TF03ca010001.jsp

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | N | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | [실전투자] 미국 : TTTT3039R 일본, 중국, 홍콩, 베트남 : TTTS3014R |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우) |
| `custtype` | 고객 타입 | string | N | 1 | B : 법인 / P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | 법인 : "001" / 개인: ""(Default) |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `CANO` | 종합계좌번호 | string | Y | 8 | 계좌번호 체계(8-2)의 앞 8자리 |
| `ACNT_PRDT_CD` | 계좌상품코드 | string | Y | 2 | 계좌번호 체계(8-2)의 뒤 2자리 |
| `INQR_STRT_DT` | 조회시작일자 | string | Y | 8 | 조회시작일자(YYYYMMDD) |
| `INQR_END_DT` | 조회종료일자 | string | Y | 8 | 조회종료일자(YYYYMMDD) |
| `INQR_DVSN_CD` | 조회구분코드 | string | Y | 2 | 00 : 전체 01 : 일반해외주식  02 : 미니스탁 |
| `PRDT_TYPE_CD` | 상품유형코드 | string | Y | 3 | [tr_id=TTTT3039R인 경우] 공백 입력 시 미국주식 전체조회 [tr_id=TTTS3014R인 경우] 공백 입력 시 아시아주식 전체조회  512 : 미국 나스닥 / 513 : 미국 뉴욕거래소 / 529 :  |
| `OVRS_EXCG_CD` | 해외거래소코드 | string | Y | 4 | [tr_id=TTTT3039R인 경우] 공백 입력 시 미국주식 전체조회 [tr_id=TTTS3014R인 경우] 공백 입력 시 아시아주식 전체조회  NASD : 나스닥 / NYSE : 뉴욕 / AMEX : 아멕스 SE |
| `CTX_AREA_FK200` | 연속조회검색조건200 | string | Y | 200 | 공란 : 최초 조회시 이전 조회 Output CTX_AREA_FK200값 : 다음페이지 조회시(2번째부터) |
| `CTX_AREA_NK200` | 연속조회키200 | string | Y | 200 | 공란 : 최초 조회시 이전 조회 Output CTX_AREA_NK200값 : 다음페이지 조회시(2번째부터) |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | F or M : 다음 데이터 있음 D or E : 마지막 데이터 |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `ctx_area_fk200` | 연속조회검색조건200 | string | Y | 200 |  |
| `ctx_area_nk200` | 연속조회키200 | string | Y | 200 |  |
| `output` | 응답상세1 | object | N |  |  |
| `cncl_yn` | 취소여부 | string | N | 1 |  |
| `rsvn_ord_rcit_dt` | 예약주문접수일자 | string | N | 8 |  |
| `ovrs_rsvn_odno` | 해외예약주문번호 | string | N | 10 |  |
| `ord_dt` | 주문일자 | string | N | 8 |  |
| `ord_gno_brno` | 주문채번지점번호 | string | N | 5 |  |
| `odno` | 주문번호 | string | N | 10 |  |
| `sll_buy_dvsn_cd` | 매도매수구분코드 | string | N | 2 |  |
| `sll_buy_dvsn_cd_name` | 매도매수구분명 | string | N | 60 |  |
| `ovrs_rsvn_ord_stat_cd` | 해외예약주문상태코드 | string | N | 2 |  |
| `ovrs_rsvn_ord_stat_cd_name` | 해외예약주문상태코드명 | string | N | 60 |  |
| `pdno` | 상품번호 | string | N | 12 |  |
| `prdt_type_cd` | 상품유형코드 | string | N | 3 |  |
| `prdt_name` | 상품명 | string | N | 60 |  |
| `ord_rcit_tmd` | 주문접수시각 | string | N | 6 |  |
| `ord_fwdg_tmd` | 주문전송시각 | string | N | 6 |  |
| `tr_dvsn_name` | 거래구분명 | string | N | 60 |  |
| `ovrs_excg_cd` | 해외거래소코드 | string | N | 4 |  |
| `tr_mket_name` | 거래시장명 | string | N | 60 |  |
| `ord_stfno` | 주문직원번호 | string | N | 6 |  |
| `ft_ord_qty` | FT주문수량 | string | N | 10 |  |
| `ft_ord_unpr3` | FT주문단가3 | string | N | 27 |  |
| `ft_ccld_qty` | FT체결수량 | string | N | 10 |  |
| `nprc_rson_text` | 미처리사유내용 | string | N | 500 |  |
| `splt_buy_attr_name` | 분할매수속성명 | string | N | 60 | 정규장 종료 주문 시에는 '정규장 종료', 시간 입력 시에는 from ~ to 시간 표시 |

**Request 예시**
```
"input": {             "ACNT_PRDT_CD": "01",             "CANO": "12345678",             "CTX_AREA_FK200": "",             "CTX_AREA_NK200": "",             "INQR_DVSN_CD": "00",             "INQR_END_DT": "20220709",             "INQR_STRT_DT": "20220705",             "OVRS_EXCG_CD": "SEHK",             "PRDT_TYPE_CD": "501"         }
```

**Response 예시**
```json
{     "ctx_area_fk200": "12345678^01^20220809^20220830^00^                                                                                                                                                                       ",     "ctx_area_nk200": "                                                                                                                                                     
```

---

### 해외주식 결제기준잔고

| 항목 | 값 |
|------|----|
| API ID | `해외주식-064` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `CTRP6010R` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/trading/inquire-paymt-stdr-balance` |

> 해외주식 결제기준잔고 API입니다. 한국투자 HTS(eFriend Plus) &gt; [0829] 해외 결제기준잔고 화면 의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.  ※ 적용환율은 당일 매매기준이며, 현재가의 경우 지연된 시세로 평가되므로 실제매도금액과 상이할 수 있습니다. ※ 주문가능수량 : 보유수량 - 미결제 매도수량 ※ 매입금액 계산 시 결제일의 최초고시환율을 적용하므로, 금일 최초고시환율을 적용하는 체결기준 잔고와는 상이합니다. ※ 해외증권 투자 및 업무문의 안내: 한국

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | CTRP6010R |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우) |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `CANO` | 종합계좌번호 | string | Y | 8 |  |
| `ACNT_PRDT_CD` | 계좌상품코드 | string | Y | 2 |  |
| `BASS_DT` | 기준일자 | string | Y | 8 |  |
| `WCRC_FRCR_DVSN_CD` | 원화외화구분코드 | string | Y | 2 | 01(원화기준),02(외화기준) |
| `INQR_DVSN_CD` | 조회구분코드 | string | Y | 2 | 00(전체), 01(일반), 02(미니스탁) |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | F or M : 다음 데이터 있음 D or E : 마지막 데이터 |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output1` | 응답상세 | object array | Y |  | array |
| `pdno` | 상품번호 | string | Y | 12 |  |
| `prdt_name` | 상품명 | string | Y | 60 |  |
| `cblc_qty13` | 잔고수량13 | string | Y | 238 |  |
| `ord_psbl_qty1` | 주문가능수량1 | string | Y | 238 |  |
| `avg_unpr3` | 평균단가3 | string | Y | 244 |  |
| `ovrs_now_pric1` | 해외현재가격1 | string | Y | 235 |  |
| `frcr_pchs_amt` | 외화매입금액 | string | Y | 235 |  |
| `frcr_evlu_amt2` | 외화평가금액2 | string | Y | 236 |  |
| `evlu_pfls_amt2` | 평가손익금액2 | string | Y | 255 |  |
| `bass_exrt` | 기준환율 | string | Y | 238 |  |
| `oprt_dtl_dtime` | 조작상세일시 | string | Y | 17 |  |
| `buy_crcy_cd` | 매수통화코드 | string | Y | 3 |  |
| `thdt_sll_ccld_qty1` | 당일매도체결수량1 | string | Y | 238 |  |
| `thdt_buy_ccld_qty1` | 당일매수체결수량1 | string | Y | 238 |  |
| `evlu_pfls_rt1` | 평가손익율1 | string | Y | 238 |  |
| `tr_mket_name` | 거래시장명 | string | Y | 60 |  |
| `natn_kor_name` | 국가한글명 | string | Y | 60 |  |
| `std_pdno` | 표준상품번호 | string | Y | 12 |  |
| `mgge_qty` | 담보수량 | string | Y | 19 |  |
| `loan_rmnd` | 대출잔액 | string | Y | 19 |  |
| `prdt_type_cd` | 상품유형코드 | string | Y | 3 |  |
| `ovrs_excg_cd` | 해외거래소코드 | string | Y | 4 |  |
| `scts_dvsn_name` | 유가증권구분명 | string | Y | 60 |  |
| `ldng_cblc_qty` | 대여잔고수량 | string | Y | 19 |  |
| `output2` | 응답상세 | object array | Y |  | array |
| `crcy_cd` | 통화코드 | string | Y | 3 |  |
| `crcy_cd_name` | 통화코드명 | string | Y | 60 |  |
| `frcr_dncl_amt_2` | 외화예수금액2 | string | Y | 236 |  |
| `frst_bltn_exrt` | 최초고시환율 | string | Y | 238 |  |
| `frcr_evlu_amt2` | 외화평가금액2 | string | Y | 236 |  |
| `output3` | 응답상세 | object | Y |  |  |
| `pchs_amt_smtl_amt` | 매입금액합계금액 | string | Y | 19 |  |
| `tot_evlu_pfls_amt` | 총평가손익금액 | string | Y | 238 |  |
| `evlu_erng_rt1` | 평가수익율1 | string | Y | 201 |  |
| `tot_dncl_amt` | 총예수금액 | string | Y | 19 |  |
| `wcrc_evlu_amt_smtl` | 원화평가금액합계 | string | Y | 236 |  |
| `tot_asst_amt2` | 총자산금액2 | string | Y | 236 |  |
| `frcr_cblc_wcrc_evlu_amt_smtl` | 외화잔고원화평가금액합계 | string | Y | 236 |  |
| `tot_loan_amt` | 총대출금액 | string | Y | 19 |  |
| `tot_ldng_evlu_amt` | 총대여평가금액 | string | Y | 9 |  |

**Request 예시**
```
CANO:12345678 ACNT_PRDT_CD:01 BASS_DT:20240524 WCRC_FRCR_DVSN_CD:01 INQR_DVSN_CD:00
```

**Response 예시**
```json
{     "output1": [         {             "pdno": "ACVA",             "prdt_name": "ACV 옥션스",             "cblc_qty13": "5.00000000",             "ord_psbl_qty1": "5.00000000",             "avg_unpr3": "11137.2000",             "ovrs_now_pric1": "26065.48600",             "frcr_pchs_amt": "55686.00000",             "frcr_evlu_amt2": "130327.000000",             "evlu_pfls_amt2": "74641.00000",     
```

---

### 해외증거금 통화별조회

| 항목 | 값 |
|------|----|
| API ID | `해외주식-035` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `TTTC2101R` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/trading/foreign-margin` |

> 해외증거금 통화별조회 API입니다. 한국투자 HTS(eFriend Plus) &gt; [7718] 해외주식 증거금상세 화면 의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | TTTC2101R |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우) |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `CANO` | 종합계좌번호 | string | Y | 8 |  |
| `ACNT_PRDT_CD` | 계좌상품코드 | string | Y | 2 |  |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | F or M : 다음 데이터 있음 D or E : 마지막 데이터 |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output` | 응답상세 | object array | Y |  | array |
| `natn_name` | 국가명 | string | Y | 60 |  |
| `crcy_cd` | 통화코드 | string | Y | 3 |  |
| `frcr_dncl_amt1` | 외화예수금액 | string | Y | 186 |  |
| `ustl_buy_amt` | 미결제매수금액 | string | Y | 182 |  |
| `ustl_sll_amt` | 미결제매도금액 | string | Y | 182 |  |
| `frcr_rcvb_amt` | 외화미수금액 | string | Y | 182 |  |
| `frcr_mgn_amt` | 외화증거금액 | string | Y | 186 |  |
| `frcr_gnrl_ord_psbl_amt` | 외화일반주문가능금액 | string | Y | 182 |  |
| `frcr_ord_psbl_amt1` | 외화주문가능금액 | string | Y | 186 | 원화주문가능환산금액 |
| `itgr_ord_psbl_amt` | 통합주문가능금액 | string | Y | 182 |  |
| `bass_exrt` | 기준환율 | string | Y | 238 |  |

**Request 예시**
```
CANO:12345678 ACNT_PRDT_CD:01
```

**Response 예시**
```json
{     "output": [         {             "natn_name": "미국",             "crcy_cd": "USD",             "frcr_dncl_amt1": "698.190000",             "ustl_buy_amt": "0.00",             "ustl_sll_amt": "0.00",             "frcr_rcvb_amt": "0.00",             "frcr_mgn_amt": "0.000000",             "frcr_gnrl_ord_psbl_amt": "694.37",             "frcr_ord_psbl_amt1": "0.000000",             "itgr_ord_ps
```

---

### 해외주식 미국주간정정취소

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-027` |
| 통신방식 | REST / POST |
| 실전 TR_ID | `TTTS6038U` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/trading/daytime-order-rvsecncl` |

> 해외주식 미국주간정정취소 API입니다.  * 미국주식 주간거래 시 아래 참고 부탁드립니다. . 포럼 &gt; FAQ &gt; 미국주식 주간거래 시 어떤 API를 사용해야 하나요?  * 미국주간거래의 경우, 모든 미국 종목 매매가 지원되지 않습니다. 일부 종목만 매매 가능한 점 유의 부탁드립니다.  * 해외주식 서비스 신청 후 이용 가능합니다. (아래 링크 3번 해외증권 거래신청 참고) https://securities.koreainvestment.com/main/bond/research/_static/TF03ca010

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | [실전투자] 미국주간 정정취소 : TTTS6038U |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `CANO` | 종합계좌번호 | string | Y | 8 | 계좌번호 체계(8-2)의 앞 8자리 |
| `ACNT_PRDT_CD` | 계좌상품코드 | string | Y | 2 | 계좌번호 체계(8-2)의 뒤 2자리 |
| `OVRS_EXCG_CD` | 해외거래소코드 | string | Y | 4 | NASD:나스닥 / NYSE:뉴욕 / AMEX:아멕스 |
| `PDNO` | 상품번호 | string | Y | 12 | 종목코드 |
| `ORGN_ODNO` | 원주문번호 | string | Y | 10 | '정정 또는 취소할 원주문번호(매매 TR의 주문번호) - 해외주식 주문체결내역api (/uapi/overseas-stock/v1/trading/inquire-nccs)에서 odno(주문번호) 참조' |
| `RVSE_CNCL_DVSN_CD` | 정정취소구분코드 | string | Y | 2 | '01 : 정정  02 : 취소' |
| `ORD_QTY` | 주문수량 | string | Y | 10 |  |
| `OVRS_ORD_UNPR` | 해외주문단가 | string | Y | 32 | 소수점 포함, 1주당 가격 |
| `CTAC_TLNO` | 연락전화번호 | string | Y | 20 | " " |
| `MGCO_APTM_ODNO` | 운용사지정주문번호 | string | Y | 12 | " " |
| `ORD_SVR_DVSN_CD` | 주문서버구분코드 | string | Y | 1 | "0" |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output` | 응답상세 | object | N |  |  |
| `KRX_FWDG_ORD_ORGNO` | 한국거래소전송주문조직번호 | string | Y | 5 | 주문시 한국투자증권 시스템에서 지정된 영업점코드 |
| `ODNO` | 주문번호 | string | Y | 10 | 주문시 한국투자증권 시스템에서 채번된 주문번호 |
| `ORD_TMD` | 주문시각 | string | Y | 6 | 주문시각(시분초HHMMSS) |

**Request 예시**
```
{     "CANO": "12345678",     "ACNT_PRDT_CD": "01",     "OVRS_EXCG_CD": "NASD",     "PDNO": "AMZN",     "ORGN_ODNO": "0000034436",     "RVSE_CNCL_DVSN_CD": "01",     "ORD_QTY": "111",     "OVRS_ORD_UNPR": "1.9",     "CTAC_TLNO": "",     "MGCO_APTM_ODNO": "",     "ORD_SVR_DVSN_CD": "0" }
```

**Response 예시**
```json
{     "rt_cd": "0",     "msg_cd": "APBK0013",     "msg1": "주문 전송 완료 되었습니다.",     "output": {         "KRX_FWDG_ORD_ORGNO": "01790",         "ODNO": "0000034437",         "ORD_TMD": "104202"     } }
```

---

### 해외주식 지정가주문번호조회

| 항목 | 값 |
|------|----|
| API ID | `해외주식-071` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `TTTS6058R` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/trading/algo-ordno` |

> TWAP, VWAP 주문에 대한 주문번호를 조회하는 API

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token 일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용) 법인(Access t |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | Y | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | TTTS6058R |
| `tr_cont` | 연속거래여부 | string | N | 1 | 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우) |
| `custtype` | 고객타입 | string | Y | 1 | B : 법인 P : 개인 |
| `seq_no` | 일련번호 | string | N | 3 | [법인 필수] 001 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호 ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | IP주소 | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `TRAD_DT` | 거래일자 | string | Y | 8 | YYYYMMDD |
| `CANO` | 계좌번호 | string | Y | 8 | 종합계좌번호 (8자리) |
| `ACNT_PRDT_CD` | 계좌상품코드 | string | Y | 2 | 계좌상품코드 (2자리) : 주식계좌는 01 |
| `CTX_AREA_NK200` | 연속조회키200 | string | N | 200 |  |
| `CTX_AREA_FK200` | 연속조회조건200 | string | N | 200 |  |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 |  |
| `tr_cont` | 연속거래여부 | string | N | 1 | F or M : 다음 데이터 있음 D or E : 마지막 데이터 |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `output` | 응답상세 | object array | Y |  |  |
| `odno` | 주문번호 | string | Y | 10 |  |
| `trad_dvsn_name` | 매매구분명 | string | Y | 60 |  |
| `pdno` | 상품번호 | string | Y | 12 |  |
| `item_name` | 종목명 | string | Y | 60 |  |
| `ft_ord_qty` | FT주문수량 | string | Y | 4 |  |
| `ft_ord_unpr3` | FT주문단가 | string | Y | 8 |  |
| `splt_buy_attr_name` | 분할매수속성명 | string | Y | 60 |  |
| `ft_ccld_qty` | FT체결수량 | string | Y | 4 |  |
| `ord_gno_brno` | 주문채번지점번호 | string | N | 5 |  |
| `rt_cd` | 성공 실패 여부 | string | Y | 1 | 0 : 성공 0 이외의 값 : 실패 |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `ctx_area_fk200` | 연속조회검색조건200 | string | Y | 200 |  |
| `ctx_area_nk200` | 연속조회키200 | string | Y | 200 |  |

**Request 예시**
```
CANO:12345678 ACNT_PRDT_CD:01 TRAD_DT:20250523 CTX_AREA_NK200: CTX_AREA_FK200:
```

**Response 예시**
```json
{     "ctx_area_nk200": "                                                                                                                                                                                                        ",     "ctx_area_fk200": "20250523^12345678^01^                                                                                                                                
```

---

### 해외주식 지정가체결내역조회

| 항목 | 값 |
|------|----|
| API ID | `해외주식-070` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `TTTS6059R` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/trading/inquire-algo-ccnl` |

> 해외주식 TWAP, VWAP 주문에 대한 체결내역 조회 API로 지정가 주문번호조회 API를 수행 후 조회해야합니다

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | N | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token 일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용) 법인(Access t |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appsecret (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | TTS6059R |
| `tr_cont` | 연속거래여부 | string | N | 1 | 공백 : 초기 조회 N : 다음 데이터 조회 (output header의 tr_cont가 M일 경우) |
| `custtype` | 고객타입 | string | Y | 1 | P : 개인 / B : 법인 |
| `seq_no` | 일련번호 | string | N | 3 | 법인 필수 : 001 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호 ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | IP주소 | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `CANO` | 계좌번호 | string | Y | 8 | 종합계좌번호 8자리 |
| `ACNT_PRDT_CD` | 계좌상품코드 | string | Y | 2 | 상품코드 2자리 (주식계좌 : 01) |
| `ORD_DT` | 주문일자 | string | Y | 8 | 주문일자 (YYYYMMDD) |
| `ORD_GNO_BRNO` | 주문채번지점번호 | string | N | 5 | TTS6058R 조회 시 해당 주문번호(odno)의 ord_gno_brno 입력 |
| `ODNO` | 주문번호 | string | Y | 10 | 지정가주문번호 (TTTS6058R)에서 조회된 주문번호 입력 |
| `TTLZ_ICLD_YN` | 집계포함여부 | string | N | 1 |  |
| `CTX_AREA_NK200` | 연속조회키200 | string | N | 200 | 연속조회 시 사용 |
| `CTX_AREA_FK200` | 연속조회조건200 | string | N | 200 | 연속조회 시 사용 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 거래ID |
| `tr_cont` | 연속거래여부 | string | N | 1 | F or M : 다음 데이터 있음 D or E : 마지막 데이터 |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메시지 | string | Y | 80 |  |
| `output` | 응답상세 | object array | Y |  |  |
| `CCLD_SEQ` | 체결순번 | string | Y | 4 |  |
| `CCLD_BTWN` | 체결시간 | string | Y | 6 | HHMMSS |
| `PDNO` | 상품번호 | string | Y | 12 |  |
| `ITEM_NAME` | 종목명 | string | Y | 60 |  |
| `FT_CCLD_QTY` | FT체결수량 | string | N | 4 |  |
| `FT_CCLD_UNPR3` | FT체결단가 | string | Y | 8 |  |
| `FT_CCLD_AMT3` | FT체결금액 | string | N | 8 |  |
| `output3` | 응답상세3 | object array | Y |  |  |
| `ODNO` | 주문번호 | string | Y | 10 |  |
| `TRAD_DVSN_NAME` | 매매구분명 | string | Y | 60 |  |
| `PDNO` | 상품번호 | string | Y | 12 |  |
| `ITEM_NAME` | 종목명 | string | Y | 60 |  |
| `FT_ORD_QTY` | FT주문수량 | string | Y | 4 |  |
| `FT_ORD_UNPR3` | FT주문단가 | string | Y | 8 |  |
| `ORD_TMD` | 주문시각 | string | Y | 6 |  |
| `SPLT_BUY_ATTR_NAME` | 분할매수속성명 | string | Y | 60 |  |
| `FT_CCLD_QTY` | FT체결수량 | string | Y | 4 |  |
| `TR_CRCY` | 거래통화 | string | Y | 3 |  |
| `FT_CCLD_UNPR3` | FT체결단가 | string | Y | 8 |  |
| `FT_CCLD_AMT3` | FT체결금액 | string | Y | 8 |  |
| `CCLD_CNT` | 체결건수 | string | Y | 4 |  |

**Request 예시**
```
CANO:12345678 ACNT_PRDT_CD:01 ORD_DT:20250523 ORD_GNO_BRNO: ODNO:0031112345 TTLZ_ICLD_YN: CTX_AREA_NK200: CTX_AREA_FK200:
```

**Response 예시**
```json
{     "ctx_area_nk200": "                                                                                                                                                                                                        ",     "ctx_area_fk200": "20250523^^0031112345^                                                                                                                                
```

---

---

## 3. 기본시세 API (REST)

### 해외주식 현재체결가

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-009` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS00000300` |
| 모의 TR_ID | `HHDFS00000300` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| 모의 Domain | `https://openapivts.koreainvestment.com:29443` |
| URL | `/uapi/overseas-price/v1/quotations/price` |

> 해외주식종목의 현재체결가를 확인하는 API 입니다.  해외주식 시세는 무료시세(지연체결가)만이 제공되며, API로는 유료시세(실시간체결가)를 받아보실 수 없습니다.  ※ 지연시세 지연시간 : 미국 - 실시간무료(0분지연) / 홍콩, 베트남, 중국, 일본 - 15분지연 (중국은 실시간시세 신청 시 무료실시간시세 제공)    미국의 경우 0분지연시세로 제공되나, 장중 당일 시가는 상이할 수 있으며, 익일 정정 표시됩니다.  ※ 2024년 12월 13일(금) 오후 5시부터 HTS(efriend Plus) [7781] 시세신청

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | N | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token 일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용) 법인(Access t |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appsecret (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | [실전투자/모의투자] HHDFS00000300 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객타입 | string | N | 1 | B : 법인 P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호 ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `AUTH` | 사용자권한정보 | string | Y | 32 | "" (Null 값 설정) |
| `EXCD` | 거래소코드 | string | Y | 4 | HKS : 홍콩 NYS : 뉴욕 NAS : 나스닥 AMS : 아멕스 TSE : 도쿄 SHS : 상해 SZS : 심천 SHI : 상해지수 SZI : 심천지수 HSX : 호치민 HNX : 하노이 BAY : 뉴욕(주간)  |
| `SYMB` | 종목코드 | string | Y | 16 |  |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | Y | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | Y | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 | 0 : 성공  0 이외의 값 : 실패 |
| `msg_cd` | 응답코드 | string | Y | 8 | 응답코드 |
| `msg1` | 응답메세지 | string | Y | 80 | 응답메세지 |
| `output` | 응답상세 | object | Y |  |  |
| `rsym` | 실시간조회종목코드 | string | Y | 16 | D+시장구분(3자리)+종목코드 예) DNASAAPL : D+NAS(나스닥)+AAPL(애플) [시장구분] NYS : 뉴욕, NAS : 나스닥, AMS : 아멕스 , TSE : 도쿄, HKS : 홍콩, SHS : 상해, |
| `zdiv` | 소수점자리수 | string | Y | 1 |  |
| `base` | 전일종가 | string | Y | 12 | 전일의 종가 |
| `pvol` | 전일거래량 | string | Y | 14 | 전일의 거래량 |
| `last` | 현재가 | string | Y | 12 | 당일 조회시점의 현재 가격 |
| `sign` | 대비기호 | string | Y | 1 | 1 : 상한 2 : 상승 3 : 보합 4 : 하한 5 : 하락 |
| `diff` | 대비 | string | Y | 12 | 전일 종가와 당일 현재가의 차이 (당일 현재가-전일 종가) |
| `rate` | 등락율 | string | Y | 12 | 전일 대비 / 당일 현재가 * 100 |
| `tvol` | 거래량 | string | Y | 14 | 당일 조회시점까지 전체 거래량 |
| `tamt` | 거래대금 | string | Y | 14 | 당일 조회시점까지 전체 거래금액 |
| `ordy` | 매수가능여부 | string | Y | 20 | 매수주문 가능 종목 여부 |

**Request 예시**
```
{ "AUTH": "", "EXCD": "NAS", "SYMB": "TSLA" }
```

**Response 예시**
```json
{   "output": {     "rsym": "DNASTSLA",     "zdiv": "4",     "base": "1091.2600",     "pvol": "26691673",     "last": "1091.2600",     "sign": "0",     "diff": "0.0000",     "rate": " 0.00",     "tvol": "0",     "tamt": "0",     "ordy": "매도불가"   },   "rt_cd": "0",   "msg_cd": "MCA00000",   "msg1": "정상처리 되었습니다." }
```

---

### 해외주식 현재가상세

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-029` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS76200200` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-price/v1/quotations/price-detail` |

> 해외주식 현재가상세 API입니다.  해당 API를 활용하여 해외주식 종목의 매매단위(vnit), 호가단위(e_hogau), PER, PBR, EPS, BPS 등의 데이터를 확인하실 수 있습니다.  해외주식 시세는 무료시세(지연시세)만이 제공되며, API로는 유료시세(실시간시세)를 받아보실 수 없습니다.  ※ 지연시세 지연시간 : 미국 - 실시간무료(0분지연) / 홍콩, 베트남, 중국, 일본 - 15분지연    미국의 경우 0분지연시세로 제공되나, 장중 당일 시가는 상이할 수 있으며, 익일 정정 표시됩니다.  ※ 20

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHDFS76200200 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | N | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `AUTH` | 사용자권한정보 | string | Y | 32 |  |
| `EXCD` | 거래소명 | string | Y | 4 | HKS : 홍콩 NYS : 뉴욕 NAS : 나스닥 AMS : 아멕스 TSE : 도쿄 SHS : 상해 SZS : 심천 SHI : 상해지수 SZI : 심천지수 HSX : 호치민 HNX : 하노이 BAY : 뉴욕(주간)  |
| `SYMB` | 종목코드 | string | Y | 16 |  |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output` | 응답상세 | object | Y |  |  |
| `rsym` | 실시간조회종목코드 | string | Y | 16 |  |
| `pvol` | 전일거래량 | string | Y | 14 |  |
| `open` | 시가 | string | Y | 12 |  |
| `high` | 고가 | string | Y | 12 |  |
| `low` | 저가 | string | Y | 12 |  |
| `last` | 현재가 | string | Y | 12 |  |
| `base` | 전일종가 | string | Y | 12 |  |
| `tomv` | 시가총액 | string | Y | 16 |  |
| `pamt` | 전일거래대금 | string | Y | 14 |  |
| `uplp` | 상한가 | string | Y | 12 |  |
| `dnlp` | 하한가 | string | Y | 12 |  |
| `h52p` | 52주최고가 | string | Y | 12 |  |
| `h52d` | 52주최고일자 | string | Y | 8 |  |
| `l52p` | 52주최저가 | string | Y | 12 |  |
| `l52d` | 52주최저일자 | string | Y | 8 |  |
| `perx` | PER | string | Y | 10 |  |
| `pbrx` | PBR | string | Y | 10 |  |
| `epsx` | EPS | string | Y | 10 |  |
| `bpsx` | BPS | string | Y | 10 |  |
| `shar` | 상장주수 | string | Y | 16 |  |
| `mcap` | 자본금 | string | Y | 16 |  |
| `curr` | 통화 | string | Y | 4 |  |
| `zdiv` | 소수점자리수 | string | Y | 1 |  |
| `vnit` | 매매단위 | string | Y | 6 |  |
| `t_xprc` | 원환산당일가격 | string | Y | 12 |  |
| `t_xdif` | 원환산당일대비 | string | Y | 12 |  |
| `t_xrat` | 원환산당일등락 | string | Y | 12 |  |
| `p_xprc` | 원환산전일가격 | string | Y | 12 |  |
| `p_xdif` | 원환산전일대비 | string | Y | 12 |  |
| `p_xrat` | 원환산전일등락 | string | Y | 12 |  |
| `t_rate` | 당일환율 | string | Y | 12 |  |
| `p_rate` | 전일환율 | string | Y | 12 |  |
| `t_xsgn` | 원환산당일기호 | string | Y | 1 | HTS 색상표시용 |
| `p_xsng` | 원환산전일기호 | string | Y | 1 | HTS 색상표시용 |
| `e_ordyn` | 거래가능여부 | string | Y | 20 |  |
| `e_hogau` | 호가단위 | string | Y | 8 |  |
| `e_icod` | 업종(섹터) | string | Y | 40 |  |
| `e_parp` | 액면가 | string | Y | 12 |  |
| `tvol` | 거래량 | string | Y | 14 |  |
| `tamt` | 거래대금 | string | Y | 14 |  |
| `etyp_nm` | ETP 분류명 | string | Y | 20 |  |

**Request 예시**
```
{ 	"AUTH":"", 	"EXCD":"NAS", 	"SYMB":"TSLA" }
```

**Response 예시**
```json
{     "output": {         "rsym": "DNASTSLA",         "zdiv": "4",         "curr": "USD",         "vnit": "1",         "open": "257.2600",         "high": "259.0794",         "low": "242.0100",         "last": "245.0100",         "base": "258.0800",         "pvol": "108861698",         "pamt": "28090405673",         "uplp": "0.0000",         "dnlp": "0.0000",         "h52p": "313.8000",         "h
```

---

### 해외주식 현재가 호가

| 항목 | 값 |
|------|----|
| API ID | `해외주식-033` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS76200100` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-price/v1/quotations/inquire-asking-price` |

> 해외주식 현재가 호가 API입니다. 미국 거래소는 10호가, 그 외 국가 거래소는 1호가만 제공됩니다.   한국투자 HTS(eFriend Plus) &gt; [7620] 해외주식 현재가 화면에서 "왼쪽 호가 창" 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.  ※ 지연시세 지연시간 : 미국 - 실시간무료(0분 지연, 나스닥 마켓센터에서 거래되는 호가 및 호가 잔량 정보)                                 홍콩, 베트남, 중국, 일본 - 15분지연    미국의 경

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHDFS76200100 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `AUTH` | 사용자권한정보 | string | Y | 32 | 공백 |
| `EXCD` | 거래소코드 | string | Y | 4 | NYS : 뉴욕 NAS : 나스닥 AMS : 아멕스  HKS : 홍콩 SHS : 상해  SZS : 심천 HSX : 호치민 HNX : 하노이 TSE : 도쿄  BAY : 뉴욕(주간) BAQ : 나스닥(주간) BAA : |
| `SYMB` | 종목코드 | string | Y | 16 | 종목코드 예)TSLA |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output1` | 응답상세 | object | Y | 100 |  |
| `rsym` | 실시간조회종목코드 | string | Y | 16 |  |
| `zdiv` | 소수점자리수 | string | Y | 1 |  |
| `curr` | 통화 | string | Y | 4 |  |
| `base` | 전일종가 | string | Y | 12 |  |
| `open` | 시가 | string | Y | 12 |  |
| `high` | 고가 | string | Y | 12 |  |
| `low` | 저가 | string | Y | 12 |  |
| `last` | 현재가 | string | Y | 12 |  |
| `dymd` | 호가일자 | string | Y | 8 |  |
| `dhms` | 호가시간 | string | Y | 6 |  |
| `bvol` | 매수호가총잔량 | string | Y | 10 |  |
| `avol` | 매도호가총잔량 | string | Y | 10 |  |
| `bdvl` | 매수호가총잔량대비 | string | Y | 10 |  |
| `advl` | 매도호가총잔량대비 | string | Y | 10 |  |
| `code` | 종목코드 | string | Y | 16 |  |
| `ropen` | 시가율 | string | Y | 12 |  |
| `rhigh` | 고가율 | string | Y | 12 |  |
| `rlow` | 저가율 | string | Y | 12 |  |
| `rclose` | 현재가율 | string | Y | 12 |  |
| `output2` | 응답상세 | array | Y | 100 |  |
| `pbid1` | 매수호가가격1 | string | Y | 12 |  |
| `pask1` | 매도호가가격1 | string | Y | 12 |  |
| `vbid1` | 매수호가잔량1 | string | Y | 10 |  |
| `vask1` | 매도호가잔량1 | string | Y | 10 |  |
| `dbid1` | 매수호가대비1 | string | Y | 10 |  |
| `dask1` | 매도호가대비1 | string | Y | 10 |  |
| `pbid2` | 매수호가가격2 | string | Y | 12 | 미국 거래소만 수신 |
| `pask2` | 매도호가가격2 | string | Y | 12 | 미국 거래소만 수신 |
| `vbid2` | 매수호가잔량2 | string | Y | 10 | 미국 거래소만 수신 |
| `vask2` | 매도호가잔량2 | string | Y | 10 | 미국 거래소만 수신 |
| `dbid2` | 매수호가대비2 | string | Y | 10 | 미국 거래소만 수신 |
| `dask2` | 매도호가대비2 | string | Y | 10 | 미국 거래소만 수신 |
| `pbid3` | 매수호가가격3 | string | Y | 12 | 미국 거래소만 수신 |
| `pask3` | 매도호가가격3 | string | Y | 12 | 미국 거래소만 수신 |
| `vbid3` | 매수호가잔량3 | string | Y | 10 | 미국 거래소만 수신 |
| `vask3` | 매도호가잔량3 | string | Y | 10 | 미국 거래소만 수신 |
| `dbid3` | 매수호가대비3 | string | Y | 10 | 미국 거래소만 수신 |
| `dask3` | 매도호가대비3 | string | Y | 10 | 미국 거래소만 수신 |
| `pbid4` | 매수호가가격4 | string | Y | 12 | 미국 거래소만 수신 |
| `pask4` | 매도호가가격4 | string | Y | 12 | 미국 거래소만 수신 |
| `vbid4` | 매수호가잔량4 | string | Y | 10 | 미국 거래소만 수신 |
| `vask4` | 매도호가잔량4 | string | Y | 10 | 미국 거래소만 수신 |
| `dbid4` | 매수호가대비4 | string | Y | 10 | 미국 거래소만 수신 |
| `dask4` | 매도호가대비4 | string | Y | 10 | 미국 거래소만 수신 |
| `pbid5` | 매수호가가격5 | string | Y | 12 | 미국 거래소만 수신 |
| `pask5` | 매도호가가격5 | string | Y | 12 | 미국 거래소만 수신 |
| `vbid5` | 매수호가잔량5 | string | Y | 10 | 미국 거래소만 수신 |
| `vask5` | 매도호가잔량5 | string | Y | 10 | 미국 거래소만 수신 |
| `dbid5` | 매수호가대비5 | string | Y | 10 | 미국 거래소만 수신 |
| `dask5` | 매도호가대비5 | string | Y | 10 | 미국 거래소만 수신 |
| `pbid6` | 매수호가가격6 | string | Y | 12 | 미국 거래소만 수신 |
| `pask6` | 매도호가가격6 | string | Y | 12 | 미국 거래소만 수신 |
| `vbid6` | 매수호가잔량6 | string | Y | 10 | 미국 거래소만 수신 |
| `vask6` | 매도호가잔량6 | string | Y | 10 | 미국 거래소만 수신 |
| `dbid6` | 매수호가대비6 | string | Y | 10 | 미국 거래소만 수신 |
| `dask6` | 매도호가대비6 | string | Y | 10 | 미국 거래소만 수신 |
| `pbid7` | 매수호가가격7 | string | Y | 12 | 미국 거래소만 수신 |
| `pask7` | 매도호가가격7 | string | Y | 12 | 미국 거래소만 수신 |
| `vbid7` | 매수호가잔량7 | string | Y | 10 | 미국 거래소만 수신 |
| `vask7` | 매도호가잔량7 | string | Y | 10 | 미국 거래소만 수신 |
| `dbid7` | 매수호가대비7 | string | Y | 10 | 미국 거래소만 수신 |
| `dask7` | 매도호가대비7 | string | Y | 10 | 미국 거래소만 수신 |
| `pbid8` | 매수호가가격8 | string | Y | 12 | 미국 거래소만 수신 |
| `pask8` | 매도호가가격8 | string | Y | 12 | 미국 거래소만 수신 |
| `vbid8` | 매수호가잔량8 | string | Y | 10 | 미국 거래소만 수신 |
| `vask8` | 매도호가잔량8 | string | Y | 10 | 미국 거래소만 수신 |
| `dbid8` | 매수호가대비8 | string | Y | 10 | 미국 거래소만 수신 |
| `dask8` | 매도호가대비8 | string | Y | 10 | 미국 거래소만 수신 |
| `pbid9` | 매수호가가격9 | string | Y | 12 | 미국 거래소만 수신 |
| `pask9` | 매도호가가격9 | string | Y | 12 | 미국 거래소만 수신 |
| `vbid9` | 매수호가잔량9 | string | Y | 10 | 미국 거래소만 수신 |
| `vask9` | 매도호가잔량9 | string | Y | 10 | 미국 거래소만 수신 |
| `dbid9` | 매수호가대비9 | string | Y | 10 | 미국 거래소만 수신 |
| `dask9` | 매도호가대비9 | string | Y | 10 | 미국 거래소만 수신 |
| `pbid10` | 매수호가가격10 | string | Y | 12 | 미국 거래소만 수신 |
| `pask10` | 매도호가가격10 | string | Y | 12 | 미국 거래소만 수신 |
| `vbid10` | 매수호가잔량10 | string | Y | 10 | 미국 거래소만 수신 |
| `vask10` | 매도호가잔량10 | string | Y | 10 | 미국 거래소만 수신 |
| `dbid10` | 매수호가대비10 | string | Y | 10 | 미국 거래소만 수신 |
| `dask10` | 매도호가대비10 | string | Y | 10 | 미국 거래소만 수신 |
| `output3` | 응답상세 | object array | Y | 100 |  |
| `vstm` | VCMStart시간 | string | Y | 6 | 데이터 없음 |
| `vetm` | VCMEnd시간 | string | Y | 6 | 데이터 없음 |
| `csbp` | CAS/VCM기준가 | string | Y | 12 | 데이터 없음 |
| `cshi` | CAS/VCMHighprice | string | Y | 12 | 데이터 없음 |
| `cslo` | CAS/VCMLowprice | string | Y | 12 | 데이터 없음 |
| `iep` | IEP | string | Y | 12 | 데이터 없음 |
| `iev` | IEV | string | Y | 12 | 데이터 없음 |

**Request 예시**
```
AUTH: EXCD:NAS SYMB:TSLA
```

**Response 예시**
```json
{     "output1": {         "rsym": "DNASTSLA",         "zdiv": "4",         "curr": "USD",         "base": "149.9300",         "open": "148.9700",         "high": "150.9400",         "low": "146.2200",         "last": "147.0500",         "dymd": "20240420",         "dhms": "090000",         "bvol": "0",         "avol": "10759",         "bdvl": "-1053",         "advl": "-985",         "code": "TSLA
```

---

### 해외주식 기간별시세

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-010` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS76240000` |
| 모의 TR_ID | `HHDFS76240000` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| 모의 Domain | `https://openapivts.koreainvestment.com:29443` |
| URL | `/uapi/overseas-price/v1/quotations/dailyprice` |

> 해외주식의 기간별시세를 확인하는 API 입니다. 실전계좌/모의계좌의 경우, 한 번의 호출에 최대 100건까지 확인 가능합니다.  해외주식 시세는 무료시세(지연체결가)만이 제공되며, API로는 유료시세(실시간체결가)를 받아보실 수 없습니다.  ※ 지연시세 지연시간 : 미국 - 실시간무료(0분지연) / 홍콩, 베트남, 중국, 일본 - 15분지연 (중국은 실시간시세 신청 시 무료실시간시세 제공)    미국의 경우 0분지연시세로 제공되나, 장중 당일 시가는 상이할 수 있으며, 익일 정정 표시됩니다.  ※ 2024년 12월 1

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | N | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token 일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용) 법인(Access t |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appsecret (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | [실전투자/모의투자] HHDFS76240000 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객타입 | string | N | 1 | B : 법인 P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호 ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `AUTH` | 사용자권한정보 | string | Y | 32 | "" (Null 값 설정) |
| `EXCD` | 거래소코드 | string | Y | 4 | HKS : 홍콩 NYS : 뉴욕 NAS : 나스닥 AMS : 아멕스 TSE : 도쿄 SHS : 상해 SZS : 심천 SHI : 상해지수 SZI : 심천지수 HSX : 호치민 HNX : 하노이 |
| `SYMB` | 종목코드 | string | Y | 16 | 종목코드 (ex. TSLA) |
| `GUBN` | 일/주/월구분 | string | Y | 1 | 0 : 일 1 : 주 2 : 월 |
| `BYMD` | 조회기준일자 | string | Y | 8 | 조회기준일자(YYYYMMDD) ※ 공란 설정 시, 기준일 오늘 날짜로 설정 |
| `MODP` | 수정주가반영여부 | string | Y | 1 | 0 : 미반영 1 : 반영 |
| `KEYB` | NEXT KEY BUFF | string | N | 1 | 응답시 다음값이 있으면 값이 셋팅되어 있으므로 다음 조회시 응답값 그대로 셋팅 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | Y | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | Y | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 | 0 : 성공  0 이외의 값 : 실패 |
| `msg_cd` | 응답코드 | string | Y | 8 | 응답코드 |
| `msg1` | 응답메세지 | string | Y | 80 | 응답메세지 |
| `output1` | 응답상세1 | object | Y |  |  |
| `rsym` | 실시간조회종목코드 | string | Y | 16 | D+시장구분(3자리)+종목코드 예) DNASAAPL : D+NAS(나스닥)+AAPL(애플) [시장구분] NYS : 뉴욕, NAS : 나스닥, AMS : 아멕스 , TSE : 도쿄, HKS : 홍콩, SHS : 상해, |
| `zdiv` | 소수점자리수 | string | Y | 1 |  |
| `nrec` | 전일종가 | string | Y | 12 |  |
| `output2` | 응답상세2 | object array | Y |  |  |
| `xymd` | 일자(YYYYMMDD) | string | Y | 8 |  |
| `clos` | 종가 | string | Y | 12 | 해당 일자의 종가 |
| `sign` | 대비기호 | string | Y | 1 | 1 : 상한 2 : 상승 3 : 보합 4 : 하한 5 : 하락 |
| `diff` | 대비 | string | Y | 12 | 해당 일자의 종가와 해당 전일 종가의 차이 (해당일 종가-해당 전일 종가) |
| `rate` | 등락율 | string | Y | 12 | 해당 전일 대비 / 해당일 종가 * 100 |
| `open` | 시가 | string | Y | 12 | 해당일 최초 거래가격 |
| `high` | 고가 | string | Y | 12 | 해당일 가장 높은 거래가격 |
| `low` | 저가 | string | Y | 12 | 해당일 가장 낮은 거래가격 |
| `tvol` | 거래량 | string | Y | 14 | 해당일 거래량 |
| `tamt` | 거래대금 | string | Y | 14 | 해당일 거래대금 |
| `pbid` | 매수호가 | string | Y | 12 | 마지막 체결이 발생한 시점의 매수호가 * 해당 일자 거래량 0인 경우 값이 수신되지 않음 |
| `vbid` | 매수호가잔량 | string | Y | 10 | * 해당 일자 거래량 0인 경우 값이 수신되지 않음 |
| `pask` | 매도호가 | string | Y | 12 | 마지막 체결이 발생한 시점의 매도호가 * 해당 일자 거래량 0인 경우 값이 수신되지 않음 |
| `vask` | 매도호가잔량 | string | Y | 10 | * 해당 일자 거래량 0인 경우 값이 수신되지 않음 |

**Request 예시**
```
{ "AUTH": "", "EXCD": "NAS", "SYMB": "TSLA", "GUBN": "0", "BYMD": "", "MODP": "0" }
```

**Response 예시**
```json
{   "output1": {     "rsym": "DNASTSLA",     "zdiv": "4",     "nrec": "100"   },   "output2": [     {       "xymd": "20220406",       "clos": "1045.7600",       "sign": "5",       "diff": "45.5000",       "rate": "-4.17",       "open": "1073.4700",       "high": "1079.0000",       "low": "1027.7000",       "tvol": "29782845",       "tamt": "31190274312",       "pbid": "1042.8900",       "vbid": "7
```

---

### 해외주식분봉조회

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-030` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS76950200` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-price/v1/quotations/inquire-time-itemchartprice` |

> 해외주식분봉조회 API입니다. 실전계좌의 경우, 한 번의 호출에 최근 120건까지 확인 가능합니다. NEXT 및 KEYB 값을 사용하여 데이터를 계속해서 다음 조회할 수 있으며, 최대 다음조회 가능 기간은 약 1개월입니다.   ※ 해외주식분봉조회 조회 방법 params . 초기 조회:   - PINC: "1" 입력  - NEXT: 처음 조회 시, "" 공백 입력  - KEYB: 처음 조회 시, "" 공백 입력 . 다음 조회:  - PINC: "1" 입력  - NEXT: "1" 입력  - KEYB: 이전 조회 결

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHDFS76950200 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | N | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `AUTH` | 사용자권한정보 | string | Y | 32 | "" 공백으로 입력 |
| `EXCD` | 거래소코드 | string | Y | 4 | NYS : 뉴욕 NAS : 나스닥 AMS : 아멕스  HKS : 홍콩 SHS : 상해  SZS : 심천 HSX : 호치민 HNX : 하노이 TSE : 도쿄   ※ 주간거래는 최대 1일치 분봉만 조회 가능 BAY :  |
| `SYMB` | 종목코드 | string | Y | 16 | 종목코드(ex. TSLA) |
| `NMIN` | 분갭 | string | Y | 4 | 분단위(1: 1분봉, 2: 2분봉, ...) |
| `PINC` | 전일포함여부 | string | Y | 1 | 0:당일 1:전일포함 ※ 다음조회 시 반드시 "1"로 입력 |
| `NEXT` | 다음여부 | string | Y | 1 | 처음조회 시, "" 공백 입력 다음조회 시, "1" 입력 |
| `NREC` | 요청갯수 | string | Y | 4 | 레코드요청갯수 (최대 120) |
| `FILL` | 미체결채움구분 | string | Y | 1 | "" 공백으로 입력 |
| `KEYB` | NEXT KEY BUFF | string | Y | 32 | 처음 조회 시, "" 공백 입력 다음 조회 시, 이전 조회 결과의 마지막 분봉 데이터를 이용하여, 1분 전 혹은 n분 전의 시간을 입력  (형식: YYYYMMDDHHMMSS, ex. 20241014140100) |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output1` | 응답상세 | object array | Y |  |  |
| `rsym` | 실시간종목코드 | string | Y | 16 |  |
| `zdiv` | 소수점자리수 | string | Y | 1 |  |
| `stim` | 장시작현지시간 | string | Y | 6 |  |
| `etim` | 장종료현지시간 | string | Y | 6 |  |
| `sktm` | 장시작한국시간 | string | Y | 6 |  |
| `ektm` | 장종료한국시간 | string | Y | 6 |  |
| `next` | 다음가능여부 | string | Y | 1 |  |
| `more` | 추가데이타여부 | string | Y | 1 |  |
| `nrec` | 레코드갯수 | string | Y | 4 |  |
| `output2` | 응답상세2 | object | Y |  | array |
| `tymd` | 현지영업일자 | string | Y | 8 |  |
| `xymd` | 현지기준일자 | string | Y | 8 |  |
| `xhms` | 현지기준시간 | string | Y | 6 |  |
| `kymd` | 한국기준일자 | string | Y | 8 |  |
| `khms` | 한국기준시간 | string | Y | 6 |  |
| `open` | 시가 | string | Y | 12 |  |
| `high` | 고가 | string | Y | 12 |  |
| `low` | 저가 | string | Y | 12 |  |
| `last` | 종가 | string | Y | 12 |  |
| `evol` | 체결량 | string | Y | 12 |  |
| `eamt` | 체결대금 | string | Y | 14 |  |

**Request 예시**
```
{ "AUTH":"", "EXCD":"NAS", "SYMB":"TSLA", "NMIN":"5", "PINC":"1", "NEXT":"1", "NREC":"120", "FILL":"", "KEYB":"" }
```

**Response 예시**
```json
{     "output1": {         "rsym": "DNASTSLA",         "zdiv": "4",         "stim": "093000",         "etim": "160000",         "sktm": "233000",         "ektm": "060000",         "next": "1",         "more": "0",         "nrec": "120"     },     "output2": [         {             "tymd": "20240222",             "xymd": "20240222",             "xhms": "160000",             "kymd": "20240223",     
```

---

### 해외주식 종목_지수_환율기간별시세(일_주_월_년)

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-012` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `FHKST03030100` |
| 모의 TR_ID | `FHKST03030100` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| 모의 Domain | `https://openapivts.koreainvestment.com:29443` |
| URL | `/uapi/overseas-price/v1/quotations/inquire-daily-chartprice` |

> 해외주식 종목/지수/환율기간별시세(일/주/월/년) API입니다.  해외지수 당일 시세의 경우 지연시세 or 종가시세가 제공됩니다.  ※ 해당 API로 미국주식 조회 시, 다우30, 나스닥100, S&P500 종목만 조회 가능합니다.    더 많은 미국주식 종목 시세를 이용할 시에는, 해외주식기간별시세 API 사용 부탁드립니다.

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | N | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | [실전투자/모의투자] FHKST03030100 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | N | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `FID_COND_MRKT_DIV_CODE` | FID 조건 시장 분류 코드 | string | Y | 2 | N: 해외지수, X 환율, I: 국채, S:금선물 |
| `FID_INPUT_ISCD` | FID 입력 종목코드 | string | Y | 12 | 종목코드 ※ 해외주식 마스터 코드 참조  (포럼 > FAQ > 종목정보 다운로드(해외) > 해외지수)  ※ 해당 API로 미국주식 조회 시, 다우30, 나스닥100, S&P500 종목만 조회 가능합니다. 더 많은 미 |
| `FID_INPUT_DATE_1` | FID 입력 날짜1 | string | Y | 10 | 시작일자(YYYYMMDD) |
| `FID_INPUT_DATE_2` | FID 입력 날짜2 | string | Y | 10 | 종료일자(YYYYMMDD) |
| `FID_PERIOD_DIV_CODE` | FID 기간 분류 코드 | string | Y | 32 | D:일, W:주, M:월, Y:년 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output1` | 응답상세1 | object | N |  | 기본정보 |
| `ovrs_nmix_prdy_vrss` | 전일 대비 | string | N | 16 | 16(11.4) 정수부분 11자리, 소수부분 4자리 |
| `prdy_vrss_sign` | 전일 대비 부호 | string | N | 1 |  |
| `prdy_ctrt` | 전일 대비율 | string | N | 11 | 11(8.2) 정수부분 8자리, 소수부분 2자리 |
| `ovrs_nmix_prdy_clpr` | 전일 종가 | string | N | 16 | 16(11.4) 정수부분 11자리, 소수부분 4자리 |
| `acml_vol` | 누적 거래량 | string | N | 18 |  |
| `hts_kor_isnm` | HTS 한글 종목명 | string | N | 40 |  |
| `ovrs_nmix_prpr` | 현재가 | string | N | 16 | 16(11.4) 정수부분 11자리, 소수부분 4자리 |
| `stck_shrn_iscd` | 단축 종목코드 | string | N | 9 |  |
| `prdy_vol` | 전일 거래량 | string | N | 18 |  |
| `ovrs_prod_oprc` | 시가 | string | N | 16 | 16(11.4) 정수부분 11자리, 소수부분 4자리 |
| `ovrs_prod_hgpr` | 최고가 | string | N | 16 | 16(11.4) 정수부분 11자리, 소수부분 4자리 |
| `ovrs_prod_lwpr` | 최저가 | string | N | 16 | 16(11.4) 정수부분 11자리, 소수부분 4자리 |
| `output2` | 응답상세2 | object array | N |  | 일자별 정보 |
| `stck_bsop_date` | 영업 일자 | string | N | 8 |  |
| `ovrs_nmix_prpr` | 현재가 | string | N | 16 | 16(11.4) 정수부분 11자리, 소수부분 4자리 |
| `ovrs_nmix_oprc` | 시가 | string | N | 16 | 16(11.4) 정수부분 11자리, 소수부분 4자리 |
| `ovrs_nmix_hgpr` | 최고가 | string | N | 16 | 16(11.4) 정수부분 11자리, 소수부분 4자리 |
| `ovrs_nmix_lwpr` | 최저가 | string | N | 16 | 16(11.4) 정수부분 11자리, 소수부분 4자리 |
| `acml_vol` | 누적 거래량 | string | N | 18 |  |
| `mod_yn` | 변경 여부 | string | N | 1 |  |

**Request 예시**
```
"input": {             "fid_cond_mrkt_div_code": "N",             "fid_input_date_1": "20220401",             "fid_input_date_2": "20220613",             "fid_input_iscd": ".DJI",             "fid_period_div_code": "D"         }
```

**Response 예시**
```json
"output1": {             "acml_vol": "397268510",             "hts_kor_isnm": "다우존스 산업지수",             "ovrs_nmix_prdy_clpr": "31029.31",             "ovrs_nmix_prdy_vrss": "-253.88",             "ovrs_nmix_prpr": "30775.43",             "ovrs_prod_hgpr": "30979.85",             "ovrs_prod_lwpr": "30431.87",             "ovrs_prod_oprc": "30790.00",             "prdy_ctrt": "-0.82",             "p
```

---

### 해외주식 체결추이

| 항목 | 값 |
|------|----|
| API ID | `해외주식-037` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS76200300` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-price/v1/quotations/inquire-ccnl` |

> 해외주식 체결추이 API입니다.

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHDFS76200300 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `EXCD` | 거래소명 | string | Y | 4 | 'NYS : 뉴욕, NAS : 나스닥,  AMS : 아멕스  HKS : 홍콩, SHS : 상해 , SZS : 심천 HSX : 호치민, HNX : 하노이 TSE : 도쿄 ' |
| `AUTH` | 사용자권한정보 | string | Y | 32 | 공백 |
| `KEYB` | NEXT KEY BUFF | string | Y | 32 | 공백 |
| `TDAY` | 당일전일구분 | string | Y | 1 | 0:전일, 1:당일 |
| `SYMB` | 종목코드 | string | Y | 16 | 해외종목코드 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output2` | 응답상세 | object array | Y |  | array |
| `khms` | 한국기준시간 | string | Y | 6 |  |
| `last` | 체결가 | string | Y | 12 |  |
| `sign` | 기호 | string | Y | 1 |  |
| `diff` | 대비 | string | Y | 12 |  |
| `rate` | 등락율 | string | Y | 12 |  |
| `evol` | 체결량 | string | Y | 10 |  |
| `tvol` | 거래량 | string | Y | 14 |  |
| `mtyp` | 시장구분 | string | Y | 1 | 0: 장중 1:장전 2:장후 |
| `pbid` | 매수호가 | string | Y | 12 |  |
| `pask` | 매도호가 | string | Y | 12 |  |
| `vpow` | 체결강도 | string | Y | 10 |  |
| `output1` | 응답상세 | object | Y |  |  |
| `rsym` | 실시간조회종목코드 | string | Y | 16 |  |
| `ZDIV` | 소수점자리수 | string | Y | 1 |  |
| `NREC` | Record Count | string | Y | 4 |  |

**Request 예시**
```
AUTH: EXCD:NAS SYMB:AAPL TDAY:0 KEYB:
```

**Response 예시**
```json
{     "output1": [         {             "khms": "085957",             "last": "195.2000",             "sign": "5",             "diff": "3.2200",             "rate": "-1.62",             "evol": "30",             "tvol": "29159135",             "mtyp": "",             "pbid": "195.1500",             "pask": "195.6000",             "vpow": "71.66"         },         {             "khms": "085957", 
```

---

### 해외주식조건검색

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-015` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS76410000` |
| 모의 TR_ID | `HHDFS76410000` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| 모의 Domain | `https://openapivts.koreainvestment.com:29443` |
| URL | `/uapi/overseas-price/v1/quotations/inquire-search` |

> 해외주식 조건검색 API입니다. 한국투자 HTS(eFriend Plus) &gt; [7641] 해외주식 조건검색 화면의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.    현재 조건검색 결과값은 최대 100개까지 조회 가능합니다. 다음 조회(100개 이후의 값) 기능에 대해서는 개선검토 중에 있습니다.  ※ 지연시세 지연시간 : 미국 - 실시간무료(0분지연) / 홍콩, 베트남, 중국, 일본 - 15분지연 (중국은 실시간시세 신청 시 무료실시간시세 제공)    미국의 경우 0분지연시세로

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHDFS76410000 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | N | 1 | B : 법인 / P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | 법인 : "001" / default   개인: "" |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `AUTH` | 사용자권한정보 | string | Y | 32 | "" (Null 값 설정) |
| `EXCD` | 거래소코드 | string | Y | 4 | NYS : 뉴욕, NAS : 나스닥,  AMS : 아멕스  HKS : 홍콩, SHS : 상해 , SZS : 심천 HSX : 호치민, HNX : 하노이 TSE : 도쿄 |
| `CO_YN_PRICECUR` | 현재가선택조건 | string | N | 1 | 해당조건 사용시(1), 미사용시 필수항목아님 |
| `CO_ST_PRICECUR` | 현재가시작범위가 | string | N | 12 | 단위: 각국통화(JPY, USD, HKD, CNY, VND) |
| `CO_EN_PRICECUR` | 현재가끝범위가 | string | N | 12 | 단위: 각국통화(JPY, USD, HKD, CNY, VND) |
| `CO_YN_RATE` | 등락율선택조건 | string | N | 1 | 해당조건 사용시(1), 미사용시 필수항목아님 |
| `CO_ST_RATE` | 등락율시작율 | string | N | 12 | % |
| `CO_EN_RATE` | 등락율끝율 | string | N | 12 | % |
| `CO_YN_VALX` | 시가총액선택조건 | string | N | 1 | 해당조건 사용시(1), 미사용시 필수항목아님 |
| `CO_ST_VALX` | 시가총액시작액 | string | N | 12 | 단위: 천 |
| `CO_EN_VALX` | 시가총액끝액 | string | N | 12 | 단위: 천 |
| `CO_YN_SHAR` | 발행주식수선택조건 | string | N | 1 | 해당조건 사용시(1), 미사용시 필수항목아님 |
| `CO_ST_SHAR` | 발행주식시작수 | string | N | 12 | 단위: 천 |
| `CO_EN_SHAR` | 발행주식끝수 | string | N | 112 | 단위: 천 |
| `CO_YN_VOLUME` | 거래량선택조건 | string | N | 1 | 해당조건 사용시(1), 미사용시 필수항목아님 |
| `CO_ST_VOLUME` | 거래량시작량 | string | N | 12 | 단위: 주 |
| `CO_EN_VOLUME` | 거래량끝량 | string | N | 12 | 단위: 주 |
| `CO_YN_AMT` | 거래대금선택조건 | string | N | 1 | 해당조건 사용시(1), 미사용시 필수항목아님 |
| `CO_ST_AMT` | 거래대금시작금 | string | N | 12 | 단위: 천 |
| `CO_EN_AMT` | 거래대금끝금 | string | N | 12 | 단위: 천 |
| `CO_YN_EPS` | EPS선택조건 | string | N | 1 | 해당조건 사용시(1), 미사용시 필수항목아님 |
| `CO_ST_EPS` | EPS시작 | string | N | 12 |  |
| `CO_EN_EPS` | EPS끝 | string | N | 12 |  |
| `CO_YN_PER` | PER선택조건 | string | N | 1 | 해당조건 사용시(1), 미사용시 필수항목아님 |
| `CO_ST_PER` | PER시작 | string | N | 12 |  |
| `CO_EN_PER` | PER끝 | string | N | 12 |  |
| `KEYB` | NEXT KEY BUFF | string | N | 8 | "" 공백 입력 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output1` | 응답상세1 | object | Y |  |  |
| `zdiv` | 소수점자리수 | string | Y | 1 | 소수점자리수 |
| `stat` | 거래상태정보 | string | Y | 20 | 거래상태정보 |
| `crec` | 현재조회종목수 | string | Y | 6 | 현재조회종목수 |
| `trec` | 전체조회종목수 | string | Y | 6 | 전체조회종목수 |
| `nrec` | Record Count | string | Y | 4 | Record Count |
| `output2` | 응답상세2 | object array | Y |  | 조회결과 상세 |
| `rsym` | 실시간조회심볼 | string | N | 32 | 실시간조회심볼  D+시장구분(3자리)+종목코드 예) DNASAAPL : D+NAS(나스닥)+AAPL(애플) [시장구분] NYS : 뉴욕, NAS : 나스닥, AMS : 아멕스 , TSE : 도쿄, HKS : 홍콩,  |
| `excd` | 거래소코드 | string | N | 4 | 거래소코드 |
| `name` | 종목명 | string | N | 48 | 종목명 |
| `symb` | 종목코드 | string | N | 16 | 종목코드 |
| `last` | 현재가 | string | N | 12 | 현재가 |
| `shar` | 발행주식 | string | N | 14 | 발행주식수(단위: 천) |
| `valx` | 시가총액 | string | N | 14 | 시가총액(단위: 천) |
| `plow` | 저가 | string | N | 12 | 저가 |
| `phigh` | 고가 | string | N | 12 | 고가 |
| `popen` | 시가 | string | N | 12 | 시가 |
| `tvol` | 거래량 | string | N | 14 | 거래량(단위: 주) |
| `rate` | 등락율 | string | N | 12 | 등락율(%) |
| `diff` | 대비 | string | N | 12 | 대비 |
| `sign` | 기호 | string | N | 1 | 기호 |
| `avol` | 거래대금 | string | N | 14 | 거래대금(단위: 천) |
| `eps` | EPS | string | N | 14 | EPS |
| `per` | PER | string | N | 14 | PER |
| `rank` | 순위 | string | N | 6 | 순위 |
| `ename` | 영문종목명 | string | N | 48 | 영문종목명 |
| `e_ordyn` | 매매가능 | string | N | 2 | 가능 : O |

**Request 예시**
```
{     "AUTH":"",     "EXCD":"NAS",     "CO_YN_PRICECUR":"1",     "CO_ST_PRICECUR":"160",     "CO_EN_PRICECUR":"161",     "CO_YN_RATE":"",     "CO_ST_RATE":"",     "CO_EN_RATE":"",     "CO_YN_VALX":"",     "CO_ST_VALX":"",     "CO_EN_VALX":"",     "CO_YN_SHAR":"",     "CO_ST_SHAR":"",     "CO_EN_SHAR":"",     "CO_YN_VOLUME":"",     "CO_ST_VOLUME":"",     "CO_EN_VOLUME":"",     "CO_YN_AMT":"",     "CO_ST_AMT":"",     "CO_EN_AMT":"",     CO_YN_EPS":"",     CO_ST_EPS":"",     CO_EN_EPS":"",     CO_YN_PER":"",     CO_ST_PER":"",     CO_EN_PER":"" }
```

**Response 예시**
```json
{     "output1": {         "zdiv": "4",         "stat": "무료실시간",         "crec": "2",         "trec": "2",         "nrec": "2"     },     "output2": [         {             "rsym": "DNASTSLA",             "excd": "NAS",             "symb": "TSLA",             "name": "테슬라",             "last": "160.9500",             "sign": "5",             "diff": "6.8700",             "rate": "-4.09",          
```

---

### 해외주식 상품기본정보

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-034` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `CTPF1702R` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-price/v1/quotations/search-info` |

> 해외주식 상품기본정보 API입니다. 시세제공기관(연합)에서 제공하는 해외주식 상품기본정보 데이터를 확인하실 수 있습니다.  ※ 해당자료는 시세제공기관(연합)의 자료를 제공하고 있으며, 오류와 지연이 발생할 수 있습니다. ※ 위 정보에 의한 투자판단의 최종책임은 정보이용자에게 있으며, 당사와 시세제공기관(연합)는 어떠한 법적인 책임도 지지 않사오니 투자에 참고로만 이용하시기 바랍니다.

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | CTPF1702R |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `PRDT_TYPE_CD` | 상품유형코드 | string | Y | 3 | 512  미국 나스닥 / 513  미국 뉴욕 / 529  미국 아멕스  515  일본 501  홍콩 / 543  홍콩CNY / 558  홍콩USD 507  베트남 하노이 / 508  베트남 호치민 551  중국 상해 |
| `PDNO` | 상품번호 | string | Y | 12 | 예) AAPL (애플) |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output` | 응답상세1 | object | Y |  |  |
| `std_pdno` | 표준상품번호 | string | Y | 12 |  |
| `prdt_eng_name` | 상품영문명 | string | Y | 60 |  |
| `natn_cd` | 국가코드 | string | Y | 3 |  |
| `natn_name` | 국가명 | string | Y | 60 |  |
| `tr_mket_cd` | 거래시장코드 | string | Y | 2 |  |
| `tr_mket_name` | 거래시장명 | string | Y | 60 |  |
| `ovrs_excg_cd` | 해외거래소코드 | string | Y | 4 |  |
| `ovrs_excg_name` | 해외거래소명 | string | Y | 60 |  |
| `tr_crcy_cd` | 거래통화코드 | string | Y | 3 |  |
| `ovrs_papr` | 해외액면가 | string | Y | 195 |  |
| `crcy_name` | 통화명 | string | Y | 60 |  |
| `ovrs_stck_dvsn_cd` | 해외주식구분코드 | string | Y | 2 | 01.주식 02.WARRANT 03.ETF 04.우선주 |
| `prdt_clsf_cd` | 상품분류코드 | string | Y | 6 |  |
| `prdt_clsf_name` | 상품분류명 | string | Y | 60 |  |
| `sll_unit_qty` | 매도단위수량 | string | Y | 10 |  |
| `buy_unit_qty` | 매수단위수량 | string | Y | 10 |  |
| `tr_unit_amt` | 거래단위금액 | string | Y | 238 |  |
| `lstg_stck_num` | 상장주식수 | string | Y | 19 |  |
| `lstg_dt` | 상장일자 | string | Y | 8 |  |
| `ovrs_stck_tr_stop_dvsn_cd` | 해외주식거래정지구분코드 | string | Y | 2 | ※ 해당 값 지연 반영될 수 있는 점 유의 부탁드립니다.  01.정상 02.거래정지(ALL) 03.거래중단 04.매도정지 05.거래정지(위탁) 06.매수정지 |
| `lstg_abol_item_yn` | 상장폐지종목여부 | string | Y | 1 |  |
| `ovrs_stck_prdt_grp_no` | 해외주식상품그룹번호 | string | Y | 20 |  |
| `lstg_yn` | 상장여부 | string | Y | 1 |  |
| `tax_levy_yn` | 세금징수여부 | string | Y | 1 |  |
| `ovrs_stck_erlm_rosn_cd` | 해외주식등록사유코드 | string | Y | 2 |  |
| `ovrs_stck_hist_rght_dvsn_cd` | 해외주식이력권리구분코드 | string | Y | 2 |  |
| `chng_bf_pdno` | 변경전상품번호 | string | Y | 12 |  |
| `prdt_type_cd_2` | 상품유형코드2 | string | Y | 3 |  |
| `ovrs_item_name` | 해외종목명 | string | Y | 60 |  |
| `sedol_no` | SEDOL번호 | string | Y | 15 |  |
| `blbg_tckr_text` | 블름버그티커내용 | string | Y | 100 |  |
| `ovrs_stck_etf_risk_drtp_cd` | 해외주식ETF위험지표코드 | string | Y | 3 | 001.ETF 002.ETN 003.ETC(Exchage Traded Commodity) 004.Others(REIT's, Mutual Fund) 005.VIX Underlying ETF 006.VIX Underly |
| `etp_chas_erng_rt_dbnb` | ETP추적수익율배수 | string | Y | 236 |  |
| `istt_usge_isin_cd` | 기관용도ISIN코드 | string | Y | 12 |  |
| `mint_svc_yn` | MINT서비스여부 | string | Y | 1 |  |
| `mint_svc_yn_chng_dt` | MINT서비스여부변경일자 | string | Y | 8 |  |
| `prdt_name` | 상품명 | string | Y | 60 |  |
| `lei_cd` | LEI코드 | string | Y | 20 |  |
| `ovrs_stck_stop_rson_cd` | 해외주식정지사유코드 | string | Y | 2 | 01.권리발생 02.ISIN상이 03.기타 04.급등락종목 05.상장폐지(예정) 06.종목코드,거래소변경 07.PTP종목 |
| `lstg_abol_dt` | 상장폐지일자 | string | Y | 8 |  |
| `mini_stk_tr_stat_dvsn_cd` | 미니스탁거래상태구분코드 | string | Y | 2 | 01.정상 02.매매 불가 03.매수 불가 04.매도 불가 |
| `mint_frst_svc_erlm_dt` | MINT최초서비스등록일자 | string | Y | 8 |  |
| `mint_dcpt_trad_psbl_yn` | MINT소수점매매가능여부 | string | Y | 1 |  |
| `mint_fnum_trad_psbl_yn` | MINT정수매매가능여부 | string | Y | 1 |  |
| `mint_cblc_cvsn_ipsb_yn` | MINT잔고전환불가여부 | string | Y | 1 |  |
| `ptp_item_yn` | PTP종목여부 | string | Y | 1 |  |
| `ptp_item_trfx_exmt_yn` | PTP종목양도세면제여부 | string | Y | 1 |  |
| `ptp_item_trfx_exmt_strt_dt` | PTP종목양도세면제시작일자 | string | Y | 8 |  |
| `ptp_item_trfx_exmt_end_dt` | PTP종목양도세면제종료일자 | string | Y | 8 |  |
| `dtm_tr_psbl_yn` | 주간거래가능여부 | string | Y | 1 |  |
| `sdrf_stop_ecls_yn` | 급등락정지제외여부 | string | Y | 1 |  |
| `sdrf_stop_ecls_erlm_dt` | 급등락정지제외등록일자 | string | Y | 8 |  |
| `memo_text1` | 메모내용1 | string | Y | 500 |  |
| `ovrs_now_pric1` | 해외현재가격1 | string | Y | 23 | 23.5 |
| `last_rcvg_dtime` | 최종수신일시 | string | Y | 14 |  |

**Request 예시**
```
{ "PDNO":"AAPL", "PRDT_TYPE_CD":"512" }
```

**Response 예시**
```json
{     "output": {         "std_pdno": "US0378331005",         "prdt_eng_name": "APPLE INC",         "natn_cd": "840",         "natn_name": "미국",         "tr_mket_cd": "01",         "tr_mket_name": "나스닥",         "ovrs_excg_cd": "NASD",         "ovrs_excg_name": "나스닥",         "tr_crcy_cd": "USD",         "ovrs_papr": "0.00000",         "crcy_name": "미국달러",         "ovrs_stck_dvsn_cd": "01",       
```

---

### 해외주식 업종별시세

| 항목 | 값 |
|------|----|
| API ID | `해외주식-048` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS76370000` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-price/v1/quotations/industry-theme` |

> 해외주식 업종별시세 API입니다.

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHDFS76370000 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `KEYB` | NEXT KEY BUFF | string | Y | 8 | 공백 |
| `AUTH` | 사용자권한정보 | string | Y | 32 | 공백 |
| `EXCD` | 거래소코드 | string | Y | 4 | 'NYS : 뉴욕, NAS : 나스닥,  AMS : 아멕스  HKS : 홍콩, SHS : 상해 , SZS : 심천 HSX : 호치민, HNX : 하노이 TSE : 도쿄 ' |
| `ICOD` | 업종코드 | string | Y | 1 | 업종코드별조회(HHDFS76370100) 를 통해 확인 |
| `VOL_RANG` | 거래량조건 | string | Y | 1 | 0(전체), 1(1백주이상), 2(1천주이상), 3(1만주이상), 4(10만주이상), 5(100만주이상), 6(1000만주이상) |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메시지 | string | Y | 80 |  |
| `output1` | 응답상세 | object | Y |  |  |
| `zdiv` | 소수점자리수 | string | Y | 1 |  |
| `stat` | 거래상태정보 | string | Y | 20 |  |
| `crec` | 현재조회종목수 | string | Y | 6 |  |
| `trec` | 전체조회종목수 | string | Y | 6 |  |
| `nrec` | RecordCount | string | Y | 4 |  |
| `output2` | 응답상세 | object array | Y |  | array |
| `rsym` | 실시간조회심볼 | string | Y | 16 |  |
| `excd` | 거래소코드 | string | Y | 4 |  |
| `symb` | 종목코드 | string | Y | 1 |  |
| `name` | 종목명 | string | Y | 48 |  |
| `last` | 현재가 | string | Y | 16 |  |
| `sign` | 기호 | string | Y | 1 |  |
| `diff` | 대비 | string | Y | 12 |  |
| `rate` | 등락율 | string | Y | 12 |  |
| `tvol` | 거래량 | string | Y | 14 |  |
| `vask` | 매도잔량 | string | Y | 10 |  |
| `pask` | 매도호가 | string | Y | 12 |  |
| `pbid` | 매수호가 | string | Y | 12 |  |
| `vbid` | 매수잔량 | string | Y | 10 |  |
| `seqn` | 순위 | string | Y | 6 |  |
| `ename` | 영문종목명 | string | Y | 48 |  |
| `e_ordyn` | 매매가능 | string | Y | 2 |  |

---

### 해외주식 업종별코드조회

| 항목 | 값 |
|------|----|
| API ID | `해외주식-049` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS76370100` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-price/v1/quotations/industry-price` |

> 해외주식 업종별코드조회 API입니다.

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHDFS76370100 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `AUTH` | 사용자권한정보 | string | Y | 32 | 공백 |
| `EXCD` | 거래소코드 | string | Y | 4 | 'NYS : 뉴욕, NAS : 나스닥,  AMS : 아멕스  HKS : 홍콩, SHS : 상해 , SZS : 심천 HSX : 호치민, HNX : 하노이 TSE : 도쿄 ' |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output1` | 응답상세 | object | Y |  |  |
| `nrec` | RecordCount | string | Y | 4 |  |
| `output2` | 응답상세 | object array | Y |  | array |
| `icod` | 업종코드 | string | Y | 4 |  |
| `name` | 업종명 | string | Y | 32 |  |

**Request 예시**
```
AUTH: EXCD:NAS
```

**Response 예시**
```json
{     "output1": {         "nrec": "42"     },     "output2": [         {             "icod": "000",             "name": "전체"         },         {             "icod": "010",             "name": "에너지 및 관련 서비스"         },...     ],     "rt_cd": "0",     "msg_cd": "MCA00000",     "msg1": "정상처리 되었습니다." }
```

---

### 해외결제일자조회

| 항목 | 값 |
|------|----|
| API ID | `해외주식-017` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `CTOS5011R` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/quotations/countries-holiday` |

> 해외결제일자조회 API입니다.

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | CTOS5011R |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | N | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `TRAD_DT` | 기준일자 | string | Y | 8 | 기준일자(YYYYMMDD) |
| `CTX_AREA_NK` | 연속조회키 | string | Y | 20 | 공백으로 입력 |
| `CTX_AREA_FK` | 연속조회검색조건 | string | Y | 20 | 공백으로 입력 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output` | 응답상세1 | object | Y |  |  |
| `prdt_type_cd` | 상품유형코드 | string | Y | 3 | 512  미국 나스닥 / 513  미국 뉴욕거래소 / 529  미국 아멕스  515  일본 501  홍콩 / 543  홍콩CNY / 558  홍콩USD 507  베트남 하노이거래소 / 508  베트남 호치민거래소 5 |
| `tr_natn_cd` | 거래국가코드 | string | Y | 3 | 840 미국 / 392 일본 / 344 홍콩 704 베트남 / 156 중국 |
| `tr_natn_name` | 거래국가명 | string | Y | 60 |  |
| `natn_eng_abrv_cd` | 국가영문약어코드 | string | Y | 2 | US 미국 / JP 일본 / HK 홍콩 VN 베트남 / CN 중국 |
| `tr_mket_cd` | 거래시장코드 | string | Y | 2 |  |
| `tr_mket_name` | 거래시장명 | string | Y | 60 |  |
| `acpl_sttl_dt` | 현지결제일자 | string | Y | 8 | 현지결제일자(YYYYMMDD) |
| `dmst_sttl_dt` | 국내결제일자 | string | Y | 8 | 국내결제일자(YYYYMMDD) |

**Request 예시**
```
{     "TRAD_DT":"20221227",     "CTX_AREA_NK":"",     "CTX_AREA_FK":"" }
```

**Response 예시**
```json
{     "ctx_area_fk": "20221227            ",     "ctx_area_nk": "                    ",     "output": [         {             "prdt_type_cd": "507",             "tr_natn_cd": "704",             "tr_natn_name": "베트남",             "natn_eng_abrv_cd": "VN",             "tr_mket_cd": "01",             "tr_mket_name": "하노이거래소",             "acpl_sttl_dt": "20221229",             "dmst_sttl_dt": "202212
```

---

### 해외지수분봉조회

| 항목 | 값 |
|------|----|
| API ID | `v1_해외주식-031` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `FHKST03030200` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-price/v1/quotations/inquire-time-indexchartprice` |

> 해외지수분봉조회 API입니다. 실전계좌의 경우, 최근 102건까지 확인 가능합니다.

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | FHKST03030200 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | N | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `FID_COND_MRKT_DIV_CODE` | 조건 시장 분류 코드 | string | Y | 2 | N 해외지수 X 환율 KX 원화환율 |
| `FID_INPUT_ISCD` | 입력 종목코드 | string | Y | 12 | 종목번호(ex. TSLA) |
| `FID_HOUR_CLS_CODE` | 시간 구분 코드 | string | Y | 5 | 0: 정규장, 1: 시간외 |
| `FID_PW_DATA_INCU_YN` | 과거 데이터 포함 여부 | string | Y | 2 | Y/N |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output1` | 응답상세 | object | Y |  |  |
| `ovrs_nmix_prdy_vrss` | 해외 지수 전일 대비 | string | Y | 114 |  |
| `prdy_vrss_sign` | 전일 대비 부호 | string | Y | 1 |  |
| `hts_kor_isnm` | HTS 한글 종목명 | string | Y | 40 |  |
| `prdy_ctrt` | 전일 대비율 | string | Y | 82 |  |
| `ovrs_nmix_prdy_clpr` | 해외 지수 전일 종가 | string | Y | 114 |  |
| `acml_vol` | 누적 거래량 | string | Y | 18 |  |
| `ovrs_nmix_prpr` | 해외 지수 현재가 | string | Y | 114 |  |
| `stck_shrn_iscd` | 주식 단축 종목코드 | string | Y | 9 |  |
| `ovrs_prod_oprc` | 해외 상품 시가2 | string | Y | 114 | 시가 |
| `ovrs_prod_hgpr` | 해외 상품 최고가 | string | Y | 114 | 최고가 |
| `ovrs_prod_lwpr` | 해외 상품 최저가 | string | Y | 114 | 최저가 |
| `output2` | 응답상세2 | object array | Y |  | array |
| `stck_bsop_date` | 주식 영업 일자 | string | Y | 8 | 영업 일자 |
| `stck_cntg_hour` | 주식 체결 시간 | string | Y | 6 | 체결 시간 |
| `optn_prpr` | 옵션 현재가 | string | Y | 112 | 현재가 |
| `optn_oprc` | 옵션 시가2 | string | Y | 112 | 시가 |
| `optn_hgpr` | 옵션 최고가 | string | Y | 112 | 최고가 |
| `optn_lwpr` | 옵션 최저가 | string | Y | 112 | 최저가 |
| `cntg_vol` | 체결 거래량 | string | Y | 18 |  |

**Request 예시**
```
{ "FID_COND_MRKT_DIV_CODE":"N", "FID_INPUT_ISCD":"SPX", "FID_HOUR_CLS_CODE":"0", "FID_PW_DATA_INCU_YN":"Y" }
```

**Response 예시**
```json
{     "output1": {         "ovrs_nmix_prdy_vrss": "105.23",         "prdy_vrss_sign": "2",         "prdy_ctrt": "2.11",         "ovrs_nmix_prdy_clpr": "4981.80",         "acml_vol": "0",         "hts_kor_isnm": "S&P500",         "ovrs_nmix_prpr": "5087.03",         "stck_shrn_iscd": "SPX",         "ovrs_prod_oprc": "5038.83",         "ovrs_prod_hgpr": "5094.39",         "ovrs_prod_lwpr": "5038.83"
```

---

---

## 4. 시세분석/랭킹 API (REST)

### 해외주식 가격급등락

| 항목 | 값 |
|------|----|
| API ID | `해외주식-038` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS76260000` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/ranking/price-fluct` |

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHDFS76260000 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `KEYB` | NEXT KEY BUFF | string | Y | 8 | 공백 |
| `AUTH` | 사용자권한정보 | string | Y | 32 | 공백 |
| `EXCD` | 거래소코드 | string | Y | 4 | 'NYS : 뉴욕, NAS : 나스닥,  AMS : 아멕스  HKS : 홍콩, SHS : 상해 , SZS : 심천 HSX : 호치민, HNX : 하노이 TSE : 도쿄 ' |
| `GUBN` | 급등/급락구분 | string | Y | 1 | 0(급락), 1(급등) |
| `MIXN` | N분전콤보값 | string | Y | 1 | N분전 : 0(1분전), 1(2분전), 2(3분전), 3(5분전), 4(10분전), 5(15분전), 6(20분전), 7(30분전), 8(60분전), 9(120분전) |
| `VOL_RANG` | 거래량조건 | string | Y | 1 | 0(전체), 1(1백주이상), 2(1천주이상), 3(1만주이상), 4(10만주이상), 5(100만주이상), 6(1000만주이상) |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output1` | 응답상세 | object | Y |  |  |
| `zdiv` | 소수점자리수 | string | Y | 1 |  |
| `stat` | 거래상태 | string | Y | 20 |  |
| `nrec` | RecordCount | string | Y | 4 |  |
| `output2` | 응답상세 | object array | Y |  | array |
| `rsym` | 실시간조회심볼 | string | Y | 16 |  |
| `excd` | 거래소코드 | string | Y | 4 |  |
| `symb` | 종목코드 | string | Y | 16 |  |
| `knam` | 종목명 | string | Y | 48 |  |
| `last` | 현재가 | string | Y | 12 |  |
| `sign` | 기호 | string | Y | 1 |  |
| `diff` | 대비 | string | Y | 12 |  |
| `rate` | 등락율 | string | Y | 12 |  |
| `tvol` | 거래량 | string | Y | 14 |  |
| `pask` | 매도호가 | string | Y | 12 |  |
| `pbid` | 매수호가 | string | Y | 12 |  |
| `n_base` | 기준가격 | string | Y | 12 |  |
| `n_diff` | 기준가격대비 | string | Y | 12 |  |
| `n_rate` | 기준가격대비율 | string | Y | 12 |  |
| `enam` | 영문종목명 | string | Y | 48 |  |
| `e_ordyn` | 매매가능 | string | Y | 2 |  |

---

### 해외주식 거래량급증

| 항목 | 값 |
|------|----|
| API ID | `해외주식-039` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS76270000` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/ranking/volume-surge` |

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHDFS76270000 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `KEYB` | NEXT KEY BUFF | string | Y | 8 | 공백 |
| `AUTH` | 사용자권한정보 | string | Y | 32 | 공백 |
| `EXCD` | 거래소코드 | string | Y | 4 | 'NYS : 뉴욕, NAS : 나스닥,  AMS : 아멕스  HKS : 홍콩, SHS : 상해 , SZS : 심천 HSX : 호치민, HNX : 하노이 TSE : 도쿄 ' |
| `MIXN` | N분전콤보값 | string | Y | 1 | N분전 : 0(1분전), 1(2분전), 2(3분전), 3(5분전), 4(10분전), 5(15분전), 6(20분전), 7(30분전), 8(60분전), 9(120분전) |
| `VOL_RANG` | 거래량조건 | string | Y | 1 | 0(전체), 1(1백주이상), 2(1천주이상), 3(1만주이상), 4(10만주이상), 5(100만주이상), 6(1000만주이상) |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output1` | 응답상세 | object | Y |  |  |
| `zdiv` | 소수점자리수 | string | Y | 1 |  |
| `stat` | 거래상태 | string | Y | 20 |  |
| `nrec` | RecordCount | string | Y | 4 |  |
| `output2` | 응답상세 | object array | Y |  | array |
| `rsym` | 실시간조회심볼 | string | Y | 16 |  |
| `excd` | 거래소코드 | string | Y | 4 |  |
| `symb` | 종목코드 | string | Y | 16 |  |
| `knam` | 종목명 | string | Y | 48 |  |
| `last` | 현재가 | string | Y | 12 |  |
| `sign` | 기호 | string | Y | 1 |  |
| `diff` | 대비 | string | Y | 12 |  |
| `rate` | 등락율 | string | Y | 12 |  |
| `tvol` | 거래량 | string | Y | 14 |  |
| `pask` | 매도호가 | string | Y | 12 |  |
| `pbid` | 매수호가 | string | Y | 12 |  |
| `n_tvol` | 기준거래량 | string | Y | 14 |  |
| `n_diff` | 증가량 | string | Y | 12 |  |
| `n_rate` | 증가율 | string | Y | 12 |  |
| `enam` | 영문종목명 | string | Y | 48 |  |
| `e_ordyn` | 매매가능 | string | Y | 2 |  |

---

### 해외주식 매수체결강도상위

| 항목 | 값 |
|------|----|
| API ID | `해외주식-040` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS76280000` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/ranking/volume-power` |

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHDFS76280000 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `KEYB` | NEXT KEY BUFF | string | Y | 8 | 공백 |
| `AUTH` | 사용자권한정보 | string | Y | 32 | 공백 |
| `EXCD` | 거래소코드 | string | Y | 4 | 'NYS : 뉴욕, NAS : 나스닥,  AMS : 아멕스  HKS : 홍콩, SHS : 상해 , SZS : 심천 HSX : 호치민, HNX : 하노이 TSE : 도쿄 ' |
| `NDAY` | N일자값 | string | Y | 1 | N분전 : 0(1분전), 1(2분전), 2(3분전), 3(5분전), 4(10분전), 5(15분전), 6(20분전), 7(30분전), 8(60분전), 9(120분전) |
| `VOL_RANG` | 거래량조건 | string | Y | 1 | 0(전체), 1(1백주이상), 2(1천주이상), 3(1만주이상), 4(10만주이상), 5(100만주이상), 6(1000만주이상) |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output1` | 응답상세 | object | Y |  |  |
| `zdiv` | 소수점자리수 | string | Y | 1 |  |
| `stat` | 거래상태 | string | Y | 20 |  |
| `nrec` | RecordCount | string | Y | 4 |  |
| `output2` | 응답상세 | object array | Y |  | array |
| `rsym` | 실시간조회심볼 | string | Y | 16 |  |
| `excd` | 거래소코드 | string | Y | 4 |  |
| `symb` | 종목코드 | string | Y | 16 |  |
| `knam` | 종목명 | string | Y | 48 |  |
| `last` | 현재가 | string | Y | 12 |  |
| `sign` | 기호 | string | Y | 1 |  |
| `diff` | 대비 | string | Y | 12 |  |
| `rate` | 등락율 | string | Y | 12 |  |
| `tvol` | 거래량 | string | Y | 14 |  |
| `pask` | 매도호가 | string | Y | 12 |  |
| `pbid` | 매수호가 | string | Y | 12 |  |
| `tpow` | 당일체결강도 | string | Y | 10 |  |
| `powx` | 체결강도 | string | Y | 10 |  |
| `enam` | 영문종목명 | string | Y | 48 |  |
| `e_ordyn` | 매매가능 | string | Y | 2 |  |

---

### 해외주식 상승율_하락율

| 항목 | 값 |
|------|----|
| API ID | `해외주식-041` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS76290000` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/ranking/updown-rate` |

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHDFS76290000 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `KEYB` | NEXT KEY BUFF | string | Y | 8 | 공백 |
| `AUTH` | 사용자권한정보 | string | Y | 32 | 공백 |
| `EXCD` | 거래소코드 | string | Y | 4 | 'NYS : 뉴욕, NAS : 나스닥,  AMS : 아멕스  HKS : 홍콩, SHS : 상해 , SZS : 심천 HSX : 호치민, HNX : 하노이 TSE : 도쿄 ' |
| `GUBN` | 상승율/하락율 구분 | string | Y | 1 | 0(하락율), 1(상승율) |
| `NDAY` | N일자값 | string | Y | 1 | N일전 : 0(당일), 1(2일), 2(3일), 3(5일), 4(10일), 5(20일전), 6(30일), 7(60일), 8(120일), 9(1년) |
| `VOL_RANG` | 거래량조건 | string | Y | 1 | 0(전체), 1(1백주이상), 2(1천주이상), 3(1만주이상), 4(10만주이상), 5(100만주이상), 6(1000만주이상) |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output1` | 응답상세 | object | Y |  |  |
| `zdiv` | 소수점자리수 | string | Y | 1 |  |
| `stat` | 거래상태정보 | string | Y | 20 |  |
| `crec` | 현재Count | string | Y | 6 |  |
| `trec` | 전체조회종목수 | string | Y | 6 |  |
| `nrec` | RecordCount | string | Y | 4 |  |
| `output2` | 응답상세 | object array | Y |  | array |
| `rsym` | 실시간조회심볼 | string | Y | 16 |  |
| `excd` | 거래소코드 | string | Y | 4 |  |
| `symb` | 종목코드 | string | Y | 1 |  |
| `name` | 종목명 | string | Y | 48 |  |
| `last` | 현재가 | string | Y | 16 |  |
| `sign` | 기호 | string | Y | 1 |  |
| `diff` | 대비 | string | Y | 12 |  |
| `rate` | 등락율 | string | Y | 12 |  |
| `tvol` | 거래량 | string | Y | 14 |  |
| `pask` | 매도호가 | string | Y | 12 |  |
| `pbid` | 매수호가 | string | Y | 12 |  |
| `n_base` | 기준가격 | string | Y | 12 |  |
| `n_diff` | 기준가격대비 | string | Y | 12 |  |
| `n_rate` | 기준가격대비율 | string | Y | 12 |  |
| `rank` | 순위 | string | Y | 6 |  |
| `ename` | 영문종목명 | string | Y | 48 |  |
| `e_ordyn` | 매매가능 | string | Y | 2 |  |

---

### 해외주식 신고_신저가

| 항목 | 값 |
|------|----|
| API ID | `해외주식-042` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS76300000` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/ranking/new-highlow` |

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHDFS76300000 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `KEYB` | NEXT KEY BUFF | string | Y | 8 | 공백 |
| `AUTH` | 사용자권한정보 | string | Y | 32 | 공백 |
| `EXCD` | 거래소코드 | string | Y | 4 | 'NYS : 뉴욕, NAS : 나스닥,  AMS : 아멕스  HKS : 홍콩, SHS : 상해 , SZS : 심천 HSX : 호치민, HNX : 하노이 TSE : 도쿄 ' |
| `GUBN` | 신고/신저 구분 | string | Y | 1 | 신고(1) 신저(0) |
| `GUBN2` | 일시돌파/돌파 구분 | string | Y | 1 | 일시돌파(0) 돌파유지(1) |
| `NDAY` | N일자값 | string | Y | 1 | N일전 : 0(5일), 1(10일), 2(20일), 3(30일), 4(60일), 5(120일전), 6(52주), 7(1년) |
| `VOL_RANG` | 거래량조건 | string | Y | 1 | 0(전체), 1(1백주이상), 2(1천주이상), 3(1만주이상), 4(10만주이상), 5(100만주이상), 6(1000만주이상) |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output1` | 응답상세 | object | Y |  |  |
| `zdiv` | 소수점자리수 | string | Y | 1 |  |
| `stat` | 거래상태정보 | string | Y | 20 |  |
| `nrec` | RecordCount | string | Y | 4 |  |
| `output2` | 응답상세 | object array | Y |  | array |
| `rsym` | 실시간조회심볼 | string | Y | 16 |  |
| `excd` | 거래소코드 | string | Y | 4 |  |
| `symb` | 종목코드 | string | Y | 1 |  |
| `name` | 종목명 | string | Y | 48 |  |
| `last` | 현재가 | string | Y | 16 |  |
| `sign` | 기호 | string | Y | 1 |  |
| `diff` | 대비 | string | Y | 12 |  |
| `rate` | 등락율 | string | Y | 12 |  |
| `tvol` | 거래량 | string | Y | 14 |  |
| `pask` | 매도호가 | string | Y | 12 |  |
| `pbid` | 매수호가 | string | Y | 12 |  |
| `n_base` | 기준가 | string | Y | 12 |  |
| `n_diff` | 기준가대비 | string | Y | 12 |  |
| `n_rate` | 기준가대비율 | string | Y | 12 |  |
| `ename` | 영문종목명 | string | Y | 48 |  |
| `e_ordyn` | 매매가능 | string | Y | 2 |  |

---

### 해외주식 거래량순위

| 항목 | 값 |
|------|----|
| API ID | `해외주식-043` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS76310010` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/ranking/trade-vol` |

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHDFS76310010 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `KEYB` | NEXT KEY BUFF | string | Y | 8 | 공백 |
| `AUTH` | 사용자권한정보 | string | Y | 32 | 공백 |
| `EXCD` | 거래소코드 | string | Y | 4 | 'NYS : 뉴욕, NAS : 나스닥,  AMS : 아멕스  HKS : 홍콩, SHS : 상해 , SZS : 심천 HSX : 호치민, HNX : 하노이 TSE : 도쿄 ' |
| `NDAY` | N일자값 | string | Y | 1 | N일전 : 0(당일), 1(2일), 2(3일), 3(5일), 4(10일), 5(20일전), 6(30일), 7(60일), 8(120일), 9(1년) |
| `PRC1` | 현재가 필터범위 1 | string | Y | 12 | 가격 ~ |
| `PRC2` | 현재가 필터범위 2 | string | Y | 12 | ~ 가격 |
| `VOL_RANG` | 거래량조건 | string | Y | 1 | 0(전체), 1(1백주이상), 2(1천주이상), 3(1만주이상), 4(10만주이상), 5(100만주이상), 6(1000만주이상) |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output1` | 응답상세 | object | Y |  |  |
| `zdiv` | 소수점자리수 | string | Y | 1 |  |
| `stat` | 거래상태정보 | string | Y | 20 |  |
| `crec` | 현재조회종목수 | string | Y | 6 |  |
| `trec` | 전체조회종목수 | string | Y | 6 |  |
| `nrec` | RecordCount | string | Y | 4 |  |
| `output2` | 응답상세 | object array | Y |  | array |
| `rsym` | 실시간조회심볼 | string | Y | 16 |  |
| `excd` | 거래소코드 | string | Y | 4 |  |
| `symb` | 종목코드 | string | Y | 1 |  |
| `name` | 종목명 | string | Y | 48 |  |
| `last` | 현재가 | string | Y | 16 |  |
| `sign` | 기호 | string | Y | 1 |  |
| `diff` | 대비 | string | Y | 12 |  |
| `rate` | 등락율 | string | Y | 12 |  |
| `pask` | 매도호가 | string | Y | 12 |  |
| `pbid` | 매수호가 | string | Y | 12 |  |
| `tvol` | 거래량 | string | Y | 14 |  |
| `tamt` | 거래대금 | string | Y | 14 |  |
| `a_tvol` | 평균거래량 | string | Y | 14 |  |
| `rank` | 순위 | string | Y | 6 |  |
| `ename` | 영문종목명 | string | Y | 48 |  |
| `e_ordyn` | 매매가능 | string | Y | 2 |  |

---

### 해외주식 거래대금순위

| 항목 | 값 |
|------|----|
| API ID | `해외주식-044` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS76320010` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/ranking/trade-pbmn` |

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHDFS76320010 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `KEYB` | NEXT KEY BUFF | string | Y | 8 | 공백 |
| `AUTH` | 사용자권한정보 | string | Y | 32 | 공백 |
| `EXCD` | 거래소코드 | string | Y | 4 | 'NYS : 뉴욕, NAS : 나스닥,  AMS : 아멕스  HKS : 홍콩, SHS : 상해 , SZS : 심천 HSX : 호치민, HNX : 하노이 TSE : 도쿄 ' |
| `NDAY` | N일자값 | string | Y | 1 | N일전 : 0(당일), 1(2일), 2(3일), 3(5일), 4(10일), 5(20일전), 6(30일), 7(60일), 8(120일), 9(1년) |
| `VOL_RANG` | 거래량조건 | string | Y | 1 | 0(전체), 1(1백주이상), 2(1천주이상), 3(1만주이상), 4(10만주이상), 5(100만주이상), 6(1000만주이상) |
| `PRC1` | 현재가 필터범위 1 | string | Y | 12 | 가격 ~ |
| `PRC2` | 현재가 필터범위 2 | string | Y | 12 | ~ 가격 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output1` | 응답상세 | object | Y |  |  |
| `zdiv` | 소수점자리수 | string | Y | 1 |  |
| `stat` | 거래상태정보 | string | Y | 20 |  |
| `crec` | 현재조회종목수 | string | Y | 6 |  |
| `trec` | 전체조회종목수 | string | Y | 6 |  |
| `nrec` | RecordCount | string | Y | 4 |  |
| `output2` | 응답상세 | object array | Y |  | array |
| `rsym` | 실시간조회심볼 | string | Y | 16 |  |
| `excd` | 거래소코드 | string | Y | 4 |  |
| `symb` | 종목코드 | string | Y | 1 |  |
| `name` | 종목명 | string | Y | 48 |  |
| `last` | 현재가 | string | Y | 16 |  |
| `sign` | 기호 | string | Y | 1 |  |
| `diff` | 대비 | string | Y | 12 |  |
| `rate` | 등락율 | string | Y | 12 |  |
| `pask` | 매도호가 | string | Y | 12 |  |
| `pbid` | 매수호가 | string | Y | 12 |  |
| `tvol` | 거래량 | string | Y | 14 |  |
| `tamt` | 거래대금 | string | Y | 14 |  |
| `a_tamt` | 평균거래대금 | string | Y | 14 |  |
| `rank` | 순위 | string | Y | 6 |  |
| `ename` | 영문종목명 | string | Y | 48 |  |
| `e_ordyn` | 매매가능 | string | Y | 2 |  |

---

### 해외주식 거래증가율순위

| 항목 | 값 |
|------|----|
| API ID | `해외주식-045` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS76330000` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/ranking/trade-growth` |

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHDFS76330000 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `KEYB` | NEXT KEY BUFF | string | Y | 8 | 공백 |
| `AUTH` | 사용자권한정보 | string | Y | 32 | 공백 |
| `EXCD` | 거래소코드 | string | Y | 4 | 'NYS : 뉴욕, NAS : 나스닥,  AMS : 아멕스  HKS : 홍콩, SHS : 상해 , SZS : 심천 HSX : 호치민, HNX : 하노이 TSE : 도쿄 ' |
| `NDAY` | N일자값 | string | Y | 1 | N일전 : 0(당일), 1(2일), 2(3일), 3(5일), 4(10일), 5(20일전), 6(30일), 7(60일), 8(120일), 9(1년) |
| `VOL_RANG` | 거래량조건 | string | Y | 1 | 0(전체), 1(1백주이상), 2(1천주이상), 3(1만주이상), 4(10만주이상), 5(100만주이상), 6(1000만주이상) |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메시지 | string | Y | 80 |  |
| `output1` | 응답상세 | object | Y |  |  |
| `zdiv` | 소수점자리수 | string | Y | 1 |  |
| `stat` | 거래상태정보 | string | Y | 20 |  |
| `crec` | 현재조회종목수 | string | Y | 6 |  |
| `trec` | 전체조회종목수 | string | Y | 6 |  |
| `nrec` | RecordCount | string | Y | 4 |  |
| `output2` | 응답상세 | object array | Y |  | array |
| `rsym` | 실시간조회심볼 | string | Y | 16 |  |
| `excd` | 거래소코드 | string | Y | 4 |  |
| `symb` | 종목코드 | string | Y | 1 |  |
| `name` | 종목명 | string | Y | 48 |  |
| `last` | 현재가 | string | Y | 16 |  |
| `sign` | 기호 | string | Y | 1 |  |
| `diff` | 대비 | string | Y | 12 |  |
| `rate` | 등락율 | string | Y | 12 |  |
| `pask` | 매도호가 | string | Y | 12 |  |
| `pbid` | 매수호가 | string | Y | 12 |  |
| `tvol` | 거래량 | string | Y | 14 |  |
| `n_tvol` | 평균거래량 | string | Y | 14 |  |
| `n_rate` | 증가율 | string | Y | 12 |  |
| `rank` | 순위 | string | Y | 6 |  |
| `ename` | 영문종목명 | string | Y | 48 |  |
| `e_ordyn` | 매매가능 | string | Y | 2 |  |

---

### 해외주식 거래회전율순위

| 항목 | 값 |
|------|----|
| API ID | `해외주식-046` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS76340000` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/ranking/trade-turnover` |

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHDFS76340000 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `KEYB` | NEXT KEY BUFF | string | Y | 8 | 공백 |
| `AUTH` | 사용자권한정보 | string | Y | 32 | 공백 |
| `EXCD` | 거래소코드 | string | Y | 4 | 'NYS : 뉴욕, NAS : 나스닥,  AMS : 아멕스  HKS : 홍콩, SHS : 상해 , SZS : 심천 HSX : 호치민, HNX : 하노이 TSE : 도쿄 ' |
| `NDAY` | N일자값 | string | Y | 1 | N일전 : 0(당일), 1(2일), 2(3일), 3(5일), 4(10일), 5(20일전), 6(30일), 7(60일), 8(120일), 9(1년) |
| `VOL_RANG` | 거래량조건 | string | Y | 1 | 0(전체), 1(1백주이상), 2(1천주이상), 3(1만주이상), 4(10만주이상), 5(100만주이상), 6(1000만주이상) |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output1` | 응답상세 | object | Y |  |  |
| `zdiv` | 소수점자리수 | string | Y | 1 |  |
| `stat` | 거래상태정보 | string | Y | 20 |  |
| `crec` | 현재조회종목수 | string | Y | 6 |  |
| `trec` | 전체조회종목수 | string | Y | 6 |  |
| `nrec` | RecordCount | string | Y | 4 |  |
| `output2` | 응답상세 | object array | Y |  | array |
| `rsym` | 실시간조회심볼 | string | Y | 16 |  |
| `excd` | 거래소코드 | string | Y | 4 |  |
| `symb` | 종목코드 | string | Y | 1 |  |
| `name` | 종목명 | string | Y | 48 |  |
| `last` | 현재가 | string | Y | 16 |  |
| `sign` | 기호 | string | Y | 1 |  |
| `diff` | 대비 | string | Y | 12 |  |
| `rate` | 등락율 | string | Y | 12 |  |
| `tvol` | 거래량 | string | Y | 14 |  |
| `pask` | 매도호가 | string | Y | 12 |  |
| `pbid` | 매수호가 | string | Y | 12 |  |
| `n_tvol` | 평균거래량 | string | Y | 14 |  |
| `shar` | 상장주식수 | string | Y | 16 |  |
| `tover` | 회전율 | string | Y | 10 |  |
| `rank` | 순위 | string | Y | 6 |  |
| `ename` | 영문종목명 | string | Y | 48 |  |
| `e_ordyn` | 매매가능 | string | Y | 2 |  |

---

### 해외주식 시가총액순위

| 항목 | 값 |
|------|----|
| API ID | `해외주식-047` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS76350100` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-stock/v1/ranking/market-cap` |

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHDFS76350100 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `KEYB` | NEXT KEY BUFF | string | Y | 1 | 공백 |
| `AUTH` | 사용자권한정보 | string | Y | 32 | 공백 |
| `EXCD` | 거래소코드 | string | Y | 4 | 'NYS : 뉴욕, NAS : 나스닥,  AMS : 아멕스  HKS : 홍콩, SHS : 상해 , SZS : 심천 HSX : 호치민, HNX : 하노이 TSE : 도쿄 ' |
| `VOL_RANG` | 거래량조건 | string | Y | 1 | 0(전체), 1(1백주이상), 2(1천주이상), 3(1만주이상), 4(10만주이상), 5(100만주이상), 6(1000만주이상) |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output1` | 응답상세 | object | Y |  |  |
| `zdiv` | 소수점자리수 | string | Y | 1 |  |
| `stat` | 거래상태정보 | string | Y | 20 |  |
| `crec` | 현재조회종목수 | string | Y | 6 |  |
| `trec` | 전체조회종목수 | string | Y | 6 |  |
| `nrec` | RecordCount | string | Y | 4 |  |
| `output2` | 응답상세 | object array | Y |  | array |
| `rsym` | 실시간조회심볼 | string | Y | 16 |  |
| `excd` | 거래소코드 | string | Y | 4 |  |
| `symb` | 종목코드 | string | Y | 1 |  |
| `name` | 종목명 | string | Y | 48 |  |
| `last` | 현재가 | string | Y | 16 |  |
| `sign` | 기호 | string | Y | 1 |  |
| `diff` | 대비 | string | Y | 12 |  |
| `rate` | 등락율 | string | Y | 12 |  |
| `tvol` | 거래량 | string | Y | 14 |  |
| `shar` | 상장주식수 | string | Y | 16 |  |
| `tomv` | 시가총액 | string | Y | 16 |  |
| `grav` | 비중 | string | Y | 10 |  |
| `rank` | 순위 | string | Y | 6 |  |
| `ename` | 영문종목명 | string | Y | 48 |  |
| `e_ordyn` | 매매가능 | string | Y | 2 |  |

---

### 해외뉴스종합(제목)

| 항목 | 값 |
|------|----|
| API ID | `해외주식-053` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHPSTH60100C1` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-price/v1/quotations/news-title` |

> 해외뉴스종합(제목) API입니다. 한국투자 HTS(eFriend Plus) &gt; [7702] 해외뉴스종합 화면의 "우측 상단 뉴스목록" 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHPSTH60100C1 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `INFO_GB` | 뉴스구분 | string | Y | 1 | 전체: 공백 |
| `CLASS_CD` | 중분류 | string | Y | 2 | 전체: 공백 |
| `NATION_CD` | 국가코드 | string | Y | 2 | 전체: 공백 CN(중국), HK(홍콩), US(미국) |
| `EXCHANGE_CD` | 거래소코드 | string | Y | 3 | 전체: 공백 |
| `SYMB` | 종목코드 | string | Y | 20 | 전체: 공백 |
| `DATA_DT` | 조회일자 | string | Y | 8 | 전체: 공백 특정일자(YYYYMMDD) ex. 20240502 |
| `DATA_TM` | 조회시간 | string | Y | 6 | 전체: 공백 전체: 공백 특정시간(HHMMSS) ex. 093500 |
| `CTS` | 다음키 | string | Y | 35 | 공백 입력 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `outblock1` | 응답상세 | object array | Y |  | array |
| `info_gb` | 뉴스구분 | string | Y | 1 |  |
| `news_key` | 뉴스키 | string | Y | 20 |  |
| `data_dt` | 조회일자 | string | Y | 8 |  |
| `data_tm` | 조회시간 | string | Y | 6 |  |
| `class_cd` | 중분류 | string | Y | 2 |  |
| `class_name` | 중분류명 | string | Y | 20 |  |
| `source` | 자료원 | string | Y | 20 |  |
| `nation_cd` | 국가코드 | string | Y | 2 |  |
| `exchange_cd` | 거래소코드 | string | Y | 3 |  |
| `symb` | 종목코드 | string | Y | 20 |  |
| `symb_name` | 종목명 | string | Y | 48 |  |
| `title` | 제목 | string | Y | 128 |  |

**Request 예시**
```
INFO_GB: CLASS_CD: NATION_CD: EXCHANGE_CD: SYMB: DATA_DT: DATA_TM: CTS:
```

**Response 예시**
```json
{     "outblock1": [         {             "info_gb": "t",             "news_key": "ICH709214",             "data_dt": "20240503",             "data_tm": "145447",             "class_cd": "05",             "class_name": "종목리포트",             "source": "연합미국",             "nation_cd": "US",             "exchange_cd": "",             "symb": "",             "symb_name": "",             "title": "톰 리 
```

---

### 해외속보(제목)

| 항목 | 값 |
|------|----|
| API ID | `해외주식-055` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `FHKST01011801` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-price/v1/quotations/brknews-title` |

> 해외속보(제목) API입니다. 한국투자 HTS(eFriend Plus) &gt; [7704] 해외속보 화면 의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.  최대 100건까지 조회 가능합니다.

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | FHKST01011801 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `FID_NEWS_OFER_ENTP_CODE` | 뉴스제공업체코드 | string | Y | 40 | 뉴스제공업체구분=>0:전체조회 |
| `FID_COND_MRKT_CLS_CODE` | 조건시장구분코드 | string | Y | 6 | 공백 |
| `FID_INPUT_ISCD` | 입력종목코드 | string | Y | 12 | 공백 |
| `FID_TITL_CNTT` | 제목내용 | string | Y | 132 | 공백 |
| `FID_INPUT_DATE_1` | 입력날짜1 | string | Y | 10 | 공백 |
| `FID_INPUT_HOUR_1` | 입력시간1 | string | Y | 10 | 공백 |
| `FID_RANK_SORT_CLS_CODE` | 순위정렬구분코드 | string | Y | 2 | 공백 |
| `FID_INPUT_SRNO` | 입력일련번호 | string | Y | 20 | 공백 |
| `FID_COND_SCR_DIV_CODE` | 조건화면분류코드 | string | Y | 5 | 화면번호:11801 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output` | 응답상세 | object array | Y |  | array |
| `cntt_usiq_srno` | 내용조회용일련번호 | string | Y | 20 |  |
| `news_ofer_entp_code` | 뉴스제공업체코드 | string | Y | 1 |  |
| `data_dt` | 작성일자 | string | Y | 8 |  |
| `data_tm` | 작성시간 | string | Y | 6 |  |
| `hts_pbnt_titl_cntt` | HTS공시제목내용 | string | Y | 400 |  |
| `news_lrdv_code` | 뉴스대구분 | string | Y | 8 |  |
| `dorg` | 자료원 | string | Y | 20 |  |
| `iscd1` | 종목코드1 | string | Y | 9 |  |
| `iscd2` | 종목코드2 | string | Y | 9 |  |
| `iscd3` | 종목코드3 | string | Y | 9 |  |
| `iscd4` | 종목코드4 | string | Y | 9 |  |
| `iscd5` | 종목코드5 | string | Y | 9 |  |
| `iscd6` | 종목코드6 | string | Y | 9 |  |
| `iscd7` | 종목코드7 | string | Y | 9 |  |
| `iscd8` | 종목코드8 | string | Y | 9 |  |
| `iscd9` | 종목코드9 | string | Y | 9 |  |
| `iscd10` | 종목코드10 | string | Y | 9 |  |
| `kor_isnm1` | 한글종목명1 | string | Y | 40 |  |
| `kor_isnm2` | 한글종목명2 | string | Y | 40 |  |
| `kor_isnm3` | 한글종목명3 | string | Y | 40 |  |
| `kor_isnm4` | 한글종목명4 | string | Y | 40 |  |
| `kor_isnm5` | 한글종목명5 | string | Y | 40 |  |
| `kor_isnm6` | 한글종목명6 | string | Y | 40 |  |
| `kor_isnm7` | 한글종목명7 | string | Y | 40 |  |
| `kor_isnm8` | 한글종목명8 | string | Y | 40 |  |
| `kor_isnm9` | 한글종목명9 | string | Y | 40 |  |
| `kor_isnm10` | 한글종목명10 | string | Y | 40 |  |

**Request 예시**
```
FID_NEWS_OFER_ENTP_CODE:0 FID_COND_MRKT_CLS_CODE:00 FID_INPUT_ISCD: FID_TITL_CNTT: FID_INPUT_DATE_1: FID_INPUT_HOUR_1: FID_RANK_SORT_CLS_CODE: FID_INPUT_SRNO: FID_COND_SCR_DIV_CODE:11801
```

**Response 예시**
```json
{     "output": [         {             "cntt_usiq_srno": "2024052817340622954",             "news_ofer_entp_code": "U",             "data_dt": "20240528",             "data_tm": "173406",             "hts_pbnt_titl_cntt": "“시진핑, 기업인들 만나 신에너지 분야 과잉투자 경고”",             "news_lrdv_code": "38",             "dorg": "서울경제",             "iscd1": "",             "iscd2": "",             "iscd3": "",     
```

---

### 해외주식 기간별권리조회

| 항목 | 값 |
|------|----|
| API ID | `해외주식-052` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `CTRGT011R` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-price/v1/quotations/period-rights` |

> 해외주식 기간별권리조회 API입니다. 한국투자 HTS(eFriend Plus) &gt; [7520] 기간별해외증권권리조회 화면을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.  ※ 확정여부가 '예정'으로 표시되는 경우는 권리정보가 변경될 수 있으니 참고자료로만 활용하시기 바랍니다.

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | CTRGT011R |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `RGHT_TYPE_CD` | 권리유형코드 | string | Y | 2 | '%%(전체), 01(유상), 02(무상), 03(배당), 11(합병),  14(액면분할), 15(액면병합), 17(감자), 54(WR청구), 61(원리금상환), 71(WR소멸), 74(배당옵션), 75(특별배당), |
| `INQR_DVSN_CD` | 조회구분코드 | string | Y | 2 | 02(현지기준일), 03(청약시작일), 04(청약종료일) |
| `INQR_STRT_DT` | 조회시작일자 | string | Y | 8 | 일자 ~ |
| `INQR_END_DT` | 조회종료일자 | string | Y | 8 | ~ 일자 |
| `PDNO` | 상품번호 | string | Y | 12 | 공백 |
| `PRDT_TYPE_CD` | 상품유형코드 | string | Y | 3 | 공백 |
| `CTX_AREA_NK50` | 연속조회키50 | string | Y | 50 | 공백 |
| `CTX_AREA_FK50` | 연속조회검색조건50 | string | Y | 50 | 공백 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output` | 응답상세 | object array | Y |  | array |
| `bass_dt` | 기준일자 | string | Y | 8 |  |
| `rght_type_cd` | 권리유형코드 | string | Y | 2 |  |
| `pdno` | 상품번호 | string | Y | 12 |  |
| `prdt_name` | 상품명 | string | Y | 60 |  |
| `prdt_type_cd` | 상품유형코드 | string | Y | 3 |  |
| `std_pdno` | 표준상품번호 | string | Y | 12 |  |
| `acpl_bass_dt` | 현지기준일자 | string | Y | 8 |  |
| `sbsc_strt_dt` | 청약시작일자 | string | Y | 8 |  |
| `sbsc_end_dt` | 청약종료일자 | string | Y | 8 |  |
| `cash_alct_rt` | 현금배정비율 | string | Y | 191 |  |
| `stck_alct_rt` | 주식배정비율 | string | Y | 2012 |  |
| `crcy_cd` | 통화코드 | string | Y | 3 |  |
| `crcy_cd2` | 통화코드2 | string | Y | 3 |  |
| `crcy_cd3` | 통화코드3 | string | Y | 3 |  |
| `crcy_cd4` | 통화코드4 | string | Y | 3 |  |
| `alct_frcr_unpr` | 배정외화단가 | string | Y | 195 |  |
| `stkp_dvdn_frcr_amt2` | 주당배당외화금액2 | string | Y | 195 |  |
| `stkp_dvdn_frcr_amt3` | 주당배당외화금액3 | string | Y | 195 |  |
| `stkp_dvdn_frcr_amt4` | 주당배당외화금액4 | string | Y | 195 |  |
| `dfnt_yn` | 확정여부 | string | Y | 1 |  |

**Request 예시**
```
RGHT_TYPE_CD:%% INQR_DVSN_CD:02 INQR_STRT_DT:20240417 INQR_END_DT:20240417 PDNO: PRDT_TYPE_CD: CTX_AREA_NK50: CTX_AREA_FK50:
```

**Response 예시**
```json
{     "ctx_area_nk50": "                                                  ",     "ctx_area_fk50": "%%!^02!^20240417!^20240417!^!^                    ",     "output": [         {             "bass_dt": "20240418",             "rght_type_cd": "03",             "pdno": "000661",             "prdt_name": "[000661]CHANGCHUN HIGH-TECH INDUSTRY (GROUP",             "prdt_type_cd": "552",             "std
```

---

### 해외주식 권리종합

| 항목 | 값 |
|------|----|
| API ID | `해외주식-050` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `HHDFS78330900` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-price/v1/quotations/rights-by-ice` |

> 해외주식 권리종합 API입니다. 한국투자 HTS(eFriend Plus) &gt; [7833] 해외주식 권리(ICE제공) 화면의 "전체" 탭 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.  ※ 조회기간 기준일 입력시 참고 - 상환: 상환일자, 조기상환: 조기상환일자, 티커변경: 적용일, 그 외: 발표일

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | HHDFS78330900 |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `NCOD` | 국가코드 | string | Y | 2 | CN:중국 HK:홍콩 US:미국 JP:일본 VN:베트남 |
| `SYMB` | 심볼 | string | Y | 20 | 종목코드 |
| `ST_YMD` | 일자 시작일 | string | Y | 8 | 미입력 시, 오늘-3개월 기간지정 시, 종료일 입력(ex. 20240514)  ※ 조회기간 기준일 입력시 참고 - 상환: 상환일자, 조기상환: 조기상환일자, 티커변경: 적용일, 그 외: 발표일 |
| `ED_YMD` | 일자 종료일 | string | Y | 8 | 미입력 시, 오늘+3개월 기간지정 시, 종료일 입력(ex. 20240514)  ※ 조회기간 기준일 입력시 참고 - 상환: 상환일자, 조기상환: 조기상환일자, 티커변경: 적용일, 그 외: 발표일 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output1` | 응답상세 | object array | Y |  | array |
| `anno_dt` | ICE공시일 | string | Y | 8 |  |
| `ca_title` | 권리유형 | string | Y | 12 |  |
| `div_lock_dt` | 배당락일 | string | Y | 8 |  |
| `pay_dt` | 지급일 | string | Y | 8 |  |
| `record_dt` | 기준일 | string | Y | 8 |  |
| `validity_dt` | 효력일자 | string | Y | 8 |  |
| `local_end_dt` | 현지지시마감일 | string | Y | 8 |  |
| `lock_dt` | 권리락일 | string | Y | 8 |  |
| `delist_dt` | 상장폐지일 | string | Y | 8 |  |
| `redempt_dt` | 상환일자 | string | Y | 8 |  |
| `early_redempt_dt` | 조기상환일자 | string | Y | 8 |  |
| `effective_dt` | 적용일 | string | Y | 8 |  |

**Request 예시**
```
NCOD:US SYMB:MAIN ST_YMD:20240214 ED_YMD:20240514
```

**Response 예시**
```json
{     "output1": [         {             "anno_dt": "20240221",             "ca_title": "현금배당",             "div_lock_dt": "20240607",             "pay_dt": "20240614",             "record_dt": "20240607",             "validity_dt": "",             "local_end_dt": "",             "lock_dt": "",             "delist_dt": "",             "redempt_dt": "",             "early_redempt_dt": "",          
```

---

### 당사 해외주식담보대출 가능 종목

| 항목 | 값 |
|------|----|
| API ID | `해외주식-051` |
| 통신방식 | REST / GET |
| 실전 TR_ID | `CTLN4050R` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `https://openapi.koreainvestment.com:9443` |
| URL | `/uapi/overseas-price/v1/quotations/colable-by-company` |

> 당사 해외주식담보대출 가능 종목 API입니다. 한국투자 HTS(eFriend Plus) &gt; [0497] 당사 해외주식담보대출 가능 종목 화면 의 기능을 API로 개발한 사항으로, 해당 화면을 참고하시면 기능을 이해하기 쉽습니다.  한 번의 호출에 20건까지 조회가 가능하며 다음조회가 불가하기에, PDNO에 데이터 확인하고자 하는 종목코드를 입력하여 단건조회용으로 사용하시기 바랍니다.

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `authorization` | 접근토큰 | string | Y | 350 | OAuth 토큰이 필요한 API 경우 발급한 Access token  일반고객(Access token 유효기간 1일, OAuth 2.0의 Client Credentials Grant 절차를 준용)  법인(Access |
| `appkey` | 앱키 | string | Y | 36 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `appsecret` | 앱시크릿키 | string | Y | 180 | 한국투자증권 홈페이지에서 발급받은 appkey (절대 노출되지 않도록 주의해주세요.) |
| `personalseckey` | 고객식별키 | string | N | 180 | [법인 필수] 제휴사 회원 관리를 위한 고객식별키 |
| `tr_id` | 거래ID | string | Y | 13 | CTLN4050R |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인  P : 개인 |
| `seq_no` | 일련번호 | string | N | 2 | [법인 필수] 001 |
| `mac_address` | 맥주소 | string | N | 12 | 법인고객 혹은 개인고객의 Mac address 값 |
| `phone_number` | 핸드폰번호 | string | N | 12 | [법인 필수] 제휴사APP을 사용하는 경우 사용자(회원) 핸드폰번호  ex) 01011112222 (하이픈 등 구분값 제거) |
| `ip_addr` | 접속 단말 공인 IP | string | N | 12 | [법인 필수] 사용자(회원)의 IP Address |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Request Query Parameter**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `PDNO` | 상품번호 | string | Y | 12 | ex)AMD |
| `PRDT_TYPE_CD` | 상품유형코드 | string | Y | 3 | 공백 |
| `INQR_STRT_DT` | 조회시작일자 | string | Y | 8 | 공백 |
| `INQR_END_DT` | 조회종료일자 | string | Y | 8 | 공백 |
| `INQR_DVSN` | 조회구분 | string | Y | 2 | 공백 |
| `NATN_CD` | 국가코드 | string | Y | 3 | 840(미국), 344(홍콩), 156(중국) |
| `INQR_SQN_DVSN` | 조회순서구분 | string | Y | 2 | 01(이름순), 02(코드순) |
| `RT_DVSN_CD` | 비율구분코드 | string | Y | 2 | 공백 |
| `RT` | 비율 | string | Y | 238 | 공백 |
| `LOAN_PSBL_YN` | 대출가능여부 | string | Y | 1 | 공백 |
| `CTX_AREA_FK100` | 연속조회검색조건100 | string | Y | 100 | 공백 |
| `CTX_AREA_NK100` | 연속조회키100 | string | Y | 100 | 공백 |

**Response Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `content-type` | 컨텐츠타입 | string | Y | 40 | application/json; charset=utf-8 |
| `tr_id` | 거래ID | string | Y | 13 | 요청한 tr_id |
| `tr_cont` | 연속 거래 여부 | string | N | 1 | tr_cont를 이용한 다음조회 불가 API |
| `gt_uid` | Global UID | string | N | 32 | [법인 전용] 거래고유번호로 사용하므로 거래별로 UNIQUE해야 함 |

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `rt_cd` | 성공 실패 여부 | string | Y | 1 |  |
| `msg_cd` | 응답코드 | string | Y | 8 |  |
| `msg1` | 응답메세지 | string | Y | 80 |  |
| `output1` | 응답상세 | array | Y |  |  |
| `pdno` | 상품번호 | string | Y | 12 |  |
| `ovrs_item_name` | 해외종목명 | string | Y | 60 |  |
| `loan_rt` | 대출비율 | string | Y | 238 |  |
| `mgge_mntn_rt` | 담보유지비율 | string | Y | 238 |  |
| `mgge_ensu_rt` | 담보확보비율 | string | Y | 238 |  |
| `loan_exec_psbl_yn` | 대출실행가능여부 | string | Y | 1 |  |
| `stff_name` | 직원명 | string | Y | 60 |  |
| `erlm_dt` | 등록일자 | string | Y | 8 |  |
| `tr_mket_name` | 거래시장명 | string | Y | 60 |  |
| `crcy_cd` | 통화코드 | string | Y | 3 |  |
| `natn_kor_name` | 국가한글명 | string | Y | 60 |  |
| `ovrs_excg_cd` | 해외거래소코드 | string | Y | 4 |  |
| `output2` | 응답상세 | object | Y |  | array |
| `loan_psbl_item_num` | 대출가능종목수 | string | Y | 20 |  |

**Request 예시**
```
PDNO:AMD PRDT_TYPE_CD: INQR_STRT_DT: INQR_END_DT: INQR_DVSN: NATN_CD:840 INQR_SQN_DVSN:02 RT_DVSN_CD: RT: LOAN_PSBL_YN: CTX_AREA_FK100: CTX_AREA_NK100:
```

**Response 예시**
```json
{     "ctx_area_fk100": "AMD!^!^!^!^!^840!^02                                                                                ",     "ctx_area_nk100": "                                                                                                    ",     "output1": [         {             "pdno": "AMD",             "ovrs_item_name": "AMD",             "loan_rt": "50.00000000",             "mgge
```

---

---

## 5. 실시간시세 API (WebSocket)

### WebSocket 공통 연결 방법

```python
import websocket, json

WS_URL = "ws://ops.koreainvestment.com:21000"  # 실전
# WS_URL = "ws://ops.koreainvestment.com:31000"  # 모의

def subscribe(ws, tr_id, tr_key):
    """실시간 구독 요청"""
    payload = {
        "header": {
            "approval_key": APPROVAL_KEY,  # 실시간 접속키 (별도 발급)
            "custtype": "P",
            "tr_type": "1",  # 1=등록, 2=해제
            "content-type": "utf-8"
        },
        "body": {
            "input": {
                "tr_id": tr_id,
                "tr_key": tr_key  # 종목코드 등
            }
        }
    }
    ws.send(json.dumps(payload))

def unsubscribe(ws, tr_id, tr_key):
    payload["body"]["input"]["tr_type"] = "2"
    ws.send(json.dumps(payload))
```

> ⚠️ **실시간 접속키**: `/oauth2/Approval` 엔드포인트에서 별도 발급 필요 (Access Token과 다름)

### 해외주식 실시간체결통보

| 항목 | 값 |
|------|----|
| API ID | `실시간-009` |
| 통신방식 | WEBSOCKET / POST |
| 실전 TR_ID | `H0GSCNI0` |
| 모의 TR_ID | `H0GSCNI9` |
| 실전 Domain | `ws://ops.koreainvestment.com:21000` |
| 모의 Domain | `ws://ops.koreainvestment.com:31000` |
| URL | `/tryitout/H0GSCNI0` |

> [참고자료]  실시간시세(웹소켓) 파이썬 샘플코드는 한국투자증권 Github 참고 부탁드립니다. https://github.com/koreainvestment/open-trading-api/blob/main/websocket/python/ws_domestic_overseas_all.py  실시간시세(웹소켓) API 사용방법에 대한 자세한 설명은 한국투자증권 Wikidocs 참고 부탁드립니다. https://wikidocs.net/book/7847 (국내주식 업데이트 완료, 추후 해외주식·국내선물옵션 업데이트 예정)

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `approval_key` | 웹소켓 접속키 | string | Y | 286 | 실시간 (웹소켓) 접속키 발급 API(/oauth2/Approval)를 사용하여 발급받은 웹소켓 접속키 |
| `tr_type` | 등록/해제 | string | Y | 1 | 1: 등록, 2:해제 |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인 / P : 개인 |
| `content-type` | 컨텐츠타입 | string | Y | 20 | utf-8 |

**Request Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `tr_id` | 거래ID | string | Y | 7 | [실전투자] H0GSCNI0 : 실시간 해외주식 체결통보  [모의투자] H0GSCNI9 : 실시간 해외주식 체결통보 |
| `tr_key` | HTSID | string | Y | 8 | HTSID |

**Response Header**

_없음_

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `CUST_ID` | 고객 ID | string | Y | 8 | '각 항목사이에는 구분자로 ^ 사용, 모든 데이터타입은 String으로 변환되어 push 처리됨' |
| `ACNT_NO` | 계좌번호 | string | Y | 10 |  |
| `ODER_NO` | 주문번호 | string | Y | 10 |  |
| `OODER_NO` | 원주문번호 | string | Y | 10 |  |
| `SELN_BYOV_CLS` | 매도매수구분 | string | Y | 2 | 01:매도 02:매수 03:전매도 04:환매수 |
| `RCTF_CLS` | 정정구분 | string | Y | 1 | 0:정상 1:정정 2:취소 |
| `ODER_KIND2` | 주문종류2 | string | Y | 1 | 1:시장가 2:지정자 6:단주시장가 7:단주지정가 A:MOO B:LOO C:MOC D:LOC |
| `STCK_SHRN_ISCD` | 주식 단축 종목코드 | string | Y | 9 |  |
| `CNTG_QTY` | 체결수량 | string | Y | 10 | - 주문통보의 경우 해당 위치에 주문수량이 출력 - 체결통보인 경우 해당 위치에 체결수량이 출력 |
| `CNTG_UNPR` | 체결단가 | string | Y | 9 | ※ 주문통보 시에는 주문단가가, 체결통보 시에는 체결단가가 수신 됩니다. ※ 체결단가의 경우, 국가에 따라 소수점 생략 위치가 상이합니다. 미국 4 일본 1 중국 3 홍콩 3 베트남 0 EX) 미국 AAPL(현재가  |
| `STCK_CNTG_HOUR` | 주식 체결 시간 | string | Y | 6 | 특정 거래소의 체결시간 데이터는 수신되지 않습니다.  체결시간 데이터가 필요할 경우, 체결통보 데이터 수신 시 타임스탬프를 찍는 것으로 대체하시길 바랍니다. |
| `RFUS_YN` | 거부여부 | string | Y | 1 | 0:정상 1:거부 |
| `CNTG_YN` | 체결여부 | string | Y | 1 | 1:주문,정정,취소,거부 2:체결 |
| `ACPT_YN` | 접수여부 | string | Y | 1 | 1:주문접수 2:확인 3:취소(FOK/IOC) |
| `BRNC_NO` | 지점번호 | string | Y | 5 |  |
| `ODER_QTY` | 주문 수량 | string | Y | 9 | - 주문통보인 경우 해당 위치 미출력 (주문통보의 주문수량은 CNTG_QTY 위치에 출력) - 체결통보인 경우 해당 위치에 주문수량이 출력 |
| `ACNT_NAME` | 계좌명 | string | Y | 12 |  |
| `CNTG_ISNM` | 체결종목명 | string | Y | 14 |  |
| `ODER_COND` | 해외종목구분 | string | Y | 1 | 4:홍콩(HKD) 5:상해B(USD)  6:NASDAQ 7:NYSE 8:AMEX 9:OTCB C:홍콩(CNY) A:상해A(CNY) B:심천B(HKD) D:도쿄 E:하노이 F:호치민 |
| `DEBT_GB` | 담보유형코드 | string | Y | 2 | 10:현금 15:해외주식담보대출 |
| `DEBT_DATE` | 담보대출일자 | string | Y | 8 | 대출일(YYYYMMDD) |
| `START_TM` | 분할매수/매도 시작시간 | string | Y | 6 | HHMMSS |
| `END_TM` | 분할매수/매도 종료시간 | string | Y | 6 | HHMMSS |
| `TM_DIV_TP` | 시간분할타입유형 | string | Y | 2 | 00 시간직접설정, 02 : 정규장까지 |
| `CNTG_UNPR12` | 체결단가12 | string | Y | 12 |  |

**Request 예시**
```
{          "header":          {                   "approval_key": "35xxxxxa-bxxa-4xxb-87xxx-f56xxxxxxxxxx",                   "custtype":"P",                   "tr_type":"1",                   "content-type":"utf-8"          },          "body":          {                   "input":                   {                            "tr_id":"H0GSCNI0",                            "tr_key":"HTS ID"                   }          } }
```

**Response 예시**
```json
# output - 등록 성공 시 {     "header": {         "tr_id": "H0GSCNI0",          "tr_key": "HTS ID",          "encrypt": "N"         },      "body": {         "rt_cd": "0",          "msg_cd": "OPSP0000",         "msg1": "SUBSCRIBE SUCCESS",          "output": {             "iv": "0123456789abcdef",              "key": "abcdefghijklmnopabcdefghijklmnop"}         } }  # output (복호화 전)  1|H0GSCNI0|001|vebQ
```

---

### 해외주식 실시간호가

| 항목 | 값 |
|------|----|
| API ID | `실시간-021` |
| 통신방식 | WEBSOCKET / POST |
| 실전 TR_ID | `HDFSASP0` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `ws://ops.koreainvestment.com:21000` |
| URL | `/tryitout/HDFSASP0` |

> 해외주식 실시간호가 API를 이용하여 미국 실시간 10호가(매수/매도) 시세가 무료로 제공됩니다. (미국은 유료시세 제공 X)  아시아 국가의 경우, HTS(efriend Plus) [7781] 시세신청(실시간) 화면에서 유료 서비스 신청 시,  "해외주식 실시간호가 HDFSASP0" 을 이용하여 아시아국가 유료시세(실시간호가)를 받아보실 수 있습니다. (24.11.29 반영) (아시아 국가 무료시세는 "해외주식 지연호가(아시아) HDFSASP1" 를 이용하시기 바랍니다.)  ※ 미국 : 실시간 무료, 매수/매도 각 10

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `approval_key` | 웹소켓 접속키 | string | Y | 286 | 실시간 (웹소켓) 접속키 발급 API(/oauth2/Approval)를 사용하여 발급받은 웹소켓 접속키 |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인 / P : 개인 |
| `tr_type` | 등록/해제 | string | Y | 1 | "1: 등록, 2:해제" |
| `content-type` | 컨텐츠타입 | string | Y | 20 | utf-8 |

**Request Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `tr_id` | 거래ID | string | Y | 7 | HDFSASP0 |
| `tr_key` | R거래소명종목코드 | string | Y | 6 | <미국 야간거래 - 무료시세> D+시장구분(3자리)+종목코드 예) DNASAAPL : D+NAS(나스닥)+AAPL(애플) [시장구분] NYS : 뉴욕, NAS : 나스닥, AMS : 아멕스  <미국 주간거래> R+시 |

**Response Header**

_없음_

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `RSYM` | 실시간종목코드 | object | Y | 16 | '각 항목사이에는 구분자로 ^ 사용, 모든 데이터타입은 String으로 변환되어 push 처리됨' |
| `SYMB` | 종목코드 | string | Y | 16 |  |
| `ZDIV` | 소숫점자리수 | string | Y | 1 |  |
| `XYMD` | 현지일자 | string | Y | 8 |  |
| `XHMS` | 현지시간 | string | Y | 6 |  |
| `KYMD` | 한국일자 | string | Y | 8 |  |
| `KHMS` | 한국시간 | string | Y | 6 |  |
| `BVOL` | 매수총잔량 | string | Y | 10 |  |
| `AVOL` | 매도총잔량 | string | Y | 10 |  |
| `BDVL` | 매수총잔량대비 | string | Y | 10 |  |
| `ADVL` | 매도총잔량대비 | string | Y | 10 |  |
| `PBID1` | 매수호가1 | string | Y | 12 |  |
| `PASK1` | 매도호가1 | string | Y | 12 |  |
| `VBID1` | 매수잔량1 | string | Y | 10 |  |
| `VASK1` | 매도잔량1 | string | Y | 10 |  |
| `DBID1` | 매수잔량대비1 | string | Y | 10 |  |
| `DASK1` | 매도잔량대비1 | string | Y | 10 |  |
| `PBID2` | 매수호가2 | string | Y | 12 |  |
| `PASK2` | 매도호가2 | string | Y | 12 |  |
| `VBID2` | 매수잔량2 | string | Y | 10 |  |
| `VASK2` | 매도잔량2 | string | Y | 10 |  |
| `DBID2` | 매수잔량대비2 | string | Y | 10 |  |
| `DASK2` | 매도잔량대비2 | string | Y | 10 |  |
| `PBID3` | 매수호가3 | string | Y | 12 |  |
| `PASK3` | 매도호가3 | string | Y | 12 |  |
| `VBID3` | 매수잔량3 | string | Y | 10 |  |
| `VASK3` | 매도잔량3 | string | Y | 10 |  |
| `DBID3` | 매수잔량대비3 | string | Y | 10 |  |
| `DASK3` | 매도잔량대비3 | string | Y | 10 |  |
| `PBID3` | 매수호가3 | string | Y | 12 |  |
| `PASK3` | 매도호가3 | string | Y | 12 |  |
| `VBID3` | 매수잔량3 | string | Y | 10 |  |
| `VASK3` | 매도잔량3 | string | Y | 10 |  |
| `DBID3` | 매수잔량대비3 | string | Y | 10 |  |
| `DASK3` | 매도잔량대비3 | string | Y | 10 |  |
| `PBID4` | 매수호가4 | string | Y | 12 |  |
| `PASK4` | 매도호가4 | string | Y | 12 |  |
| `VBID4` | 매수잔량4 | string | Y | 10 |  |
| `VASK4` | 매도잔량4 | string | Y | 10 |  |
| `DBID4` | 매수잔량대비4 | string | Y | 10 |  |
| `DASK4` | 매도잔량대비4 | string | Y | 10 |  |
| `PBID5` | 매수호가5 | string | Y | 12 |  |
| `PASK5` | 매도호가5 | string | Y | 12 |  |
| `VBID5` | 매수잔량5 | string | Y | 10 |  |
| `VASK5` | 매도잔량5 | string | Y | 10 |  |
| `DBID5` | 매수잔량대비5 | string | Y | 10 |  |
| `DASK5` | 매도잔량대비5 | string | Y | 10 |  |
| `PBID6` | 매수호가6 | string | Y | 12 |  |
| `PASK6` | 매도호가6 | string | Y | 12 |  |
| `VBID6` | 매수잔량6 | string | Y | 10 |  |
| `VASK6` | 매도잔량6 | string | Y | 10 |  |
| `DBID6` | 매수잔량대비6 | string | Y | 10 |  |
| `DASK6` | 매도잔량대비6 | string | Y | 10 |  |
| `PBID7` | 매수호가7 | string | Y | 12 |  |
| `PASK7` | 매도호가7 | string | Y | 12 |  |
| `VBID7` | 매수잔량7 | string | Y | 10 |  |
| `VASK7` | 매도잔량7 | string | Y | 10 |  |
| `DBID7` | 매수잔량대비7 | string | Y | 10 |  |
| `DASK7` | 매도잔량대비7 | string | Y | 10 |  |
| `PBID8` | 매수호가8 | string | Y | 12 |  |
| `PASK8` | 매도호가8 | string | Y | 12 |  |
| `VBID8` | 매수잔량8 | string | Y | 10 |  |
| `VASK8` | 매도잔량8 | string | Y | 10 |  |
| `DBID8` | 매수잔량대비8 | string | Y | 10 |  |
| `DASK8` | 매도잔량대비8 | string | Y | 10 |  |
| `PBID9` | 매수호가9 | string | Y | 12 |  |
| `PASK9` | 매도호가9 | string | Y | 12 |  |
| `VBID9` | 매수잔량9 | string | Y | 10 |  |
| `VASK9` | 매도잔량9 | string | Y | 10 |  |
| `DBID9` | 매수잔량대비9 | string | Y | 10 |  |
| `DASK9` | 매도잔량대비9 | string | Y | 10 |  |
| `PBID10` | 매수호가10 | string | Y | 12 |  |
| `PASK10` | 매도호가10 | string | Y | 12 |  |
| `VBID10` | 매수잔량10 | string | Y | 10 |  |
| `VASK10` | 매도잔량10 | string | Y | 10 |  |
| `DBID10` | 매수잔량대비10 | string | Y | 10 |  |
| `DASK10` | 매도잔량대비10 | string | Y | 10 |  |

**Request 예시**
```
{     "header": {         "approval_key": "35xxxxxa-bxxa-4xxb-87xxx-f56xxxxxxxxxx",         "custtype": "P",         "tr_type": "1",         "content-type": "utf-8"     },     "body": {         "input": {             "tr_id": "HDFSASP0",             "tr_key": "RBAQAAPL"         }     } }
```

**Response 예시**
```json
# 연결 확인 {     "header": {         "tr_id": "HDFSASP0",          "tr_key": "RBAQAAPL",          "encrypt": "N"         },      "body": {         "rt_cd": "0",          "msg_cd": "OPSP0000",         "msg1": "SUBSCRIBE SUCCESS",          "output": {             "iv": "0123456789abcdef",              "key": "abcdefghijklmnopabcdefghijklmnop"}         } }  # output 0|HDFSASP0|001|RBAQAAPL^AAPL^4^202405
```

---

### 해외주식 지연호가(아시아)

| 항목 | 값 |
|------|----|
| API ID | `실시간-008` |
| 통신방식 | WEBSOCKET / POST |
| 실전 TR_ID | `HDFSASP1` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `ws://ops.koreainvestment.com:21000` |
| 모의 Domain | `제공 안함` |
| URL | `/tryitout/HDFSASP1` |

> 해외주식 지연호가(아시아)의 경우 아시아 무료시세(지연호가)가 제공됩니다.  HTS(efriend Plus) [7781] 시세신청(실시간) 화면에서 유료 서비스 신청 시,  "해외주식 실시간호가 HDFSASP0" 을 이용하여 아시아국가 유료시세(실시간호가)를 받아보실 수 있습니다. (24.11.29 반영)  ※ 지연시세 지연시간 : 홍콩, 베트남, 중국, 일본 - 15분지연  [참고자료]  실시간시세(웹소켓) 파이썬 샘플코드는 한국투자증권 Github 참고 부탁드립니다. https://github.com/korea

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `approval_key` | 웹소켓 접속키 | string | Y | 286 | 실시간 (웹소켓) 접속키 발급 API(/oauth2/Approval)를 사용하여 발급받은 웹소켓 접속키 |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인 / P : 개인 |
| `tr_type` | 등록/해제 | string | Y | 1 | "1: 등록, 2:해제" |
| `content-type` | 컨텐츠타입 | string | Y | 20 | utf-8 |

**Request Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `tr_id` | 거래ID | string | Y | 7 | HDFSASP1 |
| `tr_key` | D거래소명종목코드 | string | Y | 6 | <아시아국가 - 무료시세> D+시장구분(3자리)+종목코드 예) DHKS00003 : D+HKS(홍콩)+00003(홍콩중화가스) [시장구분] TSE : 도쿄, HKS : 홍콩, SHS : 상해, SZS : 심천 HSX |

**Response Header**

_없음_

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `RSYM` | 실시간종목코드 | string | Y | 16 | '각 항목사이에는 구분자로 ^ 사용, 모든 데이터타입은 String으로 변환되어 push 처리됨' |
| `SYMB` | 종목코드 | string | Y | 16 |  |
| `ZDIV` | 소수점자리수 | string | Y | 1 |  |
| `XYMD` | 현지일자 | string | Y | 8 |  |
| `XHMS` | 현지시간 | string | Y | 6 |  |
| `KYMD` | 한국일자 | string | Y | 8 |  |
| `KHMS` | 한국시간 | string | Y | 6 |  |
| `BVOL` | 매수총잔량 | string | Y | 10 |  |
| `AVOL` | 매도총잔량 | string | Y | 10 |  |
| `BDVL` | 매수총잔량대비 | string | Y | 10 |  |
| `ADVL` | 매도총잔량대비 | string | Y | 10 |  |
| `PBID1` | 매수호가1 | string | Y | 12 |  |
| `PASK1` | 매도호가1 | string | Y | 12 |  |
| `VBID1` | 매수잔량1 | string | Y | 10 |  |
| `VASK1` | 매도잔량1 | string | Y | 10 |  |
| `DBID1` | 매수잔량대비1 | string | Y | 10 |  |
| `DASK1` | 매도잔량대비1 | string | Y | 10 |  |

---

### 해외주식 실시간지연체결가

| 항목 | 값 |
|------|----|
| API ID | `실시간-007` |
| 통신방식 | WEBSOCKET / POST |
| 실전 TR_ID | `HDFSCNT0` |
| 모의 TR_ID | `모의투자 미지원` |
| 실전 Domain | `ws://ops.koreainvestment.com:21000` |
| URL | `/tryitout/HDFSCNT0` |

> 해외주식 실시간지연체결가의 경우 기본적으로 무료시세(지연체결가)가 제공되며,  아시아 국가의 경우 HTS(efriend Plus) [7781] 시세신청(실시간) 화면에서 유료 서비스 신청 시 API로도 유료시세(실시간체결가)를 받아보실 수 있습니다. (24.11.29 반영)  ※ 지연시세 지연시간 : 미국 - 실시간무료(0분지연) / 홍콩, 베트남, 중국, 일본 - 15분지연 (중국은 실시간시세 신청 시 무료실시간시세 제공)    미국의 경우 0분지연시세로 제공되나, 장중 당일 시가는 상이할 수 있으며, 익일 정정 표시됩니다

**Request Header**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `approval_key` | 웹소켓 접속키 | string | Y | 286 | 실시간 (웹소켓) 접속키 발급 API(/oauth2/Approval)를 사용하여 발급받은 웹소켓 접속키 |
| `tr_type` | 등록/해제 | string | Y | 1 | 1: 등록, 2:해제 |
| `custtype` | 고객 타입 | string | Y | 1 | B : 법인 / P : 개인 |
| `content-type` | 컨텐츠타입 | string | Y | 20 | utf-8 |

**Request Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `tr_id` | 거래ID | string | Y | 7 | HDFSCNT0 |
| `tr_key` | D거래소명종목코드 | string | Y | 6 | <미국 야간거래/아시아 주간거래 - 무료시세> D+시장구분(3자리)+종목코드 예) DNASAAPL : D+NAS(나스닥)+AAPL(애플) [시장구분] NYS : 뉴욕, NAS : 나스닥, AMS : 아멕스 , TSE |

**Response Header**

_없음_

**Response Body**

| Element | 한글명 | Type | Required | Length | Description |
|---------|--------|------|----------|--------|-------------|
| `RSYM` | 실시간종목코드 | string | Y | 16 | '각 항목사이에는 구분자로 ^ 사용, 모든 데이터타입은 String으로 변환되어 push 처리됨' |
| `SYMB` | 종목코드 | string | Y | 16 |  |
| `ZDIV` | 수수점자리수 | string | Y | 1 |  |
| `TYMD` | 현지영업일자 | string | Y | 8 |  |
| `XYMD` | 현지일자 | string | Y | 6 |  |
| `XHMS` | 현지시간 | string | Y | 6 |  |
| `KYMD` | 한국일자 | string | Y | 6 |  |
| `KHMS` | 한국시간 | string | Y | 6 |  |
| `OPEN` | 시가 | string | Y | 6 |  |
| `HIGH` | 고가 | string | Y | 6 |  |
| `LOW` | 저가 | string | Y | 6 |  |
| `LAST` | 현재가 | string | Y | 6 |  |
| `SIGN` | 대비구분 | string | Y | 6 |  |
| `DIFF` | 전일대비 | string | Y | 8 |  |
| `RATE` | 등락율 | string | Y | 6 |  |
| `PBID` | 매수호가 | string | Y | 10 |  |
| `PASK` | 매도호가 | string | Y | 10 |  |
| `VBID` | 매수잔량 | string | Y | 10 |  |
| `VASK` | 매도잔량 | string | Y | 10 |  |
| `EVOL` | 체결량 | string | Y | 12 |  |
| `TVOL` | 거래량 | string | Y | 12 |  |
| `TAMT` | 거래대금 | string | Y | 10 |  |
| `BIVL` | 매도체결량 | string | Y | 10 | 매수호가가 매도주문 수량을 따라가서 체결된것을 표현하여 BIVL 이라는 표현을 사용 |
| `ASVL` | 매수체결량 | string | Y | 10 | 매도호가가 매수주문 수량을 따라가서 체결된것을 표현하여 ASVL 이라는 표현을 사용 |
| `STRN` | 체결강도 | string | Y | 10 |  |
| `MTYP` | 시장구분 1:장중,2:장전,3:장후 | string | Y | 10 |  |

---

---

## 6. 개발 가이드 & 주의사항

### Access Token 발급

```python
import requests

def get_access_token(app_key, app_secret, is_mock=False):
    domain = "https://openapivts.koreainvestment.com:29443" if is_mock else "https://openapi.koreainvestment.com:9443"
    res = requests.post(f"{domain}/oauth2/tokenP", json={
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret
    })
    return res.json()["access_token"]
```

### 연속조회 (페이지네이션) 패턴

```python
async def get_all_pages(tr_id, params, headers):
    results = []
    headers["tr_cont"] = ""  # 초기 조회
    
    while True:
        res = await session.get(url, headers=headers, params=params)
        data = res.json()
        results.extend(data.get("output", []))
        
        tr_cont = res.headers.get("tr_cont", "")
        if tr_cont not in ["M", "F"]:  # D, E = 마지막
            break
        
        headers["tr_cont"] = "N"  # 다음 조회
        # CTX_AREA_FK200, CTX_AREA_NK200 값도 업데이트
        params["CTX_AREA_FK200"] = data.get("ctx_area_fk200", "")
        params["CTX_AREA_NK200"] = data.get("ctx_area_nk200", "")
    
    return results
```

### 주요 오류 코드

| rt_cd | msg_cd | 의미 | 대응 |
|-------|--------|------|------|
| `1` | `EGW00123` | Access Token 만료 | 토큰 재발급 |
| `1` | `APBK0920` | 장 운영시간 외 | 시간 확인 |
| `1` | `APBK0600` | 잔고 부족 | 주문금액 확인 |
| `1` | `KIOK0560` | 조회 결과 없음 | 정상 (데이터 없음) |

### HTTP 500 처리

```python
# KIS API 주말/비장시간 HTTP 500 처리 패턴 (현재 ai-trader-us 구현)
async def _api_get(self, url, headers, params, retries=2):
    for attempt in range(retries + 1):
        try:
            res = await session.get(url, headers=headers, params=params)
            if res.status == 500:
                if attempt < retries:
                    await asyncio.sleep(attempt + 1)
                    continue
                raise Exception(f"HTTP 500")
            return await res.json()
        except Exception as e:
            if attempt == retries:
                raise
```

### 주간거래 vs 정규장 TR_ID 선택

```python
from datetime import datetime
import pytz

def get_order_tr_id(side: str, is_mock: bool = False) -> str:
    """현재 시각 기반으로 정규장/주간거래 TR_ID 자동 선택"""
    kst = datetime.now(pytz.timezone("Asia/Seoul"))
    hour = kst.hour
    
    # 주간거래 시간: 10:00 ~ 18:00 KST
    is_daytime = 10 <= hour < 18
    
    if is_daytime:
        # 주간거래: 모의투자 미지원
        if side == "buy":
            return "TTTS6036U"
        else:
            return "TTTS6037U"
    else:
        # 정규장/프리/애프터
        if is_mock:
            return "VTTT1002U" if side == "buy" else "VTTT1001U"
        else:
            return "TTTT1002U" if side == "buy" else "TTTT1006U"
```

---

## 7. ai-trader-us 활용 전략

### 현재 사용 중인 API

| API | TR_ID | 용도 |
|-----|-------|------|
| 해외주식 주문 | `TTTT1002U` / `TTTT1006U` | 매수/매도 주문 |
| 해외주식 잔고 | `TTTS3012R` | 포트폴리오 동기화 |
| 해외주식 주문체결내역 | `TTTS3035R` | 체결 내역 조회 |
| 해외주식 현재체결가 | `HHDFS00000300` | 실시간 현재가 |

### 미사용 but 유용한 API (구현 후보)

| 우선순위 | API | TR_ID | 기대 효과 |
|---------|-----|-------|-----------|
| ⭐⭐⭐ | 실시간체결통보 WS | `H0GSCNI0` | 체결 즉시 push → 15초 폴링 대체 |
| ⭐⭐⭐ | 해외주식 미체결내역 | `TTTS3018R` | 미체결 주문 확인 → 취소 자동화 |
| ⭐⭐ | 해외주식 거래량급증 | `HHDFS76270000` | 스크리너 보조 신호 |
| ⭐⭐ | 해외주식 조건검색 | `HHDFS76410000` | KIS 자체 스크리닝 (최대 100개) |
| ⭐⭐ | 해외주식 기간손익 | `TTTS3039R` | 정확한 실현 P&L 집계 |
| ⭐ | 해외주식분봉조회 | `HHDFS76950200` | 장중 기술분석 (최대 120건) |
| ⭐ | 해외주식 현재가상세 | `HHDFS76200200` | PER/PBR/EPS/BPS 조회 |
| ⭐ | 해외뉴스종합(제목) | `HHPSTH60100C1` | US 뉴스 테마 탐지 |
| ⭐ | 미국주간주문 | `TTTS6036U/37U` | 주간거래(10~18시 KST) 지원 |

### H0GSCNI0 실시간체결통보 구현 예시

```python
# ai-trader-us/src/data/feeds/kis_ws.py 에 추가
class KISTradeNotificationWS:
    """실시간 체결 통보 WebSocket (H0GSCNI0)"""
    WS_URL = "ws://ops.koreainvestment.com:21000"
    TR_ID_REAL = "H0GSCNI0"
    TR_ID_MOCK = "H0GSCNI9"

    async def subscribe(self, approval_key: str, account_no: str):
        """계좌 체결 통보 구독"""
        async with websockets.connect(self.WS_URL) as ws:
            payload = {
                "header": {
                    "approval_key": approval_key,
                    "custtype": "P",
                    "tr_type": "1",
                    "content-type": "utf-8"
                },
                "body": {"input": {"tr_id": self.TR_ID_REAL, "tr_key": account_no}}
            }
            await ws.send(json.dumps(payload))
            async for msg in ws:
                data = self._parse(msg)
                if data:
                    await self._on_fill(data)

    def _parse(self, raw: str) -> dict | None:
        """
        체결통보 데이터 파싱
        응답 포맷: PUSH 데이터 (|로 구분)
        필드 순서: tr_id | tr_key | recv_dttm | data...
        """
        if raw.startswith("{"):  # JSON 응답 (구독 확인)
            return None
        parts = raw.split("|")
        if len(parts) < 4:
            return None
        tr_id = parts[0]
        data_str = parts[3]
        fields = data_str.split("^")
        # 실제 필드 매핑은 KIS 문서 참조
        return {
            "cano": fields[0] if len(fields) > 0 else "",
            "pdno": fields[1] if len(fields) > 1 else "",  # 종목코드
            "ord_qty": fields[2] if len(fields) > 2 else "",
            "ft_ccld_unpr": fields[3] if len(fields) > 3 else "",  # 체결단가
            "sll_buy_dvsn_cd": fields[4] if len(fields) > 4 else "",  # 01=매도 02=매수
        }
```

### 미체결 주문 취소 자동화 패턴

```python
# _exit_check_loop 에 추가 가능
async def cancel_stale_orders(self, max_age_seconds: int = 60):
    """미체결 주문 자동 취소"""
    nccs = await self.broker.get_pending_orders()  # TTTS3018R
    for order in nccs:
        age = (now - order["ord_time"]).seconds
        if age > max_age_seconds:
            await self.broker.cancel_order(
                odno=order["odno"],
                tr_id="TTTT1004U"  # 정정취소주문
            )
            logger.info(f"[미체결취소] {order['pdno']} 주문번호={order['odno']}")
```

---

*문서 생성: 2026-03-03 | 출처: KIS 오픈 API 공식 xlsx 문서 4종*

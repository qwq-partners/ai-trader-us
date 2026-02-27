#!/usr/bin/env python3
"""
AI Trader US - Live Engine Quick Test

LiveEngine + AsyncAlpacaBroker(paper) 연동 테스트.
1사이클 스크리닝 → 시그널 출력 → 잔고 출력.

Usage:
    python scripts/test_live.py --dry-run          # 주문 없이 시그널만 (기본)
    python scripts/test_live.py --no-dry-run       # 실제 paper 주문 포함
    python scripts/test_live.py --symbols AAPL,MSFT,NVDA  # 특정 종목만
"""

import argparse
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from loguru import logger


async def main(config_path: str, dry_run: bool, symbols: list[str] | None):
    """테스트 실행"""
    from src.utils.logger import setup_logger
    from src.core.config import AppConfig
    from src.core.live_engine import LiveEngine

    setup_logger(level="DEBUG")

    config = AppConfig.load(config_path)

    # 브로커 타입 확인
    broker_type = config.raw.get("live", {}).get("broker", "kis")
    logger.info(f"브로커: {broker_type} | dry_run: {dry_run}")

    engine = LiveEngine(config)

    # ── 1. 브로커 연결 ──
    logger.info("=" * 60)
    logger.info("STEP 1: 브로커 연결")
    logger.info("=" * 60)

    if not await engine.broker.connect():
        logger.error("브로커 연결 실패 — 종료")
        return

    logger.info("브로커 연결 성공")

    try:
        # ── 2. 전략 로드 ──
        logger.info("=" * 60)
        logger.info("STEP 2: 전략 로드")
        logger.info("=" * 60)

        engine._load_strategies()
        logger.info(f"활성 전략: {[s.name for s in engine.strategies]}")

        # ── 3. 유니버스 (또는 지정 종목) ──
        logger.info("=" * 60)
        logger.info("STEP 3: 유니버스 구성")
        logger.info("=" * 60)

        if symbols:
            engine._universe = symbols
            logger.info(f"지정 종목: {symbols}")
        else:
            pools = config.raw.get("universe", {}).get("pools", ["sp500"])
            engine._universe = engine.universe_mgr.get_universe(pools)
            max_sym = config.raw.get("live", {}).get("max_screen_symbols", 20)
            engine._universe = engine._universe[:max_sym]
            logger.info(f"유니버스: {len(engine._universe)} 종목 (상위 {max_sym}개)")

        # ── 4. 잔고 조회 ──
        logger.info("=" * 60)
        logger.info("STEP 4: 계좌 잔고")
        logger.info("=" * 60)

        balance = await engine.broker.get_balance()
        if balance:
            acct = balance.get("account", {})
            positions = balance.get("positions", [])
            logger.info(f"  Equity:  ${acct.get('total_equity', 0):,.2f}")
            logger.info(f"  Cash:    ${acct.get('available_cash', 0):,.2f}")
            logger.info(f"  PnL:     ${acct.get('total_pnl', 0):,.2f}")
            logger.info(f"  Positions: {len(positions)}")
            for p in positions:
                logger.info(
                    f"    {p['symbol']:>6s}  {p['qty']}주  "
                    f"avg=${p['avg_price']:.2f}  cur=${p['current_price']:.2f}  "
                    f"pnl=${p.get('pnl', 0):+.2f}"
                )
        else:
            logger.warning("잔고 조회 실패")

        # ── 5. 1사이클 스크리닝 ──
        logger.info("=" * 60)
        logger.info("STEP 5: 스크리닝 (1사이클)")
        logger.info("=" * 60)

        signals = []
        processed = 0

        for symbol in engine._universe:
            try:
                history = await engine._get_history(symbol)
                if history is None or len(history) < 50:
                    continue

                for strategy in engine.strategies:
                    signal = strategy.evaluate(symbol, history, engine.portfolio)
                    if signal:
                        signals.append(signal)
                        logger.info(
                            f"  SIGNAL: {signal.symbol} | {signal.strategy.value} | "
                            f"score={signal.score:.0f} | {signal.reason}"
                        )
                        break
                processed += 1
            except Exception as e:
                logger.debug(f"  {symbol} 평가 실패: {e}")

        logger.info(f"스캔 완료: {processed}종목 처리, {len(signals)}개 시그널")

        if not signals:
            logger.info("시그널 없음 — 조건에 부합하는 종목이 없습니다")

        # ── 6. 시그널 요약 ──
        if signals:
            signals.sort(key=lambda s: s.score, reverse=True)
            logger.info("=" * 60)
            logger.info("시그널 요약 (score 내림차순)")
            logger.info("=" * 60)
            for i, sig in enumerate(signals[:10], 1):
                logger.info(
                    f"  #{i} {sig.symbol:>6s} | {sig.strategy.value:>15s} | "
                    f"score={sig.score:5.0f} | price=${sig.price:.2f} | "
                    f"{sig.reason}"
                )

        # ── 7. dry_run이 아닌 경우에만 주문 (안전장치) ──
        if not dry_run and signals:
            logger.warning("=" * 60)
            logger.warning("DRY_RUN=OFF — 상위 시그널에 대해 실제 주문 시도")
            logger.warning("=" * 60)
            max_orders = config.raw.get("live", {}).get("max_signals_per_cycle", 2)
            for sig in signals[:max_orders]:
                success = await engine._process_signal(sig)
                logger.info(f"  주문 결과: {sig.symbol} → {'성공' if success else '실패'}")
        elif dry_run:
            logger.info("[DRY_RUN] 주문 건너뜀")

    finally:
        # ── 8. 연결 해제 ──
        logger.info("=" * 60)
        logger.info("브로커 연결 해제")
        logger.info("=" * 60)
        await engine.broker.disconnect()

    logger.info("테스트 완료")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Trader US - Live Engine Test")
    parser.add_argument(
        "--config", "-c",
        default=str(project_root / "config" / "default.yml"),
        help="설정 파일 경로",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="주문 없이 시그널만 확인 (기본값)",
    )
    parser.add_argument(
        "--no-dry-run",
        action="store_true",
        default=False,
        help="실제 주문 실행 (paper trading)",
    )
    parser.add_argument(
        "--symbols", "-s",
        default=None,
        help="스크리닝 대상 종목 (쉼표 구분, e.g. AAPL,MSFT,NVDA)",
    )

    args = parser.parse_args()

    dry_run = not args.no_dry_run
    symbols = args.symbols.split(",") if args.symbols else None

    asyncio.run(main(args.config, dry_run, symbols))

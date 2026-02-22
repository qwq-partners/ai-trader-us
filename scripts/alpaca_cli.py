"""
Alpaca Paper Trading CLI.

Usage:
  python scripts/alpaca_cli.py status           # Account status
  python scripts/alpaca_cli.py positions         # Open positions
  python scripts/alpaca_cli.py orders            # Open orders
  python scripts/alpaca_cli.py buy AAPL 10       # Buy 10 shares AAPL (market)
  python scripts/alpaca_cli.py sell AAPL 10      # Sell 10 shares AAPL (market)
  python scripts/alpaca_cli.py buy AAPL 10 --limit 150.00  # Limit order
  python scripts/alpaca_cli.py close AAPL        # Close AAPL position
  python scripts/alpaca_cli.py close-all         # Close all positions
  python scripts/alpaca_cli.py cancel-all        # Cancel all orders
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from src.execution.broker.alpaca_broker import AlpacaBroker
from src.utils.logger import setup_logger


def main():
    parser = argparse.ArgumentParser(description="Alpaca Paper Trading CLI")
    parser.add_argument('action', choices=[
        'status', 'positions', 'orders',
        'buy', 'sell', 'close', 'close-all', 'cancel-all',
    ], help='Action to perform')
    parser.add_argument('symbol', nargs='?', default=None,
                        help='Stock symbol (for buy/sell/close)')
    parser.add_argument('quantity', nargs='?', type=int, default=None,
                        help='Number of shares (for buy/sell)')
    parser.add_argument('--limit', type=float, default=None,
                        help='Limit price for limit orders')
    parser.add_argument('--stop', type=float, default=None,
                        help='Stop price for stop orders')
    args = parser.parse_args()

    setup_logger("WARNING")

    try:
        broker = AlpacaBroker(paper=True)
    except Exception as e:
        print(f"Error connecting to Alpaca: {e}")
        print("  Check ALPACA_API_KEY and ALPACA_SECRET_KEY in .env")
        return

    if args.action == 'status':
        broker.print_status()

    elif args.action == 'positions':
        positions = broker.get_positions()
        if not positions:
            print("No open positions")
            return
        print(f"\nOpen Positions ({len(positions)}):")
        print(f"  {'Symbol':>7s} {'Qty':>5s} {'Entry':>8s} {'Current':>8s} "
              f"{'PnL':>9s} {'PnL%':>7s} {'Value':>10s}")
        print(f"  {'-'*60}")
        total_pnl = 0
        total_value = 0
        for p in positions:
            total_pnl += p['unrealized_pnl']
            total_value += p['market_value']
            print(f"  {p['symbol']:>7s} {p['qty']:>5d} "
                  f"${p['avg_entry_price']:>7.2f} ${p['current_price']:>7.2f} "
                  f"${p['unrealized_pnl']:>+8.2f} {p['unrealized_pnl_pct']:>+6.1f}% "
                  f"${p['market_value']:>9,.2f}")
        print(f"  {'-'*60}")
        print(f"  {'Total':>7s} {'':>5s} {'':>8s} {'':>8s} "
              f"${total_pnl:>+8.2f} {'':>7s} ${total_value:>9,.2f}")

    elif args.action == 'orders':
        orders = broker.get_orders('open')
        if not orders:
            print("No open orders")
            return
        print(f"\nOpen Orders ({len(orders)}):")
        for o in orders:
            price = ""
            if o['limit_price']:
                price = f"limit=${o['limit_price']:.2f}"
            if o['stop_price']:
                price += f" stop=${o['stop_price']:.2f}"
            print(f"  {o['side']:>4s} {o['qty']:>5d} {o['symbol']:>6s} "
                  f"{o['type']:>10s} {price} | {o['status']} | id={o['id'][:8]}")

    elif args.action == 'buy':
        if not args.symbol or not args.quantity:
            print("Usage: buy SYMBOL QUANTITY [--limit PRICE]")
            return
        if args.limit:
            result = broker.submit_limit_order(
                args.symbol, args.quantity, args.limit, side="buy"
            )
        else:
            result = broker.submit_market_order(
                args.symbol, args.quantity, side="buy"
            )
        print(f"Order submitted: {result['side']} {result['qty']} {result['symbol']} "
              f"| type={result['type']} status={result['status']} id={result['id'][:8]}")

    elif args.action == 'sell':
        if not args.symbol or not args.quantity:
            print("Usage: sell SYMBOL QUANTITY [--limit PRICE]")
            return
        if args.limit:
            result = broker.submit_limit_order(
                args.symbol, args.quantity, args.limit, side="sell"
            )
        else:
            result = broker.submit_market_order(
                args.symbol, args.quantity, side="sell"
            )
        print(f"Order submitted: {result['side']} {result['qty']} {result['symbol']} "
              f"| type={result['type']} status={result['status']} id={result['id'][:8]}")

    elif args.action == 'close':
        if not args.symbol:
            print("Usage: close SYMBOL [QUANTITY]")
            return
        result = broker.close_position(args.symbol, qty=args.quantity)
        if result:
            print(f"Position close submitted: {result['symbol']} | id={result['id'][:8]}")
        else:
            print(f"No position found for {args.symbol}")

    elif args.action == 'close-all':
        count = broker.close_all_positions()
        print(f"Closed {count} positions")

    elif args.action == 'cancel-all':
        count = broker.cancel_all_orders()
        print(f"Cancelled {count} orders")


if __name__ == "__main__":
    main()

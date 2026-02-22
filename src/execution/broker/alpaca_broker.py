"""
AI Trader US - Alpaca Broker

Live/Paper trading via Alpaca Markets API.
Supports market/limit orders, position management, account info.
"""

import os
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict
from loguru import logger


class AlpacaBroker:
    """Alpaca Markets broker for live/paper trading"""

    def __init__(
        self,
        api_key: str = None,
        secret_key: str = None,
        paper: bool = True,
    ):
        try:
            from alpaca.trading.client import TradingClient
            from alpaca.trading.requests import (
                MarketOrderRequest,
                LimitOrderRequest,
                StopOrderRequest,
                StopLimitOrderRequest,
                GetOrdersRequest,
            )
            from alpaca.trading.enums import (
                OrderSide as AlpacaOrderSide,
                OrderType as AlpacaOrderType,
                TimeInForce,
                OrderStatus as AlpacaOrderStatus,
                QueryOrderStatus,
            )
            from alpaca.common.exceptions import APIError
        except ImportError:
            raise ImportError("alpaca-py not installed: pip install alpaca-py")

        self._api_key = api_key or os.environ.get('ALPACA_API_KEY', '')
        self._secret_key = secret_key or os.environ.get('ALPACA_SECRET_KEY', '')
        self._paper = paper

        if not self._api_key or not self._secret_key:
            raise ValueError(
                "Alpaca API keys required. Set ALPACA_API_KEY and ALPACA_SECRET_KEY "
                "environment variables or pass them directly."
            )

        self._client = TradingClient(
            api_key=self._api_key,
            secret_key=self._secret_key,
            paper=self._paper,
        )

        # Store module references for later use
        self._MarketOrderRequest = MarketOrderRequest
        self._LimitOrderRequest = LimitOrderRequest
        self._StopOrderRequest = StopOrderRequest
        self._StopLimitOrderRequest = StopLimitOrderRequest
        self._GetOrdersRequest = GetOrdersRequest
        self._AlpacaOrderSide = AlpacaOrderSide
        self._AlpacaOrderType = AlpacaOrderType
        self._TimeInForce = TimeInForce
        self._AlpacaOrderStatus = AlpacaOrderStatus
        self._QueryOrderStatus = QueryOrderStatus
        self._APIError = APIError

        # Verify connection
        try:
            account = self._client.get_account()
            mode = "PAPER" if paper else "LIVE"
            logger.info(
                f"Alpaca [{mode}] connected | "
                f"Account: {account.account_number} | "
                f"Equity: ${float(account.equity):,.2f} | "
                f"Cash: ${float(account.cash):,.2f} | "
                f"Buying Power: ${float(account.buying_power):,.2f}"
            )
        except Exception as e:
            logger.error(f"Alpaca connection failed: {e}")
            raise

    # ----------------------------------------------------------------
    # Account
    # ----------------------------------------------------------------

    def get_account(self) -> Dict:
        """Get account information"""
        account = self._client.get_account()
        return {
            'account_number': account.account_number,
            'status': str(account.status),
            'equity': float(account.equity),
            'cash': float(account.cash),
            'buying_power': float(account.buying_power),
            'portfolio_value': float(account.portfolio_value),
            'day_trading_buying_power': float(account.daytrading_buying_power),
            'pattern_day_trader': account.pattern_day_trader,
            'trading_blocked': account.trading_blocked,
            'account_blocked': account.account_blocked,
            'daytrade_count': account.daytrade_count,
            'last_equity': float(account.last_equity),
            'unrealized_pnl': float(account.equity) - float(account.last_equity),
        }

    def get_buying_power(self) -> float:
        """Get available buying power"""
        account = self._client.get_account()
        return float(account.buying_power)

    # ----------------------------------------------------------------
    # Orders
    # ----------------------------------------------------------------

    def submit_market_order(
        self,
        symbol: str,
        quantity: int,
        side: str = "buy",
        time_in_force: str = "day",
    ) -> Dict:
        """Submit a market order"""
        alpaca_side = (
            self._AlpacaOrderSide.BUY if side == "buy"
            else self._AlpacaOrderSide.SELL
        )
        tif = self._TimeInForce.DAY if time_in_force == "day" else self._TimeInForce.GTC

        request = self._MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=alpaca_side,
            time_in_force=tif,
        )

        order = self._client.submit_order(request)
        logger.info(
            f"ORDER: {side.upper()} {quantity} {symbol} MARKET | "
            f"id={order.id} status={order.status}"
        )
        return self._order_to_dict(order)

    def submit_limit_order(
        self,
        symbol: str,
        quantity: int,
        limit_price: float,
        side: str = "buy",
        time_in_force: str = "day",
    ) -> Dict:
        """Submit a limit order"""
        alpaca_side = (
            self._AlpacaOrderSide.BUY if side == "buy"
            else self._AlpacaOrderSide.SELL
        )
        tif = self._TimeInForce.DAY if time_in_force == "day" else self._TimeInForce.GTC

        request = self._LimitOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=alpaca_side,
            time_in_force=tif,
            limit_price=limit_price,
        )

        order = self._client.submit_order(request)
        logger.info(
            f"ORDER: {side.upper()} {quantity} {symbol} LIMIT @${limit_price:.2f} | "
            f"id={order.id} status={order.status}"
        )
        return self._order_to_dict(order)

    def submit_stop_order(
        self,
        symbol: str,
        quantity: int,
        stop_price: float,
        side: str = "sell",
        time_in_force: str = "gtc",
    ) -> Dict:
        """Submit a stop order"""
        alpaca_side = (
            self._AlpacaOrderSide.BUY if side == "buy"
            else self._AlpacaOrderSide.SELL
        )
        tif = self._TimeInForce.DAY if time_in_force == "day" else self._TimeInForce.GTC

        request = self._StopOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=alpaca_side,
            time_in_force=tif,
            stop_price=stop_price,
        )

        order = self._client.submit_order(request)
        logger.info(
            f"ORDER: {side.upper()} {quantity} {symbol} STOP @${stop_price:.2f} | "
            f"id={order.id} status={order.status}"
        )
        return self._order_to_dict(order)

    def submit_bracket_order(
        self,
        symbol: str,
        quantity: int,
        side: str = "buy",
        take_profit_price: float = None,
        stop_loss_price: float = None,
        time_in_force: str = "day",
    ) -> Dict:
        """Submit a bracket order (entry + TP + SL)"""
        from alpaca.trading.requests import (
            MarketOrderRequest, TakeProfitRequest, StopLossRequest
        )

        alpaca_side = (
            self._AlpacaOrderSide.BUY if side == "buy"
            else self._AlpacaOrderSide.SELL
        )
        tif = self._TimeInForce.DAY if time_in_force == "day" else self._TimeInForce.GTC

        kwargs = dict(
            symbol=symbol,
            qty=quantity,
            side=alpaca_side,
            time_in_force=tif,
            order_class="bracket",
        )

        if take_profit_price:
            kwargs['take_profit'] = TakeProfitRequest(limit_price=take_profit_price)
        if stop_loss_price:
            kwargs['stop_loss'] = StopLossRequest(stop_price=stop_loss_price)

        request = MarketOrderRequest(**kwargs)
        order = self._client.submit_order(request)

        logger.info(
            f"BRACKET: {side.upper()} {quantity} {symbol} | "
            f"TP=${take_profit_price} SL=${stop_loss_price} | "
            f"id={order.id}"
        )
        return self._order_to_dict(order)

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID"""
        try:
            self._client.cancel_order_by_id(order_id)
            logger.info(f"CANCEL: order {order_id}")
            return True
        except self._APIError as e:
            logger.warning(f"Cancel failed for {order_id}: {e}")
            return False

    def cancel_all_orders(self) -> int:
        """Cancel all open orders"""
        try:
            cancelled = self._client.cancel_orders()
            count = len(cancelled) if cancelled else 0
            logger.info(f"CANCEL ALL: {count} orders cancelled")
            return count
        except Exception as e:
            logger.error(f"Cancel all failed: {e}")
            return 0

    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order by ID"""
        try:
            order = self._client.get_order_by_id(order_id)
            return self._order_to_dict(order)
        except self._APIError:
            return None

    def get_orders(self, status: str = "open") -> List[Dict]:
        """Get orders by status (open, closed, all)"""
        query_status = {
            'open': self._QueryOrderStatus.OPEN,
            'closed': self._QueryOrderStatus.CLOSED,
            'all': self._QueryOrderStatus.ALL,
        }.get(status, self._QueryOrderStatus.OPEN)

        request = self._GetOrdersRequest(status=query_status, limit=100)
        orders = self._client.get_orders(request)
        return [self._order_to_dict(o) for o in orders]

    # ----------------------------------------------------------------
    # Positions
    # ----------------------------------------------------------------

    def get_positions(self) -> List[Dict]:
        """Get all open positions"""
        positions = self._client.get_all_positions()
        return [self._position_to_dict(p) for p in positions]

    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get position for a specific symbol"""
        try:
            pos = self._client.get_open_position(symbol)
            return self._position_to_dict(pos)
        except self._APIError:
            return None

    def close_position(self, symbol: str, qty: int = None) -> Optional[Dict]:
        """Close a position (all or partial)"""
        try:
            if qty:
                order = self._client.close_position(symbol, close_options={'qty': str(qty)})
            else:
                order = self._client.close_position(symbol)
            logger.info(f"CLOSE: {symbol} qty={qty or 'ALL'} | id={order.id}")
            return self._order_to_dict(order)
        except self._APIError as e:
            logger.error(f"Close position failed for {symbol}: {e}")
            return None

    def close_all_positions(self) -> int:
        """Close all positions"""
        try:
            results = self._client.close_all_positions()
            count = len(results) if results else 0
            logger.info(f"CLOSE ALL: {count} positions closed")
            return count
        except Exception as e:
            logger.error(f"Close all failed: {e}")
            return 0

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    def _order_to_dict(self, order) -> Dict:
        """Convert Alpaca order to dict"""
        return {
            'id': str(order.id),
            'client_order_id': order.client_order_id,
            'symbol': order.symbol,
            'side': str(order.side),
            'type': str(order.type),
            'status': str(order.status),
            'qty': int(order.qty) if order.qty else 0,
            'filled_qty': int(order.filled_qty) if order.filled_qty else 0,
            'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else 0,
            'limit_price': float(order.limit_price) if order.limit_price else None,
            'stop_price': float(order.stop_price) if order.stop_price else None,
            'time_in_force': str(order.time_in_force),
            'created_at': str(order.created_at),
            'filled_at': str(order.filled_at) if order.filled_at else None,
            'submitted_at': str(order.submitted_at) if order.submitted_at else None,
        }

    def _position_to_dict(self, pos) -> Dict:
        """Convert Alpaca position to dict"""
        return {
            'symbol': pos.symbol,
            'qty': int(pos.qty),
            'side': str(pos.side),
            'avg_entry_price': float(pos.avg_entry_price),
            'current_price': float(pos.current_price),
            'market_value': float(pos.market_value),
            'cost_basis': float(pos.cost_basis),
            'unrealized_pnl': float(pos.unrealized_pl),
            'unrealized_pnl_pct': float(pos.unrealized_plpc) * 100,
            'change_today': float(pos.change_today) * 100 if pos.change_today else 0,
        }

    def print_status(self):
        """Print account status summary"""
        account = self.get_account()
        positions = self.get_positions()
        orders = self.get_orders('open')

        mode = "PAPER" if self._paper else "LIVE"
        print(f"\n{'='*60}")
        print(f"ALPACA [{mode}] ACCOUNT STATUS")
        print(f"{'='*60}")
        print(f"  Account:       {account['account_number']}")
        print(f"  Equity:        ${account['equity']:,.2f}")
        print(f"  Cash:          ${account['cash']:,.2f}")
        print(f"  Buying Power:  ${account['buying_power']:,.2f}")
        print(f"  Day Trades:    {account['daytrade_count']}")

        if positions:
            print(f"\n  POSITIONS ({len(positions)}):")
            print(f"  {'Symbol':>7s} {'Qty':>5s} {'Entry':>8s} {'Current':>8s} "
                  f"{'PnL':>9s} {'PnL%':>7s}")
            print(f"  {'-'*50}")
            for p in positions:
                print(f"  {p['symbol']:>7s} {p['qty']:>5d} "
                      f"${p['avg_entry_price']:>7.2f} ${p['current_price']:>7.2f} "
                      f"${p['unrealized_pnl']:>+8.2f} {p['unrealized_pnl_pct']:>+6.1f}%")
        else:
            print(f"\n  No open positions")

        if orders:
            print(f"\n  OPEN ORDERS ({len(orders)}):")
            for o in orders:
                print(f"  {o['side']:>4s} {o['qty']:>5d} {o['symbol']:>6s} "
                      f"{o['type']:>8s} status={o['status']}")
        else:
            print(f"  No open orders")

        print(f"{'='*60}")

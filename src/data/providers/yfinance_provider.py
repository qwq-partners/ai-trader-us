"""
AI Trader US - Yahoo Finance Data Provider

Free historical data via yfinance.
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from loguru import logger

from .base import DataProvider


class YFinanceProvider(DataProvider):
    """Yahoo Finance data provider"""

    def __init__(self):
        try:
            import yfinance as yf
            self._yf = yf
        except ImportError:
            raise ImportError("yfinance not installed: pip install yfinance")

    def get_daily_bars(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        """Get daily OHLCV data"""
        try:
            ticker = self._yf.Ticker(symbol)
            df = ticker.history(
                start=start.isoformat(),
                end=(end + timedelta(days=1)).isoformat(),
                interval="1d",
                auto_adjust=True,
            )
            if df.empty:
                logger.warning(f"No daily data for {symbol}")
                return pd.DataFrame()

            df.columns = [c.lower() for c in df.columns]
            df = df[['open', 'high', 'low', 'close', 'volume']].copy()
            df.index = pd.to_datetime(df.index).tz_localize(None)
            return df
        except Exception as e:
            logger.error(f"Failed to get daily bars for {symbol}: {e}")
            return pd.DataFrame()

    def get_intraday_bars(self, symbol: str, interval: str = "5m",
                          period: str = "60d") -> pd.DataFrame:
        """Get intraday bars (yfinance: max 60d for 1m, 60d for 5m)"""
        try:
            ticker = self._yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval, auto_adjust=True)
            if df.empty:
                logger.warning(f"No intraday data for {symbol} ({interval})")
                return pd.DataFrame()

            df.columns = [c.lower() for c in df.columns]
            df = df[['open', 'high', 'low', 'close', 'volume']].copy()
            if df.index.tz is not None:
                df.index = df.index.tz_convert('America/New_York').tz_localize(None)
            return df
        except Exception as e:
            logger.error(f"Failed to get intraday bars for {symbol}: {e}")
            return pd.DataFrame()

    def get_quote(self, symbol: str) -> Dict:
        """Get latest quote info"""
        try:
            ticker = self._yf.Ticker(symbol)
            info = ticker.fast_info
            return {
                'symbol': symbol,
                'price': float(info.get('lastPrice', 0) or info.get('previousClose', 0)),
                'volume': int(info.get('lastVolume', 0)),
                'market_cap': float(info.get('marketCap', 0)),
            }
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            return {'symbol': symbol, 'price': 0, 'volume': 0}

    def get_universe(self, index: str = "sp500") -> List[str]:
        """Get index constituents"""
        if index == "sp500":
            return self._get_sp500()
        elif index == "sp400":
            return self._get_sp400()
        else:
            logger.warning(f"Unknown index: {index}")
            return []

    def get_earnings_dates(self, symbol: str) -> pd.DataFrame:
        """Get upcoming and past earnings dates"""
        try:
            ticker = self._yf.Ticker(symbol)
            dates = ticker.earnings_dates
            if dates is not None and not dates.empty:
                return dates
            return pd.DataFrame()
        except Exception as e:
            logger.debug(f"No earnings dates for {symbol}: {e}")
            return pd.DataFrame()

    def get_info(self, symbol: str) -> Dict:
        """Get stock info (sector, industry, etc.)"""
        try:
            ticker = self._yf.Ticker(symbol)
            info = ticker.info
            return {
                'symbol': symbol,
                'name': info.get('shortName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
            }
        except Exception as e:
            logger.debug(f"No info for {symbol}: {e}")
            return {'symbol': symbol}

    def _get_sp500(self) -> List[str]:
        """Get S&P 500 tickers from Wikipedia"""
        try:
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            tables = pd.read_html(url)
            df = tables[0]
            tickers = df['Symbol'].str.replace('.', '-', regex=False).tolist()
            logger.info(f"S&P 500: {len(tickers)} tickers loaded")
            return sorted(tickers)
        except Exception as e:
            logger.error(f"Failed to load S&P 500 list: {e}")
            # Fallback: top 30 by market cap
            return [
                'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'META', 'BRK-B',
                'LLY', 'AVGO', 'JPM', 'TSLA', 'UNH', 'V', 'XOM', 'MA',
                'PG', 'JNJ', 'COST', 'HD', 'ABBV', 'MRK', 'CRM', 'BAC',
                'NFLX', 'AMD', 'CVX', 'KO', 'PEP', 'TMO', 'WMT',
            ]

    def _get_sp400(self) -> List[str]:
        """Get S&P 400 MidCap tickers"""
        try:
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies"
            tables = pd.read_html(url)
            df = tables[0]
            col = 'Ticker symbol' if 'Ticker symbol' in df.columns else df.columns[1]
            tickers = df[col].str.replace('.', '-', regex=False).tolist()
            logger.info(f"S&P 400: {len(tickers)} tickers loaded")
            return sorted(tickers)
        except Exception as e:
            logger.warning(f"Failed to load S&P 400 list: {e}")
            return []

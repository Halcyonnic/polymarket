"""Client for fetching orderbook data from Polymarket."""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import polars as pl
import requests


class OrderbookClient:
    """Client for fetching orderbook data from Polymarket's CLOB API."""

    CLOB_API_BASE = "https://clob.polymarket.com"
    DATA_API_BASE = "https://data-api.polymarket.com"
    GAMMA_API_BASE = "https://gamma-api.polymarket.com"

    def __init__(self, rate_limit_delay: float = 0.5):
        """Initialize orderbook client.

        Args:
            rate_limit_delay: Delay between API calls in seconds
        """
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0

    def _rate_limit(self):
        """Apply rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def _make_request(self, url: str, params: Optional[Dict] = None) -> Any:
        """Make HTTP request with rate limiting and error handling.

        Args:
            url: API endpoint URL
            params: Query parameters

        Returns:
            JSON response data
        """
        self._rate_limit()
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return None

    # human reviewed
    def get_markets(
        self,
        closed: bool = False,
        limit: int = 100,
        offset: int = 0,
        volume_num_min: float = 100000.0,
        end_date_min: str = (datetime.now().date()).isoformat(),
        end_date_max: str = (datetime.now().date() + timedelta(days=7)).isoformat(),
        sports_market_types: Optional[List[str]] = ["moneyline"],
    ) -> pl.DataFrame:
        """Fetch all available markets.

        Args:
            closed: Include closed markets
            limit: Maximum number of markets to fetch (default: 100)
            end_date_min: Minimum end date for markets (default: today)
            end_date_max: Maximum end date for markets (default: today + 7 days)
            offset: Offset for pagination (default: 0)
            volume_num_min: Minimum volume for markets (default: 100000.0 = 100k USD)
            sports_market_types: List of sports market types to include (default: ["moneyline"])
        Returns:
            Polars DataFrame with market information
        """

        url = f"{self.GAMMA_API_BASE}/markets"
        params = {
            "closed": str(closed).lower(),
            "limit": limit,
            "end_date_max": end_date_max,
            "offset": offset,
            "end_date_min": end_date_min,
            "volume_num_min": volume_num_min,
            "sports_market_types": "&sports_market_types=".join(sports_market_types)
            if sports_market_types
            else None,
        }
        data = self._make_request(url, params)
        if data:
            return pl.DataFrame(data)
        return pl.DataFrame()

    def get_orderbook(self, token_id: str) -> Dict[str, Any]:
        """Fetch orderbook for a specific market token.

        Args:
            token_id: Market token ID

        Returns:
            Dictionary containing bids and asks with price levels
        """
        url = f"{self.CLOB_API_BASE}/book"
        params = {"token_id": token_id}
        data = self._make_request(url, params)

        if data and isinstance(data, dict):
            return {
                "token_id": token_id,
                "bids": data.get("bids", []),
                "asks": data.get("asks", []),
                "timestamp": datetime.now().isoformat(),
            }
        return {
            "token_id": token_id,
            "bids": [],
            "asks": [],
            "timestamp": datetime.now().isoformat(),
        }

    def get_orderbook_snapshot(self, token_id: str) -> pl.DataFrame:
        """Get orderbook snapshot as structured DataFrame.

        Args:
            token_id: Market token ID

        Returns:
            Polars DataFrame with orderbook data
        """
        orderbook = self.get_orderbook(token_id)

        rows = []
        for bid in orderbook["bids"]:
            rows.append(
                {
                    "side": "BID",
                    "price": float(bid.get("price", 0)),
                    "size": float(bid.get("size", 0)),
                    "token_id": token_id,
                    "timestamp": orderbook["timestamp"],
                }
            )

        for ask in orderbook["asks"]:
            rows.append(
                {
                    "side": "ASK",
                    "price": float(ask.get("price", 0)),
                    "size": float(ask.get("size", 0)),
                    "token_id": token_id,
                    "timestamp": orderbook["timestamp"],
                }
            )

        return pl.DataFrame(rows) if rows else pl.DataFrame()

    def get_spread(self, token_id: str) -> Dict[str, Any]:
        """Calculate bid-ask spread for a market.

        Args:
            token_id: Market token ID

        Returns:
            Dictionary with best bid, best ask, and spread
        """
        orderbook = self.get_orderbook(token_id)

        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])

        best_bid = float(bids[0].get("price", 0)) if bids else 0
        best_ask = float(asks[0].get("price", 0)) if asks else 0
        spread = best_ask - best_bid if best_bid > 0 and best_ask > 0 else 0

        return {
            "token_id": token_id,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "spread_pct": (spread / best_ask * 100) if best_ask > 0 else 0,
            "timestamp": datetime.now().isoformat(),
        }

    def get_market_trades(self, token_id: str, limit: int = 100) -> pl.DataFrame:
        """Fetch recent trades for a market.

        Args:
            token_id: Market token ID
            limit: Maximum number of trades to fetch

        Returns:
            Polars DataFrame with trade history
        """
        url = f"{self.CLOB_API_BASE}/trades"
        params = {"token_id": token_id, "limit": limit}
        data = self._make_request(url, params)

        if data and isinstance(data, list):
            return pl.DataFrame(data)
        return pl.DataFrame()

    def get_market_depth(self, token_id: str, levels: int = 10) -> Dict[str, Any]:
        """Calculate market depth statistics.

        Args:
            token_id: Market token ID
            levels: Number of price levels to analyze

        Returns:
            Dictionary with depth metrics
        """
        orderbook = self.get_orderbook(token_id)

        bids = orderbook.get("bids", [])[:levels]
        asks = orderbook.get("asks", [])[:levels]

        bid_volume = sum(float(b.get("size", 0)) for b in bids)
        ask_volume = sum(float(a.get("size", 0)) for a in asks)
        total_volume = bid_volume + ask_volume

        return {
            "token_id": token_id,
            "bid_volume": bid_volume,
            "ask_volume": ask_volume,
            "total_volume": total_volume,
            "imbalance": (bid_volume - ask_volume) / total_volume
            if total_volume > 0
            else 0,
            "num_bid_levels": len(bids),
            "num_ask_levels": len(asks),
            "timestamp": datetime.now().isoformat(),
        }

    def get_multiple_orderbooks(self, token_ids: List[str]) -> pl.DataFrame:
        """Fetch orderbooks for multiple markets.

        Args:
            token_ids: List of market token IDs

        Returns:
            Polars DataFrame with all orderbook data
        """
        all_orderbooks = []
        for token_id in token_ids:
            df = self.get_orderbook_snapshot(token_id)
            if len(df) > 0:
                all_orderbooks.append(df)

        return pl.concat(all_orderbooks) if all_orderbooks else pl.DataFrame()

    def get_top_of_book(self, token_ids: List[str]) -> pl.DataFrame:
        """Get best bid/ask for multiple markets.

        Args:
            token_ids: List of market token IDs

        Returns:
            Polars DataFrame with top of book data
        """
        spreads = [self.get_spread(token_id) for token_id in token_ids]
        return pl.DataFrame(spreads) if spreads else pl.DataFrame()
        return pl.DataFrame(spreads) if spreads else pl.DataFrame()

"""Monitor for detecting and alerting on big trades across all orderbooks."""

import threading
import time
from collections import deque
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

import polars as pl

from .orderbook_client import OrderbookClient
from .sports_filter import SportsMarketFilter


class BigTradeMonitor:
    """Monitor all orderbooks for big trades and send alerts."""

    def __init__(
        self,
        orderbook_client: Optional[OrderbookClient] = None,
        poll_interval: float = 3.0,
        size_threshold: float = 500.0,
        value_threshold: float = 100.0,
    ):
        """Initialize big trade monitor.

        Args:
            orderbook_client: OrderbookClient instance (creates new one if None)
            poll_interval: Time between polling cycles in seconds
            size_threshold: Minimum trade size to trigger alert
            value_threshold: Minimum trade value (size * price) to trigger alert
        """
        self.client = orderbook_client or OrderbookClient()
        self.sports_filter = SportsMarketFilter()
        self.poll_interval = poll_interval
        self.size_threshold = size_threshold
        self.value_threshold = value_threshold

        self.is_running = False
        self.monitor_thread = None

        # Track seen trades to avoid duplicate alerts
        self.seen_trade_ids: Set[str] = set()

        # Store big trades history
        self.big_trades_history = deque(maxlen=10000)

        # Tracked markets
        self.tracked_markets: List[Dict[str, Any]] = []

        # Alert callbacks
        self.alert_callbacks: List[Callable] = []

        # Stats
        self.stats: Dict[str, Any] = {
            "total_trades_checked": int(0),
            "big_trades_detected": int(0),
            "alerts_sent": int(0),
            "markets_monitored": int(0),
            "start_time": None,
        }

    def add_alert_callback(self, callback: Callable):
        """Register a callback function for big trade alerts.

        Args:
            callback: Function to call when big trade detected.
                     Should accept dict with trade details.
        """
        self.alert_callbacks.append(callback)
        print(
            f"Alert callback registered. Total callbacks: {len(self.alert_callbacks)}"
        )

    def set_thresholds(
        self,
        size_threshold: Optional[float] = None,
        value_threshold: Optional[float] = None,
    ):
        """Update alert thresholds.

        Args:
            size_threshold: Minimum trade size
            value_threshold: Minimum trade value (size * price)
        """
        if size_threshold is not None:
            self.size_threshold = size_threshold
            print(f"Size threshold updated to: {size_threshold}")
        if value_threshold is not None:
            self.value_threshold = value_threshold
            print(f"Value threshold updated to: {value_threshold}")

    def discover_all_active_markets(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Discover all active markets to monitor.

        Args:
            limit: Maximum markets to fetch

        Returns:
            List of market dictionaries with metadata
        """
        import json

        print("Discovering all active markets...")
        markets_df = self.client.get_markets(closed=False, limit=limit, offset=0)

        if len(markets_df) == 0:
            print("No markets found")
            return []

        markets = []
        for row in markets_df.head(limit).iter_rows(named=True):
            # Get token IDs from clobTokenIds field
            clob_token_ids = row.get("clobTokenIds", "[]")
            outcomes = row.get("outcomes", "[]")

            # Parse JSON strings
            try:
                if isinstance(clob_token_ids, str):
                    token_ids = json.loads(clob_token_ids)
                else:
                    token_ids = clob_token_ids

                if isinstance(outcomes, str):
                    outcome_names = json.loads(outcomes)
                else:
                    outcome_names = outcomes

                # Create market info for each token/outcome pair
                if isinstance(token_ids, list) and isinstance(outcome_names, list):
                    for i, token_id in enumerate(token_ids):
                        outcome = (
                            outcome_names[i] if i < len(outcome_names) else "Unknown"
                        )
                        market_info = {
                            "token_id": str(token_id),
                            "outcome": outcome,
                            "question": row.get("question", ""),
                            "market_slug": row.get("slug", ""),
                            "volume": float(row.get("volume", 0)),
                            "liquidity": float(row.get("liquidity", 0)),
                        }
                        markets.append(market_info)
            except (json.JSONDecodeError, TypeError, ValueError):
                # Skip markets with parsing errors
                continue

        print(f"Found {len(markets)} active markets")
        return markets

    def set_tracked_markets(self, markets: List[Dict[str, Any]]):
        """Set list of markets to monitor.

        Args:
            markets: List of market info dictionaries
        """
        self.tracked_markets = markets
        self.stats["markets_monitored"] = len(markets)
        print(f"Now tracking {len(markets)} markets")

    def _generate_trade_id(self, trade: Dict[str, Any]) -> str:
        """Generate unique ID for a trade.

        Args:
            trade: Trade data

        Returns:
            Unique trade identifier
        """
        # Use combination of fields to create unique ID
        token_id = trade.get("market", trade.get("token_id", ""))
        price = trade.get("price", 0)
        size = trade.get("size", 0)
        timestamp = trade.get("timestamp", "")
        side = trade.get("side", "")

        return f"{token_id}_{price}_{size}_{timestamp}_{side}"

    def _is_big_trade(self, trade: Dict[str, Any]) -> bool:
        """Check if trade meets big trade criteria.

        Args:
            trade: Trade data

        Returns:
            True if trade is considered "big"
        """
        try:
            size = float(trade.get("size", 0))
            price = float(trade.get("price", 0))
            value = size * price

            return size >= self.size_threshold or value >= self.value_threshold
        except (ValueError, TypeError):
            return False

    def _process_trades(
        self, token_id: str, trades_df: pl.DataFrame, market_info: Dict[str, Any]
    ):
        """Process trades and detect big trades.

        NOTE: Trades endpoint requires API key. This method is kept for future use
        when API key is available.

        Args:
            token_id: Market token ID
            trades_df: DataFrame with trade data
            market_info: Market metadata
        """
        if len(trades_df) == 0:
            return

        for row in trades_df.iter_rows(named=True):
            self.stats["total_trades_checked"] += 1

            # Create trade dict
            trade = {
                "token_id": token_id,
                "market": token_id,
                "price": row.get("price", 0),
                "size": row.get("size", 0),
                "side": row.get("side", "UNKNOWN"),
                "timestamp": row.get("timestamp", datetime.now().isoformat()),
                "outcome": market_info.get("outcome", "Unknown"),
                "question": market_info.get("question", ""),
                "market_slug": market_info.get("market_slug", ""),
            }

            trade_id = self._generate_trade_id(trade)

            # Skip if already seen
            if trade_id in self.seen_trade_ids:
                continue

            self.seen_trade_ids.add(trade_id)

            # Check if it's a big trade
            if self._is_big_trade(trade):
                self._handle_big_trade(trade)

    def _detect_big_order_from_orderbook(
        self, orderbook: Dict[str, Any], market_info: Dict[str, Any]
    ):
        """Detect big orders from orderbook data.

        This method analyzes orderbook to detect large orders that could indicate
        big trading activity.

        Args:
            orderbook: Orderbook data with bids and asks
            market_info: Market metadata
        """
        token_id = orderbook.get("token_id")
        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])

        # Check for big orders in bids
        for bid in bids:
            try:
                size = float(bid.get("size", 0))
                price = float(bid.get("price", 0))
                value = size * price

                if size >= self.size_threshold or value >= self.value_threshold:
                    self.stats["total_trades_checked"] += 1

                    # Create unique ID for this order
                    order_id = f"{token_id}_BID_{price}_{size}"

                    if order_id not in self.seen_trade_ids:
                        self.seen_trade_ids.add(order_id)

                        big_order = {
                            "token_id": token_id,
                            "market": token_id,
                            "price": price,
                            "size": size,
                            "side": "BID",
                            "timestamp": orderbook.get(
                                "timestamp", datetime.now().isoformat()
                            ),
                            "outcome": market_info.get("outcome", "Unknown"),
                            "question": market_info.get("question", ""),
                            "market_slug": market_info.get("market_slug", ""),
                            "value": value,
                            "detection_time": datetime.now().isoformat(),
                            "type": "LIMIT_ORDER",
                        }

                        self._handle_big_trade(big_order)
            except (ValueError, TypeError):
                continue

        # Check for big orders in asks
        for ask in asks:
            try:
                size = float(ask.get("size", 0))
                price = float(ask.get("price", 0))
                value = size * price

                if size >= self.size_threshold or value >= self.value_threshold:
                    self.stats["total_trades_checked"] += 1

                    order_id = f"{token_id}_ASK_{price}_{size}"

                    if order_id not in self.seen_trade_ids:
                        self.seen_trade_ids.add(order_id)

                        big_order = {
                            "token_id": token_id,
                            "market": token_id,
                            "price": price,
                            "size": size,
                            "side": "ASK",
                            "timestamp": orderbook.get(
                                "timestamp", datetime.now().isoformat()
                            ),
                            "outcome": market_info.get("outcome", "Unknown"),
                            "question": market_info.get("question", ""),
                            "market_slug": market_info.get("market_slug", ""),
                            "value": value,
                            "detection_time": datetime.now().isoformat(),
                            "type": "LIMIT_ORDER",
                        }

                        self._handle_big_trade(big_order)
            except (ValueError, TypeError):
                continue

    def _handle_big_trade(self, trade: Dict[str, Any]):
        """Handle detection of a big trade.

        Args:
            trade: Trade data
        """
        self.stats["big_trades_detected"] += 1

        # Calculate trade value
        size = float(trade.get("size", 0))
        price = float(trade.get("price", 0))
        value = size * price

        # Enrich trade data
        big_trade = {
            **trade,
            "value": value,
            "detection_time": datetime.now().isoformat(),
        }

        # Store in history
        self.big_trades_history.append(big_trade)

        # Trigger alerts
        self._send_alerts(big_trade)

    def _send_alerts(self, big_trade: Dict[str, Any]):
        """Send alerts for big trade.

        Args:
            big_trade: Big trade data
        """
        for callback in self.alert_callbacks:
            try:
                callback(big_trade)
                self.stats["alerts_sent"] += 1
            except Exception as e:
                print(f"Alert callback error: {e}")

    def _monitor_loop(self):
        """Main monitoring loop."""
        print("\n🚀 Big Trade Monitor started!")
        print(f"   Polling interval: {self.poll_interval}s")
        print(f"   Size threshold: {self.size_threshold}")
        print(f"   Value threshold: ${self.value_threshold}")
        print(f"   Markets: {len(self.tracked_markets)}")
        print(f"   Alert callbacks: {len(self.alert_callbacks)}")
        print("   Mode: Orderbook monitoring (detects large limit orders)\n")

        cycle = 0
        while self.is_running:
            try:
                cycle += 1
                print(
                    f"[Cycle {cycle}] Checking {len(self.tracked_markets)} markets...",
                    end=" ",
                )

                cycle_start = time.time()
                trades_checked = 0

                for market_info in self.tracked_markets:
                    if not self.is_running:
                        break

                    token_id = market_info.get("token_id")
                    if not token_id:
                        continue

                    try:
                        # Fetch orderbook for this market instead of trades
                        orderbook = self.client.get_orderbook(token_id)

                        # Count orders checked
                        trades_checked += len(orderbook.get("bids", []))
                        trades_checked += len(orderbook.get("asks", []))

                        # Detect big orders from orderbook
                        self._detect_big_order_from_orderbook(orderbook, market_info)

                    except Exception:
                        # Silently continue on errors
                        pass

                cycle_time = time.time() - cycle_start
                print(f"✓ ({trades_checked} orders, {cycle_time:.1f}s)")

                # Sleep until next cycle
                sleep_time = max(0, self.poll_interval - cycle_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                print(f"\n❌ Monitor loop error: {e}")
                time.sleep(self.poll_interval)

    def start(self, auto_discover: bool = True, market_limit: int = 50):
        """Start monitoring in background thread.

        Args:
            auto_discover: Automatically discover markets if none set
            market_limit: Maximum markets to discover
        """
        if self.is_running:
            print("Monitor already running")
            return

        # Auto-discover markets if needed
        if auto_discover and not self.tracked_markets:
            markets = self.discover_all_active_markets(limit=market_limit)
            self.set_tracked_markets(markets)

        if not self.tracked_markets:
            print("❌ No markets to monitor. Add markets first.")
            return

        self.is_running = True
        self.stats["start_time"] = datetime.now().isoformat()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop(self):
        """Stop monitoring."""
        if not self.is_running:
            print("Monitor not running")
            return

        print("\n🛑 Stopping monitor...")
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("Monitor stopped")

    def get_big_trades_dataframe(self) -> pl.DataFrame:
        """Get all detected big trades as DataFrame.

        Returns:
            Polars DataFrame with big trades
        """
        if not self.big_trades_history:
            return pl.DataFrame()
        return pl.DataFrame(list(self.big_trades_history))

    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics.

        Returns:
            Dictionary with stats
        """
        if self.stats["start_time"]:
            start_dt = datetime.fromisoformat(self.stats["start_time"])
            uptime_seconds = (datetime.now() - start_dt).total_seconds()
            self.stats["uptime_seconds"] = uptime_seconds
            self.stats["uptime_minutes"] = uptime_seconds / 60

        return self.stats.copy()

    def print_stats(self):
        """Print monitoring statistics."""
        stats = self.get_stats()
        print("\n" + "=" * 60)
        print("BIG TRADE MONITOR STATISTICS")
        print("=" * 60)
        print(f"Markets monitored:     {stats.get('markets_monitored', 0)}")
        print(f"Total trades checked:  {stats.get('total_trades_checked', 0)}")
        print(f"Big trades detected:   {stats.get('big_trades_detected', 0)}")
        print(f"Alerts sent:           {stats.get('alerts_sent', 0)}")
        if stats.get("uptime_minutes"):
            print(f"Uptime:                {stats['uptime_minutes']:.1f} minutes")
        print("=" * 60 + "\n")

    def clear_history(self):
        """Clear all stored data."""
        self.big_trades_history.clear()
        self.seen_trade_ids.clear()
        self.stats["total_trades_checked"] = 0
        self.stats["big_trades_detected"] = 0
        self.stats["alerts_sent"] = 0
        print("History cleared")


# Default alert handlers
def print_alert(trade: Dict[str, Any]):
    """Simple print alert handler.

    Args:
        trade: Big trade data
    """
    size = trade.get("size", 0)
    price = trade.get("price", 0)
    value = trade.get("value", 0)
    side = trade.get("side", "UNKNOWN")
    outcome = trade.get("outcome", "Unknown")
    question = trade.get("question", "")[:60]

    print("\n" + "🔔" * 30)
    print("🚨 BIG TRADE ALERT!")
    print(f"   Market: {question}...")
    print(f"   Outcome: {outcome}")
    print(f"   Side: {side}")
    print(f"   Size: {size:,.2f}")
    print(f"   Price: ${price:.4f}")
    print(f"   Value: ${value:,.2f}")
    print(f"   Time: {trade.get('timestamp', 'N/A')}")
    print("🔔" * 30 + "\n")


def log_alert(trade: Dict[str, Any], log_file: str = "big_trades.log"):
    """Log alert to file.

    Args:
        trade: Big trade data
        log_file: Path to log file
    """
    try:
        with open(log_file, "a") as f:
            timestamp = datetime.now().isoformat()
            size = trade.get("size", 0)
            price = trade.get("price", 0)
            value = trade.get("value", 0)
            side = trade.get("side", "UNKNOWN")
            question = trade.get("question", "")

            f.write(
                f"{timestamp} | {side} | Size: {size} | Price: {price} | "
                f"Value: {value:.2f} | Market: {question}\n"
            )
    except Exception as e:
        print(f"Error logging alert: {e}")

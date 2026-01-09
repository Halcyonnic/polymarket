"""Continuous monitoring of orderbooks and trades for sports markets."""

import time
import polars as pl
from typing import List, Dict, Callable, Optional, Any
import threading
from collections import deque
from .orderbook_client import OrderbookClient
from .sports_filter import SportsMarketFilter


class TradeMonitor:
    """Monitor orderbooks and trades continuously for sports markets."""
    
    def __init__(self, orderbook_client: Optional[OrderbookClient] = None, 
                 poll_interval: float = 5.0):
        """Initialize trade monitor.
        
        Args:
            orderbook_client: OrderbookClient instance (creates new one if None)
            poll_interval: Time between polling cycles in seconds
        """
        self.client = orderbook_client or OrderbookClient()
        self.sports_filter = SportsMarketFilter()
        self.poll_interval = poll_interval
        
        self.is_running = False
        self.monitor_thread = None
        
        # Store historical data
        self.orderbook_history = deque(maxlen=1000)
        self.spread_history = deque(maxlen=1000)
        self.trade_history = deque(maxlen=5000)
        
        # Tracked markets
        self.tracked_markets: List[str] = []
        
        # Callbacks for events
        self.callbacks: Dict[str, List[Callable]] = {
            "orderbook_update": [],
            "spread_change": [],
            "new_trade": [],
            "large_order": []
        }
    
    def add_callback(self, event_type: str, callback: Callable):
        """Register a callback function for an event.
        
        Args:
            event_type: Type of event ('orderbook_update', 'spread_change', 'new_trade', 'large_order')
            callback: Function to call when event occurs
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    def set_tracked_markets(self, token_ids: List[str]):
        """Set list of markets to monitor.
        
        Args:
            token_ids: List of token IDs to track
        """
        self.tracked_markets = token_ids
        print(f"Now tracking {len(token_ids)} markets")
    
    def discover_sports_moneylines(self, limit: int = 50) -> List[str]:
        """Discover active sports moneyline markets.
        
        Args:
            limit: Maximum markets to fetch
            
        Returns:
            List of token IDs for moneyline markets
        """
        print("Discovering sports moneyline markets...")
        markets_df = self.client.get_markets(active=True, closed=False)
        
        if len(markets_df) == 0:
            print("No markets found")
            return []
        
        # Filter to moneyline markets
        moneyline_df = self.sports_filter.filter_moneyline_markets(markets_df)
        
        if len(moneyline_df) == 0:
            print("No moneyline markets found")
            return []
        
        # Extract token IDs
        token_ids = []
        if "tokens" in moneyline_df.columns:
            for row in moneyline_df.head(limit).iter_rows(named=True):
                tokens = row.get("tokens", [])
                if isinstance(tokens, list) and len(tokens) > 0:
                    # Get first token (usually the "Yes" outcome)
                    token_ids.append(tokens[0].get("token_id") if isinstance(tokens[0], dict) else str(tokens[0]))
        
        print(f"Found {len(token_ids)} moneyline markets")
        return token_ids
    
    def _poll_orderbooks(self):
        """Poll orderbooks for all tracked markets."""
        if not self.tracked_markets:
            return
        
        for token_id in self.tracked_markets:
            try:
                # Get spread data
                spread = self.client.get_spread(token_id)
                self.spread_history.append(spread)
                
                # Trigger callbacks
                for callback in self.callbacks["spread_change"]:
                    try:
                        callback(spread)
                    except Exception as e:
                        print(f"Callback error: {e}")
                
                # Get full orderbook
                orderbook = self.client.get_orderbook(token_id)
                self.orderbook_history.append(orderbook)
                
                for callback in self.callbacks["orderbook_update"]:
                    try:
                        callback(orderbook)
                    except Exception as e:
                        print(f"Callback error: {e}")
                
                # Check for large orders
                self._check_large_orders(orderbook)
                
            except Exception as e:
                print(f"Error polling {token_id}: {e}")
    
    def _check_large_orders(self, orderbook: Dict[str, Any], threshold: float = 1000):
        """Check for large orders in orderbook.
        
        Args:
            orderbook: Orderbook data
            threshold: Size threshold for large orders
        """
        token_id = orderbook.get("token_id")
        
        for bid in orderbook.get("bids", []):
            size = float(bid.get("size", 0))
            if size >= threshold:
                large_order = {
                    "token_id": token_id,
                    "side": "BID",
                    "price": float(bid.get("price", 0)),
                    "size": size,
                    "timestamp": orderbook.get("timestamp")
                }
                for callback in self.callbacks["large_order"]:
                    try:
                        callback(large_order)
                    except Exception as e:
                        print(f"Callback error: {e}")
        
        for ask in orderbook.get("asks", []):
            size = float(ask.get("size", 0))
            if size >= threshold:
                large_order = {
                    "token_id": token_id,
                    "side": "ASK",
                    "price": float(ask.get("price", 0)),
                    "size": size,
                    "timestamp": orderbook.get("timestamp")
                }
                for callback in self.callbacks["large_order"]:
                    try:
                        callback(large_order)
                    except Exception as e:
                        print(f"Callback error: {e}")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        print(f"Monitor started - polling every {self.poll_interval}s")
        
        while self.is_running:
            try:
                self._poll_orderbooks()
                time.sleep(self.poll_interval)
            except Exception as e:
                print(f"Monitor loop error: {e}")
                time.sleep(self.poll_interval)
    
    def start(self):
        """Start monitoring in background thread."""
        if self.is_running:
            print("Monitor already running")
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("Monitor started")
    
    def stop(self):
        """Stop monitoring."""
        if not self.is_running:
            print("Monitor not running")
            return
        
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("Monitor stopped")
    
    def get_spread_dataframe(self) -> pl.DataFrame:
        """Get historical spread data as DataFrame.
        
        Returns:
            Polars DataFrame with spread history
        """
        if not self.spread_history:
            return pl.DataFrame()
        return pl.DataFrame(list(self.spread_history))
    
    def get_orderbook_summary(self) -> pl.DataFrame:
        """Get summary of recent orderbook data.
        
        Returns:
            Polars DataFrame with orderbook metrics
        """
        if not self.orderbook_history:
            return pl.DataFrame()
        
        summaries = []
        for ob in self.orderbook_history:
            summaries.append({
                "token_id": ob.get("token_id"),
                "num_bids": len(ob.get("bids", [])),
                "num_asks": len(ob.get("asks", [])),
                "timestamp": ob.get("timestamp")
            })
        
        return pl.DataFrame(summaries)
    
    def get_latest_spreads(self) -> pl.DataFrame:
        """Get latest spread for each tracked market.
        
        Returns:
            Polars DataFrame with latest spreads
        """
        if not self.spread_history:
            return pl.DataFrame()
        
        # Get most recent spread for each token
        latest_spreads = {}
        for spread in reversed(self.spread_history):
            token_id = spread.get("token_id")
            if token_id not in latest_spreads:
                latest_spreads[token_id] = spread
        
        return pl.DataFrame(list(latest_spreads.values()))
    
    def clear_history(self):
        """Clear all stored historical data."""
        self.orderbook_history.clear()
        self.spread_history.clear()
        self.trade_history.clear()
        print("History cleared")

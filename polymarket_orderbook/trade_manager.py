"""Trade manager for monitoring positions and managing orders."""

import polars as pl
from typing import Dict, List, Optional, Any
from datetime import datetime
from .orderbook_client import OrderbookClient


class TradeManager:
    """Manage and track trades, positions, and orders."""
    
    def __init__(self, orderbook_client: Optional[OrderbookClient] = None):
        """Initialize trade manager.
        
        Args:
            orderbook_client: OrderbookClient instance (creates new one if None)
        """
        self.client = orderbook_client or OrderbookClient()
        
        # Track positions
        self.positions: Dict[str, Dict[str, Any]] = {}
        
        # Track order history
        self.order_history: List[Dict[str, Any]] = []
        
        # Track P&L
        self.pnl_history: List[Dict[str, Any]] = []
    
    def add_position(self, token_id: str, side: str, size: float, 
                     entry_price: float, market_name: str = ""):
        """Add a new position.
        
        Args:
            token_id: Market token ID
            side: 'LONG' or 'SHORT'
            size: Position size
            entry_price: Entry price
            market_name: Human-readable market name
        """
        position = {
            "token_id": token_id,
            "market_name": market_name,
            "side": side.upper(),
            "size": size,
            "entry_price": entry_price,
            "entry_time": datetime.now().isoformat(),
            "current_price": entry_price,
            "unrealized_pnl": 0.0,
            "unrealized_pnl_pct": 0.0
        }
        
        self.positions[token_id] = position
        print(f"Position added: {side} {size} @ {entry_price} ({market_name})")
    
    def close_position(self, token_id: str, exit_price: float):
        """Close an existing position.
        
        Args:
            token_id: Market token ID
            exit_price: Exit price
            
        Returns:
            Realized P&L
        """
        if token_id not in self.positions:
            print(f"No position found for {token_id}")
            return 0.0
        
        position = self.positions[token_id]
        size = position["size"]
        entry_price = position["entry_price"]
        side = position["side"]
        
        # Calculate P&L
        if side == "LONG":
            pnl = size * (exit_price - entry_price)
        else:  # SHORT
            pnl = size * (entry_price - exit_price)
        
        pnl_pct = (pnl / (size * entry_price)) * 100 if size * entry_price > 0 else 0
        
        # Record P&L
        pnl_record = {
            "token_id": token_id,
            "market_name": position["market_name"],
            "side": side,
            "size": size,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "entry_time": position["entry_time"],
            "exit_time": datetime.now().isoformat(),
            "realized_pnl": pnl,
            "realized_pnl_pct": pnl_pct
        }
        self.pnl_history.append(pnl_record)
        
        # Remove position
        del self.positions[token_id]
        
        print(f"Position closed: {side} {size} @ {exit_price} | P&L: ${pnl:.2f} ({pnl_pct:.2f}%)")
        return pnl
    
    def update_positions(self):
        """Update all positions with current market prices."""
        if not self.positions:
            return
        
        token_ids = list(self.positions.keys())
        spreads_df = self.client.get_top_of_book(token_ids)
        
        if len(spreads_df) == 0:
            return
        
        for row in spreads_df.iter_rows(named=True):
            token_id = row.get("token_id")
            if token_id not in self.positions:
                continue
            
            position = self.positions[token_id]
            side = position["side"]
            
            # Use mid price
            best_bid = row.get("best_bid", 0)
            best_ask = row.get("best_ask", 0)
            current_price = (best_bid + best_ask) / 2 if best_bid > 0 and best_ask > 0 else position["entry_price"]
            
            # Update position
            position["current_price"] = current_price
            
            # Calculate unrealized P&L
            size = position["size"]
            entry_price = position["entry_price"]
            
            if side == "LONG":
                unrealized_pnl = size * (current_price - entry_price)
            else:  # SHORT
                unrealized_pnl = size * (entry_price - current_price)
            
            unrealized_pnl_pct = (unrealized_pnl / (size * entry_price)) * 100 if size * entry_price > 0 else 0
            
            position["unrealized_pnl"] = unrealized_pnl
            position["unrealized_pnl_pct"] = unrealized_pnl_pct
    
    def get_positions_dataframe(self) -> pl.DataFrame:
        """Get current positions as DataFrame.
        
        Returns:
            Polars DataFrame with positions
        """
        if not self.positions:
            return pl.DataFrame()
        
        return pl.DataFrame(list(self.positions.values()))
    
    def get_pnl_dataframe(self) -> pl.DataFrame:
        """Get P&L history as DataFrame.
        
        Returns:
            Polars DataFrame with P&L records
        """
        if not self.pnl_history:
            return pl.DataFrame()
        
        return pl.DataFrame(self.pnl_history)
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary statistics.
        
        Returns:
            Dictionary with portfolio metrics
        """
        self.update_positions()
        
        total_unrealized_pnl = sum(p["unrealized_pnl"] for p in self.positions.values())
        total_realized_pnl = sum(p["realized_pnl"] for p in self.pnl_history)
        total_pnl = total_unrealized_pnl + total_realized_pnl
        
        num_positions = len(self.positions)
        num_closed_positions = len(self.pnl_history)
        
        winning_trades = sum(1 for p in self.pnl_history if p["realized_pnl"] > 0)
        losing_trades = sum(1 for p in self.pnl_history if p["realized_pnl"] < 0)
        win_rate = (winning_trades / num_closed_positions * 100) if num_closed_positions > 0 else 0
        
        return {
            "num_open_positions": num_positions,
            "num_closed_positions": num_closed_positions,
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_realized_pnl": total_realized_pnl,
            "total_pnl": total_pnl,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate_pct": win_rate,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_best_trade(self) -> Optional[Dict[str, Any]]:
        """Get best performing closed trade.
        
        Returns:
            Dictionary with best trade details
        """
        if not self.pnl_history:
            return None
        
        return max(self.pnl_history, key=lambda x: x["realized_pnl"])
    
    def get_worst_trade(self) -> Optional[Dict[str, Any]]:
        """Get worst performing closed trade.
        
        Returns:
            Dictionary with worst trade details
        """
        if not self.pnl_history:
            return None
        
        return min(self.pnl_history, key=lambda x: x["realized_pnl"])
    
    def monitor_stop_loss(self, stop_loss_pct: float = -10.0):
        """Check positions for stop loss triggers.
        
        Args:
            stop_loss_pct: Stop loss percentage threshold
            
        Returns:
            List of positions that hit stop loss
        """
        self.update_positions()
        
        triggered_positions = []
        for token_id, position in self.positions.items():
            if position["unrealized_pnl_pct"] <= stop_loss_pct:
                triggered_positions.append(position)
                print(f"STOP LOSS TRIGGERED: {position['market_name']} ({token_id}) - {position['unrealized_pnl_pct']:.2f}%")
        
        return triggered_positions
    
    def monitor_take_profit(self, take_profit_pct: float = 20.0):
        """Check positions for take profit triggers.
        
        Args:
            take_profit_pct: Take profit percentage threshold
            
        Returns:
            List of positions that hit take profit
        """
        self.update_positions()
        
        triggered_positions = []
        for token_id, position in self.positions.items():
            if position["unrealized_pnl_pct"] >= take_profit_pct:
                triggered_positions.append(position)
                print(f"TAKE PROFIT TRIGGERED: {position['market_name']} ({token_id}) - {position['unrealized_pnl_pct']:.2f}%")
        
        return triggered_positions
    
    def get_position_alerts(self, stop_loss_pct: float = -10.0, 
                          take_profit_pct: float = 20.0) -> Dict[str, List]:
        """Get all position alerts.
        
        Args:
            stop_loss_pct: Stop loss threshold
            take_profit_pct: Take profit threshold
            
        Returns:
            Dictionary with stop loss and take profit alerts
        """
        return {
            "stop_loss": self.monitor_stop_loss(stop_loss_pct),
            "take_profit": self.monitor_take_profit(take_profit_pct)
        }

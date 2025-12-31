"""High-level client for fetching data from Polymarket API."""

import requests
import polars as pl
from .api_builder import PolymarketAPIBuilder


class PolymarketClient:
    """High-level client for fetching data from Polymarket API."""
    
    def __init__(self):
        self.builder = PolymarketAPIBuilder()
    
    def fetch_leaderboard(self, category="OVERALL", time_period="DAY", order_by="PNL", limit=25):
        """Fetch leaderboard data and return as Polars DataFrame.
        
        Args:
            category: Category filter
            time_period: Time period ('DAY', 'WEEK', 'MONTH')
            order_by: Sort field
            limit: Maximum number of results
            
        Returns:
            Polars DataFrame with leaderboard data
        """
        url = self.builder.leaderboard(category, time_period, order_by, limit).build()
        response = requests.get(url)
        response.raise_for_status()
        return pl.DataFrame(response.json())
    
    def fetch_closed_positions(self, user=None, limit=100, sort_by="REALIZEDPNL", sort_direction="DESC"):
        """Fetch closed positions and return as Polars DataFrame.
        
        Args:
            user: User address (optional - if not provided, fetches from top traders)
            limit: Maximum number of results
            sort_by: Sort field
            sort_direction: Sort direction ('ASC' or 'DESC')
            
        Returns:
            Polars DataFrame with closed positions data
        """
        if user is None:
            # Fetch top traders first to get their addresses
            leaderboard = self.fetch_leaderboard(limit=10)
            if len(leaderboard) == 0 or 'proxyWallet' not in leaderboard.columns:
                return pl.DataFrame()
            
            # Get closed positions for top traders
            all_positions = []
            for trader_address in leaderboard['proxyWallet'].head(5).to_list():
                try:
                    url = self.builder.closed_positions(trader_address, limit=20, sort_by=sort_by, sort_direction=sort_direction).build()
                    response = requests.get(url)
                    if response.status_code == 200:
                        positions = response.json()
                        all_positions.extend(positions if isinstance(positions, list) else [positions])
                except:
                    continue
            
            return pl.DataFrame(all_positions[:limit]) if all_positions else pl.DataFrame()
        
        url = self.builder.closed_positions(user, limit, sort_by, sort_direction).build()
        response = requests.get(url)
        response.raise_for_status()
        return pl.DataFrame(response.json())
    
    def fetch_trades(self, limit=100, taker_only=True):
        """Fetch trades and return as Polars DataFrame.
        
        Args:
            limit: Maximum number of results
            taker_only: Filter for taker-only trades
            
        Returns:
            Polars DataFrame with trades data
        """
        url = self.builder.trades(limit, taker_only).build()
        response = requests.get(url)
        response.raise_for_status()
        return pl.DataFrame(response.json())
    
    def fetch_activity(self, user=None, limit=100, sort_by="TIMESTAMP", sort_direction="DESC"):
        """Fetch activity and return as Polars DataFrame.
        
        Args:
            user: User address (optional - if not provided, fetches from top traders)
            limit: Maximum number of results
            sort_by: Sort field
            sort_direction: Sort direction ('ASC' or 'DESC')
            
        Returns:
            Polars DataFrame with activity data
        """
        if user is None:
            # Fetch top traders first to get their addresses
            leaderboard = self.fetch_leaderboard(limit=10)
            if len(leaderboard) == 0 or 'proxyWallet' not in leaderboard.columns:
                return pl.DataFrame()
            
            # Get activity for top traders
            all_activity = []
            for trader_address in leaderboard['proxyWallet'].head(5).to_list():
                try:
                    url = self.builder.activity(trader_address, limit=20, sort_by=sort_by, sort_direction=sort_direction).build()
                    response = requests.get(url)
                    if response.status_code == 200:
                        activity = response.json()
                        all_activity.extend(activity if isinstance(activity, list) else [activity])
                except:
                    continue
            
            return pl.DataFrame(all_activity[:limit]) if all_activity else pl.DataFrame()
        
        url = self.builder.activity(user, limit, sort_by, sort_direction).build()
        response = requests.get(url)
        response.raise_for_status()
        return pl.DataFrame(response.json())
    
    def fetch_all(self, leaderboard_limit=25, positions_limit=100, trades_limit=100, activity_limit=100, user_for_details=None):
        """Fetch all data types at once.
        
        Args:
            leaderboard_limit: Limit for leaderboard results
            positions_limit: Limit for closed positions
            trades_limit: Limit for trades
            activity_limit: Limit for activity
            user_for_details: Optional user address for positions/activity. If None, will use top trader from leaderboard.
            
        Returns:
            Dictionary with keys: 'leaderboard', 'closed_positions', 'trades', 'activity'
        """
        # Fetch leaderboard first
        leaderboard = self.fetch_leaderboard(limit=leaderboard_limit)
        
        # If user not specified and leaderboard has data, use the top trader
        if user_for_details is None and len(leaderboard) > 0:
            if 'proxyWallet' in leaderboard.columns:
                user_for_details = leaderboard['proxyWallet'][0]
        
        return {
            'leaderboard': leaderboard,
            'closed_positions': self.fetch_closed_positions(user=user_for_details, limit=positions_limit),
            'trades': self.fetch_trades(limit=trades_limit),
            'activity': self.fetch_activity(user=user_for_details, limit=activity_limit)
        }
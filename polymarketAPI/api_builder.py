"""Builder class for constructing Polymarket API URLs with query parameters."""


class PolymarketAPIBuilder:
    """Builder class for constructing Polymarket API URLs with query parameters."""
    
    BASE_URL = "https://data-api.polymarket.com"
    
    def __init__(self):
        self.endpoint = None
        self.params = {}
    
    def leaderboard(self, category="OVERALL", time_period="DAY", order_by="PNL", limit=25):
        """Build leaderboard endpoint URL.
        
        Args:
            category: Category filter (e.g., 'OVERALL')
            time_period: Time period ('DAY', 'WEEK', 'MONTH')
            order_by: Sort field (e.g., 'PNL', 'VOLUME')
            limit: Maximum number of results
            
        Returns:
            self for method chaining
        """
        self.endpoint = "/v1/leaderboard"
        self.params = {
            "category": category,
            "timePeriod": time_period,
            "orderBy": order_by,
            "limit": limit
        }
        return self
    
    def closed_positions(self, user, limit=100, sort_by="REALIZEDPNL", sort_direction="DESC"):
        """Build closed positions endpoint URL.
        
        Args:
            user: User address (required)
            limit: Maximum number of results
            sort_by: Sort field (e.g., 'REALIZEDPNL')
            sort_direction: Sort direction ('ASC' or 'DESC')
            
        Returns:
            self for method chaining
        """
        self.endpoint = "/closed-positions"
        self.params = {
            "user": user,
            "limit": limit,
            "sortBy": sort_by,
            "sortDirection": sort_direction
        }
        return self
    
    def trades(self, limit=100, taker_only=True):
        """Build trades endpoint URL.
        
        Args:
            limit: Maximum number of results
            taker_only: Filter for taker-only trades
            
        Returns:
            self for method chaining
        """
        self.endpoint = "/trades"
        self.params = {
            "limit": limit,
            "takerOnly": str(taker_only).lower()
        }
        return self
    
    def activity(self, user, limit=100, sort_by="TIMESTAMP", sort_direction="DESC"):
        """Build activity endpoint URL.
        
        Args:
            user: User address (required)
            limit: Maximum number of results
            sort_by: Sort field (e.g., 'TIMESTAMP')
            sort_direction: Sort direction ('ASC' or 'DESC')
            
        Returns:
            self for method chaining
        """
        self.endpoint = "/activity"
        self.params = {
            "user": user,
            "limit": limit,
            "sortBy": sort_by,
            "sortDirection": sort_direction
        }
        return self
    
    def build(self):
        """Construct the final URL with query parameters.
        
        Returns:
            Complete URL string
            
        Raises:
            ValueError: If no endpoint has been specified
        """
        if not self.endpoint:
            raise ValueError("No endpoint specified. Call one of the endpoint methods first.")
        
        url = f"{self.BASE_URL}{self.endpoint}"
        if self.params:
            query_string = "&".join([f"{k}={v}" for k, v in self.params.items()])
            url = f"{url}?{query_string}"
        return url
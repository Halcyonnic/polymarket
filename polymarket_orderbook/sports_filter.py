"""Filter and identify sports markets on Polymarket."""

import polars as pl
from typing import List, Optional
import re


class SportsMarketFilter:
    """Filter markets to identify sports-related markets, especially moneylines."""
    
    # Sports keywords for market identification
    SPORTS_KEYWORDS = {
        # Major sports
        "nfl", "nba", "mlb", "nhl", "soccer", "football", "basketball", "baseball", "hockey",
        "mls", "premier league", "la liga", "serie a", "bundesliga", "ligue 1", "champions league",
        # Combat sports
        "ufc", "boxing", "mma", "fight", "bout",
        # Other sports
        "tennis", "golf", "cricket", "rugby", "f1", "formula 1", "nascar", "racing",
        # College sports
        "ncaa", "college football", "college basketball",
        # Sport terms (more specific)
        "game", "match", "vs", " at ", "team", "player", "score",
        # Betting terms
        "moneyline", "spread", "total", "prop"
    }
    
    # Teams and leagues for more precise filtering
    NFL_TEAMS = {
        "bills", "dolphins", "patriots", "jets", "ravens", "bengals", "browns", "steelers",
        "texans", "colts", "jaguars", "titans", "broncos", "chiefs", "raiders", "chargers",
        "cowboys", "giants", "eagles", "commanders", "bears", "lions", "packers", "vikings",
        "falcons", "panthers", "saints", "buccaneers", "cardinals", "rams", "49ers", "seahawks"
    }
    
    NBA_TEAMS = {
        "celtics", "nets", "knicks", "76ers", "raptors", "bulls", "cavaliers", "pistons",
        "pacers", "bucks", "hawks", "hornets", "heat", "magic", "wizards", "nuggets",
        "timberwolves", "thunder", "trail blazers", "jazz", "warriors", "clippers", "lakers",
        "suns", "kings", "mavericks", "rockets", "grizzlies", "pelicans", "spurs"
    }
    
    def __init__(self):
        """Initialize sports market filter."""
        self.all_teams = self.NFL_TEAMS | self.NBA_TEAMS
    
    def is_sports_market(self, market_title: str, market_description: str = "") -> bool:
        """Determine if a market is sports-related.
        
        Args:
            market_title: Market title/question
            market_description: Market description
            
        Returns:
            True if market appears to be sports-related
        """
        text = f"{market_title} {market_description}".lower()
        
        # Check for sports keywords
        for keyword in self.SPORTS_KEYWORDS:
            if keyword in text:
                return True
        
        # Check for team names
        for team in self.all_teams:
            if team in text:
                return True
        
        return False
    
    def is_moneyline_market(self, market_title: str) -> bool:
        """Identify if a market is a moneyline bet.
        
        Moneylines typically ask "Will Team A win?" or "Team A vs Team B - Winner?"
        
        Args:
            market_title: Market title/question
            
        Returns:
            True if market appears to be a moneyline
        """
        title_lower = market_title.lower()
        
        # Moneyline indicators
        moneyline_patterns = [
            r"will .+ win",
            r"who will win",
            r".+ to win",
            r".+ vs .+",
            r".+ @ .+",
            r"winner",
            r"moneyline"
        ]
        
        for pattern in moneyline_patterns:
            if re.search(pattern, title_lower):
                return True
        
        # Exclude spread/totals markets
        excluded_patterns = ["spread", "over", "under", "total points", "total score"]
        for pattern in excluded_patterns:
            if pattern in title_lower:
                return False
        
        return False
    
    def filter_sports_markets(self, markets_df: pl.DataFrame) -> pl.DataFrame:
        """Filter a DataFrame to only include sports markets.
        
        Args:
            markets_df: DataFrame with market data (must have 'question' or 'title' column)
            
        Returns:
            Filtered DataFrame with only sports markets
        """
        if len(markets_df) == 0:
            return markets_df
        
        # Determine title column
        title_col = None
        if "question" in markets_df.columns:
            title_col = "question"
        elif "title" in markets_df.columns:
            title_col = "title"
        else:
            print("Warning: No title/question column found in DataFrame")
            return pl.DataFrame()
        
        # Add description column if available
        desc_col = "description" if "description" in markets_df.columns else None
        
        # Filter sports markets
        sports_mask = []
        for row in markets_df.iter_rows(named=True):
            title = row.get(title_col, "")
            desc = row.get(desc_col, "") if desc_col else ""
            sports_mask.append(self.is_sports_market(title, desc))
        
        return markets_df.filter(pl.Series(sports_mask))
    
    def filter_moneyline_markets(self, markets_df: pl.DataFrame) -> pl.DataFrame:
        """Filter a DataFrame to only include moneyline sports markets.
        
        Args:
            markets_df: DataFrame with market data
            
        Returns:
            Filtered DataFrame with only moneyline markets
        """
        # First filter to sports markets
        sports_df = self.filter_sports_markets(markets_df)
        
        if len(sports_df) == 0:
            return sports_df
        
        # Determine title column
        title_col = "question" if "question" in sports_df.columns else "title"
        
        # Filter to moneylines
        moneyline_mask = []
        for row in sports_df.iter_rows(named=True):
            title = row.get(title_col, "")
            moneyline_mask.append(self.is_moneyline_market(title))
        
        return sports_df.filter(pl.Series(moneyline_mask))
    
    def extract_teams(self, market_title: str) -> List[str]:
        """Extract team names from market title.
        
        Args:
            market_title: Market title
            
        Returns:
            List of identified team names
        """
        title_lower = market_title.lower()
        found_teams = []
        
        for team in self.all_teams:
            if team in title_lower:
                found_teams.append(team.title())
        
        return found_teams
    
    def categorize_sport(self, market_title: str) -> Optional[str]:
        """Identify which sport a market belongs to.
        
        Args:
            market_title: Market title
            
        Returns:
            Sport name or None if unidentified
        """
        title_lower = market_title.lower()
        
        sport_categories = {
            "NFL": ["nfl", *self.NFL_TEAMS],
            "NBA": ["nba", *self.NBA_TEAMS],
            "MLB": ["mlb", "baseball"],
            "NHL": ["nhl", "hockey"],
            "Soccer": ["soccer", "premier league", "la liga", "mls", "champions league"],
            "UFC/MMA": ["ufc", "mma", "fight"],
            "Tennis": ["tennis"],
            "Golf": ["golf", "pga"],
            "NCAA": ["ncaa", "college"]
        }
        
        for sport, keywords in sport_categories.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return sport
        
        return None
    
    def get_sports_summary(self, markets_df: pl.DataFrame) -> pl.DataFrame:
        """Get summary statistics of sports markets.
        
        Args:
            markets_df: DataFrame with sports market data
            
        Returns:
            DataFrame with sport categories and counts
        """
        sports_df = self.filter_sports_markets(markets_df)
        
        if len(sports_df) == 0:
            return pl.DataFrame()
        
        title_col = "question" if "question" in sports_df.columns else "title"
        
        # Categorize each market
        categories = []
        for row in sports_df.iter_rows(named=True):
            title = row.get(title_col, "")
            sport = self.categorize_sport(title)
            categories.append({
                "sport": sport or "Other",
                "market_title": title
            })
        
        df_categories = pl.DataFrame(categories)
        
        # Count by sport
        summary = df_categories.group_by("sport").agg([
            pl.count().alias("count")
        ]).sort("count", descending=True)
        
        return summary

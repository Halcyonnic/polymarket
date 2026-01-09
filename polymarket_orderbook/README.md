# Polymarket Sports Orderbook Monitor

A Python package for real-time monitoring and management of sports moneyline markets on Polymarket. This package provides tools to fetch orderbook data, filter sports markets, monitor trades continuously, and manage positions with P&L tracking.

## Features

- 📊 **Real-time Orderbook Data**: Fetch live orderbook, spreads, and market depth
- 🏀 **Sports Market Filtering**: Automatically identify NFL, NBA, UFC, and other sports markets
- 💰 **Moneyline Detection**: Filter markets to find sports moneylines specifically
- 📈 **Continuous Monitoring**: Background polling with customizable intervals
- 🔔 **Event Callbacks**: React to spread changes, large orders, and new trades
- 💼 **Position Management**: Track positions with real-time P&L calculations
- ⚠️ **Alerts System**: Stop-loss and take-profit notifications
- 📊 **Data Export**: Export all data as Polars DataFrames for analysis

## Installation

```bash
cd polymarket
pip install -e .
```

### Dependencies

- polars >= 0.20.0
- requests >= 2.32.0
- python >= 3.13

## Quick Start

### 1. Fetch Orderbook Data

```python
from polymarket_orderbook import OrderbookClient

# Initialize client
client = OrderbookClient(rate_limit_delay=0.5)

# Get all active markets
markets = client.get_markets(active=True)

# Get orderbook for a specific token
orderbook = client.get_orderbook(token_id="your_token_id")

# Calculate spread
spread = client.get_spread(token_id="your_token_id")
print(f"Best Bid: {spread['best_bid']}, Best Ask: {spread['best_ask']}")
```

### 2. Filter Sports Markets

```python
from polymarket_orderbook import SportsMarketFilter

# Initialize filter
sports_filter = SportsMarketFilter()

# Filter markets to sports only
sports_markets = sports_filter.filter_sports_markets(markets)

# Filter to moneyline markets
moneylines = sports_filter.filter_moneyline_markets(markets)

# Categorize sports
summary = sports_filter.get_sports_summary(markets)
```

### 3. Monitor Markets Continuously

```python
from polymarket_orderbook import TradeMonitor

# Initialize monitor
monitor = TradeMonitor(poll_interval=5.0)

# Set up callback for spread changes
def on_spread_change(spread_data):
    print(f"Spread updated: {spread_data['token_id']} - {spread_data['spread_pct']:.2f}%")

monitor.add_callback('spread_change', on_spread_change)

# Discover and track sports moneylines
tokens = monitor.discover_sports_moneylines(limit=10)
monitor.set_tracked_markets(tokens[:5])

# Start monitoring
monitor.start()

# ... monitoring runs in background ...

# Stop when done
monitor.stop()

# Get collected data
spreads_df = monitor.get_spread_dataframe()
```

### 4. Manage Positions and Track P&L

```python
from polymarket_orderbook import TradeManager

# Initialize manager
manager = TradeManager()

# Add a position
manager.add_position(
    token_id="token_123",
    side="LONG",
    size=100,
    entry_price=0.55,
    market_name="Lakers vs Warriors"
)

# Update with current prices
manager.update_positions()

# Check for alerts
alerts = manager.get_position_alerts(
    stop_loss_pct=-10.0,
    take_profit_pct=20.0
)

# Close position
pnl = manager.close_position("token_123", exit_price=0.60)

# Get portfolio summary
summary = manager.get_portfolio_summary()
print(f"Total P&L: ${summary['total_pnl']:.2f}")
print(f"Win Rate: {summary['win_rate_pct']:.1f}%")
```

## Package Structure

```
polymarket_orderbook/
├── __init__.py              # Package exports
├── orderbook_client.py      # Fetch orderbook and market data
├── sports_filter.py         # Filter and categorize sports markets
├── trade_monitor.py         # Continuous monitoring with callbacks
└── trade_manager.py         # Position tracking and P&L management
```

## API Documentation

### OrderbookClient

Main client for fetching orderbook data from Polymarket APIs.

**Methods:**
- `get_markets(active=True, closed=False)` - Fetch all markets
- `get_orderbook(token_id)` - Get full orderbook for a token
- `get_orderbook_snapshot(token_id)` - Get orderbook as DataFrame
- `get_spread(token_id)` - Calculate bid-ask spread
- `get_market_depth(token_id, levels=10)` - Calculate market depth
- `get_market_trades(token_id, limit=100)` - Fetch recent trades
- `get_multiple_orderbooks(token_ids)` - Batch fetch orderbooks
- `get_top_of_book(token_ids)` - Get best bid/ask for multiple markets

### SportsMarketFilter

Filter and identify sports-related markets.

**Methods:**
- `is_sports_market(title, description)` - Check if market is sports-related
- `is_moneyline_market(title)` - Check if market is a moneyline
- `filter_sports_markets(markets_df)` - Filter DataFrame to sports markets
- `filter_moneyline_markets(markets_df)` - Filter to moneyline markets
- `extract_teams(title)` - Extract team names from title
- `categorize_sport(title)` - Identify sport category (NFL, NBA, etc.)
- `get_sports_summary(markets_df)` - Get summary statistics by sport

**Supported Sports:**
- NFL, NBA, MLB, NHL
- Soccer (Premier League, La Liga, Champions League, etc.)
- UFC/MMA, Boxing
- Tennis, Golf, Cricket, Rugby
- NASCAR, Formula 1
- NCAA (College Football, Basketball)

### TradeMonitor

Continuously monitor markets with event callbacks.

**Methods:**
- `add_callback(event_type, callback)` - Register event callback
- `set_tracked_markets(token_ids)` - Set markets to monitor
- `discover_sports_moneylines(limit)` - Auto-discover moneyline markets
- `start()` - Start background monitoring
- `stop()` - Stop monitoring
- `get_spread_dataframe()` - Get historical spread data
- `get_latest_spreads()` - Get most recent spreads
- `clear_history()` - Clear collected data

**Event Types:**
- `orderbook_update` - When orderbook changes
- `spread_change` - When spread changes
- `new_trade` - When new trade occurs
- `large_order` - When large order detected

### TradeManager

Manage positions and track profit/loss.

**Methods:**
- `add_position(token_id, side, size, entry_price, market_name)` - Add new position
- `close_position(token_id, exit_price)` - Close position and realize P&L
- `update_positions()` - Update with current market prices
- `get_positions_dataframe()` - Get current positions as DataFrame
- `get_pnl_dataframe()` - Get P&L history as DataFrame
- `get_portfolio_summary()` - Get portfolio statistics
- `monitor_stop_loss(stop_loss_pct)` - Check for stop loss triggers
- `monitor_take_profit(take_profit_pct)` - Check for take profit triggers
- `get_position_alerts(stop_loss_pct, take_profit_pct)` - Get all alerts

## Example Workflows

### Monitor NFL Moneylines

```python
from polymarket_orderbook import OrderbookClient, TradeMonitor, SportsMarketFilter

client = OrderbookClient()
monitor = TradeMonitor(client, poll_interval=10.0)

# Discover NFL moneylines
markets = client.get_markets(active=True)
sports_filter = SportsMarketFilter()

nfl_markets = []
for row in markets.iter_rows(named=True):
    title = row.get('question', '')
    if sports_filter.categorize_sport(title) == "NFL":
        if sports_filter.is_moneyline_market(title):
            # Extract token ID
            tokens = row.get('clobTokenIds', [])
            if tokens:
                nfl_markets.append(tokens[0])

# Monitor them
monitor.set_tracked_markets(nfl_markets)
monitor.add_callback('spread_change', lambda d: print(f"NFL Update: {d}"))
monitor.start()
```

### Track Portfolio Performance

```python
from polymarket_orderbook import TradeManager
import plotly.express as px

manager = TradeManager()

# Add multiple positions
positions = [
    ("token1", "LONG", 100, 0.55, "Lakers ML"),
    ("token2", "SHORT", 50, 0.65, "Warriors ML"),
    ("token3", "LONG", 75, 0.48, "Chiefs ML"),
]

for token, side, size, price, name in positions:
    manager.add_position(token, side, size, price, name)

# Monitor continuously
while True:
    manager.update_positions()
    
    # Check alerts
    alerts = manager.get_position_alerts(-10.0, 20.0)
    
    # Auto-close on stop loss
    for position in alerts['stop_loss']:
        token_id = position['token_id']
        exit_price = position['current_price']
        manager.close_position(token_id, exit_price)
    
    time.sleep(60)  # Check every minute
```

## Testing

Run the comprehensive test suite:

```bash
python test_orderbook.py
```

The test suite validates:
- ✅ OrderbookClient API calls
- ✅ Sports market filtering accuracy
- ✅ Trade monitoring with callbacks
- ✅ Position management and P&L calculations

## Demo Notebook

See [sports_orderbook_demo.ipynb](sports_orderbook_demo.ipynb) for a complete interactive demonstration with visualizations.

## Rate Limiting

The package includes built-in rate limiting to respect Polymarket's API limits:
- Default delay: 0.5 seconds between requests
- Configurable via `OrderbookClient(rate_limit_delay=1.0)`
- Automatically applied to all API calls

## Data Format

All market data is returned as **Polars DataFrames** for high-performance analysis. Convert to Pandas if needed:

```python
import polars as pl

df_polars = client.get_markets()
df_pandas = df_polars.to_pandas()
```

## API Endpoints Used

- **Gamma API** (`gamma-api.polymarket.com`): Market information
- **CLOB API** (`clob.polymarket.com`): Orderbook and trade data
- **Data API** (`data-api.polymarket.com`): Historical and analytics data

## Contributing

Contributions welcome! Areas for enhancement:
- Additional sports detection patterns
- More sophisticated market categorization
- WebSocket support for real-time updates
- Integration with trading execution APIs
- Machine learning for trade signals

## License

MIT License - See LICENSE file for details

## Disclaimer

This package is for educational and research purposes. Trading prediction markets involves risk. Always do your own research and trade responsibly.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

Built with ❤️ for the Polymarket community

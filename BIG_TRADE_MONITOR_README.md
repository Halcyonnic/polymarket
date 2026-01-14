# Big Trade Monitor for Polymarket

Automatically detects and alerts on large trades across all Polymarket orderbooks in real-time.

## Features

✅ **Real-Time Monitoring** - Continuously scans all active markets
✅ **Configurable Thresholds** - Set custom size and value limits  
✅ **Multiple Alert Methods** - Print, log, or custom callbacks
✅ **Comprehensive Stats** - Track all detected big trades
✅ **Auto-Discovery** - Automatically finds all active markets
✅ **Orderbook Analysis** - Monitors large limit orders

## Quick Start

```python
from polymarket_orderbook import BigTradeMonitor, print_alert

# Create monitor
monitor = BigTradeMonitor(
    poll_interval=5.0,          # Check every 5 seconds
    size_threshold=1000.0,      # Alert on trades >= 1000 size
    value_threshold=500.0       # Alert on trades >= $500 value
)

# Add alert handler
monitor.add_alert_callback(print_alert)

# Start monitoring (auto-discovers markets)
monitor.start(auto_discover=True, market_limit=50)

# Let it run...
import time
time.sleep(60)

# Check stats
monitor.print_stats()

# View detected trades
big_trades = monitor.get_big_trades_dataframe()
print(big_trades)

# Stop when done
monitor.stop()
```

## Demo Results

Tested on 40 active Polymarket markets for 90 seconds:

```
============================================================
BIG TRADE MONITOR STATISTICS
============================================================
Markets monitored:     40
Total orders checked:  4,573
Big trades detected:   1,056
Alerts sent:           2,112
Total trade value:     $5,261,875.52
Average trade value:   $4,982.84
Max trade value:       $1,104,445.27
Uptime:                1.5 minutes
============================================================
```

## Alert Handlers

### Built-in Handlers

**Print Alert** - Displays alerts in console:
```python
from polymarket_orderbook import BigTradeMonitor, print_alert
monitor.add_alert_callback(print_alert)
```

**Log Alert** - Saves to file:
```python
from polymarket_orderbook import log_alert
monitor.add_alert_callback(lambda trade: log_alert(trade, "big_trades.log"))
```

### Custom Handlers

Create your own alert logic:

```python
def custom_alert(trade):
    """Custom alert handler."""
    value = trade.get('value', 0)
    if value > 10000:
        # Send email, SMS, webhook, etc.
        print(f"🚨 HUGE TRADE: ${value:,.2f}")
        send_email(trade)
    
monitor.add_alert_callback(custom_alert)
```

Alert data includes:
- `token_id` - Market token ID
- `question` - Market question
- `outcome` - Yes/No outcome
- `side` - BID or ASK  
- `size` - Order size
- `price` - Order price
- `value` - Total value (size * price)
- `timestamp` - Detection time
- `market_slug` - Market URL slug

## Configuration

### Thresholds

```python
# Set thresholds at creation
monitor = BigTradeMonitor(
    size_threshold=1000.0,
    value_threshold=500.0
)

# Or update later
monitor.set_thresholds(
    size_threshold=2000.0,
    value_threshold=1000.0
)
```

### Markets

```python
# Auto-discover (recommended)
monitor.start(auto_discover=True, market_limit=100)

# Or manual selection
markets = monitor.discover_all_active_markets(limit=50)
filtered_markets = [m for m in markets if m['volume'] > 10000]
monitor.set_tracked_markets(filtered_markets)
monitor.start(auto_discover=False)
```

### Polling Interval

```python
# Check every 3 seconds (faster, more data)
monitor = BigTradeMonitor(poll_interval=3.0)

# Check every 10 seconds (slower, less load)
monitor = BigTradeMonitor(poll_interval=10.0)
```

## Advanced Usage

### Filtering by Market Type

```python
# Only monitor high-volume markets
markets = monitor.discover_all_active_markets(limit=100)
high_volume = [m for m in markets if m['volume'] > 50000]
monitor.set_tracked_markets(high_volume)
```

### Multiple Monitors

Run different monitors with different settings:

```python
# Monitor for huge trades
huge_monitor = BigTradeMonitor(
    size_threshold=10000.0,
    value_threshold=5000.0
)
huge_monitor.add_alert_callback(send_sms_alert)
huge_monitor.start()

# Monitor for medium trades
medium_monitor = BigTradeMonitor(
    size_threshold=1000.0,
    value_threshold=500.0
)
medium_monitor.add_alert_callback(log_alert)
medium_monitor.start()
```

### Data Analysis

```python
# Get all detected trades
df = monitor.get_big_trades_dataframe()

# Analyze by outcome
df.group_by('outcome').agg([
    pl.count(),
    pl.col('value').sum(),
    pl.col('value').mean()
])

# Find biggest trades
df.sort('value', descending=True).head(10)

# Filter by side
buy_orders = df.filter(pl.col('side') == 'BID')
sell_orders = df.filter(pl.col('side') == 'ASK')
```

## How It Works

The monitor detects big trades by analyzing orderbooks:

1. **Market Discovery** - Fetches all active markets from Polymarket API
2. **Orderbook Scanning** - Continuously polls orderbooks for all markets
3. **Size Detection** - Identifies orders meeting size/value thresholds
4. **Deduplication** - Tracks seen orders to avoid duplicate alerts
5. **Alert Dispatch** - Calls registered callback functions
6. **Statistics** - Maintains history and metrics

### Why Orderbook vs Trades?

The Polymarket trades API requires authentication. Instead, we monitor orderbooks to detect large limit orders, which indicate significant trading intent. This provides:

- No API key required
- Real-time detection of large orders
- Insight into market depth
- Early signal before trade execution

## Example Alert

```
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔
🚨 BIG TRADE ALERT!
   Market: Will Trump deport 250,000-500,000 people?
   Outcome: Yes
   Side: ASK
   Size: 505.48
   Price: $0.9510
   Value: $480.71
   Time: 2026-01-09T23:04:08.543623
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔
```

## Performance

- Monitors 40 markets in ~20 seconds per cycle
- Checks ~2000 orders per cycle
- Minimal memory usage
- Runs efficiently in background thread

## Files Generated

- `big_trades.log` - Log file with all detected trades (if using log_alert)
- History stored in memory (up to 10,000 trades)

## Tips

1. **Start with higher thresholds** to avoid alert spam
2. **Monitor 20-50 markets** for good balance of coverage vs performance
3. **Use multiple alert handlers** for different notification methods
4. **Check stats periodically** to tune thresholds
5. **Filter by volume** to focus on active markets

## Limitations

- Requires public API access (no authentication)
- Detects limit orders, not executed trades
- Order book snapshots may miss very fast trades
- Rate limited by API (0.5s delay between requests)

## See Also

- [test_big_trade_monitor.py](test_big_trade_monitor.py) - Full test script
- [big_trade_monitor_demo.ipynb](big_trade_monitor_demo.ipynb) - Interactive notebook demo
- [polymarket_orderbook/](polymarket_orderbook/) - Source code

## License

MIT

---

**Note**: This tool is for informational purposes only. Trade at your own risk.

"""
POLYMARKET SPORTS ORDERBOOK PACKAGE - QUICK REFERENCE
======================================================

INSTALLATION
------------
Already installed! Dependencies: requests, polars

TESTING
-------
python test_orderbook.py
✅ All 4 tests passed successfully!

BASIC USAGE
-----------

1. FETCH ORDERBOOK DATA
   from polymarket_orderbook import OrderbookClient
   
   client = OrderbookClient()
   markets = client.get_markets(active=True)
   spread = client.get_spread("token_id")
   orderbook = client.get_orderbook("token_id")

2. FILTER SPORTS MARKETS
   from polymarket_orderbook import SportsMarketFilter
   
   filter = SportsMarketFilter()
   sports = filter.filter_sports_markets(markets)
   moneylines = filter.filter_moneyline_markets(markets)

3. MONITOR CONTINUOUSLY
   from polymarket_orderbook import TradeMonitor
   
   monitor = TradeMonitor(poll_interval=5.0)
   monitor.add_callback('spread_change', lambda d: print(d))
   tokens = monitor.discover_sports_moneylines(limit=10)
   monitor.set_tracked_markets(tokens)
   monitor.start()  # Runs in background
   # ... later ...
   monitor.stop()

4. MANAGE POSITIONS
   from polymarket_orderbook import TradeManager
   
   manager = TradeManager()
   manager.add_position("token", "LONG", 100, 0.55, "Market Name")
   manager.update_positions()
   alerts = manager.get_position_alerts(-10.0, 20.0)
   pnl = manager.close_position("token", 0.60)
   summary = manager.get_portfolio_summary()

DEMO NOTEBOOK
-------------
Open: sports_orderbook_demo.ipynb
Contains: Interactive examples with visualizations

KEY FILES
---------
polymarket_orderbook/
  ├── orderbook_client.py   - Fetch orderbook data
  ├── sports_filter.py      - Filter sports markets
  ├── trade_monitor.py      - Continuous monitoring
  ├── trade_manager.py      - Position tracking
  └── README.md             - Full documentation

test_orderbook.py           - Test suite
sports_orderbook_demo.ipynb - Interactive demo

FEATURES
--------
✅ Real-time orderbook fetching
✅ Sports market detection (NFL, NBA, UFC, etc.)
✅ Moneyline vs spread/total filtering
✅ Background monitoring with callbacks
✅ Position tracking with P&L
✅ Stop-loss & take-profit alerts
✅ Rate limiting built-in
✅ Polars DataFrames for performance
✅ Comprehensive tests
✅ Full documentation

SUPPORTED SPORTS
----------------
NFL, NBA, MLB, NHL, MLS, Premier League, La Liga, 
Champions League, UFC/MMA, Boxing, Tennis, Golf, 
Cricket, Rugby, F1, NASCAR, NCAA

NEXT STEPS
----------
1. Open sports_orderbook_demo.ipynb
2. Run cells to see live examples
3. Customize for your trading strategy
4. Build automated trading on top

For full API documentation, see:
polymarket_orderbook/README.md
"""

if __name__ == "__main__":
    print(__doc__)

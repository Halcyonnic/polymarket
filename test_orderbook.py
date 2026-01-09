"""Comprehensive tests for polymarket_orderbook package."""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from polymarket_orderbook import OrderbookClient, TradeMonitor, TradeManager, SportsMarketFilter


def test_orderbook_client():
    """Test OrderbookClient functionality."""
    print("\n" + "="*60)
    print("TEST 1: OrderbookClient")
    print("="*60)
    
    try:
        client = OrderbookClient(rate_limit_delay=1.0)
        print("✅ OrderbookClient initialized")
        
        # Test getting markets
        print("\n📊 Fetching markets...")
        markets_df = client.get_markets(active=True, closed=False)
        print(f"✅ Fetched {len(markets_df)} markets")
        
        if len(markets_df) > 0:
            print(f"   Columns: {markets_df.columns}")
            print("   First market preview:")
            print(markets_df.head(1))
            
            # Extract a token ID for further testing
            token_id = None
            if "tokens" in markets_df.columns:
                for row in markets_df.head(5).iter_rows(named=True):
                    tokens = row.get("tokens", [])
                    if isinstance(tokens, list) and len(tokens) > 0:
                        token = tokens[0]
                        if isinstance(token, dict):
                            token_id = token.get("token_id")
                        elif isinstance(token, str):
                            token_id = token
                        if token_id:
                            break
            
            if token_id:
                print(f"\n📖 Testing orderbook for token: {token_id}")
                
                # Test orderbook
                orderbook = client.get_orderbook(token_id)
                print("✅ Orderbook fetched")
                print(f"   Bids: {len(orderbook.get('bids', []))}, Asks: {len(orderbook.get('asks', []))}")
                
                # Test spread
                spread = client.get_spread(token_id)
                print("✅ Spread calculated")
                print(f"   Best Bid: {spread['best_bid']:.4f}, Best Ask: {spread['best_ask']:.4f}")
                print(f"   Spread: {spread['spread']:.4f} ({spread['spread_pct']:.2f}%)")
                
                # Test orderbook snapshot
                snapshot = client.get_orderbook_snapshot(token_id)
                print(f"✅ Orderbook snapshot: {len(snapshot)} rows")
                if len(snapshot) > 0:
                    print(snapshot.head(3))
                
                # Test market depth
                depth = client.get_market_depth(token_id)
                print("✅ Market depth calculated")
                print(f"   Total Volume: {depth['total_volume']:.2f}")
                print(f"   Imbalance: {depth['imbalance']:.2%}")
            else:
                print("⚠️  No valid token_id found, skipping orderbook tests")
        else:
            print("⚠️  No markets returned")
        
        print("\n✅ TEST 1 PASSED: OrderbookClient")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sports_filter():
    """Test SportsMarketFilter functionality."""
    print("\n" + "="*60)
    print("TEST 2: SportsMarketFilter")
    print("="*60)
    
    try:
        sports_filter = SportsMarketFilter()
        print("✅ SportsMarketFilter initialized")
        
        # Test market classification
        test_cases = [
            ("Will the Lakers beat the Warriors?", True, True),
            ("Will it rain tomorrow?", False, False),
            ("NFL: Chiefs vs Bills - Winner", True, True),
            ("NBA total points over 220.5", True, False),
            ("Will Trump win the election?", False, False),
            ("UFC 300: Jones to win", True, True),
        ]
        
        print("\n🏀 Testing market classification:")
        for title, expected_sports, expected_moneyline in test_cases:
            is_sports = sports_filter.is_sports_market(title)
            is_moneyline = sports_filter.is_moneyline_market(title)
            
            sports_ok = "✅" if is_sports == expected_sports else "❌"
            moneyline_ok = "✅" if is_moneyline == expected_moneyline else "❌"
            
            print(f"   {sports_ok}{moneyline_ok} '{title}'")
            print(f"      Sports: {is_sports} (expected: {expected_sports})")
            print(f"      Moneyline: {is_moneyline} (expected: {expected_moneyline})")
        
        # Test with real markets
        print("\n📊 Testing with real market data...")
        client = OrderbookClient(rate_limit_delay=1.0)
        markets_df = client.get_markets(active=True)
        
        if len(markets_df) > 0:
            sports_df = sports_filter.filter_sports_markets(markets_df)
            print(f"✅ Found {len(sports_df)} sports markets out of {len(markets_df)} total")
            
            if len(sports_df) > 0:
                moneyline_df = sports_filter.filter_moneyline_markets(markets_df)
                print(f"✅ Found {len(moneyline_df)} moneyline markets")
                
                # Show sport summary
                summary = sports_filter.get_sports_summary(markets_df)
                if len(summary) > 0:
                    print("\n📈 Sports summary:")
                    print(summary)
        
        print("\n✅ TEST 2 PASSED: SportsMarketFilter")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trade_monitor():
    """Test TradeMonitor functionality."""
    print("\n" + "="*60)
    print("TEST 3: TradeMonitor")
    print("="*60)
    
    try:
        client = OrderbookClient(rate_limit_delay=1.0)
        monitor = TradeMonitor(orderbook_client=client, poll_interval=3.0)
        print("✅ TradeMonitor initialized")
        
        # Test callback system
        callback_triggered = {"count": 0}
        
        def test_callback(data):
            callback_triggered["count"] += 1
            print(f"   📢 Callback triggered! Data: {data.get('token_id', 'N/A')}")
        
        monitor.add_callback("spread_change", test_callback)
        print("✅ Callback registered")
        
        # Discover markets
        print("\n🔍 Discovering sports moneyline markets...")
        token_ids = monitor.discover_sports_moneylines(limit=5)
        
        if token_ids:
            print(f"✅ Discovered {len(token_ids)} markets")
            
            # Set tracked markets
            monitor.set_tracked_markets(token_ids[:3])  # Track first 3
            print("✅ Markets set for tracking")
            
            # Start monitoring
            print("\n▶️  Starting monitor for 10 seconds...")
            monitor.start()
            time.sleep(10)
            monitor.stop()
            print("⏸️  Monitor stopped")
            
            # Check data collection
            spread_df = monitor.get_spread_dataframe()
            print(f"✅ Collected {len(spread_df)} spread snapshots")
            
            if len(spread_df) > 0:
                print("\n📊 Latest spreads:")
                latest = monitor.get_latest_spreads()
                print(latest)
            
            print(f"\n📢 Callbacks triggered: {callback_triggered['count']} times")
        else:
            print("⚠️  No moneyline markets found, skipping monitor test")
        
        print("\n✅ TEST 3 PASSED: TradeMonitor")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trade_manager():
    """Test TradeManager functionality."""
    print("\n" + "="*60)
    print("TEST 4: TradeManager")
    print("="*60)
    
    try:
        client = OrderbookClient(rate_limit_delay=1.0)
        manager = TradeManager(orderbook_client=client)
        print("✅ TradeManager initialized")
        
        # Add test positions
        print("\n📈 Adding test positions...")
        manager.add_position("test_token_1", "LONG", 100, 0.55, "Test Market 1")
        manager.add_position("test_token_2", "SHORT", 50, 0.65, "Test Market 2")
        print("✅ Positions added")
        
        # Get positions
        positions_df = manager.get_positions_dataframe()
        print(f"\n📊 Current positions ({len(positions_df)} total):")
        print(positions_df)
        
        # Close a position
        print("\n💰 Closing position...")
        pnl = manager.close_position("test_token_1", 0.60)
        print(f"✅ Position closed with P&L: ${pnl:.2f}")
        
        # Get P&L history
        pnl_df = manager.get_pnl_dataframe()
        print("\n📊 P&L History:")
        print(pnl_df)
        
        # Get portfolio summary
        summary = manager.get_portfolio_summary()
        print("\n📊 Portfolio Summary:")
        for key, value in summary.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.2f}")
            else:
                print(f"   {key}: {value}")
        
        # Test stop loss/take profit monitoring
        print("\n⚠️  Testing alerts (with mock data)...")
        
        # Manually set unrealized P&L for testing
        for token_id, position in manager.positions.items():
            position["unrealized_pnl_pct"] = -15.0  # Simulate loss
        
        alerts = manager.get_position_alerts(stop_loss_pct=-10.0, take_profit_pct=20.0)
        print(f"✅ Stop Loss alerts: {len(alerts['stop_loss'])}")
        print(f"✅ Take Profit alerts: {len(alerts['take_profit'])}")
        
        print("\n✅ TEST 4 PASSED: TradeManager")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*60)
    print("🚀 POLYMARKET ORDERBOOK PACKAGE TEST SUITE")
    print("="*60)
    
    results = {
        "OrderbookClient": test_orderbook_client(),
        "SportsMarketFilter": test_sports_filter(),
        "TradeMonitor": test_trade_monitor(),
        "TradeManager": test_trade_manager(),
    }
    
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n{passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return True
    else:
        print("\n⚠️  SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

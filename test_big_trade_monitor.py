"""Quick test of Big Trade Monitor functionality."""

import time

from polymarket_orderbook.big_trade_monitor import (
    BigTradeMonitor,
    log_alert,
    print_alert,
)


def main():
    print("=" * 70)
    print("BIG TRADE MONITOR - QUICK TEST")
    print("=" * 70)

    # Create monitor
    print("\n1️⃣  Creating monitor...")
    monitor = BigTradeMonitor(
        poll_interval=5.0, size_threshold=100 * 1000.0, value_threshold=1000.0
    )
    print("✅ Monitor created")

    # Add alert callbacks
    print("\n2️⃣  Adding alert callbacks...")
    monitor.add_alert_callback(print_alert)
    monitor.add_alert_callback(lambda t: log_alert(t, "test_big_trades.log"))
    print("✅ Alert callbacks added")

    # Discover markets
    print("\n3️⃣  Discovering active markets...")
    markets = monitor.discover_all_active_markets(limit=100)

    if not markets:
        print("❌ No markets found. Cannot continue test.")
        return

    print(f"✅ Found {len(markets)} markets")
    print("\nSample markets:")
    for i, market in enumerate(markets[:3]):
        print(f"   {i + 1}. {market.get('question', 'N/A')[:60]}...")

    # Start monitoring
    print("\n4️⃣  Starting monitor...")
    monitor.set_tracked_markets(markets)
    monitor.start(auto_discover=False)
    print("✅ Monitor started\n")

    # Run for 90 seconds
    print("🔍 Monitoring for 90 seconds...")
    print("   (Watch for big trade alerts)\n")

    for i in range(6):
        time.sleep(15)
        stats = monitor.get_stats()
        print(
            f"   [{i * 15 + 15}s] Trades checked: {stats['total_trades_checked']}, "
            f"Big trades: {stats['big_trades_detected']}"
        )

    # Stop and show results
    print("\n5️⃣  Stopping monitor...")
    monitor.stop()
    print("✅ Monitor stopped\n")

    # Show final stats
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    monitor.print_stats()

    # Show detected trades
    big_trades_df = monitor.get_big_trades_dataframe()
    if len(big_trades_df) > 0:
        print(f"\n📊 Detected {len(big_trades_df)} big trades:\n")

        # Show summary columns
        display_cols = ["timestamp", "side", "size", "price", "value", "outcome"]
        available_cols = [col for col in display_cols if col in big_trades_df.columns]
        print(big_trades_df.select(available_cols))

        # Show value stats
        if "value" in big_trades_df.columns:
            print(f"\n💰 Total trade value: ${big_trades_df['value'].sum():,.2f}")
            print(f"💰 Average trade value: ${big_trades_df['value'].mean():,.2f}")
            print(f"💰 Max trade value: ${big_trades_df['value'].max():,.2f}")
    else:
        print("\n⏳ No big trades detected during this test run.")
        print("\nPossible reasons:")
        print("  - Markets may not be very active right now")
        print("  - Thresholds may be too high")
        print("  - Need to monitor for longer period")
        print("\nTry:")
        print(
            "  - Lowering thresholds: monitor.set_thresholds(size_threshold=50, value_threshold=25)"
        )
        print("  - Running for longer: monitor longer durations")
        print(
            "  - Adding more markets: increase limit in discover_all_active_markets()"
        )

    print("\n" + "=" * 70)
    print("TEST COMPLETE ✅")
    print("=" * 70)


if __name__ == "__main__":
    main()
    print("TEST COMPLETE ✅")
    print("=" * 70)


if __name__ == "__main__":
    main()

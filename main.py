"""
Main entry point for Backtest XAUUSD DCA Strategy
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.strategy_config import StrategyConfig
from src.utils.data_loader import DataLoader
from src.strategy.dca_strategy import DCAStrategy
from src.backtest.portfolio import Portfolio
from src.backtest.engine import BacktestEngine


def main():
    print("Backtest XAUUSD - DCA Gồng Lệnh Strategy")
    print("=" * 50)

    # Load configuration
    try:
        config = StrategyConfig("configs/default_config.json")
        print("DEBUG CONFIG FILE: configs/default_config.json")
        print("DEBUG entry_range.trade =", config.get("strategy.entry_range.trade"))
        print("DEBUG entry_range.count_only =", config.get("strategy.entry_range.count_only"))
        print("✅ Configuration loaded")
    except Exception as e:
        print(f"⚠️  Config error: {e}")
        print("   Using default config")
        config = None

    # Load or download data
    loader = DataLoader()

    data_file = config.get("data.data_file", "data/raw/xauusd_h1.csv") if config else "data/raw/xauusd_h1.csv"

    # Check if data file exists
    if not Path(data_file).exists():
        print(f"\n⚠️  Data file not found: {data_file}")
        print("📥 Attempting auto-download from available sources...")

        try:
            df = loader.auto_download(
                symbol="XAUUSD",
                timeframe=config.get("data.timeframe", "H1") if config else "H1",
                period="1y",
                output_path=data_file
            )
            print("✅ Data downloaded successfully!")
        except Exception as e:
            print(f"❌ Auto-download failed: {e}")
            return
    else:
        print(f"\n📂 Loading data from: {data_file}")
        try:
            df = loader.load_csv(data_file, source="auto")
            print(f"✅ Data loaded: {len(df)} rows")
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return

    # Initialize components
    print("\n🔧 Initializing components...")

    # Portfolio config
    portfolio_config = config.get("portfolio", {}) if config else {}

    initial_capital = portfolio_config.get("initial_capital", 10000)
    portfolio = Portfolio(initial_capital=initial_capital)
    print(f"✅ Portfolio initialized (Capital: ${initial_capital:,.2f})")

    # ✅ IMPORTANT FIX: pass ROOT config to strategy
    strategy = DCAStrategy(config if config else {})
    print("✅ Strategy initialized")

    # Initialize backtest engine
    engine = BacktestEngine(
        config=config if config else {},
        data=df,
        strategy=strategy,
        portfolio=portfolio
    )
    print("✅ Backtest engine initialized")

    # Hiển thị ngưỡng RSI đang sử dụng
    rsi_buy = strategy.rsi_entry_buy if hasattr(strategy, 'rsi_entry_buy') else config.get("strategy.rsi_entry_threshold.buy", 30) if config else 30
    rsi_sell = strategy.rsi_entry_sell if hasattr(strategy, 'rsi_entry_sell') else config.get("strategy.rsi_entry_threshold.sell", 70) if config else 70
    
    print("\n" + "=" * 50)
    print("📊 NGƯỠNG RSI ĐANG SỬ DỤNG:")
    print("=" * 50)
    print(f"   🟢 LỆNH MUA (BUY): RSI <= {rsi_buy}")
    print(f"   🔴 LỆNH BÁN (SELL): RSI >= {rsi_sell}")
    print("=" * 50)
    
    # Run backtest
    print("\n🚀 Running backtest...")
    print("   This may take a moment...")
    results = engine.run()

    # Generate and display report
    print("\n" + "=" * 50)
    print("📊 BACKTEST RESULTS")
    print("=" * 50)

    report = engine.generate_report()
    summary = report["summary"]

    print(f"\n📈 Summary:")
    print(f"   Total Entries: {summary['total_entries']}")
    print(f"   Total Trades: {summary['total_trades']}")
    print(f"   Total P&L: ${summary['total_pnl']:,.2f}")
    print(f"   Win Rate: {summary['win_rate']}")
    print(f"   Max Drawdown: {summary['max_drawdown']}")
    print(f"   Total Return: {summary['total_return']}")
    print(f"   Initial Capital: ${summary['initial_capital']:,.2f}")
    print(f"   Final Equity: ${summary['final_equity']:,.2f}")
    print(f"   Total Cycles: {results['total_cycles']}")
    
    # Hiển thị thống kê BUY/SELL
    buy_entries = results.get('buy_entries', 0)
    sell_entries = results.get('sell_entries', 0)
    buy_trades = results.get('buy_trades', 0)
    sell_trades = results.get('sell_trades', 0)
    
    print(f"\n📊 Phân tích Lệnh Mua/Bán:")
    print(f"   🟢 LỆNH MUA (BUY):")
    print(f"      - Số entry: {buy_entries}")
    print(f"      - Số lệnh thực tế: {buy_trades}")
    print(f"   🔴 LỆNH BÁN (SELL):")
    print(f"      - Số entry: {sell_entries}")
    print(f"      - Số lệnh thực tế: {sell_trades}")

    # Show entry details (first 10 entries) với thông tin ngưỡng
    entry_events = [e for e in report["events"] if e["type"] == "entry"]
    if entry_events:
        print(f"\n📋 Entry Details (showing first 10):")
        for i, event in enumerate(entry_events[:10], 1):
            trade_marker = "💰" if event.get("should_trade", False) else "📊"
            direction = event.get('direction', '')
            rsi_val = event.get('rsi', 0)
            
            # Hiển thị ngưỡng tương ứng
            if direction == "BUY":
                threshold_info = f"RSI: {rsi_val:.2f} (threshold: <= {rsi_buy} for BUY)"
            elif direction == "SELL":
                threshold_info = f"RSI: {rsi_val:.2f} (threshold: >= {rsi_sell} for SELL)"
            else:
                threshold_info = f"RSI: {rsi_val:.2f}"
            
            print(
                f"   {trade_marker} Entry {event['entry_number']}: "
                f"{event['timestamp']} | Price: ${event['price']:.2f} | "
                f"{threshold_info} | {direction}"
            )

        if len(entry_events) > 10:
            print(f"   ... and {len(entry_events) - 10} more entries")

    print("\n" + "=" * 50)
    print("✅ Backtest completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()

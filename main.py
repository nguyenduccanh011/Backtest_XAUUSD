"""
Main entry point for Backtest XAUUSD DCA Strategy
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.strategy_config import StrategyConfig
from src.utils.data_loader import DataLoader
from src.strategy.rsi_handler import RSIHandler
from src.strategy.dca_strategy import DCAStrategy
from src.backtest.portfolio import Portfolio
from src.backtest.engine import BacktestEngine


def main():
    """
    Main function to run backtest.
    """
    print("Backtest XAUUSD - DCA Gồng Lệnh Strategy")
    print("=" * 50)
    
    # Load configuration
    try:
        config = StrategyConfig("configs/default_config.json")
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
            # Auto download
            df = loader.auto_download(
                symbol="XAUUSD",
                timeframe=config.get("data.timeframe", "H1") if config else "H1",
                period="1y",
                output_path=data_file
            )
            print("✅ Data downloaded successfully!")
        except Exception as e:
            print(f"❌ Auto-download failed: {e}")
            print("\n💡 Please download data manually:")
            print("   - Run: python scripts/auto_download_data.py")
            print("   - Or download from HistData.com")
            print("   - See: docs/DATA_SOURCE_TROUBLESHOOTING.md")
            return
    else:
        # Load existing data
        print(f"\n📂 Loading data from: {data_file}")
        try:
            df = loader.load_csv(data_file, source="auto")
            print(f"✅ Data loaded: {len(df)} rows")
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return
    
    # TODO: Continue with backtest execution
    # 3. Initialize strategy and portfolio
    # 4. Run backtest
    # 5. Generate report
    
    print("\n📊 Data ready for backtest!")
    print(f"   Date range: {df.index.min()} to {df.index.max()}")
    print("\n💡 Next steps:")
    print("   - Implement strategy logic")
    print("   - Run backtest engine")
    print("   - Generate reports")


if __name__ == "__main__":
    main()


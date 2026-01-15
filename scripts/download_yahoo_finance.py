"""
Script để download XAUUSD H1 data từ Yahoo Finance
Yêu cầu: pip install yfinance
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    print("❌ yfinance not installed.")
    print("   Install with: pip install yfinance")
    sys.exit(1)


def download_from_yahoo_finance(symbol="GC=F", period="1y", interval="1h",
                                output_path="data/raw/xauusd_h1.csv"):
    """
    Download XAUUSD data from Yahoo Finance.
    
    Args:
        symbol: Symbol to download
            - "GC=F" (Gold Futures) - Recommended, most reliable
            - "XAUUSD=X" (XAUUSD) - May not work
        period: Period (1y, 2y, 5y, etc.)
        interval: Interval (1h for H1, 1d for D1)
        output_path: Output CSV file path
    """
    print("=" * 60)
    print("Yahoo Finance - XAUUSD Data Downloader")
    print("=" * 60)
    
    print(f"\n📥 Downloading {symbol} {interval} data from Yahoo Finance...")
    print(f"   Period: {period}")
    print(f"   Interval: {interval}")
    
    try:
        # Download data
        data = yf.download(symbol, period=period, interval=interval, progress=False)
        
        if data.empty:
            print(f"\n❌ No data received for {symbol}")
            print("   Try with different symbol: GC=F (Gold Futures)")
            return False
        
        # Normalize format
        data = data.reset_index()
        
        # Rename columns
        data.columns = [col.lower() if col != 'Date' else 'timestamp' for col in data.columns]
        if 'date' in data.columns:
            data.rename(columns={'date': 'timestamp'}, inplace=True)
        
        # Select required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close']
        if 'volume' in data.columns:
            required_cols.append('volume')
        
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            print(f"\n❌ Missing columns: {missing_cols}")
            return False
        
        data = data[required_cols]
        
        # Remove any rows with missing values
        data = data.dropna()
        
        # Save to CSV
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(output_path, index=False)
        
        print(f"\n✅ Data saved to {output_path}")
        print(f"   Rows: {len(data)}")
        print(f"   Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")
        print(f"   Price range: {data['low'].min():.2f} - {data['high'].max():.2f}")
        
        # Show sample
        print(f"\n📊 Sample data (first 5 rows):")
        print(data.head())
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error downloading from Yahoo Finance: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    
    # Try different symbols
    symbols = [
        ("GC=F", "Gold Futures - Recommended"),
        ("XAUUSD=X", "XAUUSD (may not work)")
    ]
    
    for symbol, description in symbols:
        print(f"\n{'='*60}")
        print(f"Trying: {symbol} ({description})")
        print(f"{'='*60}")
        
        success = download_from_yahoo_finance(
            symbol=symbol,
            period="1y",
            interval="1h",
            output_path="data/raw/xauusd_h1.csv"
        )
        
        if success:
            print("\n✅ Download completed successfully!")
            print("   You can now use this data for backtesting.")
            print("\n💡 Note: GC=F (Gold Futures) price is very similar to XAUUSD")
            print("   The data is suitable for backtesting your strategy.")
            break
    else:
        print("\n❌ Could not download from Yahoo Finance.")
        print("\n💡 Alternative options:")
        print("   1. Use HistData.com (requires registration)")
        print("   2. Use VPN + Dukascopy")
        print("   3. Use MetaTrader 4/5 if you have it")


if __name__ == "__main__":
    main()






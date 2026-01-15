"""
Script để download sample data từ các nguồn miễn phí
(Optional - có thể dùng để tự động hóa việc download)
"""

import pandas as pd
from pathlib import Path
import requests
from datetime import datetime, timedelta


def download_from_dukascopy(symbol="XAUUSD", timeframe="H1", start_date=None, end_date=None, output_path="data/raw/xauusd_h1.csv"):
    """
    Download data từ Dukascopy (cần implement logic download).
    
    Lưu ý: Dukascopy có thể yêu cầu format URL đặc biệt.
    Tham khảo: https://www.dukascopy.com/swiss/english/marketwatch/historical/
    
    Args:
        symbol: Symbol (XAUUSD)
        timeframe: Timeframe (H1, H4, D1)
        start_date: Start date (datetime)
        end_date: End date (datetime)
        output_path: Output file path
    """
    # TODO: Implement Dukascopy download logic
    # Có thể cần sử dụng thư viện như: dukascopy-tick-downloader
    print("Dukascopy download - TODO: Implement")
    pass


def download_from_yahoo_finance(symbol="GC=F", period="1y", interval="1h", output_path="data/raw/xauusd_h1.csv"):
    """
    Download data từ Yahoo Finance (cần cài yfinance).
    
    Lưu ý: Yahoo Finance có thể không có XAUUSD trực tiếp.
    Thử với "GC=F" (Gold Futures) hoặc "XAUUSD=X"
    
    Args:
        symbol: Symbol (GC=F cho Gold Futures)
        period: Period (1y, 2y, etc.)
        interval: Interval (1h, 1d, etc.)
        output_path: Output file path
    """
    try:
        import yfinance as yf
        
        print(f"Downloading {symbol} from Yahoo Finance...")
        data = yf.download(symbol, period=period, interval=interval)
        
        if data.empty:
            print(f"Warning: No data found for {symbol}")
            return False
        
        # Reset index để có timestamp column
        data = data.reset_index()
        
        # Rename columns
        data.columns = [col.lower() if col != 'Date' else 'timestamp' for col in data.columns]
        if 'date' in data.columns:
            data.rename(columns={'date': 'timestamp'}, inplace=True)
        
        # Select required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close']
        if 'volume' in data.columns:
            required_cols.append('volume')
        
        data = data[required_cols]
        
        # Save to CSV
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(output_path, index=False)
        
        print(f"✅ Data saved to {output_path}")
        print(f"   Rows: {len(data)}")
        print(f"   Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")
        
        return True
        
    except ImportError:
        print("❌ yfinance not installed. Install with: pip install yfinance")
        return False
    except Exception as e:
        print(f"❌ Error downloading from Yahoo Finance: {e}")
        return False


def convert_metatrader_csv(input_path, output_path="data/raw/xauusd_h1.csv"):
    """
    Convert MetaTrader CSV format to project format.
    
    Args:
        input_path: Path to MT4/MT5 CSV file
        output_path: Output file path
    """
    # TODO: Implement MT4/MT5 CSV conversion
    print("MetaTrader CSV conversion - TODO: Implement")
    pass


def main():
    """
    Main function - chọn nguồn download.
    """
    print("=" * 50)
    print("XAUUSD Data Downloader")
    print("=" * 50)
    print("\nAvailable sources:")
    print("1. Yahoo Finance (yfinance) - Requires: pip install yfinance")
    print("2. Dukascopy - Manual download recommended")
    print("3. TradingView - Manual export recommended")
    print("\nFor manual download, see DATA_SOURCES.md")
    print("\n" + "=" * 50)
    
    # Example: Try Yahoo Finance
    choice = input("\nTry Yahoo Finance download? (y/n): ").lower()
    if choice == 'y':
        # Try different symbols
        symbols = ["GC=F", "XAUUSD=X"]
        for symbol in symbols:
            print(f"\nTrying {symbol}...")
            if download_from_yahoo_finance(symbol=symbol, period="1y", interval="1h"):
                break
        else:
            print("\n❌ Could not download from Yahoo Finance.")
            print("   Please download manually from Dukascopy or TradingView.")
            print("   See DATA_SOURCES.md for instructions.")


if __name__ == "__main__":
    main()






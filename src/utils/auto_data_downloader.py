"""
Auto Data Downloader - Tự động chọn và download từ nguồn có thể truy cập được ở Việt Nam
"""

import sys
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import pandas as pd


class AutoDataDownloader:
    """
    Tự động detect và download data từ các nguồn có thể truy cập được ở Việt Nam.
    Thử các nguồn theo thứ tự ưu tiên.
    """
    
    def __init__(self, symbol="XAUUSD", timeframe="H1", period="1y"):
        """
        Initialize auto downloader.
        
        Args:
            symbol: Symbol (XAUUSD)
            timeframe: Timeframe (H1, H4, D1)
            period: Period (1y, 2y, etc.)
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.period = period
        self.downloaded_source = None
        self.downloaded_data = None
    
    def download(self, output_path: str = "data/raw/xauusd_h1.csv") -> Optional[pd.DataFrame]:
        """
        Tự động download từ nguồn có thể truy cập được.
        
        Thử các nguồn theo thứ tự:
        1. Yahoo Finance (Python) - Khuyến nghị nhất cho Việt Nam
        2. HistData - Nếu có credentials
        3. TradingView - Chỉ cho D1
        
        Args:
            output_path: Path to save CSV file
            
        Returns:
            pandas.DataFrame: Downloaded data, or None if all sources fail
        """
        print("=" * 60)
        print("Auto Data Downloader - Tự Động Chọn Nguồn Dữ Liệu")
        print("=" * 60)
        print(f"Symbol: {self.symbol}")
        print(f"Timeframe: {self.timeframe}")
        print(f"Period: {self.period}")
        print()
        
        # List of download methods to try (in priority order)
        download_methods = [
            ("Yahoo Finance", self._download_yahoo_finance),
            ("HistData", self._download_histdata),
            ("TradingView", self._download_tradingview),
        ]
        
        # Try each source
        for source_name, download_func in download_methods:
            print(f"🔄 Thử nguồn: {source_name}...")
            
            try:
                df = download_func()
                
                if df is not None and not df.empty:
                    # Save to CSV
                    output_path = Path(output_path)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    df_reset = df.reset_index() if df.index.name == 'timestamp' else df
                    if 'timestamp' not in df_reset.columns and df.index.name == 'timestamp':
                        df_reset['timestamp'] = df.index
                    
                    df_reset.to_csv(output_path, index=False)
                    
                    self.downloaded_source = source_name
                    self.downloaded_data = df
                    
                    print(f"\n✅ Thành công với {source_name}!")
                    print(f"   Rows: {len(df)}")
                    print(f"   Date range: {df.index.min()} to {df.index.max()}")
                    print(f"   Saved to: {output_path}")
                    
                    return df
                else:
                    print(f"   ⚠️  {source_name}: Không có dữ liệu")
                    
            except Exception as e:
                print(f"   ❌ {source_name}: {str(e)}")
                continue
        
        # All sources failed
        print("\n❌ Không thể download từ bất kỳ nguồn nào!")
        print("\n💡 Giải pháp:")
        print("   1. Kiểm tra kết nối internet")
        print("   2. Thử download thủ công từ HistData.com")
        print("   3. Sử dụng VPN và thử lại")
        
        return None
    
    def _download_yahoo_finance(self) -> Optional[pd.DataFrame]:
        """
        Download từ Yahoo Finance (khuyến nghị nhất cho Việt Nam).
        
        Returns:
            pandas.DataFrame or None
        """
        try:
            import yfinance as yf
        except ImportError:
            print("      ⚠️  yfinance not installed. Install with: pip install yfinance")
            return None
        
        # Map timeframe to yfinance interval
        interval_map = {
            "H1": "1h",
            "H4": "4h",
            "D1": "1d",
            "M15": "15m",
            "M30": "30m"
        }
        
        interval = interval_map.get(self.timeframe, "1h")
        
        # Try different symbols
        symbols = ["GC=F", "XAUUSD=X"]  # Gold Futures, XAUUSD
        
        for symbol in symbols:
            try:
                print(f"      Đang thử {symbol}...")
                data = yf.download(symbol, period=self.period, interval=interval, progress=False)
                
                if not data.empty:
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
                    
                    missing = [col for col in required_cols if col not in data.columns]
                    if missing:
                        continue
                    
                    data = data[required_cols].dropna()
                    
                    # Set timestamp as index
                    data['timestamp'] = pd.to_datetime(data['timestamp'])
                    data.set_index('timestamp', inplace=True)
                    data.sort_index(inplace=True)
                    
                    return data
                    
            except Exception as e:
                print(f"      ⚠️  {symbol}: {str(e)}")
                continue
        
        return None
    
    def _download_histdata(self) -> Optional[pd.DataFrame]:
        """
        Download từ HistData (cần credentials hoặc manual download).
        
        Returns:
            pandas.DataFrame or None
        """
        # HistData requires manual download or API credentials
        # For now, just check if file exists
        print("      ⚠️  HistData requires manual download")
        print("      💡 Please download from https://www.histdata.com/")
        print("      💡 Then use DataLoader.load_csv() to load the file")
        return None
    
    def _download_tradingview(self) -> Optional[pd.DataFrame]:
        """
        Download từ TradingView (chỉ D1, không có H1).
        
        Returns:
            pandas.DataFrame or None
        """
        if self.timeframe != "D1":
            print(f"      ⚠️  TradingView chỉ hỗ trợ D1, không có {self.timeframe}")
            return None
        
        # TradingView requires manual export
        print("      ⚠️  TradingView requires manual export")
        print("      💡 Please export from https://www.tradingview.com/")
        print("      💡 Then use DataLoader.load_csv() to load the file")
        return None
    
    def get_downloaded_source(self) -> Optional[str]:
        """Get the source that was successfully used."""
        return self.downloaded_source
    
    def get_downloaded_data(self) -> Optional[pd.DataFrame]:
        """Get the downloaded data."""
        return self.downloaded_data


def auto_download_xauusd(timeframe="H1", period="1y", output_path="data/raw/xauusd_h1.csv"):
    """
    Convenience function để tự động download XAUUSD data.
    
    Args:
        timeframe: Timeframe (H1, H4, D1)
        period: Period (1y, 2y, etc.)
        output_path: Output CSV path
        
    Returns:
        pandas.DataFrame or None
    """
    downloader = AutoDataDownloader(
        symbol="XAUUSD",
        timeframe=timeframe,
        period=period
    )
    
    return downloader.download(output_path)


if __name__ == "__main__":
    # Test auto download
    df = auto_download_xauusd(timeframe="H1", period="1y")
    
    if df is not None:
        print("\n✅ Download thành công!")
        print(f"   Source: {AutoDataDownloader().get_downloaded_source()}")
    else:
        print("\n❌ Download thất bại!")








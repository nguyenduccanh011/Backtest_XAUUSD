"""
Script tự động download XAUUSD data từ nguồn có thể truy cập được ở Việt Nam
Chạy: python scripts/auto_download_data.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.utils.auto_data_downloader import auto_download_xauusd


def main():
    """Main function."""
    print("=" * 60)
    print("Auto Data Downloader - Tự Động Tải Dữ Liệu XAUUSD")
    print("=" * 60)
    print("\nHệ thống sẽ tự động thử các nguồn có thể truy cập được ở Việt Nam:")
    print("  1. Yahoo Finance (Python) - Khuyến nghị nhất")
    print("  2. HistData - Nếu có credentials")
    print("  3. TradingView - Chỉ cho D1")
    print()
    
    # Configuration
    timeframe = "H1"  # 1 hour
    period = "1y"     # 1 year
    output_path = "data/raw/xauusd_h1.csv"
    
    print(f"📥 Đang download XAUUSD {timeframe} data...")
    print(f"   Period: {period}")
    print(f"   Output: {output_path}")
    print()
    
    # Auto download
    df = auto_download_xauusd(
        timeframe=timeframe,
        period=period,
        output_path=output_path
    )
    
    if df is not None:
        print("\n" + "=" * 60)
        print("✅ Download thành công!")
        print("=" * 60)
        print(f"\n📊 Thông tin dữ liệu:")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {df.columns.tolist()}")
        print(f"   Date range: {df.index.min()} to {df.index.max()}")
        
        if len(df) > 0:
            print(f"   Price range: {df['low'].min():.2f} - {df['high'].max():.2f}")
        
        print(f"\n💾 File đã được lưu tại: {output_path}")
        print("\n💡 Bước tiếp theo:")
        print("   - Test data: python test_dukascopy.py")
        print("   - Sử dụng trong backtest engine")
        
    else:
        print("\n" + "=" * 60)
        print("❌ Download thất bại!")
        print("=" * 60)
        print("\n💡 Giải pháp:")
        print("   1. Kiểm tra kết nối internet")
        print("   2. Cài đặt yfinance: pip install yfinance")
        print("   3. Download thủ công từ HistData.com")
        print("   4. Xem hướng dẫn: docs/DATA_SOURCE_TROUBLESHOOTING.md")
        
        sys.exit(1)


if __name__ == "__main__":
    main()








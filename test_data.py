"""
Test script đơn giản để kiểm tra dữ liệu
Chạy: python test_data.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.data_loader import DataLoader


def main():
    """Test data loading."""
    print("=" * 60)
    print("Test Dữ Liệu XAUUSD")
    print("=" * 60)
    
    loader = DataLoader()
    data_file = "data/raw/xauusd_h1.csv"
    
    # Check file exists
    if not Path(data_file).exists():
        print(f"\n❌ File không tìm thấy: {data_file}")
        print("\n💡 Hãy download dữ liệu trước:")
        print("   1. pip install yfinance")
        print("   2. python scripts/auto_download_data.py")
        return False
    
    try:
        # Load data
        print(f"\n📂 Đang load: {data_file}")
        df = loader.load_csv(data_file, source="auto")
        
        print("\n✅ Load thành công!")
        print(f"   Số nến: {len(df)}")
        print(f"   Cột: {df.columns.tolist()}")
        print(f"   Khoảng thời gian: {df.index.min()} đến {df.index.max()}")
        
        if len(df) > 0:
            print(f"   Giá thấp nhất: {df['low'].min():.2f}")
            print(f"   Giá cao nhất: {df['high'].max():.2f}")
        
        # Validate
        print("\n🔍 Đang kiểm tra dữ liệu...")
        loader.validate_data(df)
        print("   ✅ Dữ liệu hợp lệ!")
        
        # Show sample
        print("\n📊 Mẫu dữ liệu (5 dòng đầu):")
        print(df.head())
        
        print("\n" + "=" * 60)
        print("✅ Tất cả kiểm tra đều pass!")
        print("=" * 60)
        print("\n💡 Bạn có thể sử dụng dữ liệu này cho backtest!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)




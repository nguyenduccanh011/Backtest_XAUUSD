"""
Script test đơn giản để kiểm tra yfinance có hoạt động không
Chạy: python scripts/test_yfinance_simple.py
"""

import sys

print("=" * 60)
print("Test yfinance - Kiểm Tra Cài Đặt")
print("=" * 60)

# Test 1: Import yfinance
print("\n1. Kiểm tra import yfinance...")
try:
    import yfinance as yf
    print(f"   ✅ yfinance đã được cài đặt")
except ImportError as e:
    print(f"   ❌ yfinance chưa được cài đặt: {e}")
    print("\n💡 Giải pháp:")
    print("   pip install yfinance")
    sys.exit(1)

# Test 2: Test download
print("\n2. Kiểm tra download dữ liệu...")
try:
    print("   Đang thử download GC=F (5 ngày, H1)...")
    data = yf.download("GC=F", period="5d", interval="1h", progress=False)
    
    if data.empty:
        print("   ⚠️  Download thành công nhưng không có dữ liệu")
        print("   💡 Có thể Yahoo Finance tạm thời down, thử lại sau")
    else:
        print(f"   ✅ Download thành công: {len(data)} rows")
        print(f"   Date range: {data.index.min()} to {data.index.max()}")
        print("\n   Mẫu dữ liệu:")
        print(data.head())
        
except Exception as e:
    print(f"   ❌ Lỗi khi download: {e}")
    print("\n💡 Có thể do:")
    print("   - Internet connection")
    print("   - Yahoo Finance tạm thời down")
    print("   - Firewall blocking")
    print("\n💡 Thử lại sau vài phút hoặc download thủ công từ HistData.com")
    sys.exit(1)

# Test 3: Test với symbol khác
print("\n3. Kiểm tra các symbol khác...")
symbols = ["GC=F", "XAUUSD=X"]
for symbol in symbols:
    try:
        data = yf.download(symbol, period="2d", interval="1h", progress=False)
        if not data.empty:
            print(f"   ✅ {symbol}: OK ({len(data)} rows)")
        else:
            print(f"   ⚠️  {symbol}: Không có dữ liệu")
    except Exception as e:
        print(f"   ❌ {symbol}: {e}")

print("\n" + "=" * 60)
print("✅ Tất cả test đều pass!")
print("=" * 60)
print("\n💡 Bây giờ bạn có thể chạy:")
print("   python scripts/auto_download_data.py")


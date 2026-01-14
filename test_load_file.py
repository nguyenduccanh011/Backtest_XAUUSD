"""Quick test to load the new CSV file"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.data_loader import DataLoader

try:
    loader = DataLoader()
    df = loader.load_csv('data/raw/xauusd_h1.csv', source='auto')
    print(f"✅ Load thành công!")
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {df.columns.tolist()}")
    print(f"   Date range: {df.index.min()} to {df.index.max()}")
    print(f"\n   Sample data:")
    print(df.head())
    print("\n✅ File hợp lệ, có thể commit!")
except Exception as e:
    print(f"❌ Lỗi: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


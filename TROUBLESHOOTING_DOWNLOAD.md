# ⚠️ Xử Lý Sự Cố - Không Tải Được Dữ Liệu

Hướng dẫn xử lý các lỗi thường gặp khi download dữ liệu.

---

## 🔴 Vấn Đề: Không Tải Được

### Kiểm Tra Nhanh

1. **Internet có kết nối không?**
   - Mở trình duyệt, thử truy cập google.com
   - Nếu không được → Kiểm tra kết nối mạng

2. **Python đã cài đặt chưa?**
   ```bash
   python --version
   ```
   - Nếu thấy version (ví dụ: Python 3.9.0) → OK
   - Nếu lỗi → Cần cài Python

3. **yfinance đã cài chưa?**
   ```bash
   pip list | findstr yfinance
   ```
   - Nếu thấy yfinance → OK
   - Nếu không → Cần cài: `pip install yfinance`

---

## 🔧 Giải Pháp Từng Bước

### Lỗi 1: "pip is not recognized"

**Nguyên nhân:** pip chưa được cài hoặc không có trong PATH

**Giải pháp:**

```bash
# Thử 1: Dùng python -m pip
python -m pip install yfinance

# Thử 2: Dùng pip3
pip3 install yfinance

# Thử 3: Dùng python3
python3 -m pip install yfinance
```

---

### Lỗi 2: "yfinance not installed"

**Giải pháp:**

```bash
# Cài đặt lại
pip install yfinance

# Hoặc với user flag
pip install --user yfinance

# Hoặc upgrade pip trước
python -m pip install --upgrade pip
pip install yfinance
```

---

### Lỗi 3: "No module named 'yfinance'"

**Nguyên nhân:** yfinance chưa được cài hoặc cài vào Python khác

**Giải pháp:**

```bash
# Kiểm tra Python nào đang dùng
python --version
which python  # Mac/Linux
where python  # Windows

# Cài lại yfinance
python -m pip install yfinance --force-reinstall
```

---

### Lỗi 4: "No data found" hoặc "Empty DataFrame"

**Nguyên nhân:** 
- Yahoo Finance tạm thời down
- Symbol không đúng
- Internet connection issue

**Giải pháp:**

**Option A: Thử lại sau vài phút**

```bash
# Đợi 2-3 phút rồi chạy lại
python scripts/auto_download_data.py
```

**Option B: Thử symbol khác**

Tạo file `test_download.py`:

```python
import yfinance as yf
import pandas as pd

# Thử các symbol
symbols = ["GC=F", "XAUUSD=X", "GLD"]

for symbol in symbols:
    try:
        print(f"Thử {symbol}...")
        data = yf.download(symbol, period="60d", interval="1h", progress=False)
        if not data.empty:
            print(f"✅ Thành công với {symbol}: {len(data)} rows")
            data.to_csv("data/raw/xauusd_h1.csv")
            break
    except Exception as e:
        print(f"❌ {symbol}: {e}")
```

Chạy:
```bash
python test_download.py
```

**Option C: Download thủ công từ HistData**

1. Truy cập: https://www.histdata.com/
2. Đăng ký (chỉ cần email)
3. Download XAUUSD H1
4. Lưu vào `data/raw/xauusd_h1.csv`

---

### Lỗi 5: "Connection timeout" hoặc "Network error"

**Nguyên nhân:** 
- Firewall blocking
- Proxy settings
- Yahoo Finance bị chặn

**Giải pháp:**

**Option A: Thử lại sau**

```bash
# Đợi 5-10 phút rồi thử lại
python scripts/auto_download_data.py
```

**Option B: Dùng proxy (nếu có)**

Tạo file `.env`:
```
HTTP_PROXY=http://proxy:port
HTTPS_PROXY=http://proxy:port
```

**Option C: Download thủ công**

Xem Option C ở trên (HistData)

---

### Lỗi 6: Script chạy nhưng không có file

**Kiểm tra:**

```bash
# Kiểm tra file có tồn tại không
dir data\raw\xauusd_h1.csv  # Windows
ls data/raw/xauusd_h1.csv   # Mac/Linux
```

**Nếu không có file:**

1. Kiểm tra thư mục `data/raw/` có tồn tại không
2. Tạo thư mục nếu cần:
   ```bash
   mkdir -p data/raw
   ```
3. Chạy lại script

---

## 🆘 Giải Pháp Thay Thế (Nếu Vẫn Không Được)

### Option 1: Download Thủ Công Từ HistData ⭐

**Bước 1:** Truy cập https://www.histdata.com/

**Bước 2:** Đăng ký (chỉ cần email)

**Bước 3:** 
- Vào "Free Historical Data"
- Chọn "Forex" → "XAUUSD"
- Chọn timeframe: **H1**
- Chọn date range
- Download CSV

**Bước 4:** 
- Đổi tên file thành `xauusd_h1.csv`
- Đặt vào `data/raw/xauusd_h1.csv`

**Bước 5:** Test
```bash
python test_data.py
```

---

### Option 2: Tạo Dữ Liệu Mẫu (Để Test)

Nếu chỉ cần test code, có thể tạo dữ liệu mẫu:

Tạo file `create_sample_data.py`:

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Tạo dữ liệu mẫu 1 tháng
start_date = datetime.now() - timedelta(days=30)
dates = pd.date_range(start=start_date, periods=720, freq='1H')

# Giá mẫu (XAUUSD thường dao động 1800-2100)
base_price = 2000
prices = base_price + np.cumsum(np.random.randn(720) * 2)

data = pd.DataFrame({
    'timestamp': dates,
    'open': prices + np.random.randn(720) * 1,
    'high': prices + np.abs(np.random.randn(720) * 2),
    'low': prices - np.abs(np.random.randn(720) * 2),
    'close': prices + np.random.randn(720) * 1,
    'volume': np.random.randint(1000, 5000, 720)
})

# Đảm bảo high >= low, high >= open, high >= close, etc.
data['high'] = data[['open', 'high', 'low', 'close']].max(axis=1)
data['low'] = data[['open', 'high', 'low', 'close']].min(axis=1)

# Save
output_path = Path("data/raw/xauusd_h1.csv")
output_path.parent.mkdir(parents=True, exist_ok=True)
data.to_csv(output_path, index=False)

print(f"✅ Đã tạo dữ liệu mẫu: {len(data)} rows")
print(f"   File: {output_path}")
```

Chạy:
```bash
python create_sample_data.py
```

**Lưu ý:** Đây chỉ là dữ liệu mẫu để test, không phải dữ liệu thật!

---

## 📞 Kiểm Tra Chi Tiết

### Test 1: Kiểm Tra Python

```bash
python --version
```

Phải thấy: `Python 3.x.x`

### Test 2: Kiểm Tra pip

```bash
pip --version
```

Phải thấy: `pip x.x.x`

### Test 3: Kiểm Tra yfinance

```bash
python -c "import yfinance; print(yfinance.__version__)"
```

Phải thấy: Version number

### Test 4: Test Download Trực Tiếp

Tạo file `test_yfinance.py`:

```python
import yfinance as yf

try:
    print("Đang thử download GC=F...")
    data = yf.download("GC=F", period="5d", interval="1h", progress=False)
    print(f"✅ Thành công: {len(data)} rows")
    print(data.head())
except Exception as e:
    print(f"❌ Lỗi: {e}")
```

Chạy:
```bash
python test_yfinance.py
```

---

## 🎯 Checklist

- [ ] Internet connection OK?
- [ ] Python đã cài đặt?
- [ ] pip đã cài đặt?
- [ ] yfinance đã cài đặt?
- [ ] Đang ở đúng thư mục dự án?
- [ ] Thư mục `data/raw/` đã tồn tại?
- [ ] Firewall không block?

---

## 💡 Nếu Vẫn Không Được

**Liên hệ hoặc:**
1. Download thủ công từ HistData.com (Option 1 ở trên)
2. Tạo dữ liệu mẫu để test (Option 2 ở trên)
3. Kiểm tra log chi tiết khi chạy script

**Để xem log chi tiết:**

```bash
python scripts/auto_download_data.py > download_log.txt 2>&1
```

Sau đó mở file `download_log.txt` để xem lỗi chi tiết.

---

**💪 Đừng bỏ cuộc! Hãy thử các giải pháp trên!**




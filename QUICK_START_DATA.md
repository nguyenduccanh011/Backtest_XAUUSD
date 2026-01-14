# 🚀 Hướng Dẫn Lấy Dữ Liệu - Đơn Giản Nhất

Hướng dẫn nhanh nhất để lấy dữ liệu XAUUSD cho backtest.

---

## ⚡ Cách Đơn Giản Nhất (3 Bước)

### Bước 1: Cài đặt

**Mở Terminal/Command Prompt:**

- **Windows:** Nhấn `Win + R` → gõ `cmd` → Enter
- **Mac/Linux:** Mở Terminal (Applications → Utilities → Terminal)

**Di chuyển đến thư mục dự án:**

```bash
cd D:\CURSOR\corsor2\Backtest_XAUUSD
```

**Cài đặt package:**

```bash
pip install yfinance
```

**Lưu ý:** 
- Nếu dùng Python 3, có thể cần: `pip3 install yfinance`
- Nếu có lỗi permission, thử: `pip install --user yfinance`

### Bước 2: Chạy script

**Trong cùng Terminal/Command Prompt, chạy:**

```bash
python scripts/auto_download_data.py
```

**Lưu ý:**
- Nếu dùng Python 3, có thể cần: `python3 scripts/auto_download_data.py`
- Đảm bảo đang ở thư mục gốc của dự án

### Bước 3: Xong!

File đã được lưu tại: `data/raw/xauusd_h1.csv`

---

## 📝 Chi Tiết

### Script sẽ tự động:

1. ✅ Download dữ liệu từ Yahoo Finance (GC=F - Gold Futures)
2. ✅ Tự động normalize format
3. ✅ Validate dữ liệu
4. ✅ Lưu vào `data/raw/xauusd_h1.csv`

### Kết quả:

- **Rows:** ~8760 nến (1 năm H1 data)
- **Format:** CSV với columns: timestamp, open, high, low, close, volume
- **Sẵn sàng:** Dùng ngay cho backtest

---

## ✅ Test Dữ Liệu

**Trong Terminal/Command Prompt, chạy:**

```bash
python test_data.py
```

Nếu thấy `✅ Tất cả kiểm tra đều pass!` → Thành công!

---

## 💻 Sử Dụng Trong Code

```python
from src.utils.data_loader import DataLoader

loader = DataLoader()
df = loader.load_csv("data/raw/xauusd_h1.csv", source="auto")

print(f"Rows: {len(df)}")
print(df.head())
```

---

## ❓ Nếu Gặp Lỗi - Không Tải Được

### Bước 1: Test yfinance

```bash
python scripts/test_yfinance_simple.py
```

Script này sẽ kiểm tra:
- yfinance đã cài chưa?
- Có download được dữ liệu không?
- Symbol nào hoạt động?

### Bước 2: Xem Hướng Dẫn Chi Tiết

**Xem file:** [TROUBLESHOOTING_DOWNLOAD.md](TROUBLESHOOTING_DOWNLOAD.md)

Các lỗi thường gặp:
- ❌ "pip is not recognized" → Dùng `python -m pip install yfinance`
- ❌ "yfinance not installed" → `pip install yfinance`
- ❌ "No data found" → Thử lại sau hoặc download thủ công
- ❌ "Connection timeout" → Kiểm tra internet hoặc dùng HistData

### Bước 3: Giải Pháp Thay Thế

**Nếu vẫn không được, download thủ công:**

1. Truy cập: https://www.histdata.com/
2. Đăng ký (chỉ cần email)
3. Download XAUUSD H1
4. Lưu vào `data/raw/xauusd_h1.csv`
5. Test: `python test_data.py`

---

## 🎯 Tóm Tắt

1. **Cài đặt:** `pip install yfinance`
2. **Download:** `python scripts/auto_download_data.py`
3. **Test:** `python test_data.py`
4. **Dùng:** Load trong code

**Xong! 🎉**


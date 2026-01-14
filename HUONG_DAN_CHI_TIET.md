# 📖 Hướng Dẫn Chi Tiết - Lấy Dữ Liệu

Hướng dẫn từng bước cụ thể để lấy dữ liệu XAUUSD.

---

## 🖥️ Bước 1: Mở Terminal/Command Prompt

### Windows:

1. **Cách 1:** Nhấn `Win + R` → gõ `cmd` → Enter
2. **Cách 2:** Nhấn `Win + X` → chọn "Windows PowerShell" hoặc "Command Prompt"
3. **Cách 3:** Tìm "Command Prompt" trong Start Menu

### Mac:

1. Mở **Finder**
2. Vào **Applications** → **Utilities** → **Terminal**

### Linux:

1. Nhấn `Ctrl + Alt + T`
2. Hoặc tìm "Terminal" trong Applications

---

## 📁 Bước 2: Di Chuyển Đến Thư Mục Dự Án

**Trong Terminal/Command Prompt, gõ:**

```bash
cd D:\CURSOR\corsor2\Backtest_XAUUSD
```

**Lưu ý:**
- Thay đường dẫn bằng đường dẫn thực tế của bạn
- Trên Mac/Linux, đường dẫn sẽ khác (ví dụ: `/Users/username/Backtest_XAUUSD`)

**Kiểm tra đã vào đúng thư mục:**

```bash
# Windows
dir

# Mac/Linux
ls
```

Bạn sẽ thấy các file như: `main.py`, `README.md`, `requirements.txt`, v.v.

---

## 📦 Bước 3: Cài Đặt yfinance

**Trong Terminal/Command Prompt, gõ:**

```bash
pip install yfinance
```

**Nếu gặp lỗi:**

- **"pip is not recognized"** → Thử: `python -m pip install yfinance`
- **"Permission denied"** → Thử: `pip install --user yfinance`
- **Python 3** → Thử: `pip3 install yfinance` hoặc `python3 -m pip install yfinance`

**Đợi cho đến khi thấy:**

```
Successfully installed yfinance-x.x.x
```

---

## 📥 Bước 4: Download Dữ Liệu

**Trong Terminal/Command Prompt, gõ:**

```bash
python scripts/auto_download_data.py
```

**Nếu gặp lỗi:**

- **"python is not recognized"** → Thử: `python3 scripts/auto_download_data.py`
- **"No module named 'yfinance'"** → Chạy lại: `pip install yfinance`

**Đợi cho đến khi thấy:**

```
✅ Download thành công!
```

---

## ✅ Bước 5: Test Dữ Liệu

**Trong Terminal/Command Prompt, gõ:**

```bash
python test_data.py
```

**Nếu thấy:**

```
✅ Tất cả kiểm tra đều pass!
```

→ **Thành công!** Dữ liệu đã sẵn sàng.

---

## 📂 Kiểm Tra File

**File đã được lưu tại:**

```
D:\CURSOR\corsor2\Backtest_XAUUSD\data\raw\xauusd_h1.csv
```

**Có thể mở bằng:**
- Excel
- Notepad
- Bất kỳ text editor nào

---

## 🎯 Tóm Tắt Các Lệnh

**Copy và paste từng lệnh vào Terminal:**

```bash
# 1. Di chuyển đến thư mục dự án
cd D:\CURSOR\corsor2\Backtest_XAUUSD

# 2. Cài đặt yfinance
pip install yfinance

# 3. Download dữ liệu
python scripts/auto_download_data.py

# 4. Test dữ liệu
python test_data.py
```

---

## ❓ Câu Hỏi Thường Gặp

**Q: Terminal là gì?**  
A: Terminal (Mac/Linux) hoặc Command Prompt (Windows) là cửa sổ để chạy lệnh text.

**Q: Làm sao biết đã vào đúng thư mục?**  
A: Chạy `dir` (Windows) hoặc `ls` (Mac/Linux), bạn sẽ thấy file `main.py`, `README.md`.

**Q: Lệnh không chạy được?**  
A: Đảm bảo đang ở đúng thư mục dự án và Python đã được cài đặt.

**Q: File được lưu ở đâu?**  
A: `data/raw/xauusd_h1.csv` trong thư mục dự án.

---

**💡 Mẹo:** Copy từng lệnh và paste vào Terminal, không cần gõ lại!




# 🌐 Web Application - Backtest XAUUSD

Ứng dụng web để chạy backtest XAUUSD thay thế cho GUI desktop (tkinter).

## 🚀 Cách chạy

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Khởi động server

```bash
python web_app.py
```

Hoặc sử dụng uvicorn trực tiếp:

```bash
uvicorn web_app:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Mở trình duyệt

Truy cập: http://localhost:8000

## 📁 Cấu trúc

- `web_app.py` - FastAPI backend server
- `web_static/` - Frontend files (HTML, CSS, JavaScript)
  - `index.html` - Giao diện chính
  - `style.css` - Styling
  - `app.js` - JavaScript logic

## 🔧 Tính năng

- ✅ Điều chỉnh ngưỡng RSI (thủ công hoặc tự động tối ưu)
- ✅ Nhập dãy số tiền/lot cho từng entry
- ✅ Upload file data CSV
- ✅ Chạy backtest và hiển thị kết quả
- ✅ Lưu/tải dữ liệu lot

## 📝 API Endpoints

- `GET /` - Trang chủ (HTML)
- `POST /api/backtest` - Chạy backtest
- `POST /api/calculate-lot` - Tính lot size từ số tiền
- `GET /api/data-files` - Liệt kê file data
- `POST /api/upload-data` - Upload file data CSV
- `GET /api/chart/{filename}` - Lấy file biểu đồ

## 🔄 So sánh với GUI desktop

| Tính năng | GUI Desktop (tkinter) | Web App |
|-----------|----------------------|---------|
| Điều chỉnh RSI | ✅ | ✅ |
| Nhập số tiền/lot | ✅ | ✅ |
| Chạy backtest | ✅ | ✅ |
| Tối ưu RSI tự động | ✅ | ✅ |
| Vẽ biểu đồ | ✅ | ⚠️ (đang phát triển) |
| Lưu/tải dữ liệu | ✅ | ✅ |

## 💡 Lưu ý

- Web app sử dụng cùng logic backtest với GUI desktop
- File data cần được upload hoặc đặt trong `data/raw/`
- Kết quả backtest được hiển thị trực tiếp trên web
- Biểu đồ có thể được vẽ bằng GUI desktop nếu cần


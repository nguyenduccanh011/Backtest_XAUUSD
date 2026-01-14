# 📊 Backtest XAUUSD - DCA Gồng Lệnh Strategy

Hệ thống backtest cho chiến lược gồng lệnh DCA (Dollar Cost Averaging) trên XAUUSD với logic phức tạp dựa trên RSI.

## 🎯 Tính năng chính

- ✅ Hệ thống đếm entry thông minh (1-9: đếm, 10-40: vào lệnh, 41+: chờ chốt)
- ✅ Logic RSI phức tạp với break detection (RSI < 60 ngắt nhịp)
- ✅ Tùy chỉnh lot size cho từng entry
- ✅ Xử lý khoảng trống giữa các entry
- ✅ Báo cáo chi tiết và export kết quả

## 📚 Tài liệu

- [Project Overview](project_overview.md) - Kiến trúc và phạm vi dự án
- [Requirements](requirements.md) - Chi tiết yêu cầu kỹ thuật
- [Tasks](tasks.md) - Danh sách công việc
- [Data Sources](DATA_SOURCES.md) - Hướng dẫn lấy dữ liệu XAUUSD
- [Yahoo Finance Integration](docs/YAHOO_FINANCE_INTEGRATION.md) ⭐ - Hướng dẫn tích hợp Yahoo Finance (Khuyến nghị)
- [Dukascopy Integration](docs/DUKASCOPY_INTEGRATION.md) - Hướng dẫn tích hợp Dukascopy

## 🚀 Quick Start

1. **Cài đặt dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Lấy dữ liệu XAUUSD:** 
   
   **Xem hướng dẫn chi tiết:** [QUICK_START_DATA.md](QUICK_START_DATA.md) hoặc [HUONG_DAN_CHI_TIET.md](HUONG_DAN_CHI_TIET.md)
   
   **Tóm tắt (3 bước):**
   ```bash
   # Mở Terminal/Command Prompt, di chuyển đến thư mục dự án
   cd D:\CURSOR\corsor2\Backtest_XAUUSD
   
   # 1. Cài đặt
   pip install yfinance
   
   # 2. Download tự động
   python scripts/auto_download_data.py
   
   # 3. Test
   python test_data.py
   ```
   
   ✅ File sẽ được lưu tại: `data/raw/xauusd_h1.csv`
   ✅ Sẵn sàng dùng cho backtest!
   
   **Option B: Dukascopy** (Nếu truy cập được)
   - **Xem hướng dẫn:** [Dukascopy Integration Guide](docs/DUKASCOPY_INTEGRATION.md)
   - Truy cập: https://www.dukascopy.com/swiss/english/marketwatch/historical/
   - Chọn XAUUSD → H1 → Download CSV
   
   **Option B: Tự động từ OANDA API** (Cần VPN nếu không truy cập được)
   - Xem hướng dẫn: [OANDA Integration Guide](docs/OANDA_INTEGRATION_STEP_BY_STEP.md)
   - **Nếu không truy cập được:** Xem [Troubleshooting](docs/OANDA_TROUBLESHOOTING.md)
   - Cài đặt: `pip install oandapyV20 python-dotenv`
   - Tạo `.env` file với OANDA credentials
   - Chạy: `python scripts/download_oanda.py` hoặc dùng trong code

3. **Chạy backtest:**
   ```bash
   python main.py
   ```
   
   *(Đang trong quá trình phát triển)*

## 📋 Yêu cầu

- Python 3.8+
- pandas
- numpy
- (Backtrader - optional)

## 📝 License

MIT
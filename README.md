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

## 🚀 Quick Start

*(Sẽ được cập nhật sau khi implement)*

## 📋 Yêu cầu

- Python 3.8+
- pandas
- numpy
- (Backtrader - optional)

## 📝 License

MIT
# 📊 Backtest XAUUSD - DCA Gồng Lệnh Strategy

## 🎯 Mục đích dự án
Xây dựng hệ thống backtest cho chiến lược gồng lệnh DCA (Dollar Cost Averaging) trên XAUUSD với logic phức tạp dựa trên RSI.

## 🏗️ Kiến trúc hệ thống

### Tech Stack
- **Backtesting Engine**: Backtrader hoặc tự xây dựng với pandas
- **Data Processing**: pandas, numpy
- **Visualization**: matplotlib (optional)
- **Language**: Python 3.8+

### Cấu trúc dự án
```
Backtest_XAUUSD/
├── data/                    # Dữ liệu lịch sử XAUUSD
│   └── raw/                 # Dữ liệu thô (CSV, JSON)
├── src/
│   ├── strategy/            # Logic chiến lược
│   │   ├── dca_strategy.py  # Core strategy logic
│   │   └── rsi_handler.py  # Xử lý RSI conditions
│   ├── backtest/            # Backtest engine
│   │   ├── engine.py        # Main backtest engine
│   │   └── portfolio.py     # Quản lý portfolio
│   ├── config/              # Cấu hình
│   │   └── strategy_config.py
│   └── utils/               # Utilities
│       ├── data_loader.py   # Load dữ liệu
│       └── calculator.py    # Tính toán P&L
├── configs/                 # File config JSON/YAML
│   └── default_config.json
├── results/                 # Kết quả backtest
│   ├── reports/             # Báo cáo chi tiết
│   └── charts/              # Biểu đồ (optional)
├── tests/                   # Unit tests
└── main.py                  # Entry point

```

## 📋 Yêu cầu chức năng

### 1. Quản lý Entry System
- **Entry 1-9**: Chỉ đếm, không vào lệnh (lot = 0)
- **Entry 10-40**: Vào lệnh với số lot tùy chỉnh
- **Entry 41+**: Không vào nữa, chỉ chờ chốt lời/lỗ

### 2. Điều kiện Entry
- **RSI Entry**: RSI close <= 30 (Buy) hoặc >= 70 (Sell)
- **Chọn 1 hướng**: Chỉ Buy HOẶC Sell trong 1 chu kỳ
- **Logic đếm liên tục**:
  - Nếu RSI giữa các entry không chạm < 60 và tiếp tục > 70: Tiếp tục đếm
  - Nếu RSI về < 60: Ngắt nhịp đếm → chờ chốt

### 3. Điều kiện Chốt
- **RSI Exit**: RSI open chạm 50 (bất kể lời/lỗ)
- Chốt tất cả lệnh đang mở khi điều kiện đạt

### 4. Tùy chỉnh Lot Size
- Có thể set số lot khác nhau cho mỗi entry (10-40)
- Format: JSON/YAML config hoặc CSV
- Cho phép test nhiều kịch bản lot size

### 5. Xử lý khoảng trống RSI
- Giữa các entry có thể có khoảng RSI không đạt điều kiện
- Hệ thống phải đợi đến khi đạt điều kiện mới vào tiếp
- Logic ngắt nhịp khi RSI < 60

## 🔧 Cấu hình

### Config Structure
```json
{
  "strategy": {
    "direction": "SELL",  // hoặc "BUY"
    "rsi_period": 14,
    "rsi_entry_threshold": {
      "buy": 30,
      "sell": 70
    },
    "rsi_break_threshold": 60,
    "rsi_exit_threshold": 50,
    "entry_range": {
      "count_only": [1, 9],
      "trade": [10, 40],
      "wait_exit": [41, null]
    }
  },
  "lot_sizes": {
    "entry_10": 0.01,
    "entry_11": 0.01,
    // ... có thể tự động tính hoặc manual
  },
  "data": {
    "symbol": "XAUUSD",
    "timeframe": "H1",
    "data_file": "data/raw/xauusd_h1.csv"
  }
}
```

## 📊 Output Requirements

### Báo cáo Backtest
1. **Tổng quan**:
   - Tổng số entry đã vào
   - Tổng P&L
   - Win rate
   - Max drawdown

2. **Chi tiết từng entry**:
   - Entry number
   - Thời gian vào
   - Giá vào
   - Lot size
   - RSI tại thời điểm vào
   - P&L của entry đó

3. **Timeline**:
   - Sequence các entry
   - Các điểm ngắt nhịp (RSI < 60)
   - Điểm chốt cuối cùng

4. **Export**: CSV, JSON cho phân tích sâu hơn

## 🎯 Phạm vi dự án

### ✅ Trong phạm vi
- Backtest engine với logic DCA gồng lệnh
- Xử lý RSI conditions (entry, break, exit)
- Hệ thống đếm entry phức tạp
- Tùy chỉnh lot size per entry
- Báo cáo kết quả chi tiết
- Config-driven approach

### ❌ Ngoài phạm vi (hiện tại)
- Live trading
- Real-time data feed
- Multi-symbol backtest
- Optimization engine tự động
- GUI/Web interface

## 🚀 Roadmap Implementation

### Phase 1: Core Engine
1. Data loader cho XAUUSD
2. RSI calculator
3. Basic backtest engine

### Phase 2: Strategy Logic
1. Entry counting system (1-9, 10-40, 41+)
2. RSI entry conditions
3. Break logic (RSI < 60)
4. Exit conditions (RSI = 50)

### Phase 3: Configuration & Customization
1. Lot size configuration
2. Config file parser
3. Multiple scenario testing

### Phase 4: Reporting
1. Detailed reports
2. CSV/JSON export
3. Visualization (optional)


# 📋 Đánh giá Kế hoạch Dự án - Backtest XAUUSD DCA Strategy

## ✅ Điểm Mạnh

1. **Logic chiến lược rõ ràng**: Entry counting (1-9, 10-40, 41+), RSI conditions, break logic được mô tả chi tiết
2. **Cấu trúc dự án hợp lý**: Tách module rõ ràng (strategy, backtest, config, utils)
3. **Config-driven approach**: Dễ test nhiều kịch bản
4. **Roadmap chia phase hợp lý**: Từ core engine → strategy → config → reporting
5. **Edge cases được đề cập**: RSI boundary, data gaps, end of data

---

## ⚠️ Vấn đề Cần Làm Rõ

### 1. Logic "Chọn 1 Hướng" (Buy HOẶC Sell)

**Vấn đề:**
- Chưa rõ cách xác định hướng đầu tiên trong 1 cycle
- Nếu cả 2 điều kiện (RSI <= 30 và >= 70) cùng đạt, ưu tiên gì?
- Sau khi chốt, cycle tiếp theo xác định hướng như thế nào?

**Đề xuất:**
- **Option A**: Auto-detect dựa trên điều kiện đầu tiên đạt
  - RSI <= 30 → chọn Buy
  - RSI >= 70 → chọn Sell
  - Nếu cả 2 cùng đạt → ưu tiên theo config `direction`
- **Option B**: Force direction từ config (như hiện tại)
  - Nếu config `direction: "SELL"` → chỉ vào Sell, bỏ qua Buy signals
- **Option C**: Cho phép cả 2, nhưng tách riêng portfolio

**Khuyến nghị**: Option A + fallback to config nếu không rõ

---

### 2. Logic Ngắt Nhịp (Break Logic)

**Vấn đề:**
- Hiện tại chỉ nêu: RSI < 60 ngắt nhịp (cho Sell)
- Với Buy thì sao? Cần đối xứng: RSI > 40 ngắt nhịp?

**Đề xuất:**
```json
"rsi_break_threshold": {
  "buy": 40,    // RSI > 40 ngắt nhịp cho Buy
  "sell": 60    // RSI < 60 ngắt nhịp cho Sell
}
```

**Logic:**
- **Sell cycle**: RSI < 60 → ngắt nhịp, chờ chốt
- **Buy cycle**: RSI > 40 → ngắt nhịp, chờ chốt

---

### 3. RSI Exit Condition

**Vấn đề:**
- Dùng RSI `open` hay `close`? (hiện nêu "RSI open")
- Tolerance: 49-51 hay chính xác 50?
- Nếu RSI không bao giờ về 50 → lệnh treo mãi?

**Đề xuất:**
```json
"rsi_exit": {
  "threshold": 50,
  "tolerance": 1,        // 49-51
  "use_open": true,      // true: dùng open, false: dùng close
  "timeout_bars": null   // null: không timeout, hoặc số nến tối đa
}
```

**Edge case**: Nếu timeout → force close với giá hiện tại?

---

### 4. Entry Counting với Khoảng Trống

**Vấn đề:**
- Nếu RSI không đạt điều kiện trong nhiều nến → có timeout không?
- Có giới hạn thời gian giữa các entry không?

**Đề xuất:**
- Thêm config `max_gap_bars` (ví dụ: 100 nến)
- Nếu quá gap → reset cycle hoặc skip entry đó

---

## 🔧 Thiếu Sót Kỹ Thuật

### 1. Portfolio & Risk Management

**Thiếu:**
- Initial capital (vốn ban đầu)
- Margin/leverage ratio
- Risk limit (max drawdown, max loss per cycle)
- Position sizing constraints

**Đề xuất bổ sung vào config:**
```json
"portfolio": {
  "initial_capital": 10000,
  "leverage": 1,
  "max_drawdown_percent": 50,
  "max_loss_per_cycle": 1000
}
```

---

### 2. P&L Calculation Details

**Thiếu:**
- Spread (bid-ask spread)
- Slippage
- Commission
- Average entry price cho multiple positions cùng hướng

**Đề xuất:**
```json
"trading": {
  "spread_pips": 3,           // XAUUSD thường 2-5 pips
  "slippage_pips": 1,
  "commission_per_lot": 0,    // hoặc tính theo %
  "calculate_average_entry": true
}
```

**Logic P&L:**
- Nếu `calculate_average_entry: true` → tính weighted average
- Nếu `false` → tính riêng từng entry

---

### 3. Data Validation Module

**Thiếu trong kiến trúc:**
- Module validate dữ liệu (missing data, duplicates, outliers)
- Data quality checks

**Đề xuất:**
```
src/
├── utils/
│   ├── data_loader.py
│   ├── data_validator.py    # ← THÊM
│   └── calculator.py
```

---

### 4. Logging & Debugging

**Thiếu:**
- Logging system để debug logic phức tạp
- Trace từng entry decision
- Verbose mode

**Đề xuất:**
```
src/
├── utils/
│   ├── logger.py            # ← THÊM
│   └── ...
```

**Config:**
```json
"logging": {
  "level": "INFO",            // DEBUG, INFO, WARNING, ERROR
  "log_file": "results/logs/backtest.log",
  "verbose": false
}
```

---

## 📊 Đề Xuất Cải Thiện

### 1. Bổ Sung Config Structure

```json
{
  "strategy": {
    "direction": "AUTO",      // "AUTO", "BUY", "SELL"
    "rsi_period": 14,
    "rsi_entry_threshold": {
      "buy": 30,
      "sell": 70
    },
    "rsi_break_threshold": {
      "buy": 40,              // ← THÊM
      "sell": 60
    },
    "rsi_exit": {
      "threshold": 50,
      "tolerance": 1,
      "use_open": true,
      "timeout_bars": null
    },
    "entry_range": {
      "count_only": [1, 9],
      "trade": [10, 40],
      "wait_exit": [41, null]
    },
    "max_gap_bars": 100       // ← THÊM
  },
  "portfolio": {              // ← THÊM SECTION
    "initial_capital": 10000,
    "leverage": 1,
    "max_drawdown_percent": 50
  },
  "trading": {                // ← THÊM SECTION
    "spread_pips": 3,
    "slippage_pips": 1,
    "commission_per_lot": 0,
    "calculate_average_entry": true
  },
  "lot_sizes": {
    "entry_10": 0.01,
    "entry_11": 0.01
  },
  "data": {
    "symbol": "XAUUSD",
    "timeframe": "H1",
    "data_file": "data/raw/xauusd_h1.csv"
  },
  "logging": {                // ← THÊM SECTION
    "level": "INFO",
    "log_file": "results/logs/backtest.log",
    "verbose": false
  }
}
```

---

### 2. Bổ Sung Module vào Kiến Trúc

```
src/
├── strategy/
│   ├── dca_strategy.py
│   ├── rsi_handler.py
│   └── direction_selector.py    # ← THÊM: Logic chọn Buy/Sell
├── backtest/
│   ├── engine.py
│   ├── portfolio.py
│   └── risk_manager.py           # ← THÊM: Risk management
├── config/
│   └── strategy_config.py
└── utils/
    ├── data_loader.py
    ├── data_validator.py         # ← THÊM
    ├── calculator.py
    └── logger.py                 # ← THÊM
```

---

### 3. Bổ Sung Metrics vào Reporting

**Thiếu trong output:**
- Average entry price (nếu có multiple positions)
- Total margin used
- Return on investment (ROI)
- Sharpe ratio (nếu có)
- Number of cycles completed
- Average cycle duration

**Đề xuất bổ sung vào `project_overview.md` section "Output Requirements"**

---

### 4. Bổ Sung vào Tasks.md

**Phase 1 cần thêm:**
- [ ] Create data validator module
- [ ] Setup logging system
- [ ] Design risk management module

**Phase 2 cần thêm:**
- [ ] Implement direction selector (AUTO/BUY/SELL)
- [ ] Implement break logic cho cả Buy và Sell
- [ ] Handle timeout cho exit condition

**Phase 4 cần thêm:**
- [ ] Risk management integration
- [ ] Spread/slippage/commission calculation
- [ ] Average entry price calculation

---

## 🎯 Khuyến Nghị Ưu Tiên

### High Priority (Phải làm rõ trước khi code)
1. ✅ Logic chọn hướng (Buy/Sell) - Option A được recommend
2. ✅ Break logic cho Buy (RSI > 40)
3. ✅ RSI exit tolerance và timeout
4. ✅ Portfolio & risk management config

### Medium Priority (Nên có)
5. ⚠️ Spread/slippage/commission
6. ⚠️ Data validation module
7. ⚠️ Logging system

### Low Priority (Có thể thêm sau)
8. 📝 Advanced metrics (Sharpe ratio, etc.)
9. 📝 Visualization (optional như đã nêu)

---

## 📝 Action Items

1. **Cập nhật `project_overview.md`**:
   - Bổ sung config structure mới
   - Làm rõ logic chọn hướng
   - Bổ sung break logic cho Buy

2. **Cập nhật `requirements.md`**:
   - Thêm section về risk management
   - Thêm section về trading costs (spread, slippage)
   - Làm rõ RSI exit timeout

3. **Cập nhật `tasks.md`**:
   - Thêm tasks cho data validator
   - Thêm tasks cho logging
   - Thêm tasks cho risk management

4. **Tạo `manifest.yml`** (theo AGENTS.md rules):
   - List tất cả artifacts sẽ tạo

---

## ✅ Kết Luận

Kế hoạch **tốt và chi tiết**, nhưng cần làm rõ:
- Logic chọn hướng và break logic
- Risk management và trading costs
- Data validation và logging

Sau khi cập nhật các điểm trên, kế hoạch sẽ **sẵn sàng để implement**.


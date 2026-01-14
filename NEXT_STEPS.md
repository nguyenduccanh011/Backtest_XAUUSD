# 🚀 Hướng Dẫn Bước Tiếp Theo - Backtest XAUUSD

## 📊 Tình Trạng Hiện Tại

### ✅ Đã Hoàn Thành
- [x] Cấu trúc dự án đã được tạo
- [x] Data Loader (`src/utils/data_loader.py`) - Hỗ trợ nhiều format CSV
- [x] RSI Handler (`src/strategy/rsi_handler.py`) - Tính toán RSI và kiểm tra điều kiện
- [x] Config System (`src/config/strategy_config.py`) - Đọc config từ JSON
- [x] Portfolio Manager (`src/backtest/portfolio.py`) - Quản lý vị thế
- [x] Main entry point (`main.py`) - Skeleton đã có

### ⏳ Cần Hoàn Thiện
- [ ] **DCA Strategy Logic** - Logic đếm entry và quản lý chu kỳ
- [ ] **Backtest Engine** - Vòng lặp backtest chính
- [ ] **Tích hợp vào main.py** - Kết nối tất cả components
- [ ] **Testing với dữ liệu thực** - Kiểm tra với file CSV

---

## 🎯 Bước Tiếp Theo (Theo Thứ Tự Ưu Tiên)

### **Bước 1: Tải Dữ Liệu XAUUSD** 📥

**Mục đích:** Cần có dữ liệu lịch sử để chạy backtest.

**Các lựa chọn:**

#### Option A: Tự động download (Khuyến nghị)
```bash
# Chạy script tự động download từ Yahoo Finance
python scripts/auto_download_data.py
```

#### Option B: Download thủ công
1. Truy cập **TradingView**: https://www.tradingview.com/
2. Tìm kiếm **XAUUSD**
3. Chọn timeframe **H1** (1 giờ)
4. Export data → CSV
5. Lưu vào `data/raw/xauusd_h1.csv`

#### Option C: Dùng OANDA API (nếu có account)
```bash
python scripts/download_oanda.py
```

**Kiểm tra:**
```bash
# Xem file đã tồn tại chưa
ls data/raw/xauusd_h1.csv
```

**📚 Xem chi tiết:** `DATA_SOURCES.md`

---

### **Bước 2: Hoàn Thiện DCA Strategy Logic** 🧠

**File cần chỉnh sửa:** `src/strategy/dca_strategy.py`

**Cần implement:**

1. **Entry Counting System:**
   - Entry 1-9: Chỉ đếm, không vào lệnh (lot = 0)
   - Entry 10-40: Vào lệnh với lot size từ config
   - Entry 41+: Không vào nữa, chỉ chờ chốt

2. **RSI Entry Logic:**
   - BUY: RSI close <= 30
   - SELL: RSI close >= 70
   - Chọn 1 hướng (BUY hoặc SELL) trong 1 chu kỳ

3. **Nhịp RSI Bắt Buộc:**
   - Giữa Entry N và Entry N+1 PHẢI có nhịp RSI không đạt điều kiện
   - SELL: RSI phải xuống < 70 (ít nhất 1 nến) giữa các entry
   - BUY: RSI phải lên > 30 (ít nhất 1 nến) giữa các entry

4. **Break Detection:**
   - SELL: RSI < 60 → Ngắt nhịp đếm, chờ chốt
   - BUY: RSI > 40 → Ngắt nhịp đếm, chờ chốt

5. **Exit Logic:**
   - RSI open chạm 50 → Chốt tất cả lệnh

**Tài liệu tham khảo:** `ENTRY_COUNTING_EXPLAINED.md`

---

### **Bước 3: Hoàn Thiện Backtest Engine** ⚙️

**File cần chỉnh sửa:** `src/backtest/engine.py`

**Cần implement:**

1. **Main Backtest Loop:**
   ```python
   for timestamp, row in data.iterrows():
       # 1. Tính RSI
       # 2. Kiểm tra điều kiện entry/exit
       # 3. Thực hiện entry/exit
       # 4. Cập nhật portfolio
       # 5. Ghi log kết quả
   ```

2. **Tích hợp với Strategy:**
   - Gọi `strategy.should_enter()`
   - Gọi `strategy.should_exit()`
   - Gọi `strategy.check_break()`

3. **Tích hợp với Portfolio:**
   - `portfolio.open_position()` khi vào lệnh
   - `portfolio.close_all_positions()` khi chốt
   - `portfolio.update_pnl()` mỗi bar

4. **Tracking Results:**
   - Lưu tất cả entry/exit events
   - Tính P&L cho mỗi entry
   - Track drawdown

---

### **Bước 4: Tích Hợp Vào main.py** 🔗

**File cần chỉnh sửa:** `main.py`

**Cần thêm:**

1. **Khởi tạo các components:**
   ```python
   # Load config
   config = StrategyConfig("configs/default_config.json")
   
   # Load data
   loader = DataLoader()
   df = loader.load_csv(config.get("data.data_file"))
   
   # Initialize RSI handler
   rsi_handler = RSIHandler(period=config.get("strategy.rsi_period"))
   
   # Calculate RSI
   df['rsi'] = rsi_handler.calculate_rsi(df['close'])
   
   # Initialize strategy
   strategy = DCAStrategy(config.get("strategy"))
   
   # Initialize portfolio
   portfolio = Portfolio(config.get("portfolio"))
   
   # Initialize engine
   engine = BacktestEngine(config, df, strategy, portfolio)
   ```

2. **Chạy backtest:**
   ```python
   results = engine.run()
   ```

3. **Generate report:**
   ```python
   report = engine.generate_report()
   print(report)
   ```

---

### **Bước 5: Test với Dữ Liệu Thực** 🧪

**Sau khi implement xong:**

1. **Chạy backtest:**
   ```bash
   python main.py
   ```

2. **Kiểm tra kết quả:**
   - Xem log trong `results/logs/backtest.log`
   - Kiểm tra report trong console
   - Verify entry/exit logic đúng

3. **Debug nếu cần:**
   - Thêm logging chi tiết
   - In ra từng entry để kiểm tra
   - So sánh với tính toán thủ công

---

### **Bước 6: Generate Reports** 📊

**File cần tạo:** `src/backtest/reporter.py` (optional)

**Cần implement:**

1. **Summary Report:**
   - Tổng số entry
   - Tổng P&L
   - Win rate
   - Max drawdown

2. **Detailed Report:**
   - Chi tiết từng entry (số, thời gian, giá, lot, RSI, P&L)
   - Timeline các events
   - Export CSV/JSON

3. **Visualization (optional):**
   - Biểu đồ P&L
   - Biểu đồ entry points trên chart

---

## 📝 Checklist Thực Hiện

### Phase 1: Core Logic ✅
- [x] Data loader
- [x] RSI calculator
- [ ] **DCA Strategy logic** ← **BẮT ĐẦU TỪ ĐÂY**
- [ ] Backtest engine loop

### Phase 2: Integration
- [ ] Tích hợp vào main.py
- [ ] Test với sample data
- [ ] Fix bugs

### Phase 3: Reporting
- [ ] Generate summary report
- [ ] Generate detailed report
- [ ] Export CSV/JSON

---

## 🎯 Bước Tiếp Theo Ngay Bây Giờ

**Bắt đầu với:**

1. **Tải dữ liệu** (5 phút):
   ```bash
   python scripts/auto_download_data.py
   ```

2. **Implement DCA Strategy** (1-2 giờ):
   - Mở `src/strategy/dca_strategy.py`
   - Implement các method: `should_enter()`, `should_exit()`, `check_break()`
   - Xem `ENTRY_COUNTING_EXPLAINED.md` để hiểu logic

3. **Implement Backtest Engine** (1 giờ):
   - Mở `src/backtest/engine.py`
   - Implement method `run()` với vòng lặp chính

4. **Tích hợp vào main.py** (30 phút):
   - Kết nối tất cả components
   - Chạy thử

---

## 📚 Tài Liệu Tham Khảo

- **Logic Entry Counting:** `ENTRY_COUNTING_EXPLAINED.md`
- **Data Sources:** `DATA_SOURCES.md`
- **Project Overview:** `project_overview.md`
- **Tasks:** `tasks.md`

---

## 💡 Tips

1. **Bắt đầu đơn giản:** Implement từng phần một, test ngay sau mỗi phần
2. **Dùng logging:** Thêm `print()` hoặc logging để debug
3. **Test với ít data trước:** Dùng 100-200 nến để test nhanh
4. **Đọc kỹ logic:** `ENTRY_COUNTING_EXPLAINED.md` có giải thích chi tiết về nhịp RSI

---

## ❓ Cần Hỗ Trợ?

Nếu gặp vấn đề:
1. Kiểm tra lại `ENTRY_COUNTING_EXPLAINED.md` để hiểu rõ logic
2. Xem code examples trong các file đã implement
3. Test từng function riêng lẻ trước khi tích hợp

---

**🎯 Bắt đầu ngay:** Chạy `python scripts/auto_download_data.py` để tải dữ liệu!




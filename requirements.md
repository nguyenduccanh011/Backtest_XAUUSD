# 📝 Chi tiết Yêu cầu Kỹ thuật

## 🎯 1. Hệ thống Đếm Entry

### 1.1. Phân loại Entry
- **Entry 1-9**: 
  - Chỉ đếm số lần RSI đạt điều kiện
  - Không vào lệnh (lot = 0)
  - Vẫn theo dõi để đếm
  
- **Entry 10-40**:
  - Vào lệnh thực sự với lot size tùy chỉnh
  - Mỗi entry có thể set lot khác nhau
  
- **Entry 41+**:
  - Không vào lệnh mới
  - Chỉ chờ điều kiện chốt (RSI = 50)

### 1.2. Logic Đếm Liên tục

**Trường hợp 1: Tiếp tục đếm**
```
RSI Entry (>= 70 cho Sell) 
  → Đếm entry N
  → RSI giảm nhưng KHÔNG chạm < 60
  → RSI tăng lại >= 70
  → Đếm entry N+1 (tiếp tục chuỗi)
```

**Trường hợp 2: Ngắt nhịp**
```
RSI Entry (>= 70 cho Sell)
  → Đếm entry N
  → RSI chạm < 60
  → NGẮT NHỊP ĐẾM
  → Chờ chốt lời/lỗ khi RSI = 50
  → Sau khi chốt, reset và bắt đầu đếm lại từ 1
```

## 🎯 2. Điều kiện Entry

### 2.1. RSI Entry Conditions
- **Buy**: RSI close <= 30
- **Sell**: RSI close >= 70
- **Chọn 1 hướng**: Trong 1 chu kỳ chỉ chọn Buy HOẶC Sell

### 2.2. Xử lý khoảng trống
- Giữa các entry có thể có nhiều nến RSI không đạt điều kiện
- Hệ thống phải:
  - Đợi đến khi RSI đạt điều kiện mới vào tiếp
  - Không bỏ qua entry nào trong sequence

## 🎯 3. Điều kiện Chốt

### 3.1. Exit Condition
- **RSI Exit**: RSI open = 50 (hoặc trong khoảng 49-51 để tránh miss)
- **Chốt tất cả**: Khi điều kiện đạt, chốt tất cả lệnh đang mở
- **Bất kể lời/lỗ**: Không quan tâm P&L, chỉ dựa vào RSI

## 🎯 4. Lot Size Configuration

### 4.1. Format Configuration
Cho phép set lot size cho từng entry (10-40):
- **Option 1**: Manual config (JSON/YAML)
  ```json
  {
    "entry_10": 0.01,
    "entry_11": 0.02,
    "entry_12": 0.03,
    ...
  }
  ```

- **Option 2**: Formula-based
  ```json
  {
    "formula": "0.01 * 1.2^(entry-10)",
    "base_lot": 0.01,
    "multiplier": 1.2
  }
  ```

- **Option 3**: CSV file
  ```
  entry_number,lot_size
  10,0.01
  11,0.02
  12,0.03
  ```

### 4.2. Testing Multiple Scenarios
- Cho phép load nhiều config files
- So sánh kết quả giữa các scenarios
- Export kết quả để phân tích

## 🎯 5. Data Requirements

### 5.1. Input Data Format
- **Symbol**: XAUUSD
- **Timeframe**: Tùy chọn (H1, H4, D1...)
- **Required columns**:
  - Timestamp/Date
  - Open
  - High
  - Low
  - Close
  - Volume (optional)

### 5.2. Data Source
- CSV file
- Hoặc có thể mở rộng: API, database

## 🎯 6. Output Requirements

### 6.1. Báo cáo Tổng quan
- Tổng số entry đã vào (10-40)
- Tổng số entry đã đếm (1-9)
- Tổng P&L
- Win rate (% entry có lời)
- Max drawdown
- Số lần ngắt nhịp (RSI < 60)
- Số lần chốt thành công

### 6.2. Báo cáo Chi tiết
- **Per Entry**:
  - Entry number
  - Timestamp vào
  - Giá vào (entry price)
  - Lot size
  - RSI tại thời điểm vào
  - Giá chốt (exit price)
  - P&L của entry
  - Thời gian giữ lệnh

- **Per Cycle**:
  - Cycle ID
  - Entry range (ví dụ: entry 10-25)
  - Tổng P&L của cycle
  - Điểm ngắt nhịp (nếu có)
  - Điểm chốt

### 6.3. Export Formats
- CSV: Cho phân tích trong Excel
- JSON: Cho xử lý programmatic
- Summary report: Text/Markdown

## 🎯 7. Edge Cases cần xử lý

### 7.1. RSI Boundary
- RSI = 30.0 (Buy) hoặc 70.0 (Sell): Có tính là đạt điều kiện?
- RSI = 50.0 (Exit): Có tính là đạt điều kiện?
- → Cần config threshold với tolerance

### 7.2. Multiple RSI hits trong 1 nến
- Nếu RSI đạt điều kiện nhiều lần trong 1 nến?
- → Chỉ đếm 1 lần per nến

### 7.3. Data gaps
- Nếu thiếu dữ liệu giữa chừng?
- → Skip hoặc interpolate (cần config)

### 7.4. End of data
- Nếu hết dữ liệu mà chưa chốt?
- → Báo cáo lệnh đang mở

## 🎯 8. Performance Requirements

- Xử lý được dataset lớn (1+ năm dữ liệu H1)
- Thời gian backtest < 30 giây cho 1 năm
- Memory efficient

## 🎯 9. Testing Requirements

### 9.1. Unit Tests
- RSI calculation
- Entry counting logic
- Break detection (RSI < 60)
- Exit detection (RSI = 50)

### 9.2. Integration Tests
- Full backtest với sample data
- Multiple scenarios
- Edge cases

### 9.3. Validation
- So sánh kết quả với manual calculation
- Verify entry sequence
- Verify lot sizes


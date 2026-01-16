# Code Review: `gui.py`

**Ngày review:** $(date)  
**File:** `gui.py` (1190 dòng)  
**Trạng thái:** ✅ Không có lỗi linter

---

## 📊 Tổng quan

File `gui.py` là một GUI Tkinter phức tạp để chạy backtest XAUUSD với các tính năng:
- Điều chỉnh ngưỡng RSI (thủ công hoặc tự động tối ưu)
- Nhập dãy số tiền/lot cho từng entry
- Chạy backtest và hiển thị kết quả

**Đánh giá tổng thể:** ⭐⭐⭐⭐ (4/5) - Code tốt, nhưng có một số điểm cần cải thiện

---

## ✅ Điểm mạnh

1. **Cấu trúc code rõ ràng**
   - Tách biệt logic và UI
   - Functions độc lập, dễ test
   - Comments tiếng Việt rõ ràng

2. **Xử lý lỗi tốt**
   - Try/except đầy đủ
   - Error messages rõ ràng
   - Graceful degradation

3. **Threading đúng cách**
   - Backtest chạy trên thread riêng (dòng 1083)
   - UI không bị block
   - Sử dụng `self.after()` để update UI từ thread

4. **UX tốt**
   - Placeholder text
   - Status messages
   - Validation input
   - Scrollbar đồng bộ

---

## ⚠️ Vấn đề cần sửa

### 1. **Code Duplication: DictConfigWrapper** 🔴

**Vị trí:** Dòng 224-238

**Vấn đề:**
```python
class DictConfigWrapper:
    def __init__(self, data):
        self._data = data
    def get(self, key, default=None):
        # ... logic trùng với StrategyConfig
```

**Tác động:**
- Logic `get()` method trùng với `StrategyConfig.get()` (dòng 61-84 trong `strategy_config.py`)
- Khó maintain khi cần thay đổi logic config

**Giải pháp:**
- Option 1: Extract `DictConfigWrapper` ra module level hoặc utils
- Option 2: Tạo `StrategyConfig` từ dict (cần refactor `StrategyConfig` để hỗ trợ)
- Option 3: Import và reuse logic từ `StrategyConfig`

**Priority:** Medium

---

### 2. **Magic Numbers và Hardcoded Values** 🟡

**Vị trí:** Nhiều nơi

**Ví dụ:**
- `FIRST_TRADE_ENTRY = 1` (dòng 33) - OK, đã là constant
- `max_trade_entry = 40` (dòng 765) - Nên extract thành constant
- `buy_range=(30, 35)`, `sell_range=(65, 70)` (dòng 1040-1041) - Nên configurable

**Giải pháp:**
```python
# Thêm constants
MAX_TRADE_ENTRY = 40
DEFAULT_OPTIMIZE_BUY_RANGE = (30, 35)
DEFAULT_OPTIMIZE_SELL_RANGE = (65, 70)
DEFAULT_OPTIMIZE_STEP = 1.0
```

**Priority:** Low

---

### 3. **String Comparison với Placeholder** 🟡

**Vị trí:** Dòng 514, 660

**Vấn đề:**
```python
if content in [PLACEHOLDER_TEXT, "Paste số tiền vào đây\n(mỗi số một dòng)", "Paste số tiền vào đây", ""]:
```

**Tác động:**
- Hardcoded strings trùng với `PLACEHOLDER_TEXT`
- Dễ lỗi nếu thay đổi placeholder

**Giải pháp:**
```python
def is_placeholder_text(text):
    """Check if text is placeholder or empty"""
    if not text or not text.strip():
        return True
    # Normalize whitespace for comparison
    normalized = text.strip().replace('\r', '')
    return normalized == PLACEHOLDER_TEXT.replace('\r', '')
```

**Priority:** Low

---

### 4. **Error Handling trong Thread** 🟡

**Vị trí:** Dòng 1072-1081

**Vấn đề:**
- Exception handling tốt, nhưng có thể cải thiện error messages

**Hiện tại:**
```python
except (FileNotFoundError, ValueError, KeyError, AttributeError) as e:
    error_msg = f"Lỗi khi chạy backtest: {e}"
```

**Cải thiện:**
- Phân loại lỗi rõ ràng hơn
- Hướng dẫn user cách fix

**Priority:** Low

---

### 5. **Potential Race Condition** 🟡

**Vị trí:** Dòng 1033-1084

**Vấn đề:**
- Thread có thể access `self.lot_data`, `self.selected_data_file` sau khi user thay đổi

**Giải pháp:**
- Copy data vào local variables trước khi start thread:
```python
def run_in_thread():
    # Copy data để tránh race condition
    lot_data_copy = self.lot_data.copy()
    data_file_copy = self.selected_data_file
    direction_mode_copy = self.direction_var.get()
    # ... use copies
```

**Priority:** Medium

---

### 6. **Long Function: `on_apply_manual_input()`** 🟡

**Vị trí:** Dòng 654-801 (147 dòng)

**Vấn đề:**
- Function quá dài, khó maintain

**Giải pháp:**
- Extract methods:
  - `_parse_money_input()` - Parse text input
  - `_calculate_lot_sizes()` - Tính lot từ money
  - `_update_treeviews()` - Update UI
  - `_validate_entry_count()` - Validate số entry

**Priority:** Low

---

## 💡 Đề xuất cải thiện

### 1. **Type Hints**

Thêm type hints để code rõ ràng hơn:
```python
def run_backtest_with_params(
    buy_threshold: float,
    sell_threshold: float,
    lot_data: list[dict[str, float]],
    data_file_path: Optional[str] = None,
    silent: bool = False,
    direction_mode: str = "AUTO",
) -> dict[str, Any]:
```

### 2. **Constants File**

Tạo `gui_constants.py` cho các magic numbers:
```python
# gui_constants.py
FIRST_TRADE_ENTRY = 1
MAX_TRADE_ENTRY = 40
DEFAULT_XAUUSD_PRICE = 2000.0
DEFAULT_OPTIMIZE_BUY_RANGE = (30, 35)
DEFAULT_OPTIMIZE_SELL_RANGE = (65, 70)
```

### 3. **Logging thay vì print**

Sử dụng `logging` module thay vì `print()`:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Đang chạy backtest...")
```

### 4. **Unit Tests**

Thêm tests cho các functions quan trọng:
- `parse_money_input()`
- `calculate_lot_sizes()`
- `get_xauusd_average_price()`

---

## 📝 Checklist trước khi commit

- [ ] Refactor `DictConfigWrapper` để reuse code
- [ ] Extract magic numbers thành constants
- [ ] Fix potential race condition trong thread
- [ ] Thêm type hints cho các functions chính
- [ ] Test lại các tính năng:
  - [ ] Nhập số tiền và áp dụng
  - [ ] Chạy backtest thủ công
  - [ ] Chạy tối ưu RSI tự động
  - [ ] Lưu/tải lot data
  - [ ] Chọn file data

---

## 🎯 Priority Summary

| Priority | Issue | Effort | Impact |
|----------|-------|--------|--------|
| 🔴 High | - | - | - |
| 🟡 Medium | DictConfigWrapper duplication | Medium | Medium |
| 🟡 Medium | Race condition trong thread | Low | Medium |
| 🟡 Low | Magic numbers | Low | Low |
| 🟡 Low | Long function | Medium | Low |
| 🟡 Low | String comparison | Low | Low |

---

## ✅ Kết luận

Code **chất lượng tốt**, sẵn sàng commit với một số cải thiện nhỏ. Các vấn đề chính:
1. Code duplication (có thể fix nhanh)
2. Potential race condition (nên fix)
3. Magic numbers (nice to have)

**Khuyến nghị:** Fix các vấn đề Medium priority trước khi commit, các vấn đề Low priority có thể làm sau.


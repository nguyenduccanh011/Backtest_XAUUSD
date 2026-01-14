# 📖 Giải Thích Cách Đếm Entry - Dễ Hiểu

## 🎯 Tổng Quan

Hệ thống đếm entry giống như **đếm số lần RSI đạt điều kiện** trong một chu kỳ gồng lệnh. Mỗi lần đếm được gọi là một "entry".

---

## 📊 3 Nhóm Entry

### Nhóm 1: Entry 1-9 (Chỉ Đếm, Không Vào Lệnh)
- ✅ **Đếm**: Mỗi lần RSI đạt điều kiện → đếm +1
- ❌ **Không vào lệnh**: Lot size = 0 (không mất tiền)
- 🎯 **Mục đích**: Theo dõi xu hướng, chờ đến entry 10 mới bắt đầu vào lệnh

### Nhóm 2: Entry 10-40 (Vào Lệnh Thực Sự)
- ✅ **Đếm**: Tiếp tục đếm như bình thường
- ✅ **Vào lệnh**: Mỗi entry vào lệnh với lot size tùy chỉnh
- 🎯 **Mục đích**: Đây là giai đoạn gồng lệnh chính, vào nhiều lệnh để trung bình giá

### Nhóm 3: Entry 41+ (Dừng Vào, Chờ Chốt)
- ✅ **Đếm**: Vẫn đếm tiếp nếu RSI đạt điều kiện
- ❌ **Không vào lệnh**: Dừng vào lệnh mới
- 🎯 **Mục đích**: Đã đủ lệnh, chỉ chờ điều kiện chốt (RSI = 50)

---

## 🔄 Logic Đếm Liên Tục

### ⚠️ QUY TẮC QUAN TRỌNG: Nhịp RSI Bắt Buộc

**Giữa mỗi entry PHẢI có nhịp RSI không đạt điều kiện!**

- **SELL**: Giữa Entry N và Entry N+1, RSI PHẢI xuống < 70 (ít nhất 1 nến)
- **BUY**: Giữa Entry N và Entry N+1, RSI PHẢI lên > 30 (ít nhất 1 nến)

**Tại sao?** Để đảm bảo mỗi entry là một "lần đảo chiều" thực sự, không phải liên tiếp.

---

### Ví Dụ 1: Đếm Bình Thường (Không Ngắt Nhịp)

**Giả sử chiến lược SELL (RSI >= 70 để vào):**

```
Thời gian    RSI    Hành động                    Entry số
─────────────────────────────────────────────────────────
Nến 1        RSI = 75 → Đạt điều kiện            Entry 1 (đếm, không vào)
Nến 2        RSI = 65 → ⚠️ NHỊP < 70 (bắt buộc)   Chờ...
Nến 3        RSI = 68 → Vẫn < 70                 Chờ...
Nến 4        RSI = 72 → Đạt điều kiện            Entry 2 (đếm, không vào)
Nến 5        RSI = 69 → ⚠️ NHỊP < 70 (bắt buộc)   Chờ...
Nến 6        RSI = 71 → Đạt điều kiện            Entry 3 (đếm, không vào)
Nến 7        RSI = 68 → ⚠️ NHỊP < 70 (bắt buộc)   Chờ...
Nến 8        RSI = 73 → Đạt điều kiện            Entry 4 (đếm, không vào)
...
Nến 20       RSI = 70 → Đạt điều kiện            Entry 9 (đếm, không vào)
Nến 21       RSI = 65 → ⚠️ NHỊP < 70 (bắt buộc)   Chờ...
Nến 22       RSI = 74 → Đạt điều kiện            Entry 10 (đếm + VÀO LỆNH 0.01 lot)
Nến 23       RSI = 68 → ⚠️ NHỊP < 70 (bắt buộc)   Chờ...
Nến 24       RSI = 70 → Đạt điều kiện            Entry 11 (đếm + VÀO LỆNH 0.02 lot)
```

**Giải thích:**
- Mỗi entry đều có **nhịp RSI < 70** ở giữa (bắt buộc)
- RSI dao động nhưng **KHÔNG chạm < 60** (ngưỡng ngắt nhịp)
- → Hệ thống **TIẾP TỤC ĐẾM** khi RSI quay lại >= 70
- → Chuỗi đếm không bị ngắt

---

### Ví Dụ 2: Ngắt Nhịp (Break Logic)

**Giả sử chiến lược SELL (RSI >= 70 để vào):**

```
Thời gian    RSI    Hành động                    Entry số
─────────────────────────────────────────────────────────
Nến 1        RSI = 75 → Đạt điều kiện            Entry 1 (đếm, không vào)
Nến 2        RSI = 68 → ⚠️ NHỊP < 70 (bắt buộc)   Chờ...
Nến 3        RSI = 72 → Đạt điều kiện            Entry 2 (đếm, không vào)
Nến 4        RSI = 65 → ⚠️ NHỊP < 70 (bắt buộc)   Chờ...
Nến 5        RSI = 70 → Đạt điều kiện            Entry 3 (đếm, không vào)
Nến 6        RSI = 58 → ⚠️ CHẠM < 60             NGẮT NHỊP!
Nến 7        RSI = 55 → Vẫn < 60                 Chờ chốt (RSI = 50)
Nến 8        RSI = 52 → Gần 50, chưa chốt       Chờ...
Nến 9        RSI = 50 → ✅ ĐẠT ĐIỀU KIỆN CHỐT    Chốt tất cả lệnh
Nến 10       RSI = 48 → Sau khi chốt             RESET, bắt đầu lại từ Entry 1
Nến 11       RSI = 75 → Đạt điều kiện            Entry 1 mới (chu kỳ mới)
```

**Giải thích:**
- Mỗi entry vẫn có nhịp RSI < 70 ở giữa (bắt buộc)
- Khi RSI chạm < 60 → **NGẮT NHỊP ĐẾM**
- → Dừng đếm entry mới, chỉ chờ điều kiện chốt (RSI = 50)
- → Sau khi chốt → **RESET** và bắt đầu đếm lại từ Entry 1

---

## 🎯 Ví Dụ Hoàn Chỉnh: 1 Chu Kỳ SELL

### Timeline Chi Tiết

```
┌─────────────────────────────────────────────────────────────┐
│ CHU KỲ SELL - Bắt đầu khi RSI >= 70                         │
└─────────────────────────────────────────────────────────────┘

Entry 1-9:  Chỉ đếm, không vào lệnh
────────────────────────────────────
Nến 1:  RSI = 75 → Entry 1 (đếm)
Nến 2-4: RSI = 65-68 → ⚠️ NHỊP < 70 (bắt buộc)
Nến 5:  RSI = 72 → Entry 2 (đếm)
Nến 6-7: RSI = 68-69 → ⚠️ NHỊP < 70 (bắt buộc)
Nến 8:  RSI = 71 → Entry 3 (đếm)
Nến 9-11: RSI = 66-69 → ⚠️ NHỊP < 70 (bắt buộc)
Nến 12: RSI = 73 → Entry 4 (đếm)
Nến 13-14: RSI = 68-69 → ⚠️ NHỊP < 70 (bắt buộc)
Nến 15: RSI = 70 → Entry 5 (đếm)
Nến 16-17: RSI = 65-67 → ⚠️ NHỊP < 70 (bắt buộc)
Nến 18: RSI = 74 → Entry 6 (đếm)
Nến 19: RSI = 68 → ⚠️ NHỊP < 70 (bắt buộc)
Nến 20: RSI = 72 → Entry 7 (đếm)
Nến 21-22: RSI = 69 → ⚠️ NHỊP < 70 (bắt buộc)
Nến 23: RSI = 71 → Entry 8 (đếm)
Nến 24: RSI = 66 → ⚠️ NHỊP < 70 (bắt buộc)
Nến 25: RSI = 73 → Entry 9 (đếm)

Entry 10-40: Vào lệnh thực sự
────────────────────────────────────
Nến 26-27: RSI = 68-69 → ⚠️ NHỊP < 70 (bắt buộc)
Nến 28: RSI = 74 → Entry 10 (đếm + VÀO LỆNH 0.01 lot @ $2000)
Nến 29: RSI = 65 → ⚠️ NHỊP < 70 (bắt buộc)
Nến 30: RSI = 70 → Entry 11 (đếm + VÀO LỆNH 0.02 lot @ $1995)
Nến 31: RSI = 68 → ⚠️ NHỊP < 70 (bắt buộc)
Nến 32: RSI = 72 → Entry 12 (đếm + VÀO LỆNH 0.03 lot @ $1990)
...
Nến 48-49: RSI = 67-69 → ⚠️ NHỊP < 70 (bắt buộc)
Nến 50: RSI = 71 → Entry 20 (đếm + VÀO LỆNH 0.11 lot @ $1950)
...
Nến 78-79: RSI = 68-69 → ⚠️ NHỊP < 70 (bắt buộc)
Nến 80: RSI = 70 → Entry 40 (đếm + VÀO LỆNH 0.31 lot @ $1900)

Entry 41+: Dừng vào, chờ chốt
────────────────────────────────────
Nến 81-84: RSI = 66-69 → ⚠️ NHỊP < 70 (bắt buộc)
Nến 85: RSI = 72 → Entry 41 (chỉ đếm, KHÔNG vào lệnh)
Nến 86-89: RSI = 65-68 → ⚠️ NHỊP < 70 (bắt buộc)
Nến 90: RSI = 71 → Entry 42 (chỉ đếm, KHÔNG vào lệnh)
Nến 91-94: RSI = 58-62 → ⚠️ NGẮT NHỊP (RSI < 60)
Nến 95: RSI = 58 → ⚠️ NGẮT NHỊP (RSI < 60)
Nến 100: RSI = 52 → Chờ chốt...
Nến 105: RSI = 50 → ✅ CHỐT TẤT CẢ LỆNH @ $1920

Kết quả:
- Tổng entry đã vào: 31 lệnh (entry 10-40)
- Tổng lot: 4.96 lot
- Giá trung bình vào: ~$1970
- Giá chốt: $1920
- P&L: Tính theo công thức XAUUSD
```

---

### Ví Dụ 3: RSI Liên Tục Đạt Điều Kiện (KHÔNG Đếm Entry Tiếp Theo)

**Giả sử chiến lược SELL (RSI >= 70 để vào):**

```
Thời gian    RSI    Hành động                    Entry số
─────────────────────────────────────────────────────────
Nến 1        RSI = 75 → Đạt điều kiện            Entry 1 (đếm, không vào)
Nến 2        RSI = 72 → ⚠️ Vẫn >= 70, KHÔNG có nhịp < 70
Nến 3        RSI = 74 → ⚠️ Vẫn >= 70, KHÔNG có nhịp < 70
Nến 4        RSI = 71 → ⚠️ Vẫn >= 70, KHÔNG có nhịp < 70
Nến 5        RSI = 73 → ⚠️ Vẫn >= 70, KHÔNG có nhịp < 70
            → ❌ KHÔNG ĐẾM Entry 2 (thiếu nhịp < 70)
Nến 6        RSI = 68 → ✅ NHỊP < 70 (bắt buộc)
Nến 7        RSI = 70 → Đạt điều kiện            Entry 2 (đếm, không vào)
```

**Giải thích:**
- Nến 1: RSI = 75 → Entry 1 được đếm
- Nến 2-5: RSI liên tục >= 70 → **KHÔNG có nhịp < 70**
- → Hệ thống **KHÔNG đếm Entry 2** cho đến khi có nhịp RSI < 70
- Nến 6: RSI = 68 → Có nhịp < 70 (bắt buộc)
- Nến 7: RSI = 70 → Entry 2 được đếm (sau khi có nhịp)

**Kết luận:** Mỗi entry phải có nhịp RSI không đạt điều kiện ở giữa. Nếu RSI liên tục đạt điều kiện, hệ thống chỉ đếm Entry đầu tiên.

---

## 🔍 Các Trường Hợp Đặc Biệt

### Trường Hợp 1: Khoảng Trống Giữa Các Entry

**Vấn đề:** Giữa Entry 5 và Entry 6 có thể cách nhau 10-20 nến mà RSI không đạt điều kiện.

**Giải pháp:**
- ✅ Hệ thống **ĐỢI** đến khi RSI đạt điều kiện mới đếm Entry 6
- ✅ **BẮT BUỘC**: Phải có nhịp RSI không đạt điều kiện giữa Entry 5 và Entry 6
- ✅ Không bỏ qua entry nào trong sequence
- ✅ Entry 6 vẫn là Entry 6, không nhảy thành Entry 7

**Ví dụ:**
```
Entry 5: Nến 25, RSI = 73
[Nến 26-35: RSI = 65-68, ⚠️ NHỊP < 70 (bắt buộc)]
Entry 6: Nến 36, RSI = 71 → Vẫn là Entry 6, không nhảy số
```

**Lưu ý:** Nếu RSI liên tục >= 70 (không có nhịp < 70), hệ thống **KHÔNG** đếm Entry tiếp theo cho đến khi có nhịp.

---

### Trường Hợp 2: Ngắt Nhịp Sớm (Trước Entry 10)

**Vấn đề:** Nếu ngắt nhịp ở Entry 5 (chưa vào lệnh nào), thì sao?

**Giải pháp:**
- ✅ Vẫn chờ chốt (RSI = 50)
- ✅ Không có lệnh nào để chốt → chốt rỗng
- ✅ Sau đó reset và bắt đầu lại từ Entry 1

**Ví dụ:**
```
Entry 1-5: Đã đếm (không vào lệnh)
Nến X: RSI = 58 → NGẮT NHỊP
Nến Y: RSI = 50 → Chốt (không có lệnh nào)
→ Reset, bắt đầu lại Entry 1
```

---

### Trường Hợp 3: RSI Không Bao Giờ Về 50

**Vấn đề:** Nếu RSI không bao giờ về 50, lệnh treo mãi?

**Giải pháp (theo REVIEW.md):**
- Có thể thêm `timeout_bars` (ví dụ: 500 nến)
- Nếu quá timeout → force close với giá hiện tại
- Hoặc báo cáo "lệnh đang mở" khi hết dữ liệu

---

## 📝 Tóm Tắt Ngắn Gọn

1. **Entry 1-9**: Đếm để theo dõi, chưa vào lệnh
2. **Entry 10-40**: Vào lệnh thực sự với lot size tùy chỉnh
3. **Entry 41+**: Dừng vào, chỉ chờ chốt
4. **⚠️ NHỊP BẮT BUỘC**: Giữa mỗi entry PHẢI có nhịp RSI không đạt điều kiện
   - SELL: RSI phải xuống < 70 giữa các entry
   - BUY: RSI phải lên > 30 giữa các entry
5. **Ngắt nhịp**: RSI < 60 (Sell) hoặc > 40 (Buy) → dừng đếm, chờ chốt
6. **Tiếp tục đếm**: RSI không chạm break threshold → tiếp tục đếm khi đạt điều kiện (có nhịp)
7. **Reset**: Sau khi chốt → reset về Entry 1, bắt đầu chu kỳ mới

---

## 🎨 Sơ Đồ Logic Đơn Giản

```
BẮT ĐẦU
  ↓
RSI đạt điều kiện? (<= 30 Buy hoặc >= 70 Sell)
  ↓ CÓ
Đếm Entry N
  ↓
Entry N thuộc nhóm nào?
  ├─ 1-9:   Chỉ đếm, không vào lệnh
  ├─ 10-40: Đếm + VÀO LỆNH
  └─ 41+:   Chỉ đếm, không vào lệnh
  ↓
RSI có ngắt nhịp? (< 60 Sell hoặc > 40 Buy)
  ├─ CÓ:    Dừng đếm → Chờ chốt (RSI = 50) → Reset → Bắt đầu lại
  └─ KHÔNG: 
      ↓
      ⚠️ CÓ NHỊP RSI KHÔNG ĐẠT ĐIỀU KIỆN? (BẮT BUỘC)
      ├─ CÓ:    Đợi RSI đạt điều kiện lại → Đếm Entry N+1
      └─ KHÔNG: Tiếp tục đợi (chưa đếm Entry N+1)
```

---

## ❓ Câu Hỏi Thường Gặp

**Q: Entry 1-9 có ý nghĩa gì? Tại sao không vào lệnh luôn?**  
A: Đây là giai đoạn "warm-up" để xác nhận xu hướng. Chỉ khi đếm đủ 9 lần mới bắt đầu vào lệnh thực sự (từ Entry 10).

**Q: Nếu Entry 10-40 đã vào đủ 31 lệnh, Entry 41+ có cần đếm không?**  
A: Có, vẫn đếm để theo dõi. Nhưng không vào lệnh mới nữa, chỉ chờ điều kiện chốt.

**Q: Ngắt nhịp có nghĩa là gì?**  
A: Ngắt nhịp = RSI đã "phá vỡ" xu hướng (ví dụ: từ > 70 xuống < 60). Lúc này không nên vào lệnh tiếp, chỉ chờ chốt.

**Q: Sau khi chốt, có thể tiếp tục đếm Entry 42, 43... không?**  
A: Không. Sau khi chốt → **RESET** về Entry 1, bắt đầu chu kỳ mới hoàn toàn.

**Q: Tại sao phải có nhịp RSI không đạt điều kiện giữa các entry?**  
A: Để đảm bảo mỗi entry là một "lần đảo chiều" thực sự. Nếu RSI liên tục đạt điều kiện (ví dụ: SELL liên tục >= 70), hệ thống chỉ đếm Entry đầu tiên, không đếm tiếp cho đến khi có nhịp RSI < 70 rồi quay lại >= 70.

**Q: Nếu RSI liên tục >= 70 (không có nhịp < 70), có đếm Entry tiếp theo không?**  
A: **KHÔNG**. Hệ thống sẽ đợi đến khi RSI xuống < 70 (nhịp bắt buộc), rồi quay lại >= 70 mới đếm Entry tiếp theo.

---

## 📚 Tài Liệu Liên Quan

- `requirements.md` - Chi tiết kỹ thuật đầy đủ
- `project_overview.md` - Kiến trúc tổng quan
- `REVIEW.md` - Đánh giá và đề xuất cải thiện


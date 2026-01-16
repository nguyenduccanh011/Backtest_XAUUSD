"""
Đơn giản GUI cho Backtest XAUUSD

- Cho phép chỉnh:
  - RSI Buy threshold
  - RSI Sell threshold
  - Dãy số tiền vào lệnh / lot cho từng STT lệnh (Entry 1-40)
    Lưu ý: Entry 1-9 mặc định chỉ đếm, Entry 10-40 vào lệnh nếu > 0
    Ví dụ: Nhập 10 số 0 → Entry 1-10 đều chỉ đếm, không vào lệnh
- Gọi lại backtest và hiển thị kết quả tóm tắt.
"""

import json
import re
import threading
import traceback
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional

from pathlib import Path

from src.utils.data_loader import DataLoader
from src.strategy.dca_strategy import DCAStrategy
from src.backtest.portfolio import Portfolio
from src.backtest.engine import BacktestEngine


CONFIG_PATH = Path("configs/default_config.json")

# Constants
DEFAULT_XAUUSD_PRICE = 2000.0
FIRST_TRADE_ENTRY = 1  # Entry bắt đầu từ 1 (user nhập từ entry 1)
MAX_TRADE_ENTRY = 40  # Entry tối đa có thể vào lệnh (Entry 10-40)
ENTRY_COUNT_ONLY_START = 1  # Entry bắt đầu chỉ đếm
ENTRY_COUNT_ONLY_END = 9  # Entry kết thúc chỉ đếm
ENTRY_TRADE_START = 10  # Entry bắt đầu có thể vào lệnh
ENTRY_TRADE_END = 40  # Entry kết thúc có thể vào lệnh
ENTRY_WAIT_EXIT_START = 41  # Entry bắt đầu chờ exit

# RSI Optimization defaults
DEFAULT_OPTIMIZE_BUY_RANGE = (30, 35)
DEFAULT_OPTIMIZE_SELL_RANGE = (65, 70)
DEFAULT_OPTIMIZE_STEP = 1.0

PLACEHOLDER_TEXT = "Paste số tiền vào đây\n(mỗi số một dòng)\n\nLưu ý:\n- Entry 1-9: Mặc định chỉ đếm\n- Entry 10-40: Vào lệnh nếu > 0\n- Nhập 0 = chỉ đếm, không vào lệnh"


class DictConfigWrapper:
    """
    Wrapper để convert dict thành config-like object với method get().
    Reuse logic từ StrategyConfig để tránh code duplication.
    """
    def __init__(self, data):
        self._data = data

    def get(self, key, default=None):
        """
        Get config value by key (supports nested keys with dot notation).
        Logic giống StrategyConfig.get() để đảm bảo consistency.
        """
        if not self._data:
            return default
        
        keys = key.split(".")
        value = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value


def is_placeholder_text(text):
    """
    Check if text is placeholder or empty.
    
    Args:
        text: Text to check
        
    Returns:
        bool: True if text is placeholder or empty
    """
    if not text or not text.strip():
        return True
    # Normalize whitespace for comparison
    normalized = text.strip().replace('\r', '')
    return normalized == PLACEHOLDER_TEXT.replace('\r', '')


def get_xauusd_average_price(data_file_path=None):
    """
    Lấy giá trung bình của XAUUSD từ file data.
    
    Args:
        data_file_path: Đường dẫn file data CSV
    
    Returns:
        float: Giá trung bình, hoặc 2000 nếu không lấy được
    """
    if data_file_path and Path(data_file_path).exists():
        try:
            loader = DataLoader()
            df = loader.load_csv(data_file_path, source="auto")
            if 'close' in df.columns:
                avg_price = df['close'].mean()
                return float(avg_price)
        except (FileNotFoundError, ValueError, KeyError, AttributeError, OSError) as e:
            # Lỗi khi load file hoặc xử lý dữ liệu - dùng giá mặc định
            print(f"⚠️ Không thể lấy giá XAUUSD từ file: {e}")
            pass
    
    # Giá mặc định
    return DEFAULT_XAUUSD_PRICE


def optimize_rsi_thresholds(
    lot_data: list,
    data_file_path: str = None,
    buy_range: tuple = None,
    sell_range: tuple = None,
    step: float = None,
    direction_mode: str = "AUTO",
):
    """
    Tối ưu ngưỡng RSI bằng cách test nhiều giá trị và chọn giá trị tốt nhất.
    
    Args:
        lot_data: Danh sách lot data
        data_file_path: Đường dẫn file data
        buy_range: Khoảng giá trị RSI cho BUY (min, max), default: DEFAULT_OPTIMIZE_BUY_RANGE
        sell_range: Khoảng giá trị RSI cho SELL (min, max), default: DEFAULT_OPTIMIZE_SELL_RANGE
        step: Bước nhảy giữa các giá trị, default: DEFAULT_OPTIMIZE_STEP
        direction_mode: Hướng vào lệnh (AUTO/BUY/SELL)
    
    Returns:
        dict: Kết quả tốt nhất với keys: 'buy_threshold', 'sell_threshold', 'summary', 'all_results'
    """
    # Sử dụng defaults nếu không được cung cấp
    if buy_range is None:
        buy_range = DEFAULT_OPTIMIZE_BUY_RANGE
    if sell_range is None:
        sell_range = DEFAULT_OPTIMIZE_SELL_RANGE
    if step is None:
        step = DEFAULT_OPTIMIZE_STEP
    
    print("\n" + "=" * 60)
    print("🔍 BẮT ĐẦU TỐI ƯU NGƯỠNG RSI")
    print("=" * 60)
    print(f"   BUY range: {buy_range[0]} - {buy_range[1]} (step: {step})")
    print(f"   SELL range: {sell_range[0]} - {sell_range[1]} (step: {step})")
    print("=" * 60)
    
    best_result = None
    best_pnl = float('-inf')
    all_results = []
    
    # Tạo danh sách giá trị để test
    buy_values = [round(buy_range[0] + i * step, 1) for i in range(int((buy_range[1] - buy_range[0]) / step) + 1)]
    sell_values = [round(sell_range[0] + i * step, 1) for i in range(int((sell_range[1] - sell_range[0]) / step) + 1)]
    
    total_tests = len(buy_values) * len(sell_values)
    current_test = 0
    
    for buy_th in buy_values:
        for sell_th in sell_values:
            current_test += 1
            print(f"\n📊 Test {current_test}/{total_tests}: BUY={buy_th}, SELL={sell_th}")
            
            try:
                summary = run_backtest_with_params(
                    buy_th,
                    sell_th,
                    lot_data,
                    data_file_path,
                    silent=True,
                    direction_mode=direction_mode,
                )
                pnl = summary.get('total_pnl', 0)
                
                result = {
                    'buy_threshold': buy_th,
                    'sell_threshold': sell_th,
                    'summary': summary,
                    'total_pnl': pnl
                }
                all_results.append(result)
                
                print(f"   → Total P&L: ${pnl:,.2f}")
                
                # Cập nhật kết quả tốt nhất
                if pnl > best_pnl:
                    best_pnl = pnl
                    best_result = result
                    print(f"   ✅ MỚI: Kết quả tốt nhất hiện tại!")
                    
            except (FileNotFoundError, ValueError, KeyError, AttributeError) as e:
                # Lỗi khi chạy backtest với tham số này - bỏ qua và tiếp tục test tiếp theo
                print(f"   ❌ Lỗi: {e}")
                continue
            except Exception as e:
                # Lỗi không lường trước - log và tiếp tục
                print(f"   ❌ Lỗi không xác định: {e}")
                traceback.print_exc()
                continue
    
    print("\n" + "=" * 60)
    print("✅ HOÀN THÀNH TỐI ƯU")
    print("=" * 60)
    if best_result:
        print(f"🏆 KẾT QUẢ TỐT NHẤT:")
        print(f"   BUY threshold: {best_result['buy_threshold']}")
        print(f"   SELL threshold: {best_result['sell_threshold']}")
        print(f"   Total P&L: ${best_result['total_pnl']:,.2f}")
        print(f"   Total Return: {best_result['summary'].get('total_return', 'N/A')}")
    print("=" * 60 + "\n")
    
    return {
        'buy_threshold': best_result['buy_threshold'] if best_result else buy_range[0],
        'sell_threshold': best_result['sell_threshold'] if best_result else sell_range[0],
        'summary': best_result['summary'] if best_result else {},
        'all_results': all_results
    }


def run_backtest_with_params(
    buy_threshold: float,
    sell_threshold: float,
    lot_data: list,
    data_file_path: str = None,
    silent: bool = False,
    direction_mode: str = "AUTO",
    entry_rsi: Optional[float] = None,
    exit_rsi: Optional[float] = None,
    break_rsi: Optional[float] = None,
):
    """
    Chạy backtest với ngưỡng RSI mới và dãy lot/tiền theo STT lệnh.

    lot_data: danh sách dict với keys: 'entry_number', 'money_amount', 'lot_size'
      - Ví dụ: [{'entry_number': 2, 'money_amount': 54, 'lot_size': 0.00027}, ...]
    data_file_path: đường dẫn file data (nếu None thì dùng từ config)
    silent: Nếu True, không in thông tin debug ra console
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy file config: {CONFIG_PATH}")

    # Load config gốc
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    # Cập nhật ngưỡng RSI vào lệnh (entry)
    config_data.setdefault("strategy", {}).setdefault("rsi_entry_threshold", {})
    config_data["strategy"]["rsi_entry_threshold"]["buy"] = float(buy_threshold)
    config_data["strategy"]["rsi_entry_threshold"]["sell"] = float(sell_threshold)

    # Cập nhật hướng vào lệnh (AUTO / BUY / SELL) từ GUI
    config_data["strategy"]["direction_mode"] = str(direction_mode).upper()

    # Nếu người dùng nhập 3 mốc RSI thủ công, cập nhật lại config cho đúng hướng
    dir_upper = config_data["strategy"]["direction_mode"]
    if entry_rsi is not None:
        if dir_upper == "BUY":
            config_data["strategy"]["rsi_entry_threshold"]["buy"] = float(entry_rsi)
        elif dir_upper == "SELL":
            config_data["strategy"]["rsi_entry_threshold"]["sell"] = float(entry_rsi)

    if exit_rsi is not None:
        config_data.setdefault("strategy", {}).setdefault("rsi_exit", {})
        config_data["strategy"]["rsi_exit"]["threshold"] = float(exit_rsi)

    if break_rsi is not None:
        config_data.setdefault("strategy", {}).setdefault("rsi_break_threshold", {})
        if dir_upper == "BUY":
            config_data["strategy"]["rsi_break_threshold"]["buy"] = float(break_rsi)
        elif dir_upper == "SELL":
            config_data["strategy"]["rsi_break_threshold"]["sell"] = float(break_rsi)

    # Cập nhật lot_sizes từ lot_data
    lot_sizes = config_data.setdefault("lot_sizes", {})
    for item in lot_data:
        entry_num = item.get('entry_number', 2)
        lot_size = item.get('lot_size', 0.01)
        lot_sizes[f"entry_{entry_num}"] = float(lot_size)

    # Tạo config wrapper từ dict đã chỉnh (reuse DictConfigWrapper class)
    cfg = DictConfigWrapper(config_data)

    # Load data
    if not silent:
        print("\n" + "=" * 50)
        print("🚀 Bắt đầu chạy backtest từ GUI...")
        print("=" * 50)
    
    loader = DataLoader()
    # Sử dụng file đã chọn nếu có, nếu không thì dùng từ config
    if data_file_path:
        data_file = data_file_path
    else:
        data_file = cfg.get("data.data_file", "data/raw/xauusd_h1.csv")
    if not silent:
        print(f"📂 Đang load dữ liệu từ: {data_file}")
    df = loader.load_csv(data_file, source="auto")
    if not silent:
        print(f"✅ Đã load {len(df):,} nến dữ liệu")

    # Khởi tạo components
    if not silent:
        print("🔧 Đang khởi tạo components...")
    portfolio_cfg = cfg.get("portfolio", {}) or {}
    initial_capital = portfolio_cfg.get("initial_capital", 10000)
    portfolio = Portfolio(initial_capital=initial_capital)
    strategy = DCAStrategy(cfg)
    engine = BacktestEngine(config=cfg, data=df, strategy=strategy, portfolio=portfolio)
    if not silent:
        print("✅ Components đã sẵn sàng")
    
    # Chạy backtest
    if not silent:
        print(f"\n🚀 Đang chạy backtest trên {len(df):,} nến...")
        print("   (Quá trình này có thể mất vài phút, vui lòng đợi...)\n")
    results = engine.run()
    report = engine.generate_report()
    summary = report["summary"]
    
    if not silent:
        print("\n" + "=" * 50)
        print("✅ Backtest hoàn thành!")
        print("=" * 50)
        print(f"   Total Entries: {summary['total_entries']}")
        print(f"   Total Trades: {summary['total_trades']}")
        print(f"   Total P&L: ${summary['total_pnl']:,.2f}")
        print(f"   Total Return: {summary['total_return']}")
        print("=" * 50 + "\n")

    # Trả về tóm tắt cần cho GUI
    results_dict = results if isinstance(results, dict) else {}
    return {
        "total_entries": summary["total_entries"],
        "total_trades": summary["total_trades"],
        "total_pnl": summary["total_pnl"],
        "total_return": summary["total_return"],
        "initial_capital": summary["initial_capital"],
        "final_equity": summary["final_equity"],
        "buy_entries": results_dict.get("buy_entries", 0),
        "sell_entries": results_dict.get("sell_entries", 0),
        "buy_trades": results_dict.get("buy_trades", 0),
        "sell_trades": results_dict.get("sell_trades", 0),
    }


class BacktestGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Backtest XAUUSD - GUI đơn giản")
        # Đặt kích thước cửa sổ theo tỉ lệ như hình (rộng hơn cao)
        # Tỷ lệ: RSI (1), Lots (3), Buttons (0.5), Results (2)
        initial_width = 1300
        initial_height = 850
        self.geometry(f"{initial_width}x{initial_height}")
        # Cho phép resize cửa sổ
        self.minsize(1000, 600)
        # Đặt cửa sổ ở giữa màn hình
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Biến lưu đường dẫn file data đã chọn
        self.selected_data_file = None
        # Dữ liệu lot từ nhập thủ công
        self.lot_data = []
        # Đường dẫn file dữ liệu số tiền đã lưu
        self.saved_lot_data_file = None

        self._build_widgets()

    def _build_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Sử dụng grid để kiểm soát tỷ lệ chính xác
        # Giảm chiều cao khu vực 3 cột nhập tiền, tăng chiều cao khu vực kết quả tóm tắt
        main_frame.grid_rowconfigure(1, weight=1)  # Lots frame: thấp hơn
        main_frame.grid_rowconfigure(3, weight=4)  # Results frame: cao hơn
        main_frame.grid_columnconfigure(0, weight=1)

        # Hàng 1: RSI thresholds - Thiết kế rõ ràng cho BUY và SELL
        rsi_frame = ttk.LabelFrame(main_frame, text="📊 Ngưỡng RSI vào lệnh")
        rsi_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # Chọn hướng vào lệnh (BUY hoặc SELL) – đưa lên trên cùng
        direction_frame = ttk.Frame(rsi_frame)
        direction_frame.pack(fill="x", padx=5, pady=(5, 5))
        ttk.Label(
            direction_frame,
            text="Hướng vào lệnh:",
            font=("Arial", 9, "bold"),
        ).pack(side="left", padx=(0, 5))
        self.direction_var = tk.StringVar(value="BUY")
        # Dùng Radiobutton kiểu nút bấm (indicatoron=0) để bỏ vòng tròn trước chữ
        tk.Radiobutton(
            direction_frame,
            text="🟢 BUY",
            variable=self.direction_var,
            value="BUY",
            indicatoron=0,
            relief="raised",
            padx=5,
            pady=1,
            command=self.on_direction_change,
        ).pack(side="left", padx=5)
        tk.Radiobutton(
            direction_frame,
            text="🔴 SELL",
            variable=self.direction_var,
            value="SELL",
            indicatoron=0,
            relief="raised",
            padx=5,
            pady=1,
            command=self.on_direction_change,
        ).pack(side="left", padx=5)

        # Tùy chọn: Tự động tối ưu hoặc nhập thủ công
        mode_frame = ttk.Frame(rsi_frame)
        mode_frame.pack(fill="x", padx=5, pady=5)
        # Mặc định: NHẬP THỦ CÔNG; nếu muốn mới chọn tự động tối ưu
        self.rsi_auto_mode = tk.BooleanVar(value=False)
        ttk.Radiobutton(
            mode_frame,
            text="✏️ Nhập thủ công (3 mốc RSI)",
            variable=self.rsi_auto_mode,
            value=False,
            command=self.on_rsi_mode_change,
        ).pack(side="left", padx=5)
        ttk.Radiobutton(
            mode_frame,
            text="🤖 Tự động tối ưu (BUY: 30-35, SELL: 65-70)",
            variable=self.rsi_auto_mode,
            value=True,
            command=self.on_rsi_mode_change,
        ).pack(side="left", padx=5)

        # Khối nhập 3 mốc RSI cho hướng được chọn
        thresholds_frame = ttk.Frame(rsi_frame)
        thresholds_frame.pack(fill="x", padx=5, pady=(0, 5))

        self.rsi_entry_var = tk.StringVar(value="35")
        self.rsi_exit_var = tk.StringVar(value="50")
        self.rsi_break_var = tk.StringVar(value="40")

        self.rsi_entry_label = ttk.Label(
            thresholds_frame, text="RSI vào lệnh (BUY):", font=("Arial", 8)
        )
        self.rsi_entry_label.grid(row=0, column=0, sticky="w", padx=(0, 5), pady=2)
        self.rsi_entry_entry = ttk.Entry(
            thresholds_frame, textvariable=self.rsi_entry_var, width=8
        )
        self.rsi_entry_entry.grid(row=0, column=1, sticky="w", padx=(0, 10), pady=2)

        self.rsi_exit_label = ttk.Label(
            thresholds_frame, text="RSI đóng lệnh:", font=("Arial", 8)
        )
        self.rsi_exit_label.grid(row=0, column=2, sticky="w", padx=(0, 5), pady=2)
        self.rsi_exit_entry = ttk.Entry(
            thresholds_frame, textvariable=self.rsi_exit_var, width=8
        )
        self.rsi_exit_entry.grid(row=0, column=3, sticky="w", padx=(0, 10), pady=2)

        self.rsi_break_label = ttk.Label(
            thresholds_frame, text="RSI dừng vào lệnh:", font=("Arial", 8)
        )
        self.rsi_break_label.grid(row=0, column=4, sticky="w", padx=(0, 5), pady=2)
        self.rsi_break_entry = ttk.Entry(
            thresholds_frame, textvariable=self.rsi_break_var, width=8
        )
        self.rsi_break_entry.grid(row=0, column=5, sticky="w", padx=(0, 10), pady=2)

        self.rsi_info_label = ttk.Label(
            thresholds_frame,
            text="MUA: vào lệnh khi RSI ≤ mốc 1, chốt khi RSI ≈ mốc 2, dừng đếm khi RSI > mốc 3",
            font=("Arial", 8),
            foreground="gray",
        )
        self.rsi_info_label.grid(row=1, column=0, columnspan=6, sticky="w", pady=(2, 0))

        # Hàng 2: Lot / số tiền vào lệnh - chiếm phần lớn không gian
        lots_frame = ttk.LabelFrame(main_frame, text="Dãy lot / số tiền vào lệnh (Entry 1-9: mặc định chỉ đếm | Entry 10-40: vào lệnh nếu > 0)")
        lots_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Header với các nút: Lưu, Tải, Cập nhật, Áp dụng
        header_frame = ttk.Frame(lots_frame)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        # Nhóm nút bên trái: Lưu, Tải, Cập nhật
        left_buttons = ttk.Frame(header_frame)
        left_buttons.pack(side="left", padx=5)
        
        ttk.Button(left_buttons, text="💾 Lưu", 
                   command=self.on_save_lot_data).pack(side="left", padx=2)
        ttk.Button(left_buttons, text="📂 Tải", 
                   command=self.on_load_lot_data).pack(side="left", padx=2)
        ttk.Button(left_buttons, text="🔄 Cập nhật", 
                   command=self.on_update_lot_data).pack(side="left", padx=2)
        
        # Nút Áp dụng bên phải
        ttk.Button(header_frame, text="✅ Áp dụng", 
                   command=self.on_apply_manual_input).pack(side="right", padx=5)
        
        # Frame chứa 3 cột ngang: Số tiền (nhập) | Số tiền vào lệnh | Lot size
        self.manual_frame = ttk.Frame(lots_frame)
        self.manual_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        three_columns_frame = ttk.Frame(self.manual_frame)
        three_columns_frame.pack(fill="both", expand=True)
        
        # Frame chứa 3 cột và 1 scrollbar chung
        trees_container = ttk.Frame(three_columns_frame)
        trees_container.pack(fill="both", expand=True)
        
        # ===== CỘT 1: NHẬP SỐ TIỀN (Text widget để paste) =====
        col1_frame = ttk.LabelFrame(trees_container, text="💰 Nhập số tiền", padding=5)
        col1_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Text widget để paste số tiền
        text_input_frame = ttk.Frame(col1_frame)
        text_input_frame.pack(fill="both", expand=True)
        
        self.manual_input_text = tk.Text(
            text_input_frame,
            height=5,
            width=20,
            wrap=tk.WORD,
            font=("Arial", 9)
        )
        self.manual_input_text.pack(side="left", fill="both", expand=True)
        # Căn giữa nội dung trong ô nhập số tiền
        self.manual_input_text.tag_configure("center", justify="center")
        
        # Scrollbar cho Text widget (sẽ được đồng bộ với scrollbar chung)
        scrollbar_text = ttk.Scrollbar(text_input_frame, orient="vertical")
        scrollbar_text.pack(side="right", fill="y")
        self.manual_input_text.config(yscrollcommand=scrollbar_text.set)
        
        # Thêm placeholder
        self.manual_input_text.insert("1.0", PLACEHOLDER_TEXT)
        self.manual_input_text.config(foreground="gray")
        
        def _center_manual_input_text(event=None):
            """Căn giữa toàn bộ nội dung trong ô nhập số tiền."""
            try:
                self.manual_input_text.tag_add("center", "1.0", "end")
            except tk.TclError:
                # Trường hợp widget đã bị destroy hoặc lỗi nhỏ khác, bỏ qua
                pass
        
        def on_input_focus_in(event):
            content = self.manual_input_text.get("1.0", "end-1c").strip()
            if is_placeholder_text(content):
                self.manual_input_text.delete("1.0", tk.END)
                self.manual_input_text.config(foreground="black")
            _center_manual_input_text()
        
        def on_input_focus_out(event):
            if not self.manual_input_text.get("1.0", "end-1c").strip():
                self.manual_input_text.insert("1.0", PLACEHOLDER_TEXT)
                self.manual_input_text.config(foreground="gray")
            _center_manual_input_text()
        
        self.manual_input_text.bind("<FocusIn>", on_input_focus_in)
        self.manual_input_text.bind("<FocusOut>", on_input_focus_out)
        # Cập nhật căn giữa mỗi khi gõ phím
        self.manual_input_text.bind("<KeyRelease>", _center_manual_input_text)
        # Căn giữa nội dung ban đầu (placeholder)
        _center_manual_input_text()
        
        # ===== CỘT 2: SỐ TIỀN VÀO LỆNH =====
        col2_frame = ttk.LabelFrame(trees_container, text="💵 Số tiền vào lệnh (USD)", padding=5)
        col2_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.manual_money_tree = ttk.Treeview(col2_frame, columns=("entry", "money"), show="headings", 
                                              height=5)
        self.manual_money_tree.pack(side="left", fill="both", expand=True)
        
        self.manual_money_tree.heading("entry", text="STT Entry")
        self.manual_money_tree.heading("money", text="Số tiền (USD)")
        
        self.manual_money_tree.column("entry", width=70, anchor="center")
        self.manual_money_tree.column("money", width=100, anchor="center")
        
        # ===== CỘT 3: LOT SIZE =====
        col3_frame = ttk.LabelFrame(trees_container, text="📊 Lot Size", padding=5)
        col3_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.manual_lot_tree = ttk.Treeview(col3_frame, columns=("entry", "lot"), show="headings", 
                                            height=5)
        self.manual_lot_tree.pack(side="left", fill="both", expand=True)
        
        self.manual_lot_tree.heading("entry", text="STT Entry")
        self.manual_lot_tree.heading("lot", text="Lot Size")
        
        self.manual_lot_tree.column("entry", width=70, anchor="center")
        self.manual_lot_tree.column("lot", width=100, anchor="center")
        
        # ===== SCROLLBAR CHUNG =====
        scrollbar_common = ttk.Scrollbar(trees_container, orient="vertical")
        scrollbar_common.pack(side="right", fill="y")
        
        # Đồng bộ scroll của Text widget và 2 Treeview
        def on_scroll(*args):
            # Lấy scroll position từ args
            scrollbar_common.set(*args)
            # Áp dụng cho Text widget
            self.manual_input_text.yview_moveto(args[0])
            # Áp dụng cho 2 Treeview
            self.manual_money_tree.yview_moveto(args[0])
            self.manual_lot_tree.yview_moveto(args[0])
        
        def on_scroll_mousewheel(event):
            # Xử lý scroll bằng chuột cho Text widget
            if event.delta:
                units = int(-1 * (event.delta / 120))
                self.manual_input_text.yview_scroll(units, "units")
                self.manual_money_tree.yview_scroll(units, "units")
                self.manual_lot_tree.yview_scroll(units, "units")
        
        # Cấu hình scrollbar chung
        def update_scrollbar(*args):
            scrollbar_common.set(*args)
        
        # Cấu hình yscrollcommand cho Text widget và 2 Treeview
        self.manual_input_text.config(yscrollcommand=update_scrollbar)
        self.manual_money_tree.config(yscrollcommand=update_scrollbar)
        self.manual_lot_tree.config(yscrollcommand=update_scrollbar)
        
        scrollbar_common.config(command=on_scroll)
        
        # Bind mousewheel cho Text widget và 2 Treeview
        self.manual_input_text.bind("<MouseWheel>", on_scroll_mousewheel)
        for tree in [self.manual_money_tree, self.manual_lot_tree]:
            tree.bind("<MouseWheel>", on_scroll_mousewheel)
        
        # Thêm placeholder cho 2 Treeview
        self.manual_money_tree.insert("", "end", values=("--", "Nhập số tiền và nhấn 'Áp dụng'"))
        self.manual_lot_tree.insert("", "end", values=("--", "Nhập số tiền và nhấn 'Áp dụng'"))

        # Hàng 3: Nút chạy backtest
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        # Nút chọn file data
        self.select_file_btn = ttk.Button(btn_frame, text="Chọn file data", command=self.on_select_data_file)
        self.select_file_btn.pack(side="left", padx=(0, 5))
        
        # Label hiển thị file đã chọn
        self.file_label = ttk.Label(btn_frame, text="", foreground="gray", font=("Arial", 8))
        self.file_label.pack(side="left", padx=5)

        self.run_btn = ttk.Button(btn_frame, text="Chạy backtest", command=self.on_run_backtest)
        self.run_btn.pack(side="left")
        
        # Label hiển thị trạng thái
        self.status_label = ttk.Label(btn_frame, text="", foreground="blue")
        self.status_label.pack(side="left", padx=10)

        # Hàng 4: Kết quả - chiếm phần lớn thứ 2
        result_frame = ttk.LabelFrame(main_frame, text="Kết quả tóm tắt")
        result_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)

        self.result_text = tk.Text(result_frame, height=10)
        self.result_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Đồng bộ lại UI RSI theo chế độ mặc định (nhập thủ công)
        self.on_rsi_mode_change()

    def on_select_data_file(self):
        """Xử lý khi nhấn nút chọn file data"""
        file_path = filedialog.askopenfilename(
            title="Chọn file data",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ],
            initialdir="data/raw" if Path("data/raw").exists() else "."
        )
        
        if file_path:
            self.selected_data_file = file_path
            # Hiển thị tên file (chỉ tên file, không phải đường dẫn đầy đủ)
            file_name = Path(file_path).name
            self.file_label.config(text=f"📂 {file_name}", foreground="green")
            # Hiển thị thông báo không chặn (non-modal) trên status label
            # Thông báo này sẽ được thay thế khi người dùng nhấn nút "Chạy backtest"
            self.status_label.config(
                text=f"✅ Đã chọn file: {file_name} (bấm 'Chạy backtest' để bắt đầu)",
                foreground="green",
            )

    def _parse_money_input(self, content: str) -> list[float]:
        """
        Parse chuỗi số tiền từ text input.
        
        Args:
            content: Nội dung text từ Text widget
            
        Returns:
            list[float]: Danh sách số tiền đã parse
        """
        money_values = []
        
        # Chuẩn hóa: thay thế tất cả các ký tự phân cách (xuống dòng, tab, dấu chấm phẩy) bằng dấu phẩy
        normalized = re.sub(r'[\n\r\t;]+', ',', content)
        # Thay thế nhiều khoảng trắng hoặc dấu phẩy liên tiếp bằng một dấu phẩy
        normalized = re.sub(r'[,\s]+', ',', normalized)
        # Loại bỏ dấu phẩy ở đầu và cuối
        normalized = normalized.strip(',').strip()
        
        if not normalized:
            return []
        
        # Tách theo dấu phẩy
        parts = normalized.split(',')
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Loại bỏ ký tự đặc biệt (như dấu phẩy trong số, khoảng trắng)
            part_clean = part.replace(',', '').replace(' ', '').replace('\t', '').replace('\n', '').replace('\r', '')
            
            if not part_clean:
                continue
            
            try:
                money = float(part_clean)
                if money < 0:
                    money = 0.0
                money_values.append(money)
            except ValueError:
                # Bỏ qua giá trị không hợp lệ, không báo lỗi để không gián đoạn
                print(f"⚠️ Bỏ qua giá trị không hợp lệ: '{part}'")
                continue
        
        return money_values
    
    def _calculate_lot_size(self, entry_number: int, money: float, xauusd_price: float) -> float:
        """
        Tính lot size cho entry dựa trên entry number và số tiền.
        
        Args:
            entry_number: Số thứ tự entry
            money: Số tiền (USD)
            xauusd_price: Giá XAUUSD trung bình
            
        Returns:
            float: Lot size (0.0 nếu chỉ đếm, không vào lệnh)
        """
        # Entry 1-9: luôn set lot_size = 0 (mặc định chỉ đếm, không vào lệnh)
        if entry_number < ENTRY_TRADE_START:
            return 0.0
        # Entry 10-40: vào lệnh nếu money > 0, chỉ đếm nếu money = 0
        elif entry_number <= ENTRY_TRADE_END:
            if money > 0 and xauusd_price and xauusd_price > 0:
                return money / (xauusd_price * 100)
            else:
                return 0.0  # money = 0 → chỉ đếm, không vào lệnh
        # Entry 41+: luôn set lot_size = 0 (chỉ đếm, không vào lệnh)
        else:
            return 0.0
    
    def _update_treeviews(self, lot_data: list):
        """
        Cập nhật 2 Treeview (money và lot) với dữ liệu mới.
        
        Args:
            lot_data: Danh sách lot data với keys: entry_number, money_amount, lot_size
        """
        # Xóa dữ liệu cũ
        for item in self.manual_money_tree.get_children():
            self.manual_money_tree.delete(item)
        for item in self.manual_lot_tree.get_children():
            self.manual_lot_tree.delete(item)
        
        # Thêm dữ liệu mới
        for item in lot_data:
            entry_number = item['entry_number']
            money = item['money_amount']
            lot_size = item['lot_size']
            self.manual_money_tree.insert("", "end", values=(f"Entry {entry_number}", f"${money:,.0f}"))
            self.manual_lot_tree.insert("", "end", values=(f"Entry {entry_number}", f"{lot_size:.5f}"))
    
    def _validate_entry_count(self, money_values: list) -> bool:
        """
        Validate số lượng entry và hiển thị cảnh báo nếu vượt quá MAX_TRADE_ENTRY.
        
        Args:
            money_values: Danh sách số tiền đã nhập
            
        Returns:
            bool: True nếu hợp lệ, False nếu có cảnh báo
        """
        if len(money_values) == 0:
            return False
        
        last_entry = FIRST_TRADE_ENTRY + len(money_values) - 1
        if last_entry > MAX_TRADE_ENTRY:
            excess_entries = last_entry - MAX_TRADE_ENTRY
            messagebox.showwarning(
                "Cảnh báo",
                f"Bạn đã nhập {len(money_values)} số tiền, map vào Entry {FIRST_TRADE_ENTRY}-{last_entry}.\n\n"
                f"⚠️ Entry {MAX_TRADE_ENTRY + 1}-{last_entry} ({excess_entries} entry) sẽ KHÔNG vào lệnh thực tế\n"
                f"(Chỉ Entry {ENTRY_TRADE_START}-{ENTRY_TRADE_END} mới vào lệnh, Entry {ENTRY_WAIT_EXIT_START}+ chỉ đếm và chờ exit).\n\n"
                f"Khuyến nghị: Chỉ nhập tối đa {MAX_TRADE_ENTRY} số tiền."
            )
        return True
    
    def on_apply_manual_input(self):
        """Xử lý khi nhấn nút Áp dụng cho nhập thủ công"""
        # Lấy nội dung từ Text widget (cột nhập số tiền)
        content = self.manual_input_text.get("1.0", "end-1c").strip()
        
        # Bỏ qua placeholder text
        if is_placeholder_text(content):
            self.status_label.config(
                text="⚠️ Vui lòng nhập số tiền vào lệnh trước khi bấm 'Áp dụng'.",
                foreground="red",
            )
            return
        
        try:
            # Parse số tiền từ input
            money_values = self._parse_money_input(content)
            
            if not money_values:
                self.status_label.config(
                    text="⚠️ Không có dữ liệu số tiền để xử lý. Kiểm tra lại nội dung đã paste.",
                    foreground="red",
                )
                return
            
            # Validate số lượng entry
            if not self._validate_entry_count(money_values):
                return
            
            # Lấy giá XAUUSD trung bình từ file data nếu có
            xauusd_price = get_xauusd_average_price(self.selected_data_file)
            
            # Tạo dữ liệu lot
            self.lot_data = []
            for idx, money in enumerate(money_values):
                entry_number = idx + FIRST_TRADE_ENTRY
                lot_size = self._calculate_lot_size(entry_number, money, xauusd_price)
                
                self.lot_data.append({
                    'entry_number': entry_number,
                    'money_amount': money,
                    'lot_size': round(lot_size, 5)
                })
            
            # Cập nhật UI
            self._update_treeviews(self.lot_data)
            
            print(f"✅ Đã parse {len(money_values)} giá trị từ dữ liệu nhập thủ công")
            
            # Đếm số entry sẽ vào lệnh thực tế (Entry 10-40 với money > 0)
            trade_entries = [
                item for item in self.lot_data 
                if ENTRY_TRADE_START <= item['entry_number'] <= ENTRY_TRADE_END 
                and item['lot_size'] > 0
            ]
            count_only_entries = len(self.lot_data) - len(trade_entries)
            
            # Thông báo không chặn
            applied_entries = len(self.lot_data)
            entry_range = f"Entry {FIRST_TRADE_ENTRY}-{self.lot_data[-1]['entry_number']}" if self.lot_data else "N/A"
            status_msg = f"✅ Đã áp dụng {applied_entries} entry ({entry_range})"
            if count_only_entries > 0:
                status_msg += f" | {count_only_entries} entry chỉ đếm, {len(trade_entries)} entry vào lệnh"
            status_msg += " | Hãy chọn file data."
            self.status_label.config(
                text=status_msg,
                foreground="green",
            )
            
        except (ValueError, TypeError, AttributeError, ZeroDivisionError) as e:
            # Lỗi khi parse số hoặc tính toán
            messagebox.showerror("Lỗi", f"Lỗi khi xử lý dữ liệu: {e}\n\nVui lòng kiểm tra lại định dạng số tiền đã nhập.")
            traceback.print_exc()
        except Exception as e:
            # Lỗi không lường trước
            messagebox.showerror("Lỗi", f"Lỗi không xác định khi xử lý dữ liệu: {e}")
            traceback.print_exc()

    def on_save_lot_data(self):
        """Lưu dữ liệu số tiền vào file JSON"""
        if not self.lot_data:
            messagebox.showwarning("Cảnh báo", "Chưa có dữ liệu để lưu. Vui lòng nhập số tiền và nhấn 'Áp dụng' trước.")
            return
        
        # Chọn file để lưu
        file_path = filedialog.asksaveasfilename(
            title="Lưu dữ liệu số tiền",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="data" if Path("data").exists() else ".",
            initialfile="lot_data.json"
        )
        
        if not file_path:
            return
        
        try:
            # Chuẩn bị dữ liệu để lưu (chỉ lưu money_amount, lot_size sẽ tính lại khi tải)
            save_data = {
                "money_amounts": [item['money_amount'] for item in self.lot_data],
                "entry_numbers": [item['entry_number'] for item in self.lot_data],
                "xauusd_price": get_xauusd_average_price(self.selected_data_file)
            }
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            self.saved_lot_data_file = file_path
            self.status_label.config(
                text=f"✅ Đã lưu dữ liệu vào: {Path(file_path).name}",
                foreground="green",
            )
            messagebox.showinfo("Thành công", f"Đã lưu {len(self.lot_data)} entry vào file:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu file: {e}")
            traceback.print_exc()

    def on_load_lot_data(self):
        """Tải dữ liệu số tiền từ file JSON"""
        file_path = filedialog.askopenfilename(
            title="Tải dữ liệu số tiền",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="data" if Path("data").exists() else "."
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                save_data = json.load(f)
            
            # Kiểm tra định dạng
            if "money_amounts" not in save_data:
                messagebox.showerror("Lỗi", "File không đúng định dạng. Thiếu 'money_amounts'.")
                return
            
            money_amounts = save_data.get("money_amounts", [])
            if not money_amounts:
                messagebox.showwarning("Cảnh báo", "File không chứa dữ liệu số tiền.")
                return
            
            # Lấy giá XAUUSD (ưu tiên từ file đã lưu, sau đó từ file data hiện tại)
            xauusd_price = save_data.get("xauusd_price")
            if not xauusd_price:
                xauusd_price = get_xauusd_average_price(self.selected_data_file)
            
            # Tạo chuỗi số tiền để hiển thị trong Text widget
            money_text = "\n".join([str(int(money)) if money == int(money) else str(money) for money in money_amounts])
            
            # Cập nhật Text widget
            self.manual_input_text.delete("1.0", tk.END)
            self.manual_input_text.insert("1.0", money_text)
            self.manual_input_text.config(foreground="black")
            
            # Tự động áp dụng dữ liệu đã tải
            self.on_apply_manual_input()
            
            self.saved_lot_data_file = file_path
            self.status_label.config(
                text=f"✅ Đã tải {len(money_amounts)} entry từ: {Path(file_path).name}",
                foreground="green",
            )
            messagebox.showinfo("Thành công", f"Đã tải {len(money_amounts)} entry từ file:\n{file_path}")
            
        except json.JSONDecodeError as e:
            messagebox.showerror("Lỗi", f"File JSON không hợp lệ: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải file: {e}")
            traceback.print_exc()

    def on_update_lot_data(self):
        """Cập nhật dữ liệu đã lưu (lưu lại với file đã lưu trước đó)"""
        if not self.saved_lot_data_file:
            # Nếu chưa có file đã lưu, hỏi người dùng có muốn lưu mới không
            response = messagebox.askyesno(
                "Chưa có file đã lưu",
                "Chưa có file dữ liệu đã lưu trước đó.\n\nBạn có muốn lưu dữ liệu hiện tại không?"
            )
            if response:
                self.on_save_lot_data()
            return
        
        if not self.lot_data:
            messagebox.showwarning("Cảnh báo", "Chưa có dữ liệu để cập nhật. Vui lòng nhập số tiền và nhấn 'Áp dụng' trước.")
            return
        
        try:
            # Chuẩn bị dữ liệu để lưu
            save_data = {
                "money_amounts": [item['money_amount'] for item in self.lot_data],
                "entry_numbers": [item['entry_number'] for item in self.lot_data],
                "xauusd_price": get_xauusd_average_price(self.selected_data_file)
            }
            
            # Lưu lại vào file đã lưu trước đó
            with open(self.saved_lot_data_file, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            self.status_label.config(
                text=f"✅ Đã cập nhật dữ liệu vào: {Path(self.saved_lot_data_file).name}",
                foreground="green",
            )
            messagebox.showinfo("Thành công", f"Đã cập nhật {len(self.lot_data)} entry vào file:\n{self.saved_lot_data_file}")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể cập nhật file: {e}")
            traceback.print_exc()

    def on_rsi_mode_change(self):
        """Xử lý khi chuyển đổi giữa chế độ tự động và thủ công"""
        if self.rsi_auto_mode.get():
            # Chế độ tự động
            self.rsi_entry_entry.config(state="disabled")
            self.rsi_exit_entry.config(state="disabled")
            self.rsi_break_entry.config(state="disabled")
            self.rsi_info_label.config(
                text="Tự động tối ưu: BUY 30-35, SELL 65-70. 3 mốc bên trên sẽ được cập nhật sau khi tối ưu.",
                foreground="gray",
            )
        else:
            # Chế độ thủ công
            self.rsi_entry_entry.config(state="normal")
            self.rsi_exit_entry.config(state="normal")
            self.rsi_break_entry.config(state="normal")
            # Cập nhật mô tả theo hướng hiện tại
            self.on_direction_change()

    def on_direction_change(self):
        """Cập nhật label mô tả và giá trị mặc định khi đổi hướng BUY/SELL."""
        direction = (self.direction_var.get() or "BUY").upper()
        if direction == "BUY":
            self.rsi_entry_label.config(text="RSI vào lệnh (BUY):")
            self.rsi_info_label.config(
                text="MUA: vào khi RSI ≤ mốc 1, chốt khi RSI ≈ mốc 2, dừng đếm khi RSI < mốc 3",
                foreground="gray",
            )
            # Giá trị mặc định cho BUY
            self.rsi_entry_var.set("35")
            self.rsi_exit_var.set("50")
            self.rsi_break_var.set("40")
        else:
            self.rsi_entry_label.config(text="RSI vào lệnh (SELL):")
            self.rsi_info_label.config(
                text="BÁN: vào khi RSI ≥ mốc 1, chốt khi RSI ≈ mốc 2, dừng đếm khi RSI > mốc 3",
                foreground="gray",
            )
            # Giá trị mặc định cho SELL
            self.rsi_entry_var.set("70")
            self.rsi_exit_var.set("50")
            self.rsi_break_var.set("60")

    def on_run_backtest(self):
        """Xử lý khi nhấn nút chạy backtest - chạy trên thread riêng"""
        # Kiểm tra đã nhập và áp dụng chưa
        if not self.lot_data:
            messagebox.showerror(
                "Lỗi", 
                "Vui lòng nhập số tiền và nhấn 'Áp dụng' trước.\n\n"
                "⚠️ Lưu ý:\n"
                "- Entry 1-9: Mặc định chỉ đếm, không vào lệnh\n"
                "- Entry 10-40: Vào lệnh nếu nhập số tiền > 0\n"
                "- Nhập 0 = chỉ đếm, không vào lệnh"
            )
            return

        # Kiểm tra file data
        if not self.selected_data_file:
            response = messagebox.askyesno(
                "Cảnh báo",
                "Chưa chọn file data. Bạn có muốn tiếp tục với file mặc định từ config?"
            )
            if not response:
                return

        # Disable nút và hiển thị trạng thái
        self.run_btn.config(state="disabled")
        self.status_label.config(text="⏳ Đang chạy backtest...", foreground="blue")
        self.result_text.delete("1.0", tk.END)
        
        # Kiểm tra chế độ tự động hay thủ công
        if self.rsi_auto_mode.get():
            # Chế độ tự động tối ưu
            self.result_text.insert("1.0", "🔍 Đang tối ưu ngưỡng RSI...\n")
            self.result_text.insert(tk.END, "   BUY: 30-35, SELL: 65-70\n")
            self.result_text.insert(tk.END, "   (Quá trình này có thể mất vài phút, vui lòng đợi...)\n")
        else:
            # Chế độ thủ công
            try:
                entry_th = float(self.rsi_entry_var.get())
                exit_th = float(self.rsi_exit_var.get())
                break_th = float(self.rsi_break_var.get())
            except ValueError:
                messagebox.showerror("Lỗi", "3 mốc RSI phải là số.")
                self.run_btn.config(state="normal")
                self.status_label.config(text="")
                return
            direction = (self.direction_var.get() or "BUY").upper()
            self.result_text.insert(
                "1.0",
                f"Đang chạy backtest {direction} với 3 mốc RSI: "
                f"vào lệnh={entry_th}, đóng lệnh={exit_th}, dừng vào lệnh={break_th}...\n",
            )
        
        self.update()  # Force update UI

        # Copy data để tránh race condition khi user thay đổi trong lúc thread đang chạy
        lot_data_copy = self.lot_data.copy() if self.lot_data else []
        data_file_copy = self.selected_data_file
        rsi_auto_mode_copy = self.rsi_auto_mode.get()
        direction_mode_copy = self.direction_var.get()
        entry_th_copy = self.rsi_entry_var.get()
        exit_th_copy = self.rsi_exit_var.get()
        break_th_copy = self.rsi_break_var.get()
        
        # Chạy backtest trên thread riêng
        def run_in_thread():
            try:
                if rsi_auto_mode_copy:
                    # Chế độ tự động tối ưu - sử dụng constants
                    result = optimize_rsi_thresholds(
                        lot_data_copy, 
                        data_file_copy,
                        buy_range=DEFAULT_OPTIMIZE_BUY_RANGE,
                        sell_range=DEFAULT_OPTIMIZE_SELL_RANGE,
                        step=DEFAULT_OPTIMIZE_STEP,
                        direction_mode=direction_mode_copy,
                    )
                    # Update UI trên main thread với kết quả tối ưu
                    self.after(0, self._on_optimize_complete, result, None)
                else:
                    # Chế độ thủ công
                    entry_th = float(entry_th_copy)
                    exit_th = float(exit_th_copy)
                    break_th = float(break_th_copy)
                    direction = (direction_mode_copy or "BUY").upper()
                    # Chỉ cần ngưỡng entry tương ứng với hướng, ngưỡng còn lại có thể dùng giá trị mặc định
                    if direction == "BUY":
                        buy_th = entry_th
                        sell_th = 100.0  # dummy, không dùng khi chỉ BUY
                    else:
                        buy_th = 0.0     # dummy, không dùng khi chỉ SELL
                        sell_th = entry_th
                    summary = run_backtest_with_params(
                        buy_th,
                        sell_th,
                        lot_data_copy,
                        data_file_copy,
                        direction_mode=direction,
                        entry_rsi=entry_th,
                        exit_rsi=exit_th,
                        break_rsi=break_th,
                    )
                    # Update UI trên main thread
                    self.after(0, self._on_backtest_complete, summary, None)
            except (FileNotFoundError, ValueError, KeyError, AttributeError) as e:
                # Lỗi cụ thể từ backtest - hiển thị thông báo rõ ràng
                error_msg = f"Lỗi khi chạy backtest: {e}"
                self.after(0, self._on_backtest_complete, None, error_msg)
            except Exception as e:
                # Lỗi không lường trước - log chi tiết
                error_msg = f"Lỗi không xác định: {e}\n\nXem console để biết chi tiết."
                print(f"❌ Lỗi không xác định trong backtest: {e}")
                traceback.print_exc()
                self.after(0, self._on_backtest_complete, None, error_msg)

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()

    def _on_backtest_complete(self, summary, error):
        """Callback khi backtest hoàn thành - chạy trên main thread"""
        # Enable lại nút
        self.run_btn.config(state="normal")
        self.status_label.config(text="")

        if error:
            messagebox.showerror("Lỗi khi chạy backtest", error)
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", f"❌ Lỗi: {error}\n")
            return

        # Lấy thống kê BUY/SELL
        buy_entries = summary.get("buy_entries", 0)
        sell_entries = summary.get("sell_entries", 0)
        buy_trades = summary.get("buy_trades", 0)
        sell_trades = summary.get("sell_trades", 0)
        
        self.result_text.delete("1.0", tk.END)
        result_msg = (
            f"✅ Backtest hoàn thành!\n\n"
            f"📈 KẾT QUẢ TỔNG QUAN:\n"
            f"   Total Entries: {summary['total_entries']}\n"
            f"   Total Trades: {summary['total_trades']}\n"
            f"   Total P&L: ${summary['total_pnl']:,.2f}\n"
            f"   Total Return: {summary['total_return']}\n"
            f"   Initial Capital: ${summary['initial_capital']:,.2f}\n"
            f"   Final Equity: ${summary['final_equity']:,.2f}\n\n"
            f"📊 PHÂN TÍCH LỆNH MUA/BÁN:\n"
            f"   🟢 LỆNH MUA (BUY):\n"
            f"      - Số entry: {buy_entries}\n"
            f"      - Số lệnh thực tế: {buy_trades}\n"
            f"   🔴 LỆNH BÁN (SELL):\n"
            f"      - Số entry: {sell_entries}\n"
            f"      - Số lệnh thực tế: {sell_trades}\n\n"
            f"📝 Chi tiết: Xem console để biết:\n"
            f"   - Khi nào quyết định hướng BUY/SELL\n"
            f"   - Từng lệnh vào lệnh mua/bán\n"
        )
        self.result_text.insert(tk.END, result_msg)

    def _on_optimize_complete(self, result, error):
        """Callback khi tối ưu RSI hoàn thành - chạy trên main thread"""
        # Enable lại nút
        self.run_btn.config(state="normal")
        self.status_label.config(text="")
        
        if error:
            messagebox.showerror("Lỗi khi tối ưu RSI", error)
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", f"❌ Lỗi: {error}\n")
            return
        
        # Cập nhật giá trị RSI tốt nhất vào UI
        best_buy = result.get('buy_threshold', 30)
        best_sell = result.get('sell_threshold', 65)
        # Cập nhật mốc entry theo hướng hiện tại
        direction = (self.direction_var.get() or "BUY").upper()
        if direction == "BUY":
            self.rsi_entry_var.set(str(best_buy))
        else:
            self.rsi_entry_var.set(str(best_sell))
        
        summary = result.get('summary', {})
        buy_entries = summary.get("buy_entries", 0)
        sell_entries = summary.get("sell_entries", 0)
        buy_trades = summary.get("buy_trades", 0)
        sell_trades = summary.get("sell_trades", 0)
        
        self.result_text.delete("1.0", tk.END)
        result_msg = (
            f"🏆 TỐI ƯU HOÀN THÀNH!\n\n"
            f"📊 NGƯỠNG RSI TỐT NHẤT:\n"
            f"   🟢 BUY: RSI <= {best_buy}\n"
            f"   🔴 SELL: RSI >= {best_sell}\n\n"
            f"📈 KẾT QUẢ VỚI NGƯỠNG TỐI ƯU:\n"
            f"   Total Entries: {summary.get('total_entries', 0)}\n"
            f"   Total Trades: {summary.get('total_trades', 0)}\n"
            f"   Total P&L: ${summary.get('total_pnl', 0):,.2f}\n"
            f"   Total Return: {summary.get('total_return', 'N/A')}\n"
            f"   Initial Capital: ${summary.get('initial_capital', 0):,.2f}\n"
            f"   Final Equity: ${summary.get('final_equity', 0):,.2f}\n\n"
            f"📊 PHÂN TÍCH LỆNH MUA/BÁN:\n"
            f"   🟢 LỆNH MUA (BUY):\n"
            f"      - Số entry: {buy_entries}\n"
            f"      - Số lệnh thực tế: {buy_trades}\n"
            f"   🔴 LỆNH BÁN (SELL):\n"
            f"      - Số entry: {sell_entries}\n"
            f"      - Số lệnh thực tế: {sell_trades}\n\n"
            f"💡 Lưu ý: Giá trị RSI đã được cập nhật vào ô nhập.\n"
            f"   Bạn có thể chuyển sang chế độ 'Nhập thủ công' để chỉnh sửa.\n"
        )
        self.result_text.insert(tk.END, result_msg)


def main():
    app = BacktestGUI()
    app.mainloop()


if __name__ == "__main__":
    main()



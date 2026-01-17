"""
Backtest utility functions - extracted from gui.py for reuse in web app
"""

import json
import traceback
from pathlib import Path
from typing import Optional

from src.utils.data_loader import DataLoader
from src.strategy.dca_strategy import DCAStrategy
from src.backtest.portfolio import Portfolio
from src.backtest.engine import BacktestEngine
from src.config.strategy_config import StrategyConfig


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


def _extract_backtest_result(result):
    """
    Helper function để extract summary và engine từ kết quả backtest.
    Hỗ trợ cả tuple (summary, engine) và chỉ summary (backward compatible).
    
    Args:
        result: Kết quả từ run_backtest_with_params (tuple hoặc dict)
        
    Returns:
        tuple: (summary_dict, engine) hoặc (summary_dict, None)
    """
    if isinstance(result, tuple):
        summary = result[0] if len(result) > 0 else {}
        engine = result[1] if len(result) > 1 else None
        return summary, engine
    else:
        return result, None


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

    # Tạo config từ dict đã chỉnh (reuse StrategyConfig để tránh code duplication)
    cfg = StrategyConfig(config_dict=config_data)

    # Load data
    if not silent:
        print("\n" + "=" * 50)
        print("🚀 Bắt đầu chạy backtest...")
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

    # Trả về tóm tắt cần cho GUI và engine để vẽ biểu đồ
    results_dict = results if isinstance(results, dict) else {}
    summary_dict = {
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
    # Trả về tuple (summary, engine) để có thể vẽ biểu đồ sau
    return summary_dict, engine


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
                backtest_result = run_backtest_with_params(
                    buy_th,
                    sell_th,
                    lot_data,
                    data_file_path,
                    silent=True,
                    direction_mode=direction_mode,
                )
                # Extract summary từ kết quả (hỗ trợ cả tuple và dict)
                summary, _ = _extract_backtest_result(backtest_result)
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


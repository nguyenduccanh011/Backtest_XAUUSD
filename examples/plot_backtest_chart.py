"""
Ví dụ: Vẽ biểu đồ nến + RSI + điểm vào lệnh từ kết quả backtest
"""

from pathlib import Path
import sys

# Thêm root vào path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.data_loader import DataLoader
from src.strategy.dca_strategy import DCAStrategy
from src.backtest.portfolio import Portfolio
from src.backtest.engine import BacktestEngine
from src.config.strategy_config import StrategyConfig
from src.utils.chart_visualizer import ChartVisualizer


def main():
    """Ví dụ sử dụng ChartVisualizer"""
    
    # Load config
    config_path = Path("configs/default_config.json")
    if not config_path.exists():
        print(f"❌ Không tìm thấy config: {config_path}")
        return
    
    config = StrategyConfig(config_path=config_path)
    
    # Load data
    data_file = config.get("data.data_file", "data/raw/xauusd_h1.csv")
    loader = DataLoader()
    df = loader.load_csv(data_file, source="auto")
    print(f"✅ Đã load {len(df):,} nến dữ liệu")
    
    # Khởi tạo components
    portfolio_cfg = config.get("portfolio", {}) or {}
    initial_capital = portfolio_cfg.get("initial_capital", 10000)
    portfolio = Portfolio(initial_capital=initial_capital)
    strategy = DCAStrategy(config)
    engine = BacktestEngine(config=config, data=df, strategy=strategy, portfolio=portfolio)
    
    # Chạy backtest
    print("\n🚀 Đang chạy backtest...")
    results = engine.run()
    print("✅ Backtest hoàn thành!")
    
    # Vẽ biểu đồ
    print("\n📊 Đang vẽ biểu đồ...")
    visualizer = ChartVisualizer(
        data=engine.data,
        events=engine.events
    )
    
    # Lưu vào thư mục results/charts
    output_dir = Path("results/charts")
    output_dir.mkdir(parents=True, exist_ok=True)
    save_path = output_dir / "backtest_chart.png"
    
    visualizer.plot(
        title=f"XAUUSD Backtest - {len(engine.events)} events",
        save_path=str(save_path),
        show=True,
        max_bars=1000,  # Vẽ 1000 nến cuối cùng
    )
    
    print(f"\n✅ Hoàn thành! Biểu đồ đã được lưu tại: {save_path}")


if __name__ == "__main__":
    main()



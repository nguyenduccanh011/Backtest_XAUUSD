"""
Backtest Engine - Main engine for running backtests
"""

import pandas as pd
import numpy as np
from src.strategy.rsi_handler import RSIHandler


class BacktestEngine:
    """
    Main backtest engine.

    Processes historical data and executes strategy logic.
    """

    def __init__(self, config, data, strategy, portfolio):
        """
        Initialize backtest engine.

        Args:
            config: Configuration dict or StrategyConfig instance
            data: Historical price data (DataFrame with OHLCV)
            strategy: Strategy instance (DCAStrategy)
            portfolio: Portfolio manager instance
        """
        self.config = config
        self.data = data.copy()
        self.strategy = strategy
        self.portfolio = portfolio
        self.results = []

        # Get RSI period from config
        rsi_period = (
            config.get("strategy.rsi_period", 14)
            if hasattr(config, "get")
            else config.get("strategy", {}).get("rsi_period", 14)
        )

        # Mặc định TẮT debug để tránh log quá nhiều (rất chậm với ~500k nến)
        # Chỉ bật khi cần phân tích chi tiết:
        #   rsi_debug = config.get("debug.rsi", False)
        #   self.rsi_handler = RSIHandler(period=rsi_period, debug=rsi_debug)
        self.rsi_handler = RSIHandler(period=rsi_period, debug=False)

        # Calculate RSI
        self._calculate_rsi()

        # Track events
        self.events = []          # List of entry/exit/break events
        self.equity_curve = []    # Track equity over time

    def _calculate_rsi(self):
        """Calculate RSI for all data."""
        if 'close' not in self.data.columns:
            raise ValueError("Data must contain 'close' column")

        self.data['rsi'] = self.rsi_handler.calculate_rsi(self.data['close'])
        self.data['rsi_open'] = self.rsi_handler.calculate_rsi(self.data['open'])

    def run(self):
        """
        Run backtest on historical data.

        Returns:
            dict: Backtest results
        """
        # Reset strategy and portfolio
        self.strategy.reset()
        self.portfolio = type(self.portfolio)(self.portfolio.initial_capital)

        # Get config values
        use_open_for_exit = (
            self.config.get("strategy.rsi_exit.use_open", True)
            if hasattr(self.config, "get")
            else self.config.get("strategy", {}).get("rsi_exit", {}).get("use_open", True)
        )

        # Main backtest loop
        for idx, (timestamp, row) in enumerate(self.data.iterrows()):
            # Skip if RSI not calculated yet
            if pd.isna(row['rsi']):
                continue

            rsi_close = row['rsi']
            rsi_open = row.get('rsi_open', rsi_close)
            current_price = row['close']

            # ===== EXIT CHECK =====
            rsi_for_exit = rsi_open if use_open_for_exit else rsi_close
            if self.strategy.should_exit(rsi_for_exit):
                if self.portfolio.open_positions:
                    self.portfolio.close_all_positions(current_price, timestamp)
                    self.events.append({
                        'type': 'exit',
                        'timestamp': timestamp,
                        'price': current_price,
                        'rsi': rsi_for_exit,
                        'entry_count': self.strategy.current_entry
                    })
                    self.strategy.reset()

            # ===== BREAK CHECK =====
                      # ===== BREAK CHECK =====
            if self.strategy.check_break(rsi_close):
                self.events.append({
                    'type': 'break',
                    'timestamp': timestamp,
                    'price': current_price,
                    'rsi': rsi_close,
                    'entry_count': self.strategy.current_entry,
                    'direction': self.strategy.direction
                })

                # RESET strategy after break to allow new cycles
                self.strategy.reset()

            # ===== ENTRY CHECK =====
            should_enter, should_trade, direction = self.strategy.should_enter(rsi_close)

            if should_enter:
                entry_number = self.strategy.current_entry
                
                # Lấy ngưỡng RSI tương ứng với direction
                rsi_threshold = None
                if direction == "BUY":
                    rsi_threshold = self.strategy.rsi_entry_buy
                elif direction == "SELL":
                    rsi_threshold = self.strategy.rsi_entry_sell

                # Log khi quyết định hướng lần đầu (Entry #1)
                is_first_entry = (entry_number == 1)
                if is_first_entry:
                    print(f"\n{'='*60}")
                    print(f"🎯 QUYẾT ĐỊNH HƯỚNG LỆNH:")
                    print(f"   Thời gian: {timestamp}")
                    print(f"   Giá: ${current_price:.2f}")
                    print(f"   RSI: {rsi_close:.2f}")
                    if direction == "BUY":
                        print(f"   ✅ CHỌN HƯỚNG: 🟢 BUY (LỆNH MUA)")
                        print(f"   Lý do: RSI ({rsi_close:.2f}) <= ngưỡng BUY ({rsi_threshold})")
                    elif direction == "SELL":
                        print(f"   ✅ CHỌN HƯỚNG: 🔴 SELL (LỆNH BÁN)")
                        print(f"   Lý do: RSI ({rsi_close:.2f}) >= ngưỡng SELL ({rsi_threshold})")
                    print(f"{'='*60}\n")

                self.events.append({
                    'type': 'entry',
                    'timestamp': timestamp,
                    'price': current_price,
                    'rsi': rsi_close,
                    'entry_number': entry_number,
                    'direction': direction,
                    'should_trade': should_trade,
                    'rsi_threshold': rsi_threshold,  # Thêm thông tin ngưỡng vào event
                    'is_first_entry': is_first_entry  # Đánh dấu entry đầu tiên
                })

                if should_trade:
                    lot_size = self.strategy.get_lot_size(entry_number)
                    if lot_size > 0:
                        # Log khi thực sự vào lệnh
                        print(f"💰 VÀO LỆNH #{entry_number}: {direction} | Giá: ${current_price:.2f} | Lot: {lot_size} | RSI: {rsi_close:.2f}")
                        self.portfolio.open_position(
                            entry_number=entry_number,
                            direction=direction,
                            price=current_price,
                            lot_size=lot_size,
                            timestamp=timestamp
                        )

            # ===== EQUITY TRACKING =====
            equity = self.portfolio.get_current_equity(current_price)
            self.equity_curve.append({
                'timestamp': timestamp,
                'equity': equity,
                'open_positions': len(self.portfolio.open_positions)
            })

        # Close remaining positions at end of data
        if self.portfolio.open_positions:
            last_price = self.data.iloc[-1]['close']
            last_timestamp = self.data.index[-1]
            self.portfolio.close_all_positions(last_price, last_timestamp)
            self.events.append({
                'type': 'exit',
                'timestamp': last_timestamp,
                'price': last_price,
                'rsi': self.data.iloc[-1]['rsi'],
                'entry_count': self.strategy.current_entry,
                'reason': 'end_of_data'
            })

        return self._calculate_results()

    def _calculate_results(self):
        """Calculate backtest results."""
        entry_events = [e for e in self.events if e['type'] == 'entry']
        total_entries = len(entry_events)
        trade_entries = [e for e in entry_events if e.get('should_trade', False)]
        total_trades = len(trade_entries)
        
        # Đếm số lệnh BUY và SELL
        buy_entries = [e for e in entry_events if e.get('direction') == 'BUY']
        sell_entries = [e for e in entry_events if e.get('direction') == 'SELL']
        buy_trades = [e for e in trade_entries if e.get('direction') == 'BUY']
        sell_trades = [e for e in trade_entries if e.get('direction') == 'SELL']

        total_pnl = self.portfolio.get_total_pnl()

        closed_positions = [p for p in self.portfolio.positions if p.exit_price is not None]
        if closed_positions:
            winning_trades = sum(1 for p in closed_positions if p.pnl > 0)
            win_rate = (winning_trades / len(closed_positions)) * 100
        else:
            win_rate = 0.0

        if self.equity_curve:
            equity_values = [e['equity'] for e in self.equity_curve]
            peak = equity_values[0]
            max_drawdown = 0.0

            for equity in equity_values:
                if equity > peak:
                    peak = equity
                drawdown = ((peak - equity) / peak) * 100 if peak > 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
        else:
            max_drawdown = 0.0

        final_equity = self.portfolio.get_current_equity()
        total_return = (
            (final_equity - self.portfolio.initial_capital)
            / self.portfolio.initial_capital
        ) * 100

        return {
            "total_entries": total_entries,
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "max_drawdown": max_drawdown,
            "initial_capital": self.portfolio.initial_capital,
            "final_equity": final_equity,
            "total_return": total_return,
            "total_cycles": len([e for e in self.events if e['type'] == 'exit']),
            "events": self.events,
            "equity_curve": self.equity_curve,
            # Thống kê BUY/SELL
            "buy_entries": len(buy_entries),
            "sell_entries": len(sell_entries),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades)
        }

    def generate_report(self):
        """Generate backtest report."""
        results = self._calculate_results()

        return {
            "summary": {
                "total_entries": results["total_entries"],
                "total_trades": results["total_trades"],
                "total_pnl": results["total_pnl"],
                "win_rate": f"{results['win_rate']:.2f}%",
                "max_drawdown": f"{results['max_drawdown']:.2f}%",
                "total_return": f"{results['total_return']:.2f}%",
                "initial_capital": results["initial_capital"],
                "final_equity": results["final_equity"]
            },
            "events": results["events"],
            "equity_curve": results["equity_curve"]
        }

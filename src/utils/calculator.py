"""
Calculator - P&L and metric calculations
"""


class PnLCalculator:
    """
    Calculate P&L for XAUUSD positions.
    """
    
    def __init__(self, spread_pips=3, slippage_pips=1, commission_per_lot=0):
        """
        Initialize P&L calculator.
        
        Args:
            spread_pips: Bid-ask spread in pips
            slippage_pips: Slippage in pips
            commission_per_lot: Commission per lot
        """
        self.spread_pips = spread_pips
        self.slippage_pips = slippage_pips
        self.commission_per_lot = commission_per_lot
    
    def calculate_pnl(self, entry_price, exit_price, lot_size, direction):
        """
        Calculate P&L for a position.
        
        Args:
            entry_price: Entry price
            exit_price: Exit price
            lot_size: Lot size
            direction: "BUY" or "SELL"
            
        Returns:
            float: P&L in account currency
        """
        # TODO: Implement P&L calculation
        # For XAUUSD:
        # - BUY: P&L = (exit_price - entry_price) * lot_size * contract_size
        # - SELL: P&L = (entry_price - exit_price) * lot_size * contract_size
        # - Subtract spread, slippage, commission
        
        return 0.0
    
    def calculate_average_entry_price(self, positions):
        """
        Calculate weighted average entry price for multiple positions.
        
        Args:
            positions: List of Position objects
            
        Returns:
            float: Weighted average entry price
        """
        if not positions:
            return 0.0
        
        total_value = sum(p.entry_price * p.lot_size for p in positions)
        total_lots = sum(p.lot_size for p in positions)
        
        if total_lots == 0:
            return 0.0
        
        return total_value / total_lots


class MetricsCalculator:
    """
    Calculate backtest metrics (win rate, drawdown, etc.)
    """
    
    @staticmethod
    def calculate_win_rate(positions):
        """
        Calculate win rate.
        
        Args:
            positions: List of closed Position objects
            
        Returns:
            float: Win rate (0-1)
        """
        if not positions:
            return 0.0
        
        winning = sum(1 for p in positions if p.pnl > 0)
        return winning / len(positions)
    
    @staticmethod
    def calculate_max_drawdown(equity_curve):
        """
        Calculate maximum drawdown.
        
        Args:
            equity_curve: List of equity values over time
            
        Returns:
            float: Maximum drawdown
        """
        if not equity_curve:
            return 0.0
        
        # TODO: Implement max drawdown calculation
        return 0.0






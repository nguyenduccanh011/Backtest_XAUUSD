"""
Portfolio Manager - Track positions, P&L, and risk
"""


class Position:
    """Represents a single trading position."""
    
    def __init__(self, entry_number, direction, price, lot_size, timestamp):
        """
        Initialize position.
        
        Args:
            entry_number: Entry number (10-40)
            direction: "BUY" or "SELL"
            price: Entry price
            lot_size: Lot size
            timestamp: Entry timestamp
        """
        self.entry_number = entry_number
        self.direction = direction
        self.entry_price = price
        self.lot_size = lot_size
        self.entry_timestamp = timestamp
        self.exit_price = None
        self.exit_timestamp = None
        self.pnl = 0.0
    
    def close(self, exit_price, exit_timestamp):
        """
        Close position and calculate P&L.
        
        For XAUUSD:
        - 1 lot = 100 oz (standard contract size)
        - BUY: P&L = (exit_price - entry_price) * lot_size * 100
        - SELL: P&L = (entry_price - exit_price) * lot_size * 100
        
        Args:
            exit_price: Exit price
            exit_timestamp: Exit timestamp
        """
        self.exit_price = exit_price
        self.exit_timestamp = exit_timestamp
        
        # Calculate P&L for XAUUSD
        # Contract size: 1 lot = 100 oz
        contract_size = 100
        
        if self.direction == "BUY":
            # Profit when exit > entry
            self.pnl = (exit_price - self.entry_price) * self.lot_size * contract_size
        elif self.direction == "SELL":
            # Profit when entry > exit
            self.pnl = (self.entry_price - exit_price) * self.lot_size * contract_size
        else:
            self.pnl = 0.0


class Portfolio:
    """
    Portfolio manager - tracks all positions and calculates P&L.
    """
    
    def __init__(self, initial_capital=10000):
        """
        Initialize portfolio.
        
        Args:
            initial_capital: Starting capital
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = []  # List of Position objects
        self.open_positions = []  # Currently open positions
    
    def open_position(self, entry_number, direction, price, lot_size, timestamp):
        """
        Open a new position.
        
        Args:
            entry_number: Entry number
            direction: "BUY" or "SELL"
            price: Entry price
            lot_size: Lot size
            timestamp: Entry timestamp
            
        Returns:
            Position: Created position object
        """
        position = Position(entry_number, direction, price, lot_size, timestamp)
        self.open_positions.append(position)
        self.positions.append(position)
        return position
    
    def close_all_positions(self, exit_price, exit_timestamp):
        """
        Close all open positions.
        
        Args:
            exit_price: Exit price
            exit_timestamp: Exit timestamp
        """
        for position in self.open_positions:
            position.close(exit_price, exit_timestamp)
        self.open_positions = []
    
    def get_total_pnl(self):
        """
        Calculate total P&L from all closed positions.
        
        Returns:
            float: Total P&L
        """
        total_pnl = 0.0
        for position in self.positions:
            if position.exit_price is not None:  # Only count closed positions
                total_pnl += position.pnl
        return total_pnl
    
    def get_current_equity(self, current_price=None):
        """
        Get current equity (capital + unrealized P&L).
        
        Args:
            current_price: Current market price (for unrealized P&L)
            
        Returns:
            float: Current equity
        """
        # Start with realized P&L
        realized_pnl = self.get_total_pnl()
        equity = self.initial_capital + realized_pnl
        
        # Add unrealized P&L if current price provided
        if current_price is not None and self.open_positions:
            contract_size = 100  # 1 lot = 100 oz for XAUUSD
            unrealized_pnl = 0.0
            
            for position in self.open_positions:
                if position.direction == "BUY":
                    unrealized_pnl += (current_price - position.entry_price) * position.lot_size * contract_size
                elif position.direction == "SELL":
                    unrealized_pnl += (position.entry_price - current_price) * position.lot_size * contract_size
            
            equity += unrealized_pnl
        
        return equity




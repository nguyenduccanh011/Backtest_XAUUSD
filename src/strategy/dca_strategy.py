"""
DCA Strategy - Core logic for entry counting and position management
"""


class DCAStrategy:
    """
    Core DCA (Dollar Cost Averaging) strategy logic.
    
    Handles:
    - Entry counting (1-9: count only, 10-40: trade, 41+: wait exit)
    - RSI-based entry/exit conditions
    - Break detection (RSI break threshold)
    - RSI rhythm requirement between entries
    """
    
    def __init__(self, config):
        """
        Initialize strategy with configuration.
        
        Args:
            config: Strategy configuration dict or StrategyConfig instance
        """
        # Handle both dict and StrategyConfig
        if hasattr(config, 'get'):
            self.config = config
        else:
            # Create a simple wrapper for dict
            class ConfigWrapper:
                def __init__(self, cfg):
                    self._cfg = cfg
                def get(self, key, default=None):
                    keys = key.split('.')
                    value = self._cfg
                    for k in keys:
                        if isinstance(value, dict):
                            value = value.get(k)
                            if value is None:
                                return default
                        else:
                            return default
                    return value
            self.config = ConfigWrapper(config)
        
        self.current_entry = 0
        self.direction = None  # "BUY" or "SELL"
        self.is_break = False  # Break detected flag
        
        # Track RSI rhythm between entries
        self.last_rsi_entry = None  # RSI value when last entry was made
        self.has_rhythm = False  # Has rhythm (RSI not meeting condition) between entries
        self.waiting_for_rhythm = False  # Waiting for rhythm after last entry
        
        # Get config values
        self.rsi_entry_buy = self.config.get("strategy.rsi_entry_threshold.buy", 30)
        self.rsi_entry_sell = self.config.get("strategy.rsi_entry_threshold.sell", 70)
        self.rsi_break_buy = self.config.get("strategy.rsi_break_threshold.buy", 40)
        self.rsi_break_sell = self.config.get("strategy.rsi_break_threshold.sell", 60)
        self.rsi_exit_threshold = self.config.get("strategy.rsi_exit.threshold", 50)
        self.rsi_exit_tolerance = self.config.get("strategy.rsi_exit.tolerance", 1)
        self.rsi_exit_use_open = self.config.get("strategy.rsi_exit.use_open", True)
        
        # Entry ranges
        self.entry_count_only = self.config.get("strategy.entry_range.count_only", [1, 9])
        self.entry_trade = self.config.get("strategy.entry_range.trade", [10, 40])
        self.entry_wait_exit = self.config.get("strategy.entry_range.wait_exit", [41, None])
        
    def reset(self):
        """Reset strategy state for new cycle."""
        self.current_entry = 0
        self.direction = None
        self.is_break = False
        self.last_rsi_entry = None
        self.has_rhythm = False
        self.waiting_for_rhythm = False
    
    def should_enter(self, rsi_value):
        """
        Check if should enter based on RSI.
        
        Logic:
        - First entry: RSI must meet entry condition (<= 30 for BUY, >= 70 for SELL)
        - Subsequent entries: Must have rhythm (RSI not meeting condition) between entries
        - Cannot enter if break detected
        - Entry 1-9: count only, 10-40: trade, 41+: count only
        
        Args:
            rsi_value: Current RSI value (close or open)
            
        Returns:
            tuple: (should_enter: bool, should_trade: bool, direction: str or None)
                - should_enter: True if entry condition met (count entry)
                - should_trade: True if should actually open position (entry 10-40)
                - direction: "BUY" or "SELL" or None
        """
        # If break detected, cannot enter
        if self.is_break:
            return (False, False, None)
        
        # Determine direction on first entry
        if self.direction is None:
            # Check BUY condition
            if rsi_value <= self.rsi_entry_buy:
                self.direction = "BUY"
                self.current_entry = 1
                self.last_rsi_entry = rsi_value
                self.has_rhythm = False
                self.waiting_for_rhythm = True
                # Entry 1-9: count only, no trade
                should_trade = False
                return (True, should_trade, "BUY")
            
            # Check SELL condition
            elif rsi_value >= self.rsi_entry_sell:
                self.direction = "SELL"
                self.current_entry = 1
                self.last_rsi_entry = rsi_value
                self.has_rhythm = False
                self.waiting_for_rhythm = True
                # Entry 1-9: count only, no trade
                should_trade = False
                return (True, should_trade, "SELL")
            
            return (False, False, None)
        
        # For subsequent entries, check rhythm requirement
        if self.direction == "BUY":
            # BUY: RSI must be <= 30 to enter
            if rsi_value <= self.rsi_entry_buy:
                # Check if we have rhythm (RSI was > 30 between entries)
                if self.waiting_for_rhythm and not self.has_rhythm:
                    # Still waiting for rhythm, cannot enter yet
                    return (False, False, None)
                
                # Has rhythm or first entry, can enter
                self.current_entry += 1
                self.last_rsi_entry = rsi_value
                self.has_rhythm = False
                self.waiting_for_rhythm = True
                
                # Determine if should trade
                should_trade = (self.entry_trade[0] <= self.current_entry <= self.entry_trade[1])
                return (True, should_trade, "BUY")
            
            # Check rhythm: RSI > 30 means rhythm occurred
            elif self.waiting_for_rhythm and rsi_value > self.rsi_entry_buy:
                self.has_rhythm = True
                # Don't return True yet, wait for next entry condition
        
        elif self.direction == "SELL":
            # SELL: RSI must be >= 70 to enter
            if rsi_value >= self.rsi_entry_sell:
                # Check if we have rhythm (RSI was < 70 between entries)
                if self.waiting_for_rhythm and not self.has_rhythm:
                    # Still waiting for rhythm, cannot enter yet
                    return (False, False, None)
                
                # Has rhythm or first entry, can enter
                self.current_entry += 1
                self.last_rsi_entry = rsi_value
                self.has_rhythm = False
                self.waiting_for_rhythm = True
                
                # Determine if should trade
                should_trade = (self.entry_trade[0] <= self.current_entry <= self.entry_trade[1])
                return (True, should_trade, "SELL")
            
            # Check rhythm: RSI < 70 means rhythm occurred
            elif self.waiting_for_rhythm and rsi_value < self.rsi_entry_sell:
                self.has_rhythm = True
                # Don't return True yet, wait for next entry condition
        
        return (False, False, None)
    
    def should_exit(self, rsi_value):
        """
        Check if should exit based on RSI.
        
        Exit condition: RSI = 50 (with tolerance)
        
        Args:
            rsi_value: Current RSI value (should use open if configured)
            
        Returns:
            bool: True if exit condition met
        """
        if self.direction is None:
            return False
        
        # Check if RSI is at exit threshold (50)
        return abs(rsi_value - self.rsi_exit_threshold) <= self.rsi_exit_tolerance
    
    def check_break(self, rsi_value):
        """
        Check if RSI break threshold is hit.
        
        Break conditions:
        - BUY: RSI > 40 (break threshold)
        - SELL: RSI < 60 (break threshold)
        
        Args:
            rsi_value: Current RSI value
            
        Returns:
            bool: True if break detected
        """
        if self.direction is None:
            return False
        
        if self.direction == "BUY":
            if rsi_value > self.rsi_break_buy:
                self.is_break = True
                return True
        elif self.direction == "SELL":
            if rsi_value < self.rsi_break_sell:
                self.is_break = True
                return True
        
        return False
    
    def get_lot_size(self, entry_number):
        """
        Get lot size for entry number.
        
        Args:
            entry_number: Entry number (10-40)
            
        Returns:
            float: Lot size, or 0.0 if not in trade range
        """
        if not (self.entry_trade[0] <= entry_number <= self.entry_trade[1]):
            return 0.0
        
        # Get lot size from config
        lot_key = f"lot_sizes.entry_{entry_number}"
        lot_size = self.config.get(lot_key, 0.0)
        return float(lot_size) if lot_size else 0.0




"""
RSI Handler - Calculate and process RSI indicators
"""

import pandas as pd
import numpy as np


class RSIHandler:
    """
    Handle RSI calculation and condition checking.
    """
    
    def __init__(self, period=14):
        """
        Initialize RSI handler.
        
        Args:
            period: RSI period (default: 14)
        """
        self.period = period
    
    def calculate_rsi(self, prices):
        """
        Calculate RSI from price series.
        
        Args:
            prices: pandas Series of closing prices
            
        Returns:
            pandas Series: RSI values
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def check_entry_condition(self, rsi_value, direction):
        """
        Check if RSI meets entry condition.
        
        Args:
            rsi_value: Current RSI value
            direction: "BUY" or "SELL"
            
        Returns:
            bool: True if entry condition met
        """
        if direction == "BUY":
            return rsi_value <= 30
        elif direction == "SELL":
            return rsi_value >= 70
        return False
    
    def check_exit_condition(self, rsi_value, tolerance=1):
        """
        Check if RSI meets exit condition (RSI = 50).
        
        Args:
            rsi_value: Current RSI value
            tolerance: Tolerance around 50 (default: 1)
            
        Returns:
            bool: True if exit condition met
        """
        return abs(rsi_value - 50) <= tolerance
    
    def check_break_condition(self, rsi_value, direction):
        """
        Check if RSI break threshold is hit.
        
        Args:
            rsi_value: Current RSI value
            direction: "BUY" or "SELL"
            
        Returns:
            bool: True if break detected
        """
        if direction == "BUY":
            return rsi_value > 40  # Break for Buy
        elif direction == "SELL":
            return rsi_value < 60  # Break for Sell
        return False




"""
RSI Handler - Calculate and process RSI indicators
"""

import pandas as pd
import numpy as np


class RSIHandler:
    """
    Handle RSI calculation and condition checking.
    """

    def __init__(self, period=14, debug=False):
        """
        Initialize RSI handler.

        Args:
            period: RSI period (default: 14)
            debug: enable debug logging (default: False)
        """
        self.period = period
        self.debug = debug

    def _log(self, message: str):
        """Internal logger (prints only when debug=True)."""
        if self.debug:
            print(message)

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
            ok = rsi_value <= 30
        elif direction == "SELL":
            ok = rsi_value >= 70
        else:
            ok = False

        self._log(f"[RSI] ENTRY? dir={direction} rsi={rsi_value:.2f} -> {ok}")
        return ok

    def check_exit_condition(self, rsi_value, tolerance=1):
        """
        Check if RSI meets exit condition (RSI = 50).

        Args:
            rsi_value: Current RSI value
            tolerance: Tolerance around 50 (default: 1)

        Returns:
            bool: True if exit condition met
        """
        ok = abs(rsi_value - 50) <= tolerance
        self._log(f"[RSI] EXIT? rsi={rsi_value:.2f} tol={tolerance} -> {ok}")
        return ok

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
            ok = rsi_value > 40  # Break for Buy
        elif direction == "SELL":
            ok = rsi_value < 60  # Break for Sell
        else:
            ok = False

        self._log(f"[RSI] BREAK? dir={direction} rsi={rsi_value:.2f} -> {ok}")
        return ok





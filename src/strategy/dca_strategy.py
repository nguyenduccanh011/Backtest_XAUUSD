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
        if hasattr(config, "get"):
            self.config = config
        else:
            # Create a simple wrapper for dict
            class ConfigWrapper:
                def __init__(self, cfg):
                    self._cfg = cfg

                def get(self, key, default=None):
                    keys = key.split(".")
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

        # Direction mode: cho phép người dùng chọn sẵn BUY hoặc SELL, hoặc AUTO như trước
        # - "AUTO": chọn hướng dựa trên lần chạm ngưỡng RSI đầu tiên (hành vi cũ)
        # - "BUY": chỉ tìm cơ hội BUY (RSI <= buy threshold), bỏ qua SELL
        # - "SELL": chỉ tìm cơ hội SELL (RSI >= sell threshold), bỏ qua BUY
        self.direction_mode = (
            (self.config.get("strategy.direction_mode", "AUTO") or "AUTO")
        ).upper()

        # Debug flag: mặc định False để không spam log (rất chậm với nhiều nến)
        # Có thể bật qua config: "debug.strategy": true
        self.debug = bool(self.config.get("debug.strategy", False))

        # Get config values
        self.rsi_entry_buy = self.config.get("strategy.rsi_entry_threshold.buy", 30)
        self.rsi_entry_sell = self.config.get("strategy.rsi_entry_threshold.sell", 70)
        self.rsi_break_buy = self.config.get("strategy.rsi_break_threshold.buy", 40)
        self.rsi_break_sell = self.config.get("strategy.rsi_break_threshold.sell", 60)
        self.rsi_exit_threshold = self.config.get("strategy.rsi_exit.threshold", 50)
        self.rsi_exit_tolerance = self.config.get("strategy.rsi_exit.tolerance", 1)
        self.rsi_exit_use_open = self.config.get("strategy.rsi_exit.use_open", True)

        # Minimum entries before break can occur (to prevent early reset)
        # Default: 9 entries (allows Entry 1-9 to accumulate before break can trigger)
        self.min_entries_before_break = self.config.get("strategy.min_entries_before_break", 9)

        # Entry ranges
        # Support BOTH config layouts:
        # - strategy.entry_range.trade
        # - entry_range.trade
        # Entry 1-9: count only (no trade, lot = 0)
        # Entry 10-40: count + trade (actual positions with lot size from user input)
        # Entry 41+: count only, wait for exit (lot = 0)
        self.entry_count_only = self.config.get(
            "strategy.entry_range.count_only",
            self.config.get("entry_range.count_only", []),
        )
        self.entry_trade = self.config.get(
            "strategy.entry_range.trade",
            self.config.get("entry_range.trade", [1, 40]),
        )
        self.entry_wait_exit = self.config.get(
            "strategy.entry_range.wait_exit",
            self.config.get("entry_range.wait_exit", [41, None]),
        )

    def reset(self):
        """Reset strategy state for new cycle."""
        self.current_entry = 0
        # Với AUTO: reset hướng về None để chu kỳ mới tự chọn lại
        # Với BUY/SELL cố định: cho phép giữ nguyên mode nhưng hướng sẽ được
        # thiết lập lại khi chạm điều kiện đầu tiên (dưới/ trên ngưỡng RSI tương ứng)
        self.direction = None
        self.is_break = False
        self.last_rsi_entry = None
        self.has_rhythm = False
        self.waiting_for_rhythm = False

    def should_enter(self, rsi_value):
        """
        Check if should enter based on RSI.

        Logic:
        - First entry: RSI must meet entry condition (<= buy threshold for BUY, >= sell threshold for SELL)
        - Subsequent entries: Must have rhythm (RSI not meeting condition) between entries
          * Entry 1-5: Skip rhythm requirement (allow quick accumulation)
          * Entry 6+: Require rhythm - RSI must cross threshold then return (RSI > buy_threshold then <= buy_threshold for BUY, RSI < sell_threshold then >= sell_threshold for SELL)
        - Cannot enter if break detected (is_break = True)
        - Entry ranges:
          * Entry 1-9: count only (no trade, lot = 0)
          * Entry 10-40: count + trade (lot from user input)
          * Entry 41+: count only, wait for EXIT (lot = 0)

        Args:
            rsi_value: Current RSI value (close or open)

        Returns:
            tuple: (should_enter: bool, should_trade: bool, direction: str or None)
                - should_enter: True if entry condition met (count entry)
                - should_trade: True if should actually open position (entry in trade range)
                - direction: "BUY" or "SELL" or None
        """

        # If break detected, cannot enter
        if self.is_break:
            if self.debug:
                print(
                    f"[STRAT] should_enter BLOCKED_BY_BREAK | rsi={rsi_value:.2f} | "
                    f"dir={self.direction} | entry={self.current_entry}"
                )
            return (False, False, None)

        # Determine direction on first entry
        if self.direction is None:
            # Check BUY condition
            if self.direction_mode in ("AUTO", "BUY") and rsi_value <= self.rsi_entry_buy:
                self.direction = "BUY"
                self.current_entry = 1
                self.last_rsi_entry = rsi_value
                self.has_rhythm = False
                self.waiting_for_rhythm = True

                # Check if entry #1 is in trade range
                should_trade = (self.entry_trade[0] <= self.current_entry <= self.entry_trade[1])
                if self.debug:
                    print(f"[STRAT] ENTRY#1 | BUY | rsi={rsi_value:.2f} | should_trade={should_trade}")
                return (True, should_trade, "BUY")

            # Check SELL condition
            if self.direction_mode in ("AUTO", "SELL") and rsi_value >= self.rsi_entry_sell:
                self.direction = "SELL"
                self.current_entry = 1
                self.last_rsi_entry = rsi_value
                self.has_rhythm = False
                self.waiting_for_rhythm = True

                # Check if entry #1 is in trade range
                should_trade = (self.entry_trade[0] <= self.current_entry <= self.entry_trade[1])
                if self.debug:
                    print(f"[STRAT] ENTRY#1 | SELL | rsi={rsi_value:.2f} | should_trade={should_trade}")
                return (True, should_trade, "SELL")

            return (False, False, None)

        # For subsequent entries, check rhythm requirement
        if self.direction == "BUY":
            # Nếu đã đạt tới ngưỡng "chỉ chờ chốt" (ví dụ: từ entry 41 trở đi)
            # thì không được phép tạo thêm entry mới nữa.
            max_wait_entry = self.entry_wait_exit[0] if self.entry_wait_exit else None
            if max_wait_entry is not None and (self.current_entry + 1) >= max_wait_entry:
                if self.debug:
                    print(
                        f"[STRAT] MAX_ENTRY_REACHED | BUY | current_entry={self.current_entry} "
                        f"| next_entry={self.current_entry + 1} | max_wait_entry={max_wait_entry}"
                    )
                return (False, False, "BUY")

            # BUY: RSI must be <= buy threshold to enter
            if rsi_value <= self.rsi_entry_buy:
                # Need rhythm (RSI was > threshold) between entries
                # BUT: Skip rhythm requirement for first few entries (1-5) to allow accumulation
                skip_rhythm_for_early_entries = self.current_entry < 5
                
                if self.waiting_for_rhythm and not self.has_rhythm and not skip_rhythm_for_early_entries:
                    if self.debug:
                        print(
                            f"[STRAT] NO_RHYTHM_YET | BUY | rsi={rsi_value:.2f} | entry={self.current_entry} | "
                            f"need_rsi>{self.rsi_entry_buy} between entries"
                        )
                    return (False, False, None)
                
                # If skipping rhythm for early entries, mark rhythm as OK
                if skip_rhythm_for_early_entries and not self.has_rhythm:
                    self.has_rhythm = True
                    if self.debug:
                        print(f"[STRAT] SKIP_RHYTHM | BUY | entry={self.current_entry} < 5, auto-allow rhythm")

                # Has rhythm -> can enter
                self.current_entry += 1
                self.last_rsi_entry = rsi_value
                self.has_rhythm = False
                self.waiting_for_rhythm = True

                # DEBUG: show trade range actually used
                if self.debug:
                    print(f"[DEBUG] entry_trade={self.entry_trade} current_entry={self.current_entry}")

                should_trade = (self.entry_trade[0] <= self.current_entry <= self.entry_trade[1])
                if self.debug:
                    print(
                        f"[STRAT] ENTRY#{self.current_entry} | BUY | rsi={rsi_value:.2f} | should_trade={should_trade}"
                    )
                return (True, should_trade, "BUY")

            # Rhythm condition: RSI > buy threshold means rhythm occurred
            if self.waiting_for_rhythm and rsi_value > self.rsi_entry_buy:
                if not self.has_rhythm:
                    self.has_rhythm = True
                    if self.debug:
                        print(f"[STRAT] RHYTHM_OK | BUY | rsi={rsi_value:.2f} (> {self.rsi_entry_buy})")

        elif self.direction == "SELL":
            # SELL direction
            # Nếu đã đạt tới ngưỡng "chỉ chờ chốt" (ví dụ: từ entry 41 trở đi)
            # thì không được phép tạo thêm entry mới nữa.
            max_wait_entry = self.entry_wait_exit[0] if self.entry_wait_exit else None
            if max_wait_entry is not None and (self.current_entry + 1) >= max_wait_entry:
                if self.debug:
                    print(
                        f"[STRAT] MAX_ENTRY_REACHED | SELL | current_entry={self.current_entry} "
                        f"| next_entry={self.current_entry + 1} | max_wait_entry={max_wait_entry}"
                    )
                return (False, False, "SELL")

            # SELL: RSI must be >= sell threshold to enter
            if rsi_value >= self.rsi_entry_sell:
                # Need rhythm (RSI was < threshold) between entries
                # BUT: Skip rhythm requirement for first few entries (1-5) to allow accumulation
                skip_rhythm_for_early_entries = self.current_entry < 5
                
                if self.waiting_for_rhythm and not self.has_rhythm and not skip_rhythm_for_early_entries:
                    if self.debug:
                        print(
                            f"[STRAT] NO_RHYTHM_YET | SELL | rsi={rsi_value:.2f} | entry={self.current_entry} | "
                            f"need_rsi<{self.rsi_entry_sell} between entries"
                        )
                    return (False, False, None)
                
                # If skipping rhythm for early entries, mark rhythm as OK
                if skip_rhythm_for_early_entries and not self.has_rhythm:
                    self.has_rhythm = True
                    if self.debug:
                        print(f"[STRAT] SKIP_RHYTHM | SELL | entry={self.current_entry} < 5, auto-allow rhythm")

                # Has rhythm -> can enter
                self.current_entry += 1
                self.last_rsi_entry = rsi_value
                self.has_rhythm = False
                self.waiting_for_rhythm = True

                # DEBUG: show trade range actually used
                if self.debug:
                    print(f"[DEBUG] entry_trade={self.entry_trade} current_entry={self.current_entry}")

                should_trade = (self.entry_trade[0] <= self.current_entry <= self.entry_trade[1])
                if self.debug:
                    print(
                        f"[STRAT] ENTRY#{self.current_entry} | SELL | rsi={rsi_value:.2f} | should_trade={should_trade}"
                    )
                return (True, should_trade, "SELL")

            # Rhythm condition: RSI < sell threshold means rhythm occurred
            if self.waiting_for_rhythm and rsi_value < self.rsi_entry_sell:
                if not self.has_rhythm:
                    self.has_rhythm = True
                    if self.debug:
                        print(f"[STRAT] RHYTHM_OK | SELL | rsi={rsi_value:.2f} (< {self.rsi_entry_sell})")

        return (False, False, None)

    def should_exit(self, rsi_value):
        """
        Check if should exit based on RSI.

        Exit condition: RSI = threshold (with tolerance)
        BUT: Only allow exit after at least one entry has been made

        Args:
            rsi_value: Current RSI value (should use open if configured)

        Returns:
            bool: True if exit condition met
        """
        if self.direction is None:
            return False

        # Prevent exit before at least one entry has been made
        if self.current_entry < 1:
            if self.debug:
                print(
                    f"[STRAT] should_exit BLOCKED | entry={self.current_entry} < 1 | "
                    f"rsi={rsi_value:.2f} | dir={self.direction}"
                )
            return False

        if self.debug:
            print(
                f"[STRAT] should_exit | rsi={rsi_value:.2f} | dir={self.direction} | entry={self.current_entry}"
            )
        return abs(rsi_value - self.rsi_exit_threshold) <= self.rsi_exit_tolerance

    def check_break(self, rsi_value):
        """
        Check if RSI break threshold is hit.

        Break conditions:
        - BUY: RSI > buy break threshold
        - SELL: RSI < sell break threshold
        - Only triggers if current_entry >= min_entries_before_break (to prevent early reset)

        Args:
            rsi_value: Current RSI value

        Returns:
            bool: True if break detected
        """
        if self.direction is None:
            return False

        # Check minimum entries requirement before allowing break
        if self.current_entry < self.min_entries_before_break:
            if self.debug:
                print(
                    f"[STRAT] check_break BLOCKED | entry={self.current_entry} < min_entries={self.min_entries_before_break} | "
                    f"rsi={rsi_value:.2f} | dir={self.direction}"
                )
            return False

        if self.debug:
            print(
                f"[STRAT] check_break | rsi={rsi_value:.2f} | dir={self.direction} | entry={self.current_entry}"
            )

        if self.direction == "BUY":
            if rsi_value > self.rsi_break_buy:
                self.is_break = True
                if self.debug:
                    print(f"[STRAT] BREAK_HIT | BUY | rsi={rsi_value:.2f} > {self.rsi_break_buy} | entry={self.current_entry}")
                return True

        elif self.direction == "SELL":
            if rsi_value < self.rsi_break_sell:
                self.is_break = True
                if self.debug:
                    print(f"[STRAT] BREAK_HIT | SELL | rsi={rsi_value:.2f} < {self.rsi_break_sell} | entry={self.current_entry}")
                return True

        return False

    def get_lot_size(self, entry_number):
        """
        Get lot size for entry number.

        Args:
            entry_number: Entry number (10-40 for trading, returns 0.0 for 1-9 and 41+)

        Returns:
            float: Lot size for entry 10-40, or 0.0 if not in trade range (1-9, 41+)
        """
        # Only return lot size for entries in trade range (10-40)
        # Entry 1-9: count only, no trade, lot = 0
        # Entry 41+: count only, wait for exit, lot = 0
        if not (self.entry_trade[0] <= entry_number <= self.entry_trade[1]):
            return 0.0

        lot_key = f"lot_sizes.entry_{entry_number}"
        lot_size = self.config.get(lot_key, 0.0)
        result = float(lot_size) if lot_size else 0.0
        
        # Debug: Log khi lot_size = 0 cho entry trong trade range
        if result == 0.0 and (self.entry_trade[0] <= entry_number <= self.entry_trade[1]):
            print(f"⚠️ [DEBUG] Entry #{entry_number} trong trade range nhưng lot_size=0.0")
            print(f"   lot_key={lot_key}, config_value={lot_size}")
            print(f"   entry_trade range: {self.entry_trade[0]}-{self.entry_trade[1]}")
        
        return result

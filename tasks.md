# 📋 Task List - Backtest XAUUSD DCA Strategy

## Phase 1: Setup & Core Infrastructure

### ✅ Completed
- [x] Project structure planning
- [x] Requirements documentation
- [x] Setup project structure
- [x] Create data loader module (`src/utils/data_loader.py`)
- [x] Implement RSI calculator (`src/strategy/rsi_handler.py`)
- [x] Setup configuration system (`src/config/strategy_config.py`)
- [x] Create basic backtest engine skeleton (`src/backtest/engine.py`)
- [x] Create portfolio manager (`src/backtest/portfolio.py`)
- [x] Create DCA strategy skeleton (`src/strategy/dca_strategy.py`)

### ⏳ Pending
- [ ] **NEXT: Implement DCA Strategy logic** (see `NEXT_STEPS.md`)

---

## Phase 2: Strategy Logic Implementation

### ⏳ Pending
- [ ] Implement entry counting system (1-9, 10-40, 41+)
- [ ] Implement RSI entry conditions (<=30 Buy, >=70 Sell)
- [ ] Implement break logic (RSI < 60 ngắt nhịp)
- [ ] Implement exit conditions (RSI = 50)
- [ ] Handle gaps between entries
- [ ] Direction selection (Buy OR Sell per cycle)

---

## Phase 3: Lot Size & Configuration

### ⏳ Pending
- [ ] Design lot size configuration format
- [ ] Implement lot size loader (JSON/YAML/CSV)
- [ ] Support formula-based lot calculation
- [ ] Support manual lot assignment
- [ ] Create default config template

---

## Phase 4: Backtest Engine

### ⏳ Pending
- [ ] Integrate strategy logic into engine
- [ ] Portfolio management (track open positions)
- [ ] P&L calculation
- [ ] Position sizing based on lot config
- [ ] Handle multiple cycles (reset after exit)

---

## Phase 5: Reporting & Analysis

### ⏳ Pending
- [ ] Generate summary report
- [ ] Generate detailed per-entry report
- [ ] Generate per-cycle report
- [ ] CSV export functionality
- [ ] JSON export functionality
- [ ] Calculate metrics (win rate, drawdown, etc.)

---

## Phase 6: Testing & Validation

### ⏳ Pending
- [ ] Unit tests for RSI calculation
- [ ] Unit tests for entry counting
- [ ] Unit tests for break detection
- [ ] Unit tests for exit detection
- [ ] Integration test with sample data
- [ ] Validation against manual calculation
- [ ] Edge case testing

---

## Phase 7: Documentation & Polish

### ⏳ Pending
- [ ] User guide
- [ ] Configuration guide
- [ ] Example configs
- [ ] README update with usage examples

---

## Notes
- Priority: Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7
- Each phase should be testable independently
- Keep code modular for easy modification


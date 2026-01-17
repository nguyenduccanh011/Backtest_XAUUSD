"""
Web application cho Backtest XAUUSD
FastAPI backend với HTML/CSS/JS frontend
"""

import json
from pathlib import Path
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import pandas as pd

from src.utils.data_loader import DataLoader
from src.strategy.dca_strategy import DCAStrategy
from src.backtest.portfolio import Portfolio
from src.backtest.engine import BacktestEngine
from src.config.strategy_config import StrategyConfig
from src.utils.chart_visualizer import ChartVisualizer
from src.utils.backtest_utils import (
    run_backtest_with_params,
    optimize_rsi_thresholds,
    get_xauusd_average_price,
    DEFAULT_OPTIMIZE_BUY_RANGE,
    DEFAULT_OPTIMIZE_SELL_RANGE,
    DEFAULT_OPTIMIZE_STEP,
    FIRST_TRADE_ENTRY,
    MAX_TRADE_ENTRY,
    ENTRY_TRADE_START,
    ENTRY_TRADE_END,
    _extract_backtest_result,
)

CONFIG_PATH = Path("configs/default_config.json")

app = FastAPI(title="Backtest XAUUSD Web App")


def convert_events_to_serializable(engine):
    """Convert engine events to JSON-serializable format"""
    events = []
    if engine and hasattr(engine, 'events'):
        for event in engine.events:
            event_dict = {
                'type': event.get('type'),
                'timestamp': event.get('timestamp'),
                'price': event.get('price'),
                'rsi': event.get('rsi'),
            }
            # Add optional fields
            if 'entry_number' in event:
                event_dict['entry_number'] = event['entry_number']
            if 'direction' in event:
                event_dict['direction'] = event['direction']
            if 'should_trade' in event:
                event_dict['should_trade'] = event['should_trade']
            if 'entry_count' in event:
                event_dict['entry_count'] = event['entry_count']
            # Convert timestamp to ISO string if it's a pandas Timestamp
            if hasattr(event.get('timestamp'), 'isoformat'):
                event_dict['timestamp'] = event['timestamp'].isoformat()
            elif isinstance(event.get('timestamp'), pd.Timestamp):
                event_dict['timestamp'] = event['timestamp'].isoformat()
            events.append(event_dict)
    return events

# CORS middleware for TradingView
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (HTML, CSS, JS)
static_dir = Path("web_static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount TradingView library
charting_library_dir = Path("charting_library-30.0.0")
if charting_library_dir.exists():
    app.mount("/charting_library", StaticFiles(directory=str(charting_library_dir / "charting_library")), name="charting_library")
    app.mount("/datafeeds", StaticFiles(directory=str(charting_library_dir / "datafeeds")), name="datafeeds")


# Pydantic models for request/response
class LotDataItem(BaseModel):
    entry_number: int
    money_amount: float
    lot_size: float


class CalculateLotRequest(BaseModel):
    money_values: List[float]
    data_file_path: Optional[str] = None


class BacktestRequest(BaseModel):
    buy_threshold: float
    sell_threshold: float
    lot_data: List[LotDataItem]
    data_file_path: Optional[str] = None
    direction_mode: str = "BUY"
    entry_rsi: Optional[float] = None
    exit_rsi: Optional[float] = None
    break_rsi: Optional[float] = None
    auto_optimize: bool = False


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve main HTML page"""
    html_file = static_dir / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    return HTMLResponse("""
    <html>
        <head><title>Backtest XAUUSD</title></head>
        <body>
            <h1>Backtest XAUUSD Web App</h1>
            <p>Please create web_static/index.html</p>
        </body>
    </html>
    """)


@app.post("/api/backtest")
async def run_backtest(request: BacktestRequest):
    """Chạy backtest với tham số từ request"""
    try:
        # Convert Pydantic models to dicts
        lot_data = [item.dict() for item in request.lot_data]
        
        if request.auto_optimize:
            # Chế độ tự động tối ưu
            result = optimize_rsi_thresholds(
                lot_data,
                request.data_file_path,
                buy_range=DEFAULT_OPTIMIZE_BUY_RANGE,
                sell_range=DEFAULT_OPTIMIZE_SELL_RANGE,
                step=DEFAULT_OPTIMIZE_STEP,
                direction_mode=request.direction_mode,
            )
            
            # Chạy lại với tham số tốt nhất để lấy engine
            best_buy = result.get('buy_threshold', 30)
            best_sell = result.get('sell_threshold', 65)
            direction = request.direction_mode.upper()
            
            if direction == "BUY":
                buy_th = best_buy
                sell_th = 100.0
            else:
                buy_th = 0.0
                sell_th = best_sell
            
            _, engine = run_backtest_with_params(
                buy_th,
                sell_th,
                lot_data,
                request.data_file_path,
                silent=True,
                direction_mode=direction,
            )
            
            # Convert events to serializable format
            events = convert_events_to_serializable(engine)
            
            return {
                "success": True,
                "optimized": True,
                "best_buy_threshold": best_buy,
                "best_sell_threshold": best_sell,
                "summary": result.get('summary', {}),
                "all_results": result.get('all_results', []),
                "events": events,
            }
        else:
            # Chế độ thủ công
            direction = request.direction_mode.upper()
            if direction == "BUY":
                buy_th = request.entry_rsi or request.buy_threshold
                sell_th = 100.0
            else:
                buy_th = 0.0
                sell_th = request.entry_rsi or request.sell_threshold
            
            summary, engine = run_backtest_with_params(
                buy_th,
                sell_th,
                lot_data,
                request.data_file_path,
                silent=True,
                direction_mode=direction,
                entry_rsi=request.entry_rsi,
                exit_rsi=request.exit_rsi,
                break_rsi=request.break_rsi,
            )
            
            # Convert events to serializable format
            events = convert_events_to_serializable(engine)
            
            return {
                "success": True,
                "optimized": False,
                "summary": summary,
                "events": events,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/calculate-lot")
async def calculate_lot(request: CalculateLotRequest):
    """Tính lot size từ danh sách số tiền"""
    try:
        xauusd_price = get_xauusd_average_price(request.data_file_path)
        
        # Đảm bảo xauusd_price là số hợp lệ
        if not xauusd_price or xauusd_price <= 0:
            xauusd_price = 2000.0  # Giá mặc định
        
        lot_data = []
        for idx, money in enumerate(request.money_values):
            entry_number = idx + FIRST_TRADE_ENTRY
            
            # Tính lot size
            if entry_number < ENTRY_TRADE_START:
                lot_size = 0.0
            elif entry_number <= ENTRY_TRADE_END:
                if money > 0 and xauusd_price > 0:
                    lot_size = money / (xauusd_price * 100)
                else:
                    lot_size = 0.0
            else:
                lot_size = 0.0
            
            lot_data.append({
                "entry_number": entry_number,
                "money_amount": money,
                "lot_size": round(lot_size, 5)
            })
        
        return {
            "success": True,
            "lot_data": lot_data,
            "xauusd_price": xauusd_price,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data-files")
async def list_data_files():
    """Liệt kê các file data có sẵn"""
    data_dir = Path("data/raw")
    files = []
    if data_dir.exists():
        for file in data_dir.glob("*.csv"):
            files.append({
                "name": file.name,
                "path": str(file),
            })
    return {"files": files}


@app.post("/api/upload-data")
async def upload_data_file(file: UploadFile = File(...)):
    """Upload file data CSV"""
    try:
        upload_dir = Path("data/raw")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return {
            "success": True,
            "filename": file.filename,
            "path": str(file_path),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def plot_chart_auto(engine, direction: str = "BUY"):
    """
    Tự động vẽ biểu đồ sau khi backtest hoàn thành.
    
    Args:
        engine: BacktestEngine instance
        direction: Direction mode (BUY/SELL)
    
    Returns:
        str: Chart filename
    """
    try:
        if engine is None or engine.data is None or len(engine.data) == 0:
            return None
        
        # Lấy events từ engine
        events = engine.events if hasattr(engine, 'events') and engine.events is not None else []
        if not isinstance(events, list):
            events = []
        
        # Tạo visualizer
        visualizer = ChartVisualizer(
            data=engine.data,
            events=events
        )
        
        # Tạo thư mục lưu biểu đồ
        output_dir = Path("results/charts")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Tên file với timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_filename = f"backtest_chart_{timestamp}.png"
        save_path = output_dir / chart_filename
        
        # Đếm số events
        entry_events = [e for e in events if isinstance(e, dict) and e.get('type') == 'entry']
        exit_events = [e for e in events if isinstance(e, dict) and e.get('type') == 'exit']
        
        # Tạo title
        title = f"XAUUSD Backtest {direction} - {len(entry_events)} entries, {len(exit_events)} exits"
        
        # Vẽ biểu đồ (không hiển thị, chỉ lưu file)
        visualizer.plot(
            title=title,
            save_path=str(save_path),
            show=False,
            max_bars=1000,
        )
        
        return chart_filename
    except Exception as e:
        print(f"⚠️ Lỗi khi vẽ biểu đồ tự động: {e}")
        import traceback
        traceback.print_exc()
        return None


# TradingView UDF Datafeed Endpoints
@app.get("/api/tv/config")
async def tv_config():
    """TradingView UDF config endpoint"""
    return {
        "supports_search": False,
        "supports_group_request": True,
        "supports_marks": False,
        "supports_timescale_marks": False,
        "supports_time": True,
        "exchanges": [
            {"value": "FOREX", "name": "Forex", "desc": "Forex"}
        ],
        "symbols_types": [
            {"name": "forex", "value": "forex"}
        ],
        "supported_resolutions": ["1", "5", "15", "30", "60", "240", "1D", "1W", "1M"],
    }


@app.get("/api/tv/symbols")
async def tv_symbols(
    symbol: str = Query(..., description="Symbol name"),
    currency_code: Optional[str] = None,
    unit_id: Optional[str] = None,
):
    """TradingView UDF symbol info endpoint"""
    return {
        "name": symbol,
        "ticker": symbol,
        "description": "XAU/USD",
        "type": "forex",
        "session": "24x7",
        "timezone": "Etc/UTC",
        "exchange": "FOREX",
        "listed_exchange": "FOREX",
        "exchange_listed_name": "FOREX:XAUUSD",
        "minmov": 1,
        "pricescale": 100,
        "has_intraday": True,
        "has_daily": True,
        "has_weekly_and_monthly": True,
        "supported_resolutions": ["1", "5", "15", "30", "60", "240", "1D", "1W", "1M"],
        "intraday_multipliers": ["1", "5", "15", "30", "60", "240"],
        "volume_precision": 0,
        "data_status": "streaming",
        "format": "price",
    }


@app.get("/api/tv/history")
async def tv_history(
    request: Request,
    symbol: str = Query(..., description="Symbol name"),
    resolution: str = Query(..., description="Resolution (1, 5, 15, 30, 60, 1D, etc.)"),
):
    """TradingView UDF history endpoint"""
    try:
        # Get query parameters - TradingView sends 'from' and 'to', not 'from_time' and 'to_time'
        query_params = dict(request.query_params)
        from_time = query_params.get('from') or query_params.get('from_time')
        to_time = query_params.get('to') or query_params.get('to_time')
        countback = query_params.get('countback')
        
        if from_time is None or to_time is None:
            return {"s": "error", "errmsg": "Missing required parameters: from and to"}
        
        try:
            from_time = int(from_time)
            to_time = int(to_time)
        except (ValueError, TypeError):
            return {"s": "error", "errmsg": "Invalid timestamp format"}
        
        if countback:
            try:
                countback = int(countback)
            except (ValueError, TypeError):
                countback = None
        # Load data from default or last used file
        data_file_path = None
        data_dir = Path("data/raw")
        if data_dir.exists():
            csv_files = list(data_dir.glob("*.csv"))
            if csv_files:
                # Use the most recent file
                data_file_path = str(max(csv_files, key=lambda p: p.stat().st_mtime))
        
        if not data_file_path:
            return {"s": "no_data"}
        
        loader = DataLoader()
        df = loader.load_csv(data_file_path, source="auto")
        
        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            else:
                return {"s": "error", "errmsg": "Data must have datetime index"}
        
        # Make timezone-aware if not already
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        
        # Convert resolution to pandas frequency
        resolution_map = {
            "1": "1min",
            "5": "5min",
            "15": "15min",
            "30": "30min",
            "60": "1h",  # Changed from '1H' to '1h' (deprecated)
            "240": "4h",  # Changed from '4H' to '4h' (deprecated)
            "1D": "1D",
            "1W": "1W",
            "1M": "1M",
        }
        
        freq = resolution_map.get(resolution, "1h")  # Changed from '1H' to '1h'
        
        # Resample if needed (only for intraday resolutions)
        if resolution in ["1", "5", "15", "30", "60", "240"]:
            try:
                df = df.resample(freq).agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum' if 'volume' in df.columns else 'first',
                }).dropna()
            except Exception as e:
                return {"s": "error", "errmsg": f"Resampling error: {str(e)}"}
        
        # Filter by time range
        from_dt = pd.Timestamp.fromtimestamp(from_time, tz='UTC')
        to_dt = pd.Timestamp.fromtimestamp(to_time, tz='UTC')
        
        # Debug: Log data range
        print(f"DEBUG: Requested range: {from_dt} to {to_dt}")
        print(f"DEBUG: Data range: {df.index.min()} to {df.index.max()}")
        print(f"DEBUG: Data shape before filter: {df.shape}")
        
        df_filtered = df[(df.index >= from_dt) & (df.index <= to_dt)]
        
        print(f"DEBUG: Data shape after filter: {df_filtered.shape}")
        
        # If no data in exact range, try to return available data
        if df_filtered.empty:
            # If we have data but not in the requested range, return what we have
            # This helps TradingView display something while it adjusts the time range
            if not df.empty:
                # Return the most recent data (last 500 bars to avoid too much data)
                df_filtered = df.tail(500)
                print(f"DEBUG: No data in exact range, returning last 500 bars")
            else:
                return {"s": "no_data"}
        
        if df_filtered.empty:
            return {"s": "no_data"}
        
        # Convert to UDF format
        bars = []
        for idx, row in df_filtered.iterrows():
            timestamp = int(idx.timestamp())
            bars.append({
                "t": timestamp,
                "o": float(row['open']),
                "h": float(row['high']),
                "l": float(row['low']),
                "c": float(row['close']),
                "v": float(row.get('volume', 0)),
            })
        
        # Sort by time (ascending)
        bars.sort(key=lambda x: x["t"])
        
        # Calculate nextTime for TradingView to know where data is available
        nextTime = None
        if bars:
            # nextTime should be the timestamp of the last bar + 1 period
            last_timestamp = bars[-1]["t"]
            # Add one period based on resolution
            resolution_seconds = {
                "1": 60,
                "5": 300,
                "15": 900,
                "30": 1800,
                "60": 3600,
                "240": 14400,
                "1D": 86400,
                "1W": 604800,
                "1M": 2592000,
            }.get(resolution, 3600)
            nextTime = last_timestamp + resolution_seconds
        
        response_data = {
            "s": "ok",
            "t": [b["t"] for b in bars],
            "o": [b["o"] for b in bars],
            "h": [b["h"] for b in bars],
            "l": [b["l"] for b in bars],
            "c": [b["c"] for b in bars],
            "v": [b["v"] for b in bars],
        }
        
        if nextTime:
            response_data["nextTime"] = nextTime
        
        print(f"DEBUG: Returning {len(bars)} bars, nextTime: {nextTime}")
        
        return response_data
    except Exception as e:
        return {"s": "error", "errmsg": str(e)}


@app.get("/api/tv/time")
async def tv_time():
    """TradingView UDF server time endpoint"""
    return int(datetime.now().timestamp())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


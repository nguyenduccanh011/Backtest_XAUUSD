"""
Data Loader - Load and validate historical price data
Supports multiple CSV formats from different sources (Dukascopy, TradingView, MetaTrader, etc.)
Also supports direct download from OANDA API
"""

import pandas as pd
import numpy as np
import csv
from pathlib import Path
from typing import Optional, Union
from datetime import datetime, timedelta


class DataLoader:
    """
    Load historical XAUUSD data from CSV files.
    Supports multiple formats from different data sources.
    """
    
    def __init__(self):
        """Initialize data loader."""
        pass
    
    def _detect_delimiter(self, file_path):
        """
        Auto-detect CSV delimiter using Python's csv.Sniffer.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            str: Detected delimiter (default: ',')
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read first 2KB to detect delimiter
                sample = f.read(2048)
                if not sample:
                    return ','
                
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                # Validate delimiter is comma or semicolon (common formats)
                if delimiter in [',', ';']:
                    return delimiter
                else:
                    # If detected delimiter is not comma/semicolon, 
                    # try to determine by checking sample
                    comma_count = sample.count(',')
                    semicolon_count = sample.count(';')
                    
                    if semicolon_count > comma_count:
                        return ';'
                    elif comma_count > 0:
                        return ','
                    else:
                        return ','
        except Exception:
            # Fallback: try to detect by counting occurrences
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    sample = f.read(2048)
                    comma_count = sample.count(',')
                    semicolon_count = sample.count(';')
                    
                    if semicolon_count > comma_count:
                        return ';'
                    else:
                        return ','
            except Exception:
                # Ultimate fallback: default to comma
                return ','
    
    def load_csv(self, file_path, symbol="XAUUSD", source="auto"):
        """
        Load data from CSV file with automatic format detection.
        
        Supported sources:
        - "auto": Auto-detect format
        - "dukascopy": Dukascopy format
        - "tradingview": TradingView format
        - "metatrader": MetaTrader format
        - "standard": Standard format (timestamp, open, high, low, close, volume)
        
        Args:
            file_path: Path to CSV file
            symbol: Symbol name (default: XAUUSD)
            source: Data source format (default: "auto")
            
        Returns:
            pandas.DataFrame: OHLCV data with datetime index
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")
        
        # Auto-detect delimiter using csv.Sniffer
        delimiter = self._detect_delimiter(file_path)
        df = pd.read_csv(file_path, sep=delimiter)
        
        # Validate: ensure we have multiple columns (not single column due to wrong delimiter)
        if len(df.columns) == 1:
            # Try alternative delimiter if only 1 column detected
            alternative_delimiter = ',' if delimiter == ';' else ';'
            df_alt = pd.read_csv(file_path, sep=alternative_delimiter)
            if len(df_alt.columns) > len(df.columns):
                df = df_alt
                delimiter = alternative_delimiter
        
        # Auto-detect format if needed
        if source == "auto":
            source = self._detect_format(df)
        
        # Normalize based on source
        df = self._normalize_format(df, source)
        
        # Validate and get cleaned DataFrame
        df = self.validate_data(df)
        
        # Set datetime index
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
        
        return df
    
    def _detect_format(self, df):
        """
        Auto-detect CSV format from column names.
        
        Args:
            df: DataFrame with raw data
            
        Returns:
            str: Detected format name
        """
        columns_lower = [col.lower() for col in df.columns]
        
        # Dukascopy format: "Local time,Open,High,Low,Close,Volume" or "Date;Open;High;Low;Close;Volume"
        if 'local time' in columns_lower or ('date' in columns_lower and 'time' not in columns_lower):
            if 'open' in columns_lower and 'high' in columns_lower:
                return "dukascopy"
        
        # MetaTrader format: "Date,Time,Open,High,Low,Close,Volume"
        if 'date' in columns_lower and 'time' in columns_lower:
            return "metatrader"
        
        # TradingView format: "time,open,high,low,close,volume"
        if 'time' in columns_lower and 'open' in columns_lower and 'date' not in columns_lower:
            return "tradingview"
        
        # Standard format: "timestamp,open,high,low,close,volume"
        if 'timestamp' in columns_lower:
            return "standard"
        
        # Default: try standard
        return "standard"
    
    def _normalize_format(self, df, source):
        """
        Normalize DataFrame to standard format.
        
        Args:
            df: Raw DataFrame
            source: Source format name
            
        Returns:
            pandas.DataFrame: Normalized DataFrame
        """
        df = df.copy()
        columns_lower = {col.lower(): col for col in df.columns}
        
        if source == "dukascopy":
            # Dukascopy: "Local time,Open,High,Low,Close,Volume" or "Date;Open;High;Low;Close;Volume"
            mapping = {
                'local time': 'timestamp',
                'date': 'timestamp',
                'time': 'timestamp',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            }
            rename_dict = {}
            for old_key, new_key in mapping.items():
                if old_key in columns_lower:
                    rename_dict[columns_lower[old_key]] = new_key
            df.rename(columns=rename_dict, inplace=True)
            
            # If timestamp column exists, parse it
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        elif source == "tradingview":
            # TradingView: "time,open,high,low,close,volume"
            if 'time' in columns_lower:
                df.rename(columns={columns_lower['time']: 'timestamp'}, inplace=True)
        
        elif source == "metatrader":
            # MetaTrader: "Date,Time,Open,High,Low,Close,Volume"
            if 'date' in columns_lower and 'time' in columns_lower:
                date_col = columns_lower['date']
                time_col = columns_lower['time']
                df['timestamp'] = pd.to_datetime(
                    df[date_col].astype(str) + ' ' + df[time_col].astype(str)
                )
                df.drop(columns=[date_col, time_col], inplace=True, errors='ignore')
            
            # Rename OHLC columns to lowercase
            ohlc_mapping = {
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            }
            rename_dict = {}
            for old_key, new_key in ohlc_mapping.items():
                if old_key in columns_lower:
                    rename_dict[columns_lower[old_key]] = new_key
            df.rename(columns=rename_dict, inplace=True)
        
        # Ensure required columns exist
        required = ['timestamp', 'open', 'high', 'low', 'close']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Could not normalize format. Missing columns: {missing}")
        
        # Select only required columns (volume is optional)
        cols_to_keep = ['timestamp', 'open', 'high', 'low', 'close']
        if 'volume' in df.columns:
            cols_to_keep.append('volume')
        
        df = df[cols_to_keep]
        
        # Convert OHLC to float
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        if 'volume' in df.columns:
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        return df
    
    def validate_data(self, df):
        """
        Validate loaded data.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            pandas.DataFrame: Validated and cleaned DataFrame
            
        Raises:
            ValueError: If data is invalid
        """
        required_columns = ['open', 'high', 'low', 'close']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Check for missing values in OHLC
        for col in required_columns:
            if df[col].isna().any():
                raise ValueError(f"Missing values found in column: {col}")
        
        # Validate OHLC relationships
        invalid_high_low = (df['high'] < df['low']).any()
        if invalid_high_low:
            raise ValueError("Invalid OHLC: high < low found")
        
        invalid_open = ((df['open'] < df['low']) | (df['open'] > df['high'])).any()
        invalid_close = ((df['close'] < df['low']) | (df['close'] > df['high'])).any()
        
        if invalid_open:
            raise ValueError("Invalid OHLC: open price outside high/low range")
        if invalid_close:
            raise ValueError("Invalid OHLC: close price outside high/low range")
        
        # Check for duplicates (if timestamp is index)
        if df.index.name == 'timestamp' or 'timestamp' in df.columns:
            if df.index.duplicated().any():
                print("Warning: Duplicate timestamps found. Keeping first occurrence.")
                df = df[~df.index.duplicated(keep='first')]
        
        return df
    
    def load_from_oanda(self, api_key: str, account_id: str, 
                        symbol: str = "XAU_USD", timeframe: str = "H1",
                        start_date: Optional[Union[datetime, str]] = None,
                        end_date: Optional[Union[datetime, str]] = None,
                        count: int = 5000,
                        environment: str = "practice",
                        save_to_csv: Optional[str] = None) -> pd.DataFrame:
        """
        Load historical data directly from OANDA API.
        
        Requires: pip install oandapyV20
        
        Args:
            api_key: OANDA API key
            account_id: OANDA account ID
            symbol: Symbol (XAU_USD for Gold, default: XAU_USD)
            timeframe: Timeframe (M1, M5, M15, M30, H1, H4, D1, W, M)
            start_date: Start date (datetime or ISO string)
            end_date: End date (datetime or ISO string)
            count: Number of candles (max 5000, used if dates not provided)
            environment: "practice" or "live" (default: "practice")
            save_to_csv: Optional path to save CSV file
            
        Returns:
            pandas.DataFrame: OHLCV data with datetime index
            
        Raises:
            ImportError: If oandapyV20 not installed
            Exception: If API request fails
        """
        try:
            from oandapyV20 import API
            from oandapyV20.endpoints import instruments
        except ImportError:
            raise ImportError(
                "oandapyV20 library not installed. "
                "Install with: pip install oandapyV20"
            )
        
        # Initialize API client
        api = API(
            access_token=api_key,
            environment=environment
        )
        
        # Prepare parameters
        params = {
            "granularity": timeframe,
            "price": "M"  # Mid prices
        }
        
        if start_date and end_date:
            # Convert to ISO format
            if isinstance(start_date, datetime):
                start_date_str = start_date.isoformat() + "Z"
            else:
                start_date_str = start_date
            
            if isinstance(end_date, datetime):
                end_date_str = end_date.isoformat() + "Z"
            else:
                end_date_str = end_date
            
            params["from"] = start_date_str
            params["to"] = end_date_str
        else:
            params["count"] = min(count, 5000)  # OANDA max is 5000
        
        # Make API request
        r = instruments.InstrumentsCandles(
            instrument=symbol,
            params=params
        )
        
        response = api.request(r)
        
        # Parse response
        data = []
        for candle in response['candles']:
            if candle['complete']:  # Only completed candles
                data.append({
                    'timestamp': pd.to_datetime(candle['time']),
                    'open': float(candle['mid']['o']),
                    'high': float(candle['mid']['h']),
                    'low': float(candle['mid']['l']),
                    'close': float(candle['mid']['c']),
                    'volume': int(candle['volume'])
                })
        
        if not data:
            raise ValueError("No data received from OANDA API")
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Validate data and get cleaned DataFrame
        df = self.validate_data(df)
        
        # Save to CSV if requested
        if save_to_csv:
            output_path = Path(save_to_csv)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.reset_index(inplace=True)
            df.to_csv(output_path, index=False)
            print(f"✅ Data saved to {save_to_csv}")
        
        return df
    
    def auto_download(self, symbol="XAUUSD", timeframe="H1", period="1y",
                     output_path="data/raw/xauusd_h1.csv"):
        """
        Tự động download data từ nguồn có thể truy cập được ở Việt Nam.
        
        Thử các nguồn theo thứ tự ưu tiên:
        1. Yahoo Finance (Python) - Khuyến nghị nhất
        2. HistData - Nếu có credentials
        3. TradingView - Chỉ cho D1
        
        Args:
            symbol: Symbol (XAUUSD)
            timeframe: Timeframe (H1, H4, D1)
            period: Period (1y, 2y, etc.)
            output_path: Output CSV path
            
        Returns:
            pandas.DataFrame: Downloaded data
        """
        from src.utils.auto_data_downloader import AutoDataDownloader
        
        downloader = AutoDataDownloader(symbol=symbol, timeframe=timeframe, period=period)
        df = downloader.download(output_path)
        
        if df is None:
            raise ValueError(
                "Không thể download từ bất kỳ nguồn nào. "
                "Vui lòng download thủ công hoặc kiểm tra kết nối internet."
            )
        
        return df
    
    def load_from_oanda_simple(self, api_key: str, symbol: str = "XAU_USD",
                               timeframe: str = "H1", count: int = 500,
                               environment: str = "practice") -> pd.DataFrame:
        """
        Load data from OANDA using requests (no library required).
        
        Args:
            api_key: OANDA API key
            symbol: Symbol (XAU_USD for Gold)
            timeframe: Timeframe (H1, H4, D1, etc.)
            count: Number of candles (max 5000)
            environment: "practice" or "live"
            
        Returns:
            pandas.DataFrame: OHLCV data
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests library required. Install with: pip install requests")
        
        # Determine base URL
        if environment == "practice":
            base_url = "https://api-fxpractice.oanda.com"
        else:
            base_url = "https://api-fxtrade.oanda.com"
        
        url = f"{base_url}/v3/instruments/{symbol}/candles"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "granularity": timeframe,
            "count": min(count, 5000),
            "price": "M"
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse to DataFrame
        candles = []
        for candle in data['candles']:
            if candle['complete']:
                candles.append({
                    'timestamp': pd.to_datetime(candle['time']),
                    'open': float(candle['mid']['o']),
                    'high': float(candle['mid']['h']),
                    'low': float(candle['mid']['l']),
                    'close': float(candle['mid']['c']),
                    'volume': int(candle['volume'])
                })
        
        df = pd.DataFrame(candles)
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Validate and get cleaned DataFrame
        df = self.validate_data(df)
        
        return df


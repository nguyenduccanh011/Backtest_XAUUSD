"""
Script để download XAUUSD data từ OANDA API
Yêu cầu: pip install oandapyV20
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from oandapyV20 import API
    from oandapyV20.endpoints import instruments
    import pandas as pd
except ImportError:
    print("❌ oandapyV20 not installed.")
    print("   Install with: pip install oandapyV20")
    sys.exit(1)


def download_from_oanda(api_key, account_id, symbol="XAU_USD", timeframe="H1",
                       start_date=None, end_date=None, count=5000,
                       output_path="data/raw/xauusd_h1.csv", environment="practice"):
    """
    Download historical data from OANDA API.
    
    Args:
        api_key: OANDA API key
        account_id: OANDA account ID
        symbol: Symbol (XAU_USD for Gold)
        timeframe: Timeframe (M1, M5, M15, M30, H1, H4, D1, W, M)
        start_date: Start date (datetime)
        end_date: End date (datetime)
        count: Number of candles (max 5000 per request)
        output_path: Output CSV file path
        environment: "practice" or "live"
    """
    # Initialize API client
    api = API(
        access_token=api_key,
        environment=environment
    )
    
    print(f"📥 Downloading {symbol} {timeframe} data from OANDA...")
    print(f"   Environment: {environment}")
    
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
        print(f"   Date range: {start_date_str} to {end_date_str}")
    else:
        params["count"] = min(count, 5000)  # OANDA max is 5000
        print(f"   Count: {params['count']} candles")
    
    # Make API request
    try:
        r = instruments.InstrumentsCandles(
            instrument=symbol,
            params=params
        )
        
        print("   Requesting data...")
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
            print("❌ No data received")
            return False
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Save to CSV
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.reset_index(inplace=True)
        df.to_csv(output_path, index=False)
        
        print(f"✅ Data saved to {output_path}")
        print(f"   Rows: {len(df)}")
        print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading from OANDA: {e}")
        return False


def main():
    """
    Main function.
    """
    print("=" * 60)
    print("OANDA API - XAUUSD Data Downloader")
    print("=" * 60)
    
    # Get credentials from environment variables or user input
    api_key = os.getenv("OANDA_API_KEY")
    account_id = os.getenv("OANDA_ACCOUNT_ID")
    
    if not api_key:
        print("\n⚠️  OANDA_API_KEY not found in environment variables.")
        print("   You can set it with: export OANDA_API_KEY=your-key")
        api_key = input("\nEnter OANDA API Key: ").strip()
    
    if not account_id:
        print("\n⚠️  OANDA_ACCOUNT_ID not found in environment variables.")
        account_id = input("Enter OANDA Account ID: ").strip()
    
    if not api_key or not account_id:
        print("\n❌ API Key and Account ID are required.")
        print("\nTo get credentials:")
        print("1. Create demo account at https://www.oanda.com/")
        print("2. Go to Manage API Access in account settings")
        print("3. Create API Token and copy API Key and Account ID")
        print("\nSee docs/OANDA_API_GUIDE.md for detailed instructions.")
        return
    
    # Configuration
    symbol = "XAU_USD"
    timeframe = "H1"
    environment = "practice"  # or "live"
    
    # Date range (last 1 year)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # Download
    success = download_from_oanda(
        api_key=api_key,
        account_id=account_id,
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        output_path="data/raw/xauusd_h1.csv",
        environment=environment
    )
    
    if success:
        print("\n✅ Download completed successfully!")
        print("   You can now use this data for backtesting.")
    else:
        print("\n❌ Download failed. Please check your credentials and try again.")


if __name__ == "__main__":
    main()







from src.utils.data_loader import DataLoader

def main():
    dl = DataLoader()
    df = dl.load_csv("data/raw/xauusd_h1.csv")

    close = df["close"]
    d = close.diff()
    up = d.clip(lower=0)
    down = (-d).clip(lower=0)

    n = 14
    rs = up.rolling(n).mean() / down.rolling(n).mean()
    rsi = 100 - (100 / (1 + rs))

    print("✅ Columns:", df.columns.tolist())
    print("Rows:", len(df))
    print("RSI<=30:", int((rsi <= 30).sum()))
    print("RSI>=70:", int((rsi >= 70).sum()))
    print(rsi.dropna().describe())

if __name__ == "__main__":
    main()

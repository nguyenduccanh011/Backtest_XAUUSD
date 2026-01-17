"""
Script khởi động web application
"""
import uvicorn

if __name__ == "__main__":
    print("🚀 Đang khởi động Backtest XAUUSD Web App...")
    print("📂 Truy cập: http://localhost:8000")
    print("⏹️  Nhấn Ctrl+C để dừng server\n")
    
    uvicorn.run(
        "web_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload khi code thay đổi
    )


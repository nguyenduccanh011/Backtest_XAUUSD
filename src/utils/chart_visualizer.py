"""
Chart Visualizer - Vẽ biểu đồ nến + RSI + điểm vào lệnh
"""

# Kiểm tra các thư viện cần thiết - báo lỗi rõ ràng nếu thiếu
try:
    import matplotlib
except ImportError:
    raise ImportError(
        "Thiếu thư viện matplotlib.\n"
        "Cài đặt: pip install matplotlib\n"
        "Hoặc chạy: pip install -r requirements.txt"
    )

try:
    import mplfinance as mpf
except ImportError:
    raise ImportError(
        "Thiếu thư viện mplfinance.\n"
        "Cài đặt: pip install mplfinance\n"
        "Hoặc chạy: pip install -r requirements.txt"
    )

import pandas as pd
import numpy as np
# Set backend trước khi import pyplot
# Sử dụng 'Agg' backend cho web app (headless, không cần GUI)
# Chỉ set backend nếu chưa được set (để cho phép override từ bên ngoài)
if matplotlib.get_backend() == 'module://matplotlib_inline.backend_inline':
    # Nếu đang dùng inline backend (Jupyter), giữ nguyên
    pass
elif 'Agg' not in matplotlib.get_backend() and 'TkAgg' not in matplotlib.get_backend() and 'Qt' not in matplotlib.get_backend():
    # Chỉ set backend nếu chưa được set
    try:
        matplotlib.use('Agg')  # Agg backend cho web app (headless, không cần GUI)
    except Exception:
        # Nếu Agg không khả dụng, thử backend khác
        try:
            matplotlib.use('TkAgg')  # Fallback cho Windows
        except Exception:
            try:
                matplotlib.use('Qt5Agg')  # Fallback cho Qt
            except Exception:
                # Dùng backend mặc định
                pass

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from pathlib import Path
from typing import Optional, List, Dict


class ChartVisualizer:
    """
    Vẽ biểu đồ nến kết hợp với RSI và đánh dấu điểm vào/ra lệnh.
    """

    def __init__(self, data: pd.DataFrame, events: List[Dict] = None):
        """
        Khởi tạo visualizer.

        Args:
            data: DataFrame với OHLCV + RSI (columns: open, high, low, close, volume, rsi)
            events: Danh sách events từ backtest (entry/exit points)
        """
        self.data = data.copy()
        self.events = events or []
        
        # Lưu index gốc để match với events
        self.original_index = self.data.index.copy()
        
        # Chuẩn bị data cho mplfinance (cần index là DatetimeIndex)
        if not isinstance(self.data.index, pd.DatetimeIndex):
            if 'timestamp' in self.data.columns:
                self.data.index = pd.to_datetime(self.data['timestamp'])
                self.index_mapping = None
            else:
                # Tạo index giả nếu không có timestamp
                # Lưu mapping từ index gốc sang DatetimeIndex mới
                new_index = pd.date_range(start='2020-01-01', periods=len(self.data), freq='H')
                self.index_mapping = dict(zip(self.original_index, new_index))
                self.data.index = new_index
        else:
            self.index_mapping = None
        
        # Chuẩn hóa RSI về khoảng 0-100 nếu cần
        if 'rsi' in self.data.columns:
            rsi_values = self.data['rsi'].dropna()
            if len(rsi_values) > 0:
                max_rsi = rsi_values.max()
                min_rsi = rsi_values.min()
                # Nếu RSI có giá trị > 100 hoặc < 0, hoặc có giá trị quá lớn (> 1000), chuẩn hóa
                if max_rsi > 1000 or min_rsi < -100:
                    # Giả định RSI đang ở dạng khác (có thể đã nhân với 100 hoặc sai)
                    # Thử chia cho 100 nếu giá trị quá lớn
                    if max_rsi > 1000:
                        self.data['rsi'] = self.data['rsi'] / 100
                    # Đảm bảo RSI trong khoảng 0-100
                    self.data['rsi'] = self.data['rsi'].clip(0, 100)

    def plot(
        self,
        title: str = "XAUUSD - Candlestick + RSI",
        save_path: Optional[str] = None,
        show: bool = True,
        max_bars: int = 1000,
    ):
        """
        Vẽ biểu đồ nến + RSI + điểm vào lệnh.

        Args:
            title: Tiêu đề biểu đồ
            save_path: Đường dẫn lưu file (nếu None thì không lưu)
            show: Hiển thị biểu đồ (default: True)
            max_bars: Số nến tối đa để vẽ (để tránh quá tải, default: 1000)
        """
        # Kiểm tra dữ liệu có đủ cột cần thiết
        required_cols = ['open', 'high', 'low', 'close']
        missing_cols = [col for col in required_cols if col not in self.data.columns]
        if missing_cols:
            raise ValueError(f"Thiếu cột dữ liệu: {missing_cols}. Cần có: {required_cols}")
        
        # Kiểm tra dữ liệu có rỗng không
        if len(self.data) == 0:
            raise ValueError("Dữ liệu rỗng, không thể vẽ biểu đồ")
        
        # Giới hạn số nến để vẽ (lấy nến cuối cùng)
        plot_data = self.data.tail(max_bars).copy()
        
        # Kiểm tra plot_data có dữ liệu hợp lệ
        if len(plot_data) == 0:
            raise ValueError(f"Không có dữ liệu để vẽ sau khi giới hạn {max_bars} nến")
        
        # Loại bỏ các hàng có giá trị NaN trong các cột cần thiết
        plot_data = plot_data.dropna(subset=required_cols)
        if len(plot_data) == 0:
            raise ValueError("Tất cả dữ liệu đều có giá trị NaN, không thể vẽ biểu đồ")
        
        # Đổi tên cột sang chữ hoa cho mplfinance (yêu cầu: Open, High, Low, Close, Volume)
        # Lưu ý: Giữ nguyên RSI column (có thể là 'rsi' hoặc 'RSI')
        column_mapping = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }
        
        # Đổi tên RSI nếu có (có thể là 'rsi' hoặc đã là 'RSI')
        if 'rsi' in plot_data.columns:
            column_mapping['rsi'] = 'RSI'
        # Nếu đã có 'RSI' thì giữ nguyên
        
        for old_col, new_col in column_mapping.items():
            if old_col in plot_data.columns:
                plot_data.rename(columns={old_col: new_col}, inplace=True)
        
        # Đảm bảo có Volume (nếu không có thì tạo cột giả)
        if 'Volume' not in plot_data.columns:
            plot_data['Volume'] = 0
        
        # Kiểm tra lại sau khi rename
        required_mpl_cols = ['Open', 'High', 'Low', 'Close']
        missing_mpl_cols = [col for col in required_mpl_cols if col not in plot_data.columns]
        if missing_mpl_cols:
            raise ValueError(
                f"Sau khi đổi tên cột, thiếu: {missing_mpl_cols}. "
                f"Các cột hiện có: {list(plot_data.columns)}"
            )
        
        # Kiểm tra giá trị có hợp lệ không (không phải inf hoặc NaN quá nhiều)
        for col in required_mpl_cols:
            if plot_data[col].isna().all():
                raise ValueError(f"Cột {col} toàn bộ là NaN, không thể vẽ biểu đồ")
            # Thay thế inf bằng NaN rồi fillna
            plot_data[col] = plot_data[col].replace([np.inf, -np.inf], np.nan)
            # Fill NaN bằng giá trị trước đó (forward fill) - dùng ffill() thay vì fillna(method='ffill')
            plot_data[col] = plot_data[col].ffill().bfill()
            # Nếu vẫn còn NaN, fill bằng giá trị trung bình
            if plot_data[col].isna().any():
                mean_val = plot_data[col].mean()
                if pd.notna(mean_val):
                    plot_data[col] = plot_data[col].fillna(mean_val)
                else:
                    # Nếu không có giá trị trung bình, dùng giá trị đầu tiên hợp lệ
                    first_valid = plot_data[col].dropna().iloc[0] if len(plot_data[col].dropna()) > 0 else 0
                    plot_data[col] = plot_data[col].fillna(first_valid)
        
        # Chuẩn bị markers cho entry/exit/break points
        entry_markers = []
        exit_markers = []
        break_markers = []
        
        # Tạo dict để map timestamp -> price cho markers
        entry_dict = {}
        exit_dict = {}
        break_dict = {}
        
        for event in self.events:
            if event['type'] == 'entry':
                timestamp = event['timestamp']
                price = event['price']
                direction = event.get('direction', 'BUY')
                entry_number = event.get('entry_number', 0)
                should_trade = event.get('should_trade', False)
                
                # Chuyển đổi timestamp để khớp với index của plot_data
                # Sử dụng index_mapping nếu có (khi index gốc không phải DatetimeIndex)
                if self.index_mapping is not None:
                    # Tìm timestamp trong mapping
                    if timestamp in self.index_mapping:
                        timestamp = self.index_mapping[timestamp]
                    else:
                        continue  # Bỏ qua nếu không tìm thấy trong mapping
                else:
                    # Nếu index là DatetimeIndex, chuyển timestamp sang datetime
                    if isinstance(plot_data.index, pd.DatetimeIndex):
                        if not isinstance(timestamp, pd.Timestamp):
                            try:
                                timestamp = pd.to_datetime(timestamp)
                            except (ValueError, TypeError):
                                continue
                
                # Tìm timestamp gần nhất trong index nếu không khớp chính xác
                if timestamp not in plot_data.index:
                    # Tìm timestamp gần nhất (trong vòng 1 giờ)
                    try:
                        if isinstance(plot_data.index, pd.DatetimeIndex):
                            time_diff = abs(plot_data.index - timestamp)
                            closest_idx = time_diff.argmin()
                            if time_diff.iloc[closest_idx] <= pd.Timedelta(hours=1):
                                timestamp = plot_data.index[closest_idx]
                            else:
                                continue  # Bỏ qua nếu quá xa
                        else:
                            continue  # Không khớp và không phải DatetimeIndex
                    except (ValueError, TypeError, AttributeError):
                        continue  # Bỏ qua nếu có lỗi
                
                # Chỉ đánh dấu nếu trong phạm vi data đang vẽ
                if timestamp in plot_data.index:
                    # Màu: xanh cho BUY, đỏ cho SELL
                    # Kích thước: lớn hơn nếu should_trade=True (vào lệnh thực tế)
                    color = 'green' if direction == 'BUY' else 'red'
                    size = 200 if should_trade else 100
                    
                    entry_dict[timestamp] = {
                        'price': price,
                        'color': color,
                        'size': size,
                        'entry_number': entry_number,
                        'direction': direction
                    }
            
            elif event['type'] == 'exit':
                timestamp = event['timestamp']
                price = event['price']
                
                # Chuyển đổi timestamp để khớp với index của plot_data
                if self.index_mapping is not None:
                    if timestamp in self.index_mapping:
                        timestamp = self.index_mapping[timestamp]
                    else:
                        continue
                else:
                    if isinstance(plot_data.index, pd.DatetimeIndex):
                        if not isinstance(timestamp, pd.Timestamp):
                            try:
                                timestamp = pd.to_datetime(timestamp)
                            except (ValueError, TypeError):
                                continue
                
                # Tìm timestamp gần nhất trong index nếu không khớp chính xác
                if timestamp not in plot_data.index:
                    try:
                        if isinstance(plot_data.index, pd.DatetimeIndex):
                            time_diff = abs(plot_data.index - timestamp)
                            closest_idx = time_diff.argmin()
                            if time_diff.iloc[closest_idx] <= pd.Timedelta(hours=1):
                                timestamp = plot_data.index[closest_idx]
                            else:
                                continue
                        else:
                            continue
                    except (ValueError, TypeError, AttributeError):
                        continue
                
                if timestamp in plot_data.index:
                    exit_dict[timestamp] = price
            
            elif event['type'] == 'break':
                timestamp = event['timestamp']
                price = event['price']
                direction = event.get('direction', 'BUY')
                
                # Chuyển đổi timestamp để khớp với index của plot_data
                if self.index_mapping is not None:
                    if timestamp in self.index_mapping:
                        timestamp = self.index_mapping[timestamp]
                    else:
                        continue
                else:
                    if isinstance(plot_data.index, pd.DatetimeIndex):
                        if not isinstance(timestamp, pd.Timestamp):
                            try:
                                timestamp = pd.to_datetime(timestamp)
                            except (ValueError, TypeError):
                                continue
                
                # Tìm timestamp gần nhất trong index nếu không khớp chính xác
                if timestamp not in plot_data.index:
                    try:
                        if isinstance(plot_data.index, pd.DatetimeIndex):
                            time_diff = abs(plot_data.index - timestamp)
                            closest_idx = time_diff.argmin()
                            if time_diff.iloc[closest_idx] <= pd.Timedelta(hours=1):
                                timestamp = plot_data.index[closest_idx]
                            else:
                                continue
                        else:
                            continue
                    except (ValueError, TypeError, AttributeError):
                        continue
                
                if timestamp in plot_data.index:
                    break_dict[timestamp] = {
                        'price': price,
                        'direction': direction
                    }
        
        # Tạo list markers cho mplfinance
        # Format: [(timestamp, price, marker_style), ...]
        for ts, info in entry_dict.items():
            entry_markers.append((ts, info['price'], info['color'], info['size']))
        
        for ts, price in exit_dict.items():
            exit_markers.append((ts, price, 'orange', 150))
        
        for ts, info in break_dict.items():
            break_markers.append((ts, info['price'], 'purple', 180))
        
        # Chuẩn bị RSI panel (nếu có)
        rsi_plot = []
        if 'RSI' in plot_data.columns:
            rsi_data = plot_data['RSI'].dropna()
            if len(rsi_data) > 0:
                # Đảm bảo RSI trong khoảng 0-100
                rsi_data = rsi_data.clip(0, 100)
                
                # Tạo custom plot cho RSI với màu gradient
                # Lưu ý: mplfinance không hỗ trợ mplkwargs trong một số phiên bản
                # Loại bỏ mplkwargs và để mặc định, sau đó chỉnh lại bằng matplotlib
                rsi_plot = [
                    mpf.make_addplot(
                        rsi_data,
                        panel=1,
                        type='line',
                        color='#6366f1',  # Indigo color
                        ylabel='RSI',
                        secondary_y=False,
                    ),
                    # Đường ngưỡng RSI 30 (oversold - xanh lá)
                    mpf.make_addplot(
                        pd.Series([30] * len(rsi_data), index=rsi_data.index),
                        panel=1,
                        color='#10b981',
                        linestyle='--',
                        alpha=0.7,
                    ),
                    # Đường ngưỡng RSI 50 (neutral - vàng)
                    mpf.make_addplot(
                        pd.Series([50] * len(rsi_data), index=rsi_data.index),
                        panel=1,
                        color='#f59e0b',
                        linestyle='--',
                        alpha=0.7,
                    ),
                    # Đường ngưỡng RSI 70 (overbought - đỏ)
                    mpf.make_addplot(
                        pd.Series([70] * len(rsi_data), index=rsi_data.index),
                        panel=1,
                        color='#ef4444',
                        linestyle='--',
                        alpha=0.7,
                    ),
                ]
        
        # Thêm markers vào plot
        if entry_markers:
            # Tạo DataFrame cho markers
            entry_df = pd.DataFrame(index=plot_data.index)
            entry_df['entry_price'] = np.nan
            entry_df['entry_color'] = ''
            entry_df['entry_size'] = 0
            
            for ts, price, color, size in entry_markers:
                if ts in entry_df.index:
                    entry_df.loc[ts, 'entry_price'] = price
                    entry_df.loc[ts, 'entry_color'] = color
                    entry_df.loc[ts, 'entry_size'] = size
            
            # Vẽ entry markers bằng scatter (sẽ thêm sau)
            # Note: mplfinance không hỗ trợ scatter trực tiếp, cần dùng matplotlib
            
        # Tạo custom style đẹp hơn
        # Lưu ý: Một số phiên bản mplfinance không hỗ trợ cú pháp make_marketcolors với 'up'/'down'
        # Dùng style có sẵn hoặc mặc định để tránh lỗi tương thích
        style = None
        try:
            # Thử tạo marketcolors với cú pháp chuẩn
            mc = mpf.make_marketcolors(
                up='#10b981',      # Xanh lá cho nến tăng
                down='#ef4444',    # Đỏ cho nến giảm
                edge='inherit',    # Viền cùng màu
                wick={'upcolor': '#10b981', 'downcolor': '#ef4444'},
                volume='in',
                ohlc='i'
            )
            # Tạo style với marketcolors tùy chỉnh
            style = mpf.make_mpf_style(
                marketcolors=mc,
                gridstyle='-',
                gridcolor='#e5e7eb',
                gridwidth=0.5,
                y_on_right=False,
                facecolor='#ffffff',
                edgecolor='#d1d5db',
                figcolor='#ffffff',
                rc={
                    'axes.labelcolor': '#374151',
                    'axes.edgecolor': '#d1d5db',
                    'axes.linewidth': 1.0,
                    'xtick.color': '#6b7280',
                    'ytick.color': '#6b7280',
                    'text.color': '#111827',
                    'font.size': 10,
                    'font.family': 'sans-serif',
                    'axes.titlesize': 14,
                    'axes.labelsize': 11,
                    'xtick.labelsize': 9,
                    'ytick.labelsize': 9,
                    'legend.fontsize': 10,
                    'figure.titlesize': 16,
                }
            )
        except (KeyError, TypeError, ValueError, Exception) as e:
            # Nếu lỗi, dùng style có sẵn (yahoo, binance, hoặc default)
            print(f"⚠️ Không thể tạo custom marketcolors (lỗi: {e}), dùng style 'yahoo'")
            # Dùng style có sẵn 'yahoo' (đẹp và tương thích tốt)
            # Nếu 'yahoo' không có, mplfinance sẽ tự động dùng mặc định
            style = 'yahoo'
        
        # Vẽ biểu đồ với error handling tốt hơn
        try:
            fig, axes = mpf.plot(
                plot_data,
                type='candle',
                style=style,
                addplot=rsi_plot if rsi_plot else None,
                volume=True if 'Volume' in plot_data.columns and plot_data['Volume'].sum() > 0 else False,
                title=title,
                ylabel='Price (USD)',
                ylabel_lower='RSI' if rsi_plot else None,
                returnfig=True,
                figsize=(18, 11),
                show_nontrading=False,
                tight_layout=True,
            )
        except KeyError as e:
            # Lỗi KeyError thường do cấu trúc dữ liệu không đúng
            error_key = str(e).strip("'\"")
            raise ValueError(
                f"Lỗi cấu trúc dữ liệu: Không tìm thấy key '{error_key}'. "
                f"Cần có các cột: open, high, low, close, volume (optional), rsi (optional). "
                f"Các cột hiện có: {list(plot_data.columns)}"
            ) from e
        except Exception as e:
            # Lỗi khác - hiển thị thông báo rõ ràng hơn
            raise RuntimeError(
                f"Không thể vẽ biểu đồ: {str(e)}\n"
                f"Kiểm tra:\n"
                f"  - Dữ liệu có đủ cột: open, high, low, close?\n"
                f"  - Index có phải là DatetimeIndex?\n"
                f"  - Dữ liệu có giá trị hợp lệ (không phải NaN)?"
            ) from e
        
        # Vẽ entry/exit markers bằng matplotlib trực tiếp
        # Kiểm tra axes có phải là list/tuple không
        if not isinstance(axes, (list, tuple)) or len(axes) == 0:
            raise ValueError(f"Axes không hợp lệ: {type(axes)}. Cần là list/tuple với ít nhất 1 phần tử.")
        
        ax_price = axes[0]  # Axes cho giá
        
        # Xác định RSI axis: nếu có volume thì RSI ở axes[2], nếu không thì ở axes[1]
        has_volume = 'Volume' in plot_data.columns and plot_data['Volume'].sum() > 0
        if rsi_plot:
            ax_rsi = axes[2] if has_volume and len(axes) > 2 else (axes[1] if len(axes) > 1 else None)
        else:
            ax_rsi = None
        
        # Chỉnh linewidth cho các đường RSI sau khi plot (vì mplfinance không hỗ trợ mplkwargs)
        if ax_rsi is not None and rsi_plot:
            try:
                lines = ax_rsi.get_lines()
                if len(lines) >= 4:
                    # Đường RSI chính (đầu tiên) - linewidth 2
                    lines[0].set_linewidth(2)
                    # Các đường ngưỡng (3 đường tiếp theo) - linewidth 1.5
                    for i in range(1, min(4, len(lines))):
                        lines[i].set_linewidth(1.5)
            except Exception as e:
                # Nếu không chỉnh được linewidth, không sao - chỉ là styling
                print(f"⚠️ Không thể chỉnh linewidth cho RSI: {e}")
        
        # Vẽ entry markers với styling đẹp hơn và text labels
        buy_marker_drawn = False
        sell_marker_drawn = False
        entry_info_dict = {}  # Lưu thông tin entry để hiển thị text
        
        # Thu thập thông tin entry từ events
        for event in self.events:
            if event['type'] == 'entry':
                timestamp = event['timestamp']
                # Chuyển đổi timestamp nếu cần
                if self.index_mapping is not None:
                    if timestamp in self.index_mapping:
                        timestamp = self.index_mapping[timestamp]
                    else:
                        continue
                else:
                    if isinstance(plot_data.index, pd.DatetimeIndex):
                        if not isinstance(timestamp, pd.Timestamp):
                            try:
                                timestamp = pd.to_datetime(timestamp)
                            except (ValueError, TypeError):
                                continue
                
                if timestamp in plot_data.index:
                    entry_info_dict[timestamp] = {
                        'entry_number': event.get('entry_number', 0),
                        'direction': event.get('direction', 'BUY'),
                        'should_trade': event.get('should_trade', False)
                    }
        
        for ts, price, color, size in entry_markers:
            if ts in plot_data.index:
                marker_color = '#10b981' if color == 'green' else '#ef4444'
                marker_style = '^' if color == 'green' else 'v'
                label = ''
                if color == 'green' and not buy_marker_drawn:
                    label = 'Entry BUY'
                    buy_marker_drawn = True
                elif color == 'red' and not sell_marker_drawn:
                    label = 'Entry SELL'
                    sell_marker_drawn = True
                
                # Vẽ marker
                ax_price.scatter(
                    ts,
                    price,
                    c=marker_color,
                    s=size * 2.0,  # Tăng kích thước để dễ nhìn hơn
                    marker=marker_style,
                    edgecolors='#ffffff',
                    linewidths=2.5,
                    zorder=10,
                    alpha=0.95,
                    label=label if label else ''
                )
                
                # Thêm text label với entry number nếu có
                if ts in entry_info_dict:
                    entry_info = entry_info_dict[ts]
                    entry_num = entry_info['entry_number']
                    should_trade = entry_info.get('should_trade', False)
                    # Chỉ hiển thị text cho các entry quan trọng (entry số <= 20 hoặc should_trade=True)
                    if entry_num <= 20 or should_trade:
                        text_label = f"E{entry_num}"
                        if should_trade:
                            text_label += "💰"
                        # Đặt text phía trên marker cho BUY, phía dưới cho SELL
                        y_offset = (plot_data['High'].max() - plot_data['Low'].min()) * 0.02 if color == 'green' else -(plot_data['High'].max() - plot_data['Low'].min()) * 0.02
                        ax_price.annotate(
                            text_label,
                            xy=(ts, price),
                            xytext=(0, y_offset),
                            textcoords='offset points',
                            fontsize=8,
                            fontweight='bold',
                            color=marker_color,
                            ha='center',
                            va='bottom' if color == 'green' else 'top',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=marker_color, alpha=0.8, linewidth=1),
                            zorder=11
                        )
        
        # Vẽ exit markers với styling đẹp hơn và text labels
        exit_count = 0
        exit_info_dict = {}  # Lưu thông tin exit
        
        # Thu thập thông tin exit từ events
        for event in self.events:
            if event['type'] == 'exit':
                timestamp = event['timestamp']
                # Chuyển đổi timestamp nếu cần
                if self.index_mapping is not None:
                    if timestamp in self.index_mapping:
                        timestamp = self.index_mapping[timestamp]
                    else:
                        continue
                else:
                    if isinstance(plot_data.index, pd.DatetimeIndex):
                        if not isinstance(timestamp, pd.Timestamp):
                            try:
                                timestamp = pd.to_datetime(timestamp)
                            except (ValueError, TypeError):
                                continue
                
                if timestamp in plot_data.index:
                    exit_info_dict[timestamp] = {
                        'entry_count': event.get('entry_count', 0),
                        'was_break': event.get('was_break', False)
                    }
        
        for ts, price in exit_dict.items():
            if ts in plot_data.index:
                ax_price.scatter(
                    ts,
                    price,
                    c='#f59e0b',
                    s=250,  # Tăng kích thước
                    marker='X',
                    edgecolors='#ffffff',
                    linewidths=2.5,
                    zorder=10,
                    alpha=0.95,
                    label='Exit' if exit_count == 0 else ''
                )
                
                # Thêm text label
                if ts in exit_info_dict:
                    exit_info = exit_info_dict[ts]
                    entry_count = exit_info.get('entry_count', 0)
                    text_label = f"Exit (E{entry_count})"
                    y_offset = (plot_data['High'].max() - plot_data['Low'].min()) * 0.03
                    ax_price.annotate(
                        text_label,
                        xy=(ts, price),
                        xytext=(0, y_offset),
                        textcoords='offset points',
                        fontsize=8,
                        fontweight='bold',
                        color='#f59e0b',
                        ha='center',
                        va='bottom',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#f59e0b', alpha=0.8, linewidth=1),
                        zorder=11
                    )
                
                exit_count += 1
        
        # Vẽ break markers (stop loss) với styling đẹp hơn và text labels
        break_count = 0
        break_info_dict = {}  # Lưu thông tin break
        
        # Thu thập thông tin break từ events
        for event in self.events:
            if event['type'] == 'break':
                timestamp = event['timestamp']
                # Chuyển đổi timestamp nếu cần
                if self.index_mapping is not None:
                    if timestamp in self.index_mapping:
                        timestamp = self.index_mapping[timestamp]
                    else:
                        continue
                else:
                    if isinstance(plot_data.index, pd.DatetimeIndex):
                        if not isinstance(timestamp, pd.Timestamp):
                            try:
                                timestamp = pd.to_datetime(timestamp)
                            except (ValueError, TypeError):
                                continue
                
                if timestamp in plot_data.index:
                    break_info_dict[timestamp] = {
                        'entry_count': event.get('entry_count', 0),
                        'direction': event.get('direction', 'BUY')
                    }
        
        for ts, info in break_dict.items():
            if ts in plot_data.index:
                ax_price.scatter(
                    ts,
                    info['price'],
                    c='#9333ea',  # Purple color for break/stop loss
                    s=280,  # Tăng kích thước
                    marker='*',  # Star marker for break
                    edgecolors='#ffffff',
                    linewidths=2.5,
                    zorder=10,
                    alpha=0.95,
                    label='Break/Stop Loss' if break_count == 0 else ''
                )
                
                # Thêm text label
                if ts in break_info_dict:
                    break_info = break_info_dict[ts]
                    entry_count = break_info.get('entry_count', 0)
                    text_label = f"Break (E{entry_count})"
                    y_offset = -(plot_data['High'].max() - plot_data['Low'].min()) * 0.03
                    ax_price.annotate(
                        text_label,
                        xy=(ts, info['price']),
                        xytext=(0, y_offset),
                        textcoords='offset points',
                        fontsize=8,
                        fontweight='bold',
                        color='#9333ea',
                        ha='center',
                        va='top',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#9333ea', alpha=0.8, linewidth=1),
                        zorder=11
                    )
                
                break_count += 1
        
        # Cải thiện legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='^', color='w', markerfacecolor='#10b981', 
                   markersize=12, label='Entry BUY', markeredgecolor='#ffffff', markeredgewidth=1.5),
            Line2D([0], [0], marker='v', color='w', markerfacecolor='#ef4444', 
                   markersize=12, label='Entry SELL', markeredgecolor='#ffffff', markeredgewidth=1.5),
            Line2D([0], [0], marker='X', color='w', markerfacecolor='#f59e0b', 
                   markersize=12, label='Exit', markeredgecolor='#ffffff', markeredgewidth=1.5),
            Line2D([0], [0], marker='*', color='w', markerfacecolor='#9333ea', 
                   markersize=12, label='Break/Stop Loss', markeredgecolor='#ffffff', markeredgewidth=1.5),
        ]
        ax_price.legend(
            handles=legend_elements, 
            loc='upper left',
            frameon=True,
            fancybox=True,
            shadow=True,
            framealpha=0.95,
            edgecolor='#d1d5db',
            facecolor='#ffffff',
            fontsize=10
        )
        
        # Cải thiện RSI axis nếu có
        if ax_rsi is not None:
            ax_rsi.set_ylim(0, 100)  # Đảm bảo RSI luôn hiển thị 0-100
            ax_rsi.set_yticks([0, 30, 50, 70, 100])
            ax_rsi.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
            ax_rsi.axhspan(70, 100, alpha=0.1, color='#ef4444', label='Overbought')
            ax_rsi.axhspan(0, 30, alpha=0.1, color='#10b981', label='Oversold')
            ax_rsi.set_facecolor('#f9fafb')
        
        # Cải thiện price axis
        ax_price.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax_price.set_facecolor('#ffffff')
        
        # Format x-axis dates và cải thiện volume axis nếu có
        if has_volume and len(axes) > 1:
            ax_volume = axes[1]
            if ax_volume is not None:
                ax_volume.set_facecolor('#f9fafb')
                ax_volume.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)
        
        # Format date labels
        for ax in axes:
            if hasattr(ax, 'xaxis'):
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d, %H:%M'))
                ax.xaxis.set_major_locator(mdates.AutoDateLocator())
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Cải thiện title
        fig.suptitle(title, fontsize=16, fontweight='bold', color='#111827', y=0.995)
        fig.patch.set_facecolor('#ffffff')
        
        # Adjust layout để tránh overlap
        plt.tight_layout(rect=[0, 0, 1, 0.98])
        
        # Lưu file nếu có (luôn lưu trước khi show để đảm bảo có file)
        if save_path:
            try:
                save_path = Path(save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                fig.savefig(save_path, dpi=150, bbox_inches='tight')
                print(f"✅ Đã lưu biểu đồ: {save_path}")
            except Exception as e:
                print(f"⚠️ Không thể lưu biểu đồ: {e}")
                # Vẫn tiếp tục để hiển thị biểu đồ
        
        # Hiển thị biểu đồ tương tác (có thể zoom/pan)
        if show:
            try:
                # Đảm bảo toolbar được bật để có các công cụ zoom/pan
                # Matplotlib tự động có toolbar với các công cụ:
                # - Zoom: Click và kéo để zoom vào vùng được chọn
                # - Pan: Click và kéo để di chuyển biểu đồ
                # - Home: Reset về view ban đầu
                # - Back/Forward: Quay lại/tiến tới view trước đó
                
                # Kiểm tra xem có đang chạy trong thread không
                import threading
                is_main_thread = threading.current_thread() is threading.main_thread()
                
                if is_main_thread:
                    # Nếu là main thread, hiển thị biểu đồ tương tác
                    # block=False để không block GUI, nhưng vẫn giữ cửa sổ mở
                    plt.show(block=False)
                    # Pause ngắn để đảm bảo cửa sổ được render
                    plt.pause(0.1)
                    print("✅ Biểu đồ tương tác đã được mở. Bạn có thể:")
                    print("   - Zoom: Click và kéo để chọn vùng cần zoom")
                    print("   - Pan: Click và kéo để di chuyển biểu đồ")
                    print("   - Reset: Nhấn nút Home trên toolbar")
                else:
                    # Nếu là thread khác, vẫn cố gắng hiển thị
                    # (có thể hoạt động với một số backend)
                    if save_path:
                        print(f"✅ Biểu đồ đã được lưu tại: {save_path}")
                    try:
                        # Thử hiển thị trong cửa sổ riêng (có thể hoạt động với Qt backend)
                        plt.show(block=False)
                        plt.pause(0.1)
                        print("✅ Biểu đồ tương tác đã được mở. Bạn có thể zoom/pan.")
                    except Exception as e:
                        # Nếu không show được từ thread, ít nhất đã lưu file
                        print(f"⚠️ Không thể hiển thị biểu đồ tương tác từ thread: {e}")
                        if save_path:
                            print(f"   Biểu đồ đã được lưu tại: {save_path}")
                            print("   Vui lòng mở file để xem.")
            except Exception as e:
                print(f"⚠️ Không thể hiển thị biểu đồ: {e}")
                # Nếu không show được, vẫn giữ figure mở nếu đã lưu file
                if save_path:
                    print(f"   Biểu đồ đã được lưu tại: {save_path}")
        else:
            # Nếu show=False, vẫn giữ figure mở nếu có save_path (để có thể show sau)
            if save_path:
                # Không đóng figure, để có thể show sau nếu cần
                pass
            else:
                plt.close(fig)
        
        return fig, axes


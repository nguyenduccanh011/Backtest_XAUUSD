// API Base URL
const API_BASE = '/api';

// State
let lotData = [];
let selectedDataFile = null;
let lastBacktestResult = null;

// DOM Elements
const directionRadios = document.querySelectorAll('input[name="direction"]');
const rsiModeRadios = document.querySelectorAll('input[name="rsi-mode"]');
const rsiEntryInput = document.getElementById('rsi-entry');
const rsiExitInput = document.getElementById('rsi-exit');
const rsiBreakInput = document.getElementById('rsi-break');
const rsiEntryLabel = document.getElementById('rsi-entry-label');
const rsiInfoText = document.getElementById('rsi-info');
const rsiThresholdsDiv = document.getElementById('rsi-thresholds');
const moneyInputTbody = document.getElementById('money-input-tbody');
const moneyTbody = document.getElementById('money-tbody');
const lotTbody = document.getElementById('lot-tbody');
const btnApply = document.getElementById('btn-apply');
const btnSave = document.getElementById('btn-save');
const btnLoad = document.getElementById('btn-load');
const btnUpdate = document.getElementById('btn-update');
const btnSelectFile = document.getElementById('btn-select-file');
const btnRun = document.getElementById('btn-run');
const fileLabel = document.getElementById('file-label');
const statusLabel = document.getElementById('status-label');
const resultText = document.getElementById('result-text');

// Event Listeners
directionRadios.forEach(radio => {
    radio.addEventListener('change', onDirectionChange);
});

rsiModeRadios.forEach(radio => {
    radio.addEventListener('change', onRsiModeChange);
});

btnApply.addEventListener('click', onApplyManualInput);
btnSave.addEventListener('click', onSaveLotData);
btnLoad.addEventListener('click', onLoadLotData);
btnUpdate.addEventListener('click', onUpdateLotData);
btnSelectFile.addEventListener('click', onSelectDataFile);
btnRun.addEventListener('click', onRunBacktest);

// Initialize
onRsiModeChange();
onDirectionChange();
initMoneyInputTable();

function onDirectionChange() {
    const direction = document.querySelector('input[name="direction"]:checked').value;
    
    if (direction === 'BUY') {
        rsiEntryLabel.textContent = 'RSI vào lệnh (BUY):';
        rsiInfoText.textContent = 'MUA: vào khi RSI ≤ mốc 1, chốt khi RSI ≈ mốc 2, dừng đếm khi RSI < mốc 3';
        rsiEntryInput.value = '35';
        rsiExitInput.value = '50';
        rsiBreakInput.value = '40';
    } else {
        rsiEntryLabel.textContent = 'RSI vào lệnh (SELL):';
        rsiInfoText.textContent = 'BÁN: vào khi RSI ≥ mốc 1, chốt khi RSI ≈ mốc 2, dừng đếm khi RSI > mốc 3';
        rsiEntryInput.value = '70';
        rsiExitInput.value = '50';
        rsiBreakInput.value = '60';
    }
}

function onRsiModeChange() {
    const mode = document.querySelector('input[name="rsi-mode"]:checked').value;
    const isAuto = mode === 'auto';
    
    rsiEntryInput.disabled = isAuto;
    rsiExitInput.disabled = isAuto;
    rsiBreakInput.disabled = isAuto;
    
    if (isAuto) {
        rsiInfoText.textContent = 'Tự động tối ưu: BUY 30-35, SELL 65-70. 3 mốc bên trên sẽ được cập nhật sau khi tối ưu.';
    } else {
        onDirectionChange();
    }
}

function initMoneyInputTable() {
    // Không tạo sẵn dòng, chỉ tạo khi người dùng nhập
    // Tạo 1 dòng trống để người dùng có thể bắt đầu nhập
    addNewInputRow();
    
    // Thêm event listener cho paste event trên bảng
    moneyInputTbody.addEventListener('paste', handlePasteEvent);
}

function addNewInputRow() {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td class="stt-cell"></td>
        <td class="amount-cell">
            <input type="number" class="money-amount-input" step="0.01" min="0" placeholder="">
        </td>
    `;
    moneyInputTbody.appendChild(row);
    
    const input = row.querySelector('.money-amount-input');
    input.addEventListener('input', handleMoneyInput);
    input.addEventListener('blur', handleMoneyInput);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            // Tạo dòng mới nếu đang ở dòng cuối
            const rows = moneyInputTbody.querySelectorAll('tr');
            if (row === rows[rows.length - 1]) {
                addNewInputRow();
                const nextInput = moneyInputTbody.querySelectorAll('.money-amount-input')[rows.length];
                if (nextInput) nextInput.focus();
            }
        }
    });
    
    return input;
}

function handleMoneyInput(e) {
    const input = e.target;
    const valueStr = input.value.trim();
    const row = input.closest('tr');
    
    // Cập nhật STT lệnh cho tất cả các dòng
    updateSTTCount();
    
    // Nếu người dùng nhập số (kể cả 0) và đang ở dòng cuối, tạo dòng mới
    if (valueStr !== '' && !isNaN(parseFloat(valueStr))) {
        const rows = moneyInputTbody.querySelectorAll('tr');
        if (row === rows[rows.length - 1]) {
            addNewInputRow();
        }
    }
}

function handlePasteEvent(e) {
    e.preventDefault();
    
    // Lấy dữ liệu từ clipboard
    const pastedData = (e.clipboardData || window.clipboardData).getData('text');
    
    if (!pastedData) return;
    
    // Parse dữ liệu: Excel thường paste với tab hoặc newline
    const lines = pastedData.split(/\r?\n/).filter(line => line.trim() !== '');
    const values = [];
    
    lines.forEach(line => {
        // Xử lý nếu có tab (paste từ Excel cột)
        const parts = line.split(/\t/);
        parts.forEach(part => {
            const trimmed = part.trim();
            if (trimmed !== '') {
                // Thử parse số
                const num = parseFloat(trimmed.replace(/[,\s]/g, ''));
                if (!isNaN(num)) {
                    values.push(num);
                }
            }
        });
    });
    
    if (values.length === 0) return;
    
    // Tìm input đang focus hoặc input đầu tiên
    const activeInput = document.activeElement;
    let startRow = null;
    let startIndex = 0;
    
    if (activeInput && activeInput.classList.contains('money-amount-input')) {
        startRow = activeInput.closest('tr');
        const allRows = Array.from(moneyInputTbody.querySelectorAll('tr'));
        startIndex = allRows.indexOf(startRow);
    }
    
    // Nếu không có row được chọn, bắt đầu từ row đầu tiên
    if (startIndex === -1) {
        startIndex = 0;
        const allRows = moneyInputTbody.querySelectorAll('tr');
        if (allRows.length > 0) {
            startRow = allRows[0];
        }
    }
    
    // Đảm bảo có đủ dòng
    const allRows = Array.from(moneyInputTbody.querySelectorAll('tr'));
    while (allRows.length < startIndex + values.length) {
        addNewInputRow();
        const newRows = moneyInputTbody.querySelectorAll('tr');
        allRows.push(newRows[newRows.length - 1]);
    }
    
    // Paste giá trị vào các dòng
    values.forEach((value, idx) => {
        const rowIndex = startIndex + idx;
        const row = allRows[rowIndex] || moneyInputTbody.querySelectorAll('tr')[rowIndex];
        if (row) {
            const input = row.querySelector('.money-amount-input');
            if (input) {
                input.value = value;
                // Trigger input event để cập nhật STT
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    });
    
    // Cập nhật STT sau khi paste
    updateSTTCount();
    
    // Focus vào input cuối cùng được paste
    const lastIndex = startIndex + values.length - 1;
    const lastRow = allRows[lastIndex] || moneyInputTbody.querySelectorAll('tr')[lastIndex];
    if (lastRow) {
        const lastInput = lastRow.querySelector('.money-amount-input');
        if (lastInput) {
            setTimeout(() => lastInput.focus(), 10);
        }
    }
}

function updateSTTCount() {
    const rows = moneyInputTbody.querySelectorAll('tr');
    let sttCount = 0;
    
    rows.forEach((row) => {
        const input = row.querySelector('.money-amount-input');
        const sttCell = row.querySelector('.stt-cell');
        const value = input.value.trim();
        
        // Nếu có giá trị (kể cả 0), đếm STT
        if (value !== '' && !isNaN(parseFloat(value))) {
            sttCount++;
            sttCell.textContent = sttCount;
        } else {
            sttCell.textContent = '';
        }
    });
}

function getMoneyValuesFromTable() {
    const values = [];
    const rows = moneyInputTbody.querySelectorAll('tr');
    
    rows.forEach(row => {
        const input = row.querySelector('.money-amount-input');
        const value = parseFloat(input.value) || 0;
        if (value > 0) {
            values.push(value);
        }
    });
    
    return values;
}

async function onApplyManualInput() {
    const moneyValues = getMoneyValuesFromTable();
    
    if (moneyValues.length === 0) {
        showStatus('⚠️ Vui lòng nhập số tiền vào lệnh trước khi bấm \'Áp dụng\'.', 'error');
        return;
    }
    
    try {
        // Call API to calculate lot sizes
        const response = await fetch(`${API_BASE}/calculate-lot`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                money_values: moneyValues,
                data_file_path: selectedDataFile,
            }),
        });
        
        if (!response.ok) {
            throw new Error('Failed to calculate lot sizes');
        }
        
        const data = await response.json();
        lotData = data.lot_data;
        
        // Update tables
        updateTables(lotData);
        
        const tradeEntries = lotData.filter(item => 
            item.entry_number >= 10 && item.entry_number <= 40 && item.lot_size > 0
        );
        const countOnlyEntries = lotData.length - tradeEntries.length;
        
        showStatus(
            `✅ Đã áp dụng ${lotData.length} entry | ${countOnlyEntries} entry chỉ đếm, ${tradeEntries.length} entry vào lệnh | Hãy chọn file data.`,
            'success'
        );
    } catch (error) {
        showStatus(`❌ Lỗi: ${error.message}`, 'error');
        console.error(error);
    }
}

// parseMoneyInput function removed - now using getMoneyValuesFromTable()

function updateTables(lotData) {
    moneyTbody.innerHTML = '';
    lotTbody.innerHTML = '';
    
    if (lotData.length === 0) {
        moneyTbody.innerHTML = '<tr><td colspan="2">Nhập số tiền và nhấn \'Áp dụng\'</td></tr>';
        lotTbody.innerHTML = '<tr><td colspan="2">Nhập số tiền và nhấn \'Áp dụng\'</td></tr>';
        return;
    }
    
    lotData.forEach(item => {
        const moneyRow = document.createElement('tr');
        moneyRow.innerHTML = `
            <td>Entry ${item.entry_number}</td>
            <td>$${item.money_amount.toLocaleString('en-US', {maximumFractionDigits: 0})}</td>
        `;
        moneyTbody.appendChild(moneyRow);
        
        const lotRow = document.createElement('tr');
        lotRow.innerHTML = `
            <td>Entry ${item.entry_number}</td>
            <td>${item.lot_size.toFixed(5)}</td>
        `;
        lotTbody.appendChild(lotRow);
    });
}

function onSelectDataFile() {
    // Create file input
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv';
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`${API_BASE}/upload-data`, {
                method: 'POST',
                body: formData,
            });
            
            if (!response.ok) {
                throw new Error('Failed to upload file');
            }
            
            const data = await response.json();
            selectedDataFile = data.path;
            fileLabel.textContent = `📂 ${file.name}`;
            showStatus(`✅ Đã chọn file: ${file.name} (bấm 'Chạy backtest' để bắt đầu)`, 'success');
        } catch (error) {
            showStatus(`❌ Lỗi upload file: ${error.message}`, 'error');
            console.error(error);
        }
    };
    input.click();
}

async function onRunBacktest() {
    if (lotData.length === 0) {
        alert('Vui lòng nhập số tiền và nhấn \'Áp dụng\' trước.');
        return;
    }
    
    if (!selectedDataFile) {
        if (!confirm('Chưa chọn file data. Bạn có muốn tiếp tục với file mặc định từ config?')) {
            return;
        }
    }
    
    btnRun.disabled = true;
    showStatus('⏳ Đang chạy backtest...', 'info');
    resultText.textContent = 'Đang chạy backtest...\nVui lòng đợi...';
    
    const direction = document.querySelector('input[name="direction"]:checked').value;
    const isAuto = document.querySelector('input[name="rsi-mode"]:checked').value === 'auto';
    
    const request = {
        buy_threshold: parseFloat(rsiEntryInput.value) || 35,
        sell_threshold: parseFloat(rsiEntryInput.value) || 70,
        lot_data: lotData,
        data_file_path: selectedDataFile,
        direction_mode: direction,
        auto_optimize: isAuto,
    };
    
    if (!isAuto) {
        request.entry_rsi = parseFloat(rsiEntryInput.value);
        request.exit_rsi = parseFloat(rsiExitInput.value);
        request.break_rsi = parseFloat(rsiBreakInput.value);
    }
    
    try {
        const response = await fetch(`${API_BASE}/backtest`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Backtest failed');
        }
        
        const data = await response.json();
        lastBacktestResult = data;
        
        displayResults(data);
        
        // Vẽ markers trên TradingView chart
        if (data.events && data.events.length > 0) {
            drawBacktestMarkers(data.events);
        }
        
        showStatus('✅ Backtest hoàn thành!', 'success');
    } catch (error) {
        showStatus(`❌ Lỗi: ${error.message}`, 'error');
        resultText.textContent = `❌ Lỗi: ${error.message}`;
    } finally {
        btnRun.disabled = false;
    }
}

function displayResults(data) {
    const summary = data.summary;
    const isOptimized = data.optimized;
    
    let result = '';
    
    if (isOptimized) {
        result += `🏆 TỐI ƯU HOÀN THÀNH!\n\n`;
        result += `📊 NGƯỠNG RSI TỐT NHẤT:\n`;
        result += `   🟢 BUY: RSI <= ${data.best_buy_threshold}\n`;
        result += `   🔴 SELL: RSI >= ${data.best_sell_threshold}\n\n`;
    } else {
        result += `✅ Backtest hoàn thành!\n\n`;
    }
    
    result += `📈 KẾT QUẢ TỔNG QUAN:\n`;
    result += `   Total Entries: ${summary.total_entries}\n`;
    result += `   Total Trades: ${summary.total_trades}\n`;
    result += `   Total P&L: $${summary.total_pnl.toLocaleString('en-US', {maximumFractionDigits: 2})}\n`;
    result += `   Total Return: ${summary.total_return}\n`;
    result += `   Initial Capital: $${summary.initial_capital.toLocaleString('en-US', {maximumFractionDigits: 2})}\n`;
    result += `   Final Equity: $${summary.final_equity.toLocaleString('en-US', {maximumFractionDigits: 2})}\n\n`;
    
    result += `📊 PHÂN TÍCH LỆNH MUA/BÁN:\n`;
    result += `   🟢 LỆNH MUA (BUY):\n`;
    result += `      - Số entry: ${summary.buy_entries || 0}\n`;
    result += `      - Số lệnh thực tế: ${summary.buy_trades || 0}\n`;
    result += `   🔴 LỆNH BÁN (SELL):\n`;
    result += `      - Số entry: ${summary.sell_entries || 0}\n`;
    result += `      - Số lệnh thực tế: ${summary.sell_trades || 0}\n`;
    
    resultText.textContent = result;
}


function onSaveLotData() {
    if (lotData.length === 0) {
        alert('Chưa có dữ liệu để lưu. Vui lòng nhập số tiền và nhấn \'Áp dụng\' trước.');
        return;
    }
    
    const dataStr = JSON.stringify({
        money_amounts: lotData.map(item => item.money_amount),
        entry_numbers: lotData.map(item => item.entry_number),
    }, null, 2);
    
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'lot_data.json';
    a.click();
    URL.revokeObjectURL(url);
    
    showStatus('✅ Đã lưu dữ liệu', 'success');
}

function onLoadLotData() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const data = JSON.parse(event.target.result);
                const moneyAmounts = data.money_amounts || [];
                
                // Clear all existing rows
                moneyInputTbody.innerHTML = '';
                
                // Create rows for each amount
                moneyAmounts.forEach((amount) => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td class="stt-cell"></td>
                        <td class="amount-cell">
                            <input type="number" class="money-amount-input" step="0.01" min="0" value="${amount}">
                        </td>
                    `;
                    moneyInputTbody.appendChild(row);
                    
                    const inputField = row.querySelector('.money-amount-input');
                    inputField.addEventListener('input', handleMoneyInput);
                    inputField.addEventListener('blur', handleMoneyInput);
                    inputField.addEventListener('keydown', (e) => {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            const rows = moneyInputTbody.querySelectorAll('tr');
                            if (row === rows[rows.length - 1]) {
                                addNewInputRow();
                                const nextInput = moneyInputTbody.querySelectorAll('.money-amount-input')[rows.length];
                                if (nextInput) nextInput.focus();
                            }
                        }
                    });
                });
                
                // Add one empty row at the end
                addNewInputRow();
                
                updateSTTCount();
                onApplyManualInput();
                
                showStatus(`✅ Đã tải ${moneyAmounts.length} entry`, 'success');
            } catch (error) {
                showStatus(`❌ Lỗi đọc file: ${error.message}`, 'error');
            }
        };
        reader.readAsText(file);
    };
    input.click();
}

function onUpdateLotData() {
    onSaveLotData();
}

function showStatus(message, type = 'info') {
    statusLabel.textContent = message;
    statusLabel.className = 'status-label';
    
    if (type === 'success') {
        statusLabel.style.color = '#28a745';
    } else if (type === 'error') {
        statusLabel.style.color = '#dc3545';
    } else {
        statusLabel.style.color = '#17a2b8';
    }
}

// TradingView Chart Initialization
let tvWidget = null;

function initTradingViewChart() {
    if (typeof TradingView === 'undefined' || typeof BacktestDatafeed === 'undefined') {
        console.warn('TradingView library not loaded yet, retrying...');
        setTimeout(initTradingViewChart, 500);
        return;
    }

    // Hide loading indicator
    const loadingEl = document.getElementById('tv_loading');
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }

    if (tvWidget) {
        tvWidget.remove();
        tvWidget = null;
    }

    const datafeed = new BacktestDatafeed('/api/tv');

    tvWidget = new TradingView.widget({
        debug: false,
        fullscreen: false,
        symbol: 'XAUUSD',
        interval: '1H',
        container: 'tv_chart_container',
        datafeed: datafeed,
        library_path: '/charting_library/',
        locale: 'vi',
        disabled_features: [
            'use_localstorage_for_settings',
            'volume_force_overlay',
        ],
        enabled_features: [
            'study_templates',
        ],
        charts_storage_url: 'https://saveload.tradingview.com',
        charts_storage_api_version: '1.1',
        client_id: 'backtest_xauusd',
        user_id: 'public_user_id',
        theme: 'light',
        toolbar_bg: '#f1f3f6',
        overrides: {
            'paneProperties.background': '#ffffff',
            'paneProperties.vertGridProperties.color': '#e0e0e0',
            'paneProperties.horzGridProperties.color': '#e0e0e0',
        },
    });

    console.log('TradingView chart initialized');
}

// Initialize chart with lazy loading - only load when visible or after a delay
let chartInitAttempted = false;

function initChartWhenReady() {
    if (chartInitAttempted) return;
    
    // Check if TradingView library is loaded
    if (typeof TradingView === 'undefined' || typeof BacktestDatafeed === 'undefined') {
        // Retry after a short delay
        setTimeout(initChartWhenReady, 500);
        return;
    }
    
    chartInitAttempted = true;
    initTradingViewChart();
}

// Lazy load chart - only initialize when:
// 1. User scrolls to chart section (Intersection Observer)
// 2. Or after page is fully loaded (fallback)
window.addEventListener('DOMContentLoaded', () => {
    const chartContainer = document.getElementById('tv_chart_container');
    if (!chartContainer) return;
    
    // Use Intersection Observer to load chart only when visible
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !chartInitAttempted) {
                    initChartWhenReady();
                    observer.disconnect();
                }
            });
        }, {
            rootMargin: '100px' // Start loading 100px before chart is visible
        });
        
        observer.observe(chartContainer);
        
        // Fallback: Load after 3 seconds even if not visible
        setTimeout(() => {
            if (!chartInitAttempted) {
                initChartWhenReady();
                observer.disconnect();
            }
        }, 3000);
    } else {
        // Fallback for browsers without IntersectionObserver
        setTimeout(initChartWhenReady, 2000);
    }
});

// Function to draw backtest markers on TradingView chart
function drawBacktestMarkers(events) {
    if (!tvWidget) {
        console.warn('TradingView widget not initialized yet');
        // Retry after a short delay
        setTimeout(() => drawBacktestMarkers(events), 1000);
        return;
    }

    // Wait for chart to be ready
    tvWidget.onChartReady(() => {
        try {
            const chart = tvWidget.activeChart();
            if (!chart) {
                console.warn('Chart not ready');
                return;
            }

            // Clear existing markers (optional - comment out if you want to keep previous markers)
            // chart.removeAllShapes();

            // Draw markers for each event
            events.forEach((event, index) => {
                try {
                    // Convert timestamp to Unix timestamp (seconds)
                    let timestamp;
                    if (typeof event.timestamp === 'string') {
                        // ISO string format
                        timestamp = Math.floor(new Date(event.timestamp).getTime() / 1000);
                    } else if (event.timestamp instanceof Date) {
                        timestamp = Math.floor(event.timestamp.getTime() / 1000);
                    } else if (typeof event.timestamp === 'number') {
                        // Already a timestamp, check if it's in seconds or milliseconds
                        timestamp = event.timestamp > 1e12 ? Math.floor(event.timestamp / 1000) : event.timestamp;
                    } else {
                        console.warn('Invalid timestamp format:', event.timestamp);
                        return;
                    }

                    const price = parseFloat(event.price);
                    if (isNaN(price)) {
                        console.warn('Invalid price:', event.price);
                        return;
                    }

                    let shapeType, color, text, markerSymbol;

                    if (event.type === 'entry') {
                        // Entry marker: use text with emoji/unicode for BUY/SELL
                        shapeType = 'text';
                        if (event.direction === 'BUY') {
                            color = '#10b981'; // Green
                            markerSymbol = '▲'; // Up arrow
                            text = `▲ Entry #${event.entry_number || ''} BUY`;
                        } else if (event.direction === 'SELL') {
                            color = '#ef4444'; // Red
                            markerSymbol = '▼'; // Down arrow
                            text = `▼ Entry #${event.entry_number || ''} SELL`;
                        } else {
                            color = '#6b7280'; // Gray
                            markerSymbol = '●';
                            text = `● Entry #${event.entry_number || ''}`;
                        }
                    } else if (event.type === 'exit') {
                        // Exit marker: X symbol
                        shapeType = 'text';
                        color = '#3b82f6'; // Blue
                        markerSymbol = '✕';
                        text = `✕ Exit #${event.entry_count || ''}`;
                    } else if (event.type === 'break') {
                        // Break marker: warning symbol
                        shapeType = 'text';
                        color = '#f59e0b'; // Orange/Amber
                        markerSymbol = '⚠';
                        text = `⚠ Break #${event.entry_count || ''}`;
                    } else {
                        // Unknown event type
                        return;
                    }

                    // Create text marker with symbol
                    chart.createShape(
                        { time: timestamp, price: price },
                        {
                            shape: 'text',
                            lock: true,
                            disableSelection: true,
                            disableSave: false,
                            overrides: {
                                text: markerSymbol,
                                fontsize: 16,
                                textcolor: color,
                                bold: true,
                            },
                        }
                    ).catch(err => {
                        console.warn(`Failed to create marker for event ${index}:`, err);
                        // Fallback: try with simpler approach
                        console.log(`Event ${index} details:`, { type: event.type, timestamp, price });
                    });

                } catch (error) {
                    console.error(`Error processing event ${index}:`, error);
                }
            });

            console.log(`✅ Đã vẽ ${events.length} markers trên biểu đồ`);
        } catch (error) {
            console.error('Error drawing markers:', error);
        }
    });
}


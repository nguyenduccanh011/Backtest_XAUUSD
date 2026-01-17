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
const moneyInput = document.getElementById('money-input');
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

async function onApplyManualInput() {
    const content = moneyInput.value.trim();
    
    if (!content) {
        showStatus('⚠️ Vui lòng nhập số tiền vào lệnh trước khi bấm \'Áp dụng\'.', 'error');
        return;
    }
    
    // Parse money values
    const moneyValues = parseMoneyInput(content);
    
    if (moneyValues.length === 0) {
        showStatus('⚠️ Không có dữ liệu số tiền để xử lý. Kiểm tra lại nội dung đã paste.', 'error');
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

function parseMoneyInput(content) {
    // Normalize: replace all separators with comma
    let normalized = content.replace(/[\n\r\t;]+/g, ',');
    normalized = normalized.replace(/[,\s]+/g, ',');
    normalized = normalized.trim().replace(/^,|,$/g, '');
    
    if (!normalized) return [];
    
    const values = [];
    const parts = normalized.split(',');
    
    for (const part of parts) {
        const clean = part.trim().replace(/[,\s\t\n\r]/g, '');
        if (!clean) continue;
        
        const num = parseFloat(clean);
        if (!isNaN(num) && num >= 0) {
            values.push(num);
        }
    }
    
    return values;
}

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
        
        // Tự động hiển thị biểu đồ nếu có chart_filename
        if (data.chart_filename) {
            await displayChart(data.chart_filename);
        }
        
        showStatus('✅ Backtest hoàn thành! Biểu đồ đã được vẽ tự động.', 'success');
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

async function displayChart(chartFilename) {
    try {
        const chartUrl = `${API_BASE}/chart/${chartFilename}`;
        
        // Tạo hoặc cập nhật section biểu đồ
        let chartSection = document.getElementById('chart-section');
        if (!chartSection) {
            chartSection = document.createElement('section');
            chartSection.id = 'chart-section';
            chartSection.className = 'card';
            chartSection.innerHTML = `
                <h2>📊 Biểu đồ Backtest</h2>
                <div style="text-align: center; margin: 20px 0;">
                    <img id="chart-image" src="${chartUrl}" alt="Backtest Chart" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px;">
                </div>
            `;
            
            // Chèn vào sau section kết quả
            const resultsSection = document.querySelector('section:has(#result-text)');
            if (resultsSection) {
                resultsSection.insertAdjacentElement('afterend', chartSection);
            } else {
                document.querySelector('.container').appendChild(chartSection);
            }
        } else {
            // Cập nhật ảnh nếu section đã tồn tại
            const chartImage = document.getElementById('chart-image');
            if (chartImage) {
                chartImage.src = chartUrl;
            }
        }
    } catch (error) {
        console.error('Lỗi khi hiển thị biểu đồ:', error);
    }
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
                
                moneyInput.value = moneyAmounts.join('\n');
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

// Initialize chart when page loads
window.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for all scripts to load
    setTimeout(initTradingViewChart, 1000);
});


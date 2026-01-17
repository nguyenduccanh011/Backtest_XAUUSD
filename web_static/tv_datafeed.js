// Custom TradingView Datafeed for Backtest XAUUSD
(function() {
    'use strict';

    const API_BASE = '/api/tv';

    class Requester {
        constructor(headers) {
            this._headers = headers || {};
        }

        sendRequest(datafeedUrl, endpoint, params) {
            return new Promise((resolve, reject) => {
                let url = `${datafeedUrl}/${endpoint}`;
                const paramKeys = Object.keys(params || {});
                
                if (paramKeys.length > 0) {
                    url += '?' + paramKeys.map(key => 
                        `${encodeURIComponent(key)}=${encodeURIComponent(params[key].toString())}`
                    ).join('&');
                }

                const options = {
                    credentials: 'same-origin',
                };

                if (Object.keys(this._headers).length > 0) {
                    options.headers = this._headers;
                }

                fetch(url, options)
                    .then(response => response.text())
                    .then(responseText => {
                        try {
                            const result = JSON.parse(responseText);
                            resolve(result);
                        } catch (parseError) {
                            reject(`Parse error: ${parseError.message}`);
                        }
                    })
                    .catch(error => {
                        const errorMessage = error instanceof Error ? error.message : String(error);
                        reject(`Network error: ${errorMessage}`);
                    });
            });
        }
    }

    class UDFCompatibleDatafeed {
        constructor(datafeedUrl, updateFrequency = 10000) {
            this._datafeedUrl = datafeedUrl;
            this._configuration = null;
            this._symbolsStorage = null;
            this._requester = new Requester();
            this._configurationReadyPromise = this._requestConfiguration();
        }

        onReady(callback) {
            this._configurationReadyPromise.then(() => {
                callback(this._configuration);
            });
        }

        _requestConfiguration() {
            return this._requester.sendRequest(this._datafeedUrl, 'config', {})
                .then(config => {
                    this._configuration = config || {
                        supports_search: false,
                        supports_group_request: true,
                        supported_resolutions: ['1', '5', '15', '30', '60', '240', '1D', '1W', '1M'],
                        supports_marks: false,
                        supports_timescale_marks: false,
                    };
                    return this._configuration;
                })
                .catch(error => {
                    console.error('Configuration request error:', error);
                    this._configuration = {
                        supports_search: false,
                        supports_group_request: true,
                        supported_resolutions: ['1', '5', '15', '30', '60', '240', '1D', '1W', '1M'],
                        supports_marks: false,
                        supports_timescale_marks: false,
                    };
                    return this._configuration;
                });
        }

        resolveSymbol(symbolName, onResolve, onError, extension) {
            const params = { symbol: symbolName };
            if (extension && extension.currencyCode) {
                params.currency_code = extension.currencyCode;
            }
            if (extension && extension.unitId) {
                params.unit_id = extension.unitId;
            }

            this._requester.sendRequest(this._datafeedUrl, 'symbols', params)
                .then(response => {
                    if (response.s === 'error') {
                        onError(response.errmsg || 'Unknown error');
                        return;
                    }
                    onResolve(response);
                })
                .catch(error => {
                    onError(error);
                });
        }

        getBars(symbolInfo, resolution, periodParams, onHistoryCallback, onErrorCallback) {
            // Validate callbacks
            if (typeof onHistoryCallback !== 'function') {
                console.error('onHistoryCallback is not a function');
                return;
            }
            if (typeof onErrorCallback !== 'function') {
                console.error('onErrorCallback is not a function');
                return;
            }

            const params = {
                symbol: symbolInfo.name || symbolInfo.ticker,
                resolution: resolution,
                from: periodParams.from,
                to: periodParams.to,
            };

            if (periodParams.countBack !== undefined) {
                params.countback = periodParams.countBack;
            }

            console.log('TradingView getBars request:', params);
            
            this._requester.sendRequest(this._datafeedUrl, 'history', params)
                .then(response => {
                    console.log('TradingView getBars response:', response);
                    
                    if (!response || typeof response !== 'object') {
                        console.error('Invalid response from server:', response);
                        onErrorCallback('Invalid response from server');
                        return;
                    }

                    if (response.s === 'error') {
                        console.error('Server error:', response.errmsg);
                        onErrorCallback(response.errmsg || 'Unknown error');
                        return;
                    }

                    if (response.s === 'no_data') {
                        console.warn('No data in requested range');
                        onHistoryCallback([], { noData: true });
                        return;
                    }

                    if (!response.t || !Array.isArray(response.t) || response.t.length === 0) {
                        console.warn('Empty data array in response');
                        onHistoryCallback([], { noData: true });
                        return;
                    }

                    console.log(`Received ${response.t.length} bars`);

                    const bars = [];
                    const meta = {
                        noData: false,
                    };

                    if (response.nextTime) {
                        meta.nextTime = response.nextTime;
                    }

                    for (let i = 0; i < response.t.length; i++) {
                        const bar = {
                            time: response.t[i] * 1000, // Convert to milliseconds
                            low: parseFloat(response.l[i]),
                            high: parseFloat(response.h[i]),
                            open: parseFloat(response.o[i]),
                            close: parseFloat(response.c[i]),
                        };

                        if (response.v && response.v[i] !== undefined) {
                            bar.volume = parseFloat(response.v[i]);
                        }

                        bars.push(bar);
                    }

                    onHistoryCallback(bars, meta);
                })
                .catch(error => {
                    const errorMessage = error instanceof Error ? error.message : String(error);
                    onErrorCallback(errorMessage);
                });
        }

        subscribeBars(symbolInfo, resolution, onTick, subscriberUID, onResetCacheNeededCallback) {
            // Real-time subscription not implemented yet
            // Can be extended later if needed
        }

        unsubscribeBars(subscriberUID) {
            // Real-time unsubscription not implemented yet
        }

        getServerTime(callback) {
            this._requester.sendRequest(this._datafeedUrl, 'time', {})
                .then(time => {
                    callback(time);
                })
                .catch(error => {
                    console.error('Server time request error:', error);
                });
        }
    }

    // Export to global scope
    window.BacktestDatafeed = UDFCompatibleDatafeed;
})();


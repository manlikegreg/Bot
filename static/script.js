/**
 * Trading Signal Bot Dashboard JavaScript
 * Handles all frontend interactions and real-time updates
 */

class TradingBotDashboard {
    constructor() {
        this.autoRefreshInterval = null;
        this.refreshIntervalSeconds = 30;
        this.isLoading = false;
        this.charts = {};
        
        this.init();
    }
    
    init() {
        // Bind event listeners
        this.bindEvents();
        
        // Initial data load
        this.loadAllData();
        
        // Start auto-refresh if checkbox is checked
        const autoRefreshCheckbox = document.getElementById('auto-refresh');
        if (autoRefreshCheckbox && autoRefreshCheckbox.checked) {
            this.startAutoRefresh();
        }
    }
    
    bindEvents() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadAllData());
        }
        
        // Run analysis button
        const runAnalysisBtn = document.getElementById('run-analysis-btn');
        if (runAnalysisBtn) {
            runAnalysisBtn.addEventListener('click', () => this.runAnalysis());
        }
        
        // Test Telegram button
        const testTelegramBtn = document.getElementById('test-telegram-btn');
        if (testTelegramBtn) {
            testTelegramBtn.addEventListener('click', () => this.testTelegram());
        }
        
        // Start bot button
        const startBotBtn = document.getElementById('start-bot-btn');
        if (startBotBtn) {
            startBotBtn.addEventListener('click', () => this.startBot());
        }
        
        // Stop bot button
        const stopBotBtn = document.getElementById('stop-bot-btn');
        if (stopBotBtn) {
            stopBotBtn.addEventListener('click', () => this.stopBot());
        }
        
        // Auto-refresh toggle
        const autoRefreshCheckbox = document.getElementById('auto-refresh');
        if (autoRefreshCheckbox) {
            autoRefreshCheckbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.startAutoRefresh();
                } else {
                    this.stopAutoRefresh();
                }
            });
        }
        
        // Tab change events
        const tabLinks = document.querySelectorAll('#main-tabs .nav-link');
        tabLinks.forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                const targetId = e.target.getAttribute('href').substring(1);
                this.onTabChange(targetId);
            });
        });
    }
    
    async loadAllData() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState();
        
        try {
            // Load all data concurrently
            await Promise.allSettled([
                this.loadStatus(),
                this.loadCurrentSignals(),
                this.loadSignalHistory(),
                this.loadErrors(),
                this.loadConfiguration(),
                this.loadStatistics()
            ]);
        } catch (error) {
            console.error('Error loading data:', error);
            this.showAlert('Error loading dashboard data', 'danger');
        } finally {
            this.isLoading = false;
            this.hideLoadingState();
        }
    }
    
    async loadStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.success) {
                this.updateStatusDisplay(data.data);
            } else {
                throw new Error(data.error || 'Failed to load status');
            }
        } catch (error) {
            console.error('Error loading status:', error);
            this.updateStatusDisplay({
                running: false,
                last_run: 'Error',
                total_signals_sent: 0,
                errors: [],
                current_signals: {}
            });
        }
    }
    
    async loadCurrentSignals() {
        try {
            const response = await fetch('/api/signals/current');
            const data = await response.json();
            
            if (data.success) {
                this.displayCurrentSignals(data.data);
            } else {
                throw new Error(data.error || 'Failed to load current signals');
            }
        } catch (error) {
            console.error('Error loading current signals:', error);
            this.displayCurrentSignals([]);
        }
    }
    
    async loadSignalHistory() {
        try {
            const response = await fetch('/api/signals/history?limit=50');
            const data = await response.json();
            
            if (data.success) {
                this.displaySignalHistory(data.data);
            } else {
                throw new Error(data.error || 'Failed to load signal history');
            }
        } catch (error) {
            console.error('Error loading signal history:', error);
            this.displaySignalHistory([]);
        }
    }
    
    async loadErrors() {
        try {
            const response = await fetch('/api/errors');
            const data = await response.json();
            
            if (data.success) {
                this.displayErrors(data.data);
            } else {
                throw new Error(data.error || 'Failed to load errors');
            }
        } catch (error) {
            console.error('Error loading errors:', error);
            this.displayErrors({ recent_errors: [], error_history: [] });
        }
    }
    
    async loadConfiguration() {
        try {
            const response = await fetch('/api/config');
            const data = await response.json();
            
            if (data.success) {
                this.displayConfiguration(data.data);
            } else {
                throw new Error(data.error || 'Failed to load configuration');
            }
        } catch (error) {
            console.error('Error loading configuration:', error);
            this.displayConfiguration({});
        }
    }
    
    async loadStatistics() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            
            if (data.success) {
                this.displayStatistics(data.data);
            } else {
                throw new Error(data.error || 'Failed to load statistics');
            }
        } catch (error) {
            console.error('Error loading statistics:', error);
            this.displayStatistics({});
        }
    }
    
    updateStatusDisplay(status) {
        // Update bot status indicator
        const statusElement = document.getElementById('bot-status');
        if (statusElement) {
            const isRunning = status.running;
            statusElement.className = `badge ${isRunning ? 'bg-success' : 'bg-danger'} me-3`;
            statusElement.innerHTML = `<i class="fas fa-circle me-1"></i>${isRunning ? 'Running' : 'Stopped'}`;
        }
        
        // Update status cards
        const totalSignalsElement = document.getElementById('total-signals');
        if (totalSignalsElement) {
            totalSignalsElement.textContent = status.total_signals_sent || 0;
        }
        
        const lastRunElement = document.getElementById('last-run');
        if (lastRunElement) {
            if (status.last_run && status.last_run !== 'Never') {
                const lastRunDate = new Date(status.last_run);
                lastRunElement.textContent = lastRunDate.toLocaleString();
            } else {
                lastRunElement.textContent = 'Never';
            }
        }
        
        const activeSignalsElement = document.getElementById('active-signals');
        if (activeSignalsElement) {
            const activeSignals = Object.values(status.current_signals || {}).filter(
                signal => signal.consensus && signal.consensus.signal !== 'HOLD'
            ).length;
            activeSignalsElement.textContent = activeSignals;
        }
        
        const errorCountElement = document.getElementById('error-count');
        if (errorCountElement) {
            errorCountElement.textContent = (status.errors || []).length;
        }
        
        // Update bot control buttons based on running status
        this.updateBotControlButtons(status.running);
    }
    
    displayCurrentSignals(signals) {
        const container = document.getElementById('current-signals');
        if (!container) return;
        
        if (!signals || signals.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center text-muted">
                    <i class="fas fa-chart-line fa-2x"></i>
                    <p class="mt-2">No active signals available</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = signals.map(signal => this.createSignalCard(signal)).join('');
    }
    
    createSignalCard(signal) {
        const signalType = signal.signal.toLowerCase();
        const confidence = signal.confidence || 0;
        const confidenceClass = confidence >= 80 ? 'confidence-high' : 
                               confidence >= 60 ? 'confidence-medium' : 'confidence-low';
        
        const signalIcon = signal.signal === 'BUY' ? 'fa-arrow-up text-success' :
                          signal.signal === 'SELL' ? 'fa-arrow-down text-danger' :
                          'fa-minus text-warning';
        
        return `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card signal-card ${signalType}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h6 class="card-title mb-0">${signal.symbol}</h6>
                            <span class="signal-badge ${signalType}">
                                <i class="fas ${signalIcon.split(' ')[0]} me-1"></i>
                                ${signal.signal}
                            </span>
                        </div>
                        
                        <div class="mb-2">
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <small class="text-muted">Price</small>
                                <span class="price-display">$${signal.price.toFixed(4)}</span>
                            </div>
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <small class="text-muted">Confidence</small>
                                <strong>${confidence.toFixed(1)}%</strong>
                            </div>
                            <div class="confidence-bar">
                                <div class="confidence-progress ${confidenceClass}" style="width: ${confidence}%"></div>
                            </div>
                        </div>
                        
                        <div class="mb-2">
                            <small class="text-muted d-block">Analysis</small>
                            <small>${signal.reason || 'No analysis available'}</small>
                        </div>
                        
                        ${signal.individual_signals && signal.individual_signals.length > 0 ? `
                            <div class="individual-signals">
                                <small class="text-muted d-block mb-1">Individual Signals:</small>
                                ${signal.individual_signals.map(is => `
                                    <div class="individual-signal">
                                        <span class="signal-source">${is.source}</span>
                                        <span class="signal-confidence">${is.signal} (${is.confidence.toFixed(0)}%)</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                        
                        <div class="text-end">
                            <small class="text-muted">
                                ${signal.timestamp ? new Date(signal.timestamp).toLocaleTimeString() : 'Unknown time'}
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    displaySignalHistory(history) {
        const container = document.getElementById('signal-history');
        if (!container) return;
        
        if (!history || history.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-history fa-2x"></i>
                    <p class="mt-2">No signal history available</p>
                </div>
            `;
            return;
        }
        
        const historyHtml = history.slice(-20).reverse().map(signal => {
            const signalType = signal.signal ? signal.signal.toLowerCase() : 'hold';
            const timestamp = signal.timestamp ? new Date(signal.timestamp).toLocaleString() : 'Unknown';
            const confidence = signal.confidence || 0;
            
            return `
                <div class="history-item ${signalType}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1">${signal.symbol} - ${signal.signal || 'UNKNOWN'}</h6>
                            <p class="mb-1 text-muted">${signal.reason || 'No reason provided'}</p>
                            <small class="text-muted">${timestamp}</small>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-secondary">${confidence.toFixed(1)}%</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        container.innerHTML = `<div class="scrollable">${historyHtml}</div>`;
    }
    
    displayErrors(errorData) {
        const container = document.getElementById('error-log');
        if (!container) return;
        
        const recentErrors = errorData.recent_errors || [];
        const errorHistory = errorData.error_history || [];
        const allErrors = [...recentErrors.map(e => ({ message: e, timestamp: new Date().toISOString() })), ...errorHistory];
        
        if (allErrors.length === 0) {
            container.innerHTML = `
                <div class="text-center text-success">
                    <i class="fas fa-check-circle fa-2x"></i>
                    <p class="mt-2">No errors reported</p>
                </div>
            `;
            return;
        }
        
        const errorsHtml = allErrors.slice(-15).reverse().map(error => {
            const timestamp = error.timestamp ? new Date(error.timestamp).toLocaleString() : 'Unknown';
            const message = error.error_message || error.message || 'Unknown error';
            
            return `
                <div class="error-item">
                    <div class="error-message">${message}</div>
                    <div class="error-time">${timestamp}</div>
                </div>
            `;
        }).join('');
        
        container.innerHTML = `<div class="scrollable">${errorsHtml}</div>`;
    }
    
    displayConfiguration(config) {
        const container = document.getElementById('configuration');
        if (!container) return;
        
        const configHtml = `
            <div class="row">
                <div class="col-md-6">
                    <div class="config-section">
                        <h6 class="mb-3">Trading Symbols</h6>
                        ${(config.trading_symbols || []).map(symbol => `
                            <div class="config-item">
                                <span class="config-label">${symbol}</span>
                                <span class="badge bg-primary">Active</span>
                            </div>
                        `).join('')}
                    </div>
                    
                    <div class="config-section">
                        <h6 class="mb-3">Technical Indicators</h6>
                        <div class="config-item">
                            <span class="config-label">RSI Period</span>
                            <span class="config-value">${config.rsi_period || 'N/A'}</span>
                        </div>
                        <div class="config-item">
                            <span class="config-label">Bollinger Period</span>
                            <span class="config-value">${config.bollinger_period || 'N/A'}</span>
                        </div>
                        <div class="config-item">
                            <span class="config-label">MA Short Period</span>
                            <span class="config-value">${config.ma_periods ? config.ma_periods.short : 'N/A'}</span>
                        </div>
                        <div class="config-item">
                            <span class="config-label">MA Long Period</span>
                            <span class="config-value">${config.ma_periods ? config.ma_periods.long : 'N/A'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="config-section">
                        <h6 class="mb-3">MACD Settings</h6>
                        <div class="config-item">
                            <span class="config-label">Fast Period</span>
                            <span class="config-value">${config.macd_periods ? config.macd_periods.fast : 'N/A'}</span>
                        </div>
                        <div class="config-item">
                            <span class="config-label">Slow Period</span>
                            <span class="config-value">${config.macd_periods ? config.macd_periods.slow : 'N/A'}</span>
                        </div>
                        <div class="config-item">
                            <span class="config-label">Signal Period</span>
                            <span class="config-value">${config.macd_periods ? config.macd_periods.signal : 'N/A'}</span>
                        </div>
                    </div>
                    
                    <div class="config-section">
                        <h6 class="mb-3">Alert Settings</h6>
                        <div class="config-item">
                            <span class="config-label">Confidence Threshold</span>
                            <span class="config-value">${config.confidence_threshold || 'N/A'}%</span>
                        </div>
                        <div class="config-item">
                            <span class="config-label">Telegram Configured</span>
                            <span class="badge ${config.telegram_configured ? 'bg-success' : 'bg-danger'}">
                                ${config.telegram_configured ? 'Yes' : 'No'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = configHtml;
    }
    
    displayStatistics(stats) {
        const container = document.getElementById('statistics');
        if (!container) return;
        
        const statsHtml = `
            <div class="row">
                <div class="col-md-6">
                    <div class="config-section">
                        <h6 class="mb-3">General Statistics</h6>
                        <div class="config-item">
                            <span class="config-label">Total Cycles</span>
                            <span class="config-value">${stats.total_cycles || 0}</span>
                        </div>
                        <div class="config-item">
                            <span class="config-label">Successful Cycles</span>
                            <span class="config-value">${stats.successful_cycles || 0}</span>
                        </div>
                        <div class="config-item">
                            <span class="config-label">Total Signals</span>
                            <span class="config-value">${stats.total_signals || 0}</span>
                        </div>
                        <div class="config-item">
                            <span class="config-label">Average Confidence</span>
                            <span class="config-value">${stats.avg_confidence ? stats.avg_confidence.toFixed(1) + '%' : 'N/A'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="config-section">
                        <h6 class="mb-3">Signal Distribution</h6>
                        <canvas id="signal-chart" width="300" height="200"></canvas>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = statsHtml;
        
        // Create signal distribution chart
        this.createSignalChart(stats.signals_by_type || {});
    }
    
    createSignalChart(signalsData) {
        const canvas = document.getElementById('signal-chart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart if it exists
        if (this.charts.signalChart) {
            this.charts.signalChart.destroy();
        }
        
        this.charts.signalChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['BUY', 'SELL', 'HOLD'],
                datasets: [{
                    data: [
                        signalsData.BUY || 0,
                        signalsData.SELL || 0,
                        signalsData.HOLD || 0
                    ],
                    backgroundColor: [
                        '#28a745',
                        '#dc3545',
                        '#ffc107'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    async runAnalysis() {
        const button = document.getElementById('run-analysis-btn');
        if (!button) return;
        
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Running...';
        button.disabled = true;
        
        try {
            const response = await fetch('/api/run-analysis', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('Analysis cycle triggered successfully', 'success');
                // Reload data after a short delay
                setTimeout(() => this.loadAllData(), 3000);
            } else {
                throw new Error(data.error || 'Failed to run analysis');
            }
        } catch (error) {
            console.error('Error running analysis:', error);
            this.showAlert('Failed to trigger analysis: ' + error.message, 'danger');
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }
    
    async testTelegram() {
        const button = document.getElementById('test-telegram-btn');
        if (!button) return;
        
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Testing...';
        button.disabled = true;
        
        try {
            const response = await fetch('/api/test-telegram', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('Telegram test message sent successfully', 'success');
            } else {
                throw new Error(data.error || 'Failed to send test message');
            }
        } catch (error) {
            console.error('Error testing Telegram:', error);
            this.showAlert('Telegram test failed: ' + error.message, 'danger');
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }
    
    async startBot() {
        const button = document.getElementById('start-bot-btn');
        if (!button) return;
        
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Starting...';
        button.disabled = true;
        
        try {
            const response = await fetch('/api/start-bot', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('Trading bot started successfully', 'success');
                // Update button states
                this.updateBotControlButtons(true);
                // Reload data after a short delay
                setTimeout(() => this.loadAllData(), 2000);
            } else {
                throw new Error(data.error || 'Failed to start bot');
            }
        } catch (error) {
            console.error('Error starting bot:', error);
            this.showAlert('Failed to start bot: ' + error.message, 'danger');
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }
    
    async stopBot() {
        const button = document.getElementById('stop-bot-btn');
        if (!button) return;
        
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Stopping...';
        button.disabled = true;
        
        try {
            const response = await fetch('/api/stop-bot', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('Trading bot stopped successfully', 'warning');
                // Update button states
                this.updateBotControlButtons(false);
                // Reload data after a short delay
                setTimeout(() => this.loadAllData(), 2000);
            } else {
                throw new Error(data.error || 'Failed to stop bot');
            }
        } catch (error) {
            console.error('Error stopping bot:', error);
            this.showAlert('Failed to stop bot: ' + error.message, 'danger');
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }
    
    updateBotControlButtons(isRunning) {
        const startBtn = document.getElementById('start-bot-btn');
        const stopBtn = document.getElementById('stop-bot-btn');
        
        if (startBtn && stopBtn) {
            if (isRunning) {
                startBtn.disabled = true;
                stopBtn.disabled = false;
                startBtn.classList.add('disabled');
                stopBtn.classList.remove('disabled');
            } else {
                startBtn.disabled = false;
                stopBtn.disabled = true;
                startBtn.classList.remove('disabled');
                stopBtn.classList.add('disabled');
            }
        }
    }
    
    startAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
        
        this.autoRefreshInterval = setInterval(() => {
            if (!this.isLoading) {
                this.loadAllData();
            }
        }, this.refreshIntervalSeconds * 1000);
    }
    
    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }
    
    onTabChange(tabId) {
        // Load specific data when tab is activated
        switch (tabId) {
            case 'history':
                this.loadSignalHistory();
                break;
            case 'errors':
                this.loadErrors();
                break;
            case 'config':
                this.loadConfiguration();
                break;
            case 'stats':
                this.loadStatistics();
                break;
        }
    }
    
    showLoadingState() {
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            refreshBtn.disabled = true;
        }
    }
    
    hideLoadingState() {
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
            refreshBtn.disabled = false;
        }
    }
    
    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alert-container');
        if (!alertContainer) return;
        
        const alertId = 'alert-' + Date.now();
        const alertHtml = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertContainer.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alertElement = document.getElementById(alertId);
            if (alertElement) {
                const bsAlert = new bootstrap.Alert(alertElement);
                bsAlert.close();
            }
        }, 5000);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TradingBotDashboard();
});

// Handle page visibility changes for auto-refresh
document.addEventListener('visibilitychange', () => {
    const dashboard = window.tradingBotDashboard;
    if (dashboard) {
        if (document.hidden) {
            dashboard.stopAutoRefresh();
        } else {
            const autoRefreshCheckbox = document.getElementById('auto-refresh');
            if (autoRefreshCheckbox && autoRefreshCheckbox.checked) {
                dashboard.startAutoRefresh();
            }
        }
    }
});

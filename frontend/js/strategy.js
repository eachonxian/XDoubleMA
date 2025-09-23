document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const strategyForm = document.getElementById('strategyForm');
    const etfSelect = document.getElementById('etfSelect');
    const loadingContainer = document.getElementById('loadingContainer');
    const resultsContainer = document.getElementById('resultsContainer');
    
    // 设置日期默认值
    setDefaultDates();
    
    // 加载ETF代码列表
    loadEtfCodes();
    
    // 表单提交事件
    strategyForm.addEventListener('submit', function(e) {
        e.preventDefault();
        calculateStrategy();
    });
    
    // 表单重置事件
    strategyForm.addEventListener('reset', function() {
        resultsContainer.style.display = 'none';
        setDefaultDates();
    });
    
    // 设置默认日期（过去一年）
    function setDefaultDates() {
        const today = new Date();
        const oneYearAgo = new Date();
        oneYearAgo.setFullYear(today.getFullYear() - 1);
        
        document.getElementById('endDate').value = formatDate(today);
        document.getElementById('startDate').value = formatDate(oneYearAgo);
    }
    
    // 格式化日期为YYYY-MM-DD
    function formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    // 加载ETF代码列表
    function loadEtfCodes() {
        fetch('/api/etf_codes')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    populateEtfSelect(data.data);
                } else {
                    showError('加载ETF代码失败: ' + data.message);
                }
            })
            .catch(error => {
                showError('网络错误: ' + error.message);
            });
    }
    
    // 填充ETF选择下拉框
    function populateEtfSelect(etfList) {
        etfSelect.innerHTML = '<option value="">-- 请选择ETF --</option>';
        
        etfList.forEach(etf => {
            const option = document.createElement('option');
            option.value = etf.ts_code;
            option.textContent = `${etf.name} (${etf.ts_code})`;
            etfSelect.appendChild(option);
        });
    }
    
    // 计算策略
    function calculateStrategy() {
        // 获取表单数据
        const ts_code = etfSelect.value;
        const startDateInput = document.getElementById('startDate').value;
        const endDateInput = document.getElementById('endDate').value;
        const shortPeriod = parseInt(document.getElementById('shortPeriod').value);
        const longPeriod = parseInt(document.getElementById('longPeriod').value);
        
        // 验证表单
        if (!ts_code) {
            showError('请选择ETF');
            return;
        }
        
        if (!startDateInput || !endDateInput) {
            showError('请选择日期范围');
            return;
        }
        
        if (shortPeriod >= longPeriod) {
            showError('短周期均线必须小于长周期均线');
            return;
        }
        
        // 转换日期格式为YYYYMMDD
        const start_date = startDateInput.replace(/-/g, '');
        const end_date = endDateInput.replace(/-/g, '');
        
        // 显示加载中
        loadingContainer.style.display = 'flex';
        resultsContainer.style.display = 'none';
        
        // 发送请求到后端API
        fetch('/api/strategy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ts_code,
                start_date,
                end_date,
                short_period: shortPeriod,
                long_period: longPeriod
            })
        })
        .then(response => response.json())
        .then(data => {
            // 隐藏加载中
            loadingContainer.style.display = 'none';
            
            if (data.success) {
                // 显示结果
                displayResults(data.data);
            } else {
                showError('策略计算失败: ' + data.message);
            }
        })
        .catch(error => {
            loadingContainer.style.display = 'none';
            showError('网络错误: ' + error.message);
        });
    }
    
    // 显示结果
    function displayResults(data) {
        // 显示回测结果
        const backtest = data.backtest;
        
        document.getElementById('totalReturn').textContent = backtest.total_return + '%';
        document.getElementById('totalReturn').className = backtest.total_return >= 0 ? 'positive' : 'negative';
        
        document.getElementById('annualReturn').textContent = backtest.annual_return + '%';
        document.getElementById('annualReturn').className = backtest.annual_return >= 0 ? 'positive' : 'negative';
        
        document.getElementById('maxDrawdown').textContent = backtest.max_drawdown + '%';
        document.getElementById('maxDrawdown').className = 'negative';
        
        document.getElementById('winRate').textContent = backtest.win_rate + '%';
        document.getElementById('winRate').className = backtest.win_rate >= 50 ? 'positive' : 'negative';
        
        document.getElementById('trades').textContent = backtest.trades;
        
        // 显示信号表格
        const signalsTable = document.getElementById('signalsTable').getElementsByTagName('tbody')[0];
        signalsTable.innerHTML = '';
        
        data.signals.forEach(signal => {
            const row = signalsTable.insertRow();
            
            // 格式化日期 YYYYMMDD -> YYYY-MM-DD
            const date = signal.date;
            const formattedDate = `${date.substring(0, 4)}-${date.substring(4, 6)}-${date.substring(6, 8)}`;
            
            const dateCell = row.insertCell(0);
            const priceCell = row.insertCell(1);
            const typeCell = row.insertCell(2);
            
            dateCell.textContent = formattedDate;
            priceCell.textContent = signal.price;
            typeCell.textContent = signal.type;
            typeCell.className = signal.type === '买入' ? 'buy-signal' : 'sell-signal';
        });
        
        // 绘制价格走势图
        if (data.chart) {
            drawPriceChart(data.chart, etfSelect.options[etfSelect.selectedIndex].text);
        }
        
        // 显示结果容器 - 使用visibility而不是display，保持布局计算
        resultsContainer.style.visibility = 'visible';
        resultsContainer.style.display = 'flex';
        
        // 强制浏览器重新计算布局
        setTimeout(function() {
            window.dispatchEvent(new Event('resize'));
        }, 100);
    }
    
    // 绘制价格走势图
    function drawPriceChart(chartData, etfName) {
        // 初始化ECharts实例
        const chartDom = document.getElementById('priceChart');
        // 确保容器可见并有正确的尺寸
        chartDom.style.visibility = 'visible';
        chartDom.style.height = '600px';
        // 初始化图表
        const myChart = echarts.init(chartDom, 'dark');
        
        // 格式化日期
        const formattedDates = chartData.dates.map(date => {
            return `${date.substring(0, 4)}-${date.substring(4, 6)}-${date.substring(6, 8)}`;
        });
        
        // 准备K线数据
        const candlestickData = [];
        for (let i = 0; i < chartData.dates.length; i++) {
            candlestickData.push([
                chartData.prices.open[i],
                chartData.prices.close[i],
                chartData.prices.low[i],
                chartData.prices.high[i]
            ]);
        }
        
        // 准备买入点和卖出点数据
        const buyPoints = [];
        const sellPoints = [];
        
        // 将买入点和卖出点映射到数据索引
        chartData.signals.buy.dates.forEach((date, index) => {
            const dateIndex = chartData.dates.indexOf(date);
            if (dateIndex !== -1) {
                buyPoints.push({
                    coord: [dateIndex, chartData.signals.buy.prices[index]],
                    value: '买入',
                    itemStyle: {
                        color: '#f44336'
                    }
                });
            }
        });
        
        chartData.signals.sell.dates.forEach((date, index) => {
            const dateIndex = chartData.dates.indexOf(date);
            if (dateIndex !== -1) {
                sellPoints.push({
                    coord: [dateIndex, chartData.signals.sell.prices[index]],
                    value: '卖出',
                    itemStyle: {
                        color: '#4CAF50'
                    }
                });
            }
        });
        
        // 图表配置项
        const option = {
            title: {
                text: `${etfName} 双均线策略 (${document.getElementById('shortPeriod').value}/${document.getElementById('longPeriod').value})`,
                left: 'center',
                textStyle: {
                    color: '#fff'
                }
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                },
                backgroundColor: 'rgba(45, 45, 45, 0.8)',
                borderColor: '#333',
                textStyle: {
                    color: '#fff'
                }
            },
            legend: {
                data: ['K线', `${document.getElementById('shortPeriod').value}日均线`, `${document.getElementById('longPeriod').value}日均线`, '买入点', '卖出点'],
                top: 30,
                textStyle: {
                    color: '#b0b0b0'
                }
            },
            grid: {
                left: '3%',
                right: '3%',
                bottom: '10%',
                top: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: formattedDates,
                scale: true,
                axisLine: {
                    lineStyle: {
                        color: '#8392A5'
                    }
                },
                axisLabel: {
                    rotate: 30,
                    formatter: function (value) {
                        return value.substring(5); // 只显示月-日
                    }
                }
            },
            yAxis: {
                scale: true,
                splitArea: {
                    show: true,
                    areaStyle: {
                        color: ['rgba(45, 45, 45, 0.3)', 'rgba(50, 50, 50, 0.3)']
                    }
                },
                axisLine: {
                    lineStyle: {
                        color: '#8392A5'
                    }
                }
            },
            dataZoom: [
                {
                    type: 'inside',
                    start: 0,
                    end: 100
                },
                {
                    show: true,
                    type: 'slider',
                    bottom: 0,
                    start: 0,
                    end: 100
                }
            ],
            series: [
                {
                    name: 'K线',
                    type: 'candlestick',
                    data: candlestickData,
                    itemStyle: {
                        color: '#f44336',
                        color0: '#4CAF50',
                        borderColor: '#f44336',
                        borderColor0: '#4CAF50'
                    }
                },
                {
                    name: `${document.getElementById('shortPeriod').value}日均线`,
                    type: 'line',
                    data: chartData.ma_short,
                    smooth: true,
                    lineStyle: {
                        width: 2,
                        color: '#2196F3'
                    },
                    symbol: 'none'
                },
                {
                    name: `${document.getElementById('longPeriod').value}日均线`,
                    type: 'line',
                    data: chartData.ma_long,
                    smooth: true,
                    lineStyle: {
                        width: 2,
                        color: '#FF9800'
                    },
                    symbol: 'none'
                },
                {
                    name: '买入点',
                    type: 'scatter',
                    data: buyPoints,
                    symbolSize: 15,
                    itemStyle: {
                        color: '#f44336'
                    },
                    label: {
                        show: true,
                        position: 'top',
                        formatter: '{b}',
                        color: '#f44336',
                        fontSize: 12
                    }
                },
                {
                    name: '卖出点',
                    type: 'scatter',
                    data: sellPoints,
                    symbolSize: 15,
                    itemStyle: {
                        color: '#4CAF50'
                    },
                    label: {
                        show: true,
                        position: 'bottom',
                        formatter: '{b}',
                        color: '#4CAF50',
                        fontSize: 12
                    }
                }
            ]
        };
        
        // 设置图表配置项并渲染
        myChart.setOption(option);
        
        // 响应窗口大小变化
        window.addEventListener('resize', function() {
            myChart.resize();
        });
        
        // 确保图表正确渲染
        setTimeout(function() {
            myChart.resize();
        }, 200); // 延迟200ms确保DOM已完全渲染
    }
    
    // 显示错误信息
    function showError(message) {
        alert(message);
    }
});
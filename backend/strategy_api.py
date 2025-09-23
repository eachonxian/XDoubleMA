import pandas as pd
import numpy as np
import tushare as ts
import os
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# 设置Tushare API Token
# 使用环境变量或配置文件中的token
import os

# 尝试从环境变量获取token，如果没有则使用默认测试token
# 注意：测试token有调用限制，建议用户设置自己的token
ts_token = os.environ.get('TUSHARE_TOKEN', 'YOUR_TUSHARE_TOKEN')
ts.set_token(ts_token)
pro = ts.pro_api()

# 读取ETF代码列表
def load_etf_codes():
    try:
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fund_code.csv')
        df = pd.read_csv(csv_path)
        return df
    except Exception as e:
        print(f"加载ETF代码出错: {e}")
        return pd.DataFrame(columns=['ts_code', 'name'])

# # 获取股票前复权数据
# def get_stock_data(ts_code, start_date, end_date):
#     try:
#         # 使用Tushare获取日线数据（前复权）
#         df = pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
#         # 如果数据为空，尝试使用股票日线接口
#         if df.empty:
#             df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date, adj='qfq')
        
#         # 确保数据按日期排序
#         if not df.empty:
#             df = df.sort_values('trade_date')
            
#         return df
#     except Exception as e:
#         print(f"获取股票数据出错: {e}")
#         return pd.DataFrame()

# 获取基金前复权数据
def get_fund_data(ts_code, start_date, end_date):
    try:
        # 获取基金日线数据
        df = pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if df.empty:
            return pd.DataFrame()
        
        # 确保数据按日期排序
        df = df.sort_values('trade_date')
        
        # 获取复权因子
        adj_df = pro.fund_adj(ts_code=ts_code)
        
        if not adj_df.empty:
            # 合并复权因子
            df = pd.merge(df, adj_df, on='trade_date', how='left')
            # 计算前复权价格

            # 计算前复权价格
            latest_adj_factor = adj_df.sort_values('trade_date',ascending=False).iloc[0]['adj_factor']
            df['adj_factor'] = df['adj_factor'].fillna(1.0)
            df['adj_factor_ratio'] = df['adj_factor'] / latest_adj_factor
            df['close'] = df['close'] * df['adj_factor_ratio']
            df['open'] = df['open'] * df['adj_factor_ratio']
            df['high'] = df['high'] * df['adj_factor_ratio']
            df['low'] = df['low'] * df['adj_factor_ratio']
        
        return df
    except Exception as e:
        print(f"获取基金数据出错: {e}")
        return pd.DataFrame()

# 修改原来的get_stock_data函数
def get_stock_data(ts_code, start_date, end_date):
    try:
        # 首先尝试获取基金数据
        df = get_fund_data(ts_code, start_date, end_date)
        
        # 如果数据为空，尝试使用股票日线接口
        if df.empty:
            df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date, adj='qfq')
        
        # 确保数据按日期排序
        if not df.empty:
            df = df.sort_values('trade_date')
            
        return df
    except Exception as e:
        print(f"获取股票数据出错: {e}")
        return pd.DataFrame()

# 计算双均线策略
def calculate_dual_ma_strategy(df, short_period, long_period):
    if df.empty:
        return pd.DataFrame()
    
    # 复制数据，避免修改原始数据
    result = df.copy()
    
    # 计算短期和长期移动平均线
    result[f'ma_{short_period}'] = result['close'].rolling(window=short_period).mean()
    result[f'ma_{long_period}'] = result['close'].rolling(window=long_period).mean()
    
    # 生成买入信号：短期均线上穿长期均线
    result['signal'] = 0
    result['position'] = 0
    
    # 计算金叉死叉
    for i in range(1, len(result)):
        # 金叉：短期均线从下方穿过长期均线
        if (result[f'ma_{short_period}'].iloc[i-1] <= result[f'ma_{long_period}'].iloc[i-1] and 
            result[f'ma_{short_period}'].iloc[i] > result[f'ma_{long_period}'].iloc[i]):
            result.loc[result.index[i], 'signal'] = 1  # 买入信号
        
        # 死叉：短期均线从上方穿过长期均线
        elif (result[f'ma_{short_period}'].iloc[i-1] >= result[f'ma_{long_period}'].iloc[i-1] and 
              result[f'ma_{short_period}'].iloc[i] < result[f'ma_{long_period}'].iloc[i]):
            result.loc[result.index[i], 'signal'] = -1  # 卖出信号
    
    # 计算持仓
    position = 0
    for i in range(len(result)):
        if result['signal'].iloc[i] == 1:
            position = 1
        elif result['signal'].iloc[i] == -1:
            position = 0
        result.loc[result.index[i], 'position'] = position
    
    return result

# 执行回测
def backtest(df):
    if df.empty or 'position' not in df.columns:
        return {
            'total_return': 0,
            'annual_return': 0,
            'max_drawdown': 0,
            'win_rate': 0,
            'trades': 0
        }
    
    # 计算每日收益率
    df['daily_return'] = df['close'].pct_change()
    
    # 计算策略收益率
    df['strategy_return'] = df['position'].shift(1) * df['daily_return']
    df['strategy_return'] = df['strategy_return'].fillna(0)
    
    # 计算累计收益率
    df['cumulative_return'] = (1 + df['strategy_return']).cumprod() - 1
    
    # 计算最大回撤
    df['cummax'] = df['cumulative_return'].cummax()
    df['drawdown'] = df['cummax'] - df['cumulative_return']
    max_drawdown = df['drawdown'].max()
    
    # 计算交易次数和胜率
    trades = df[df['signal'] != 0]
    buy_signals = trades[trades['signal'] == 1]
    sell_signals = trades[trades['signal'] == -1]
    
    # 确保买卖信号数量匹配
    min_trades = min(len(buy_signals), len(sell_signals))
    
    # 如果最后一个信号是买入但没有对应的卖出，我们使用最后一天的价格
    if len(buy_signals) > len(sell_signals):
        last_buy_date = buy_signals.iloc[-1].name
        last_price = df.iloc[-1]['close']
        profit_trades = 0
        
        for i in range(min_trades):
            buy_price = buy_signals.iloc[i]['close']
            sell_price = sell_signals.iloc[i]['close']
            if sell_price > buy_price:
                profit_trades += 1
        
        # 检查最后一笔未平仓交易
        if last_buy_date > sell_signals.iloc[-1].name if not sell_signals.empty else True:
            buy_price = df.loc[last_buy_date, 'close']
            if last_price > buy_price:
                profit_trades += 1
            min_trades += 1
    else:
        profit_trades = sum(1 for i in range(min_trades) 
                          if sell_signals.iloc[i]['close'] > buy_signals.iloc[i]['close'])
    
    win_rate = profit_trades / min_trades if min_trades > 0 else 0
    
    # 计算总收益和年化收益
    total_return = df['cumulative_return'].iloc[-1] if not df.empty else 0
    days = len(df)
    annual_return = (1 + total_return) ** (252 / days) - 1 if days > 0 else 0
    
    return {
        'total_return': round(total_return * 100, 2),  # 转为百分比
        'annual_return': round(annual_return * 100, 2),  # 转为百分比
        'max_drawdown': round(max_drawdown * 100, 2),  # 转为百分比
        'win_rate': round(win_rate * 100, 2),  # 转为百分比
        'trades': min_trades
    }

# 获取策略结果
def get_strategy_result(ts_code, start_date, end_date, short_period, long_period):
    # 获取股票数据
    df = get_stock_data(ts_code, start_date, end_date)
    
    if df.empty:
        return {
            'success': False,
            'message': '获取股票数据失败'
        }
    
    # 计算策略
    result = calculate_dual_ma_strategy(df, short_period, long_period)
    
    # 执行回测
    backtest_result = backtest(result)
    
    # 提取买卖信号
    signals = result[result['signal'] != 0].copy()
    signals['signal_type'] = signals['signal'].apply(lambda x: '买入' if x == 1 else '卖出')
    
    # 格式化输出
    signals_list = []
    for _, row in signals.iterrows():
        signals_list.append({
            'date': row['trade_date'],
            'price': round(row['close'], 2),
            'type': row['signal_type']
        })
    
    # 准备图表数据
    chart_data = prepare_chart_data(result, short_period, long_period)
    
    # 准备返回数据
    return {
        'success': True,
        'data': {
            'backtest': backtest_result,
            'signals': signals_list,
            'chart': chart_data
        }
    }

# 准备图表数据
def prepare_chart_data(df, short_period, long_period):
    # 确保数据按日期排序
    df = df.sort_values('trade_date')
    
    # 过滤掉均线中的NaN值
    # 找到两个均线都有有效值的起始索引
    valid_ma_start = max(short_period, long_period) - 1
    valid_df = df.iloc[valid_ma_start:].copy()
    
    # 提取图表所需数据
    chart_data = {
        'dates': valid_df['trade_date'].tolist(),
        'prices': {
            'open': valid_df['open'].round(2).tolist(),
            'close': valid_df['close'].round(2).tolist(),
            'high': valid_df['high'].round(2).tolist(),
            'low': valid_df['low'].round(2).tolist(),
        },
        'ma_short': valid_df[f'ma_{short_period}'].round(2).tolist(),
        'ma_long': valid_df[f'ma_{long_period}'].round(2).tolist(),
        'volume': valid_df['vol'].tolist() if 'vol' in df.columns else []
    }
    
    # 提取买卖信号点
    buy_signals = valid_df[valid_df['signal'] == 1].copy()
    sell_signals = valid_df[valid_df['signal'] == -1].copy()
    
    chart_data['signals'] = {
        'buy': {
            'dates': buy_signals['trade_date'].tolist(),
            'prices': buy_signals['close'].round(2).tolist(),
            'indices': buy_signals.index.tolist()
        },
        'sell': {
            'dates': sell_signals['trade_date'].tolist(),
            'prices': sell_signals['close'].round(2).tolist(),
            'indices': sell_signals.index.tolist()
        }
    }
    
    return chart_data

# 如果直接运行此脚本，执行测试
if __name__ == '__main__':
    # 测试策略
    etf_code = '159915.SZ'  # 创业板指ETF
    start_date = '20220101'
    end_date = '20221231'
    short_period = 5
    long_period = 20
    
    result = get_strategy_result(etf_code, start_date, end_date, short_period, long_period)
    print(result)
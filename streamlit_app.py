"""
Dona Invest - XAUUSD Trading System
Professional trading dashboard for gold (XAUUSD) analysis
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/workspace')

from src.data_fetcher import XAUUSDDataFetcher, generate_sample_data
from src.indicators import TechnicalIndicators, analyze_trend
from src.signals import SignalGenerator, SignalType, SignalStrength
from src.risk_manager import RiskManager, PositionType
from src.backtester import Backtester, compare_strategies
from src.charts import (
    create_candlestick_chart,
    create_indicator_chart,
    create_bollinger_chart,
    create_equity_curve,
    create_drawdown_chart,
    create_trade_distribution,
    create_signal_chart
)
from src.mt5_connector import get_mt5_connector, OrderType, MT5SimulatorConnector

st.set_page_config(
    page_title="Dona Invest - XAUUSD Trading",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="expanded"
)

REFRESH_INTERVAL = 30

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FFD700;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #9E9E9E;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #1E3A5F;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #FFD700;
    }
    .signal-buy {
        background-color: rgba(0, 200, 83, 0.2);
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #00C853;
    }
    .signal-sell {
        background-color: rgba(255, 82, 82, 0.2);
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #FF5252;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data(period: str = "1y", interval: str = "1d", use_sample: bool = False):
    """Load XAUUSD data with caching"""
    if use_sample:
        df = generate_sample_data(365)
    else:
        fetcher = XAUUSDDataFetcher()
        df = fetcher.get_historical_data(period=period, interval=interval)
        
        if df.empty:
            st.warning("Unable to fetch live data, using sample data instead.")
            df = generate_sample_data(365)
    
    indicators = TechnicalIndicators(df)
    df = indicators.add_all_indicators()
    
    return df


@st.cache_data(ttl=10)
def get_current_price_info():
    """Get current price information - updates every 10 seconds"""
    fetcher = XAUUSDDataFetcher()
    return fetcher.get_current_price()


@st.cache_data(ttl=5)
def get_realtime_price():
    """Get realtime price - updates every 5 seconds"""
    import yfinance as yf
    try:
        ticker = yf.Ticker("GC=F")
        data = ticker.history(period="1d", interval="1m")
        if not data.empty:
            last_row = data.iloc[-1]
            prev_close = data.iloc[0]['Open']
            current = last_row['Close']
            return {
                'price': current,
                'open': data.iloc[0]['Open'],
                'high': data['High'].max(),
                'low': data['Low'].min(),
                'change': current - prev_close,
                'change_percent': ((current - prev_close) / prev_close) * 100,
                'time': data.index[-1]
            }
    except:
        pass
    return None


def render_header():
    """Render the main header"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<p class="main-header">🥇 DONA INVEST</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Professional XAUUSD Trading System</p>', unsafe_allow_html=True)


def render_price_overview(df: pd.DataFrame):
    """Render price overview section with realtime data"""
    
    realtime = get_realtime_price()
    
    if realtime:
        current_price = realtime['price']
        change = realtime['change']
        change_pct = realtime['change_percent']
        high_24h = realtime['high']
        low_24h = realtime['low']
        last_update = realtime['time']
    else:
        current_price = df['close'].iloc[-1]
        prev_price = df['close'].iloc[-2]
        change = current_price - prev_price
        change_pct = (change / prev_price) * 100
        high_24h = df['high'].iloc[-1]
        low_24h = df['low'].iloc[-1]
        last_update = df.index[-1]
    
    analysis = analyze_trend(df)
    
    st.markdown(f"**🕐 Last Update:** {last_update}")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        delta_color = "normal" if change >= 0 else "inverse"
        st.metric(
            label="🥇 XAUUSD Price",
            value=f"${current_price:,.2f}",
            delta=f"{change:+.2f} ({change_pct:+.2f}%)"
        )
    
    with col2:
        st.metric(
            label="📈 24H High",
            value=f"${high_24h:,.2f}"
        )
    
    with col3:
        st.metric(
            label="📉 24H Low",
            value=f"${low_24h:,.2f}"
        )
    
    with col4:
        trend_color = "🟢" if analysis['trend'] == 'BULLISH' else "🔴" if analysis['trend'] == 'BEARISH' else "🟡"
        st.metric(
            label="📊 Trend",
            value=f"{trend_color} {analysis['trend']}"
        )
    
    with col5:
        st.metric(
            label="💪 Strength",
            value=f"{analysis['strength']}%"
        )


def render_sidebar():
    """Render sidebar controls"""
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        
        st.markdown("#### 📊 Data Settings")
        use_sample = st.checkbox("Use Sample Data", value=False, 
                                help="Use generated sample data instead of live data")
        
        period = st.selectbox(
            "Data Period",
            options=["1mo", "3mo", "6mo", "1y", "2y"],
            index=3
        )
        
        interval = st.selectbox(
            "Interval",
            options=["1h", "1d", "1wk"],
            index=1
        )
        
        st.markdown("---")
        st.markdown("#### 📈 Indicators")
        
        show_sma = st.checkbox("SMA (20, 50)", value=True)
        show_ema = st.checkbox("EMA (12, 26)", value=False)
        show_bb = st.checkbox("Bollinger Bands", value=True)
        
        st.markdown("---")
        st.markdown("#### 💰 Risk Management")
        
        account_balance = st.number_input(
            "Account Balance ($)",
            min_value=100,
            max_value=1000000,
            value=10000,
            step=1000
        )
        
        risk_per_trade = st.slider(
            "Risk per Trade (%)",
            min_value=0.5,
            max_value=5.0,
            value=2.0,
            step=0.5
        )
        
        st.markdown("---")
        st.markdown("#### ℹ️ About")
        st.markdown("""
        **Dona Invest** is a professional trading system for XAUUSD (Gold).
        
        Features:
        - Real-time price data
        - Technical analysis
        - Trading signals
        - Risk management
        - Backtesting
        """)
        
        return {
            'use_sample': use_sample,
            'period': period,
            'interval': interval,
            'show_sma': show_sma,
            'show_ema': show_ema,
            'show_bb': show_bb,
            'account_balance': account_balance,
            'risk_per_trade': risk_per_trade
        }


def render_dashboard_tab(df: pd.DataFrame, settings: dict):
    """Render main dashboard tab"""
    
    col_refresh, col_status = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 Refresh Price"):
            st.cache_data.clear()
            st.rerun()
    with col_status:
        st.markdown("_💡 Click refresh to get latest price | Data updates every ~10 seconds_")
    
    render_price_overview(df)
    
    st.markdown("---")
    
    indicators = []
    if settings['show_sma']:
        indicators.extend(['sma_20', 'sma_50'])
    if settings['show_ema']:
        indicators.extend(['ema_12', 'ema_26'])
    
    chart = create_candlestick_chart(
        df.tail(100),
        title="XAUUSD Price Chart",
        show_volume=True,
        indicators=indicators
    )
    st.plotly_chart(chart, use_container_width=True)
    
    if settings['show_bb']:
        bb_chart = create_bollinger_chart(df.tail(100))
        st.plotly_chart(bb_chart, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### RSI Indicator")
        rsi_chart = create_indicator_chart(df.tail(100), 'rsi')
        st.plotly_chart(rsi_chart, use_container_width=True)
    
    with col2:
        st.markdown("### MACD Indicator")
        macd_chart = create_indicator_chart(df.tail(100), 'macd')
        st.plotly_chart(macd_chart, use_container_width=True)


def render_signals_tab(df: pd.DataFrame):
    """Render trading signals tab"""
    st.markdown("### 📊 Trading Signals")
    
    signal_gen = SignalGenerator(df)
    signals, summary = signal_gen.generate_combined_signals()
    recommendation = signal_gen.get_current_recommendation()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Signals", summary['total_signals'])
    with col2:
        st.metric("Buy Signals", summary['buy_signals'])
    with col3:
        st.metric("Sell Signals", summary['sell_signals'])
    with col4:
        st.metric("Avg Confidence", f"{summary['avg_confidence']:.1%}")
    
    st.markdown("---")
    
    st.markdown("### 🎯 Current Recommendation")
    
    if recommendation['action'] == 'BUY':
        st.success(f"**{recommendation['action']}** - {recommendation['reason']} (Confidence: {recommendation['confidence']:.1%})")
    elif recommendation['action'] == 'SELL':
        st.error(f"**{recommendation['action']}** - {recommendation['reason']} (Confidence: {recommendation['confidence']:.1%})")
    else:
        st.warning(f"**{recommendation['action']}** - {recommendation['reason']}")
    
    st.markdown("---")
    
    if signals:
        signal_chart = create_signal_chart(df.tail(50), signals[:20])
        st.plotly_chart(signal_chart, use_container_width=True)
    
    st.markdown("### 📋 Recent Signals")
    
    if signals:
        signal_data = []
        for s in signals[:15]:
            signal_data.append({
                'Time': s.timestamp.strftime('%Y-%m-%d %H:%M') if hasattr(s.timestamp, 'strftime') else str(s.timestamp),
                'Type': s.type.value,
                'Strength': s.strength.value,
                'Price': f"${s.price:,.2f}",
                'Strategy': s.strategy,
                'Reason': s.reason,
                'Confidence': f"{s.confidence:.1%}",
                'Stop Loss': f"${s.stop_loss:,.2f}" if s.stop_loss else "N/A",
                'Take Profit': f"${s.take_profit:,.2f}" if s.take_profit else "N/A"
            })
        
        df_signals = pd.DataFrame(signal_data)
        st.dataframe(df_signals, use_container_width=True, hide_index=True)
    else:
        st.info("No signals detected in the current data.")


def render_analysis_tab(df: pd.DataFrame):
    """Render technical analysis tab"""
    st.markdown("### 📈 Technical Analysis")
    
    analysis = analyze_trend(df)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Trend Analysis")
        
        if analysis['trend'] == 'BULLISH':
            st.success(f"**Overall Trend: {analysis['trend']}** (Strength: {analysis['strength']}%)")
        elif analysis['trend'] == 'BEARISH':
            st.error(f"**Overall Trend: {analysis['trend']}** (Strength: {analysis['strength']}%)")
        else:
            st.warning(f"**Overall Trend: {analysis['trend']}** (Strength: {analysis['strength']}%)")
        
        st.markdown("#### Indicator Signals")
        for signal in analysis['signals']:
            indicator, direction, description = signal
            if direction in ['BULLISH', 'OVERSOLD']:
                st.markdown(f"🟢 **{indicator}**: {description}")
            elif direction in ['BEARISH', 'OVERBOUGHT']:
                st.markdown(f"🔴 **{indicator}**: {description}")
            else:
                st.markdown(f"🟡 **{indicator}**: {description}")
    
    with col2:
        st.markdown("#### Key Levels")
        
        current_price = df['close'].iloc[-1]
        indicators_obj = TechnicalIndicators(df)
        pivots = indicators_obj.add_pivot_points()
        
        levels_data = {
            'Level': ['Current Price', 'Pivot', 'R1', 'R2', 'R3', 'S1', 'S2', 'S3'],
            'Price': [
                f"${current_price:,.2f}",
                f"${pivots['pivot']:,.2f}",
                f"${pivots['r1']:,.2f}",
                f"${pivots['r2']:,.2f}",
                f"${pivots['r3']:,.2f}",
                f"${pivots['s1']:,.2f}",
                f"${pivots['s2']:,.2f}",
                f"${pivots['s3']:,.2f}"
            ]
        }
        
        st.dataframe(pd.DataFrame(levels_data), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("#### Price Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Price", f"${df['close'].iloc[-1]:,.2f}")
        st.metric("Open", f"${df['open'].iloc[-1]:,.2f}")
    
    with col2:
        st.metric("High", f"${df['high'].iloc[-1]:,.2f}")
        st.metric("Low", f"${df['low'].iloc[-1]:,.2f}")
    
    with col3:
        if 'rsi' in df.columns:
            st.metric("RSI (14)", f"{df['rsi'].iloc[-1]:.1f}")
        if 'atr' in df.columns:
            st.metric("ATR (14)", f"${df['atr'].iloc[-1]:,.2f}")
    
    with col4:
        if 'sma_20' in df.columns:
            st.metric("SMA 20", f"${df['sma_20'].iloc[-1]:,.2f}")
        if 'sma_50' in df.columns:
            st.metric("SMA 50", f"${df['sma_50'].iloc[-1]:,.2f}")


def render_risk_tab(df: pd.DataFrame, settings: dict):
    """Render risk management tab"""
    st.markdown("### 💰 Risk Management")
    
    risk_manager = RiskManager(
        account_balance=settings['account_balance'],
        max_risk_per_trade=settings['risk_per_trade']
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Position Size Calculator")
        
        current_price = float(df['close'].iloc[-1])
        atr_value = float(df['atr'].iloc[-1]) if not pd.isna(df['atr'].iloc[-1]) else current_price * 0.01
        
        entry_price = st.number_input(
            "Entry Price ($)",
            min_value=100.0,
            max_value=10000.0,
            value=current_price,
            step=1.0
        )
        
        default_sl = max(100.0, entry_price - atr_value * 2)
        stop_loss = st.number_input(
            "Stop Loss ($)",
            min_value=100.0,
            max_value=10000.0,
            value=default_sl,
            step=1.0
        )
        
        if st.button("Calculate Position Size"):
            result = risk_manager.calculate_position_size(entry_price, stop_loss)
            
            st.markdown("#### Results")
            st.metric("Recommended Lot Size", f"{result['lot_size']:.2f} lots")
            st.metric("Risk Amount", f"${result['risk_amount']:,.2f}")
            st.metric("Margin Required", f"${result['margin_required']:,.2f}")
            st.metric("Position Value", f"${result['position_value']:,.2f}")
            
            st.markdown("#### Take Profit Levels")
            for ratio, price in result['risk_reward_info'].items():
                st.write(f"**{ratio}**: ${price:,.2f}")
    
    with col2:
        st.markdown("#### Risk Metrics")
        
        risk_metrics = risk_manager.get_risk_metrics(df)
        
        st.metric("Annual Volatility", f"{risk_metrics['volatility_annual']:.2f}%")
        st.metric("Sharpe Ratio", f"{risk_metrics['sharpe_ratio']:.2f}")
        st.metric("Max Drawdown", f"{risk_metrics['max_drawdown']:.2f}%")
        st.metric("VaR (95%)", f"{risk_metrics['var_95']:.2f}%")
        st.metric("Avg Daily Return", f"{risk_metrics['avg_daily_return']:.3f}%")
        st.metric("Best Day", f"{risk_metrics['best_day']:.2f}%")
        st.metric("Worst Day", f"{risk_metrics['worst_day']:.2f}%")


def render_backtest_tab(df: pd.DataFrame, settings: dict):
    """Render backtesting tab"""
    st.markdown("### 🔬 Strategy Backtesting")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        strategy = st.selectbox(
            "Select Strategy",
            options=["MA Crossover", "RSI", "MACD", "Bollinger Bands", "Compare All"]
        )
        
        initial_balance = st.number_input(
            "Initial Balance ($)",
            min_value=1000,
            max_value=100000,
            value=settings['account_balance'],
            step=1000
        )
        
        run_backtest = st.button("🚀 Run Backtest", type="primary")
    
    if run_backtest:
        with st.spinner("Running backtest..."):
            backtester = Backtester(df, initial_balance)
            
            if strategy == "Compare All":
                results = compare_strategies(df, initial_balance)
                
                st.markdown("### Strategy Comparison")
                
                comparison_data = []
                for name, result in results.items():
                    comparison_data.append({
                        'Strategy': name,
                        'Total Return': f"{result.total_return_percent:.2f}%",
                        'Win Rate': f"{result.win_rate:.1f}%",
                        'Profit Factor': f"{result.profit_factor:.2f}",
                        'Max Drawdown': f"{result.max_drawdown_percent:.2f}%",
                        'Sharpe Ratio': f"{result.sharpe_ratio:.2f}",
                        'Total Trades': result.total_trades
                    })
                
                st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)
                
                best_strategy = max(results.items(), key=lambda x: x[1].total_return_percent)
                st.success(f"**Best Strategy: {best_strategy[0]}** with {best_strategy[1].total_return_percent:.2f}% return")
                
            else:
                if strategy == "MA Crossover":
                    result = backtester.run_ma_crossover_strategy()
                elif strategy == "RSI":
                    result = backtester.run_rsi_strategy()
                elif strategy == "MACD":
                    result = backtester.run_macd_strategy()
                else:
                    result = backtester.run_bollinger_strategy()
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Return", f"${result.total_return:,.2f}", 
                             f"{result.total_return_percent:+.2f}%")
                with col2:
                    st.metric("Win Rate", f"{result.win_rate:.1f}%")
                with col3:
                    st.metric("Profit Factor", f"{result.profit_factor:.2f}")
                with col4:
                    st.metric("Max Drawdown", f"{result.max_drawdown_percent:.2f}%")
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Equity Curve")
                    equity_chart = create_equity_curve(result.equity_curve, f"{strategy} Equity Curve")
                    st.plotly_chart(equity_chart, use_container_width=True)
                
                with col2:
                    st.markdown("#### Drawdown")
                    dd_chart = create_drawdown_chart(result.equity_curve)
                    st.plotly_chart(dd_chart, use_container_width=True)
                
                if result.trades:
                    st.markdown("#### Trade Distribution")
                    trade_chart = create_trade_distribution(result.trades)
                    st.plotly_chart(trade_chart, use_container_width=True)
                
                st.markdown("### Detailed Statistics")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### Performance")
                    st.write(f"Initial Balance: ${result.initial_balance:,.2f}")
                    st.write(f"Final Balance: ${result.final_balance:,.2f}")
                    st.write(f"Total Return: {result.total_return_percent:.2f}%")
                    st.write(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
                
                with col2:
                    st.markdown("#### Trade Statistics")
                    st.write(f"Total Trades: {result.total_trades}")
                    st.write(f"Winning Trades: {result.winning_trades}")
                    st.write(f"Losing Trades: {result.losing_trades}")
                    st.write(f"Win Rate: {result.win_rate:.1f}%")
                
                with col3:
                    st.markdown("#### P&L Analysis")
                    st.write(f"Avg Trade P&L: ${result.avg_trade_pnl:.2f}")
                    st.write(f"Avg Win: ${result.avg_win:.2f}")
                    st.write(f"Avg Loss: ${result.avg_loss:.2f}")
                    st.write(f"Largest Win: ${result.largest_win:.2f}")
                    st.write(f"Largest Loss: ${result.largest_loss:.2f}")
                
                if result.trades:
                    st.markdown("### Trade History")
                    
                    trade_data = []
                    for t in result.trades[-20:]:
                        trade_data.append({
                            'Entry Date': t.entry_date.strftime('%Y-%m-%d') if hasattr(t.entry_date, 'strftime') else str(t.entry_date),
                            'Exit Date': t.exit_date.strftime('%Y-%m-%d') if hasattr(t.exit_date, 'strftime') else str(t.exit_date),
                            'Type': t.trade_type,
                            'Entry': f"${t.entry_price:,.2f}",
                            'Exit': f"${t.exit_price:,.2f}",
                            'P&L': f"${t.pnl:.2f}",
                            'Result': t.result.value,
                            'Reason': t.reason
                        })
                    
                    st.dataframe(pd.DataFrame(trade_data), use_container_width=True, hide_index=True)


def render_trading_tab(df: pd.DataFrame, settings: dict):
    """Render MT5 trading tab"""
    st.markdown("### 🤖 Live Trading - MT5")
    
    if 'mt5_connector' not in st.session_state:
        st.session_state.mt5_connector = None
        st.session_state.mt5_connected = False
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        use_demo = st.checkbox("Use Demo Mode", value=True, 
                              help="Use simulated trading instead of real MT5")
    
    with col2:
        if st.button("🔌 Connect MT5", type="primary"):
            with st.spinner("Connecting..."):
                connector = get_mt5_connector(use_simulator=use_demo)
                success, message = connector.connect()
                
                if success:
                    st.session_state.mt5_connector = connector
                    st.session_state.mt5_connected = True
                    st.success(message)
                else:
                    st.error(message)
    
    with col3:
        if st.button("🔌 Disconnect"):
            if st.session_state.mt5_connector:
                st.session_state.mt5_connector.disconnect()
                st.session_state.mt5_connected = False
                st.session_state.mt5_connector = None
                st.info("Disconnected from MT5")
    
    st.markdown("---")
    
    if st.session_state.mt5_connected and st.session_state.mt5_connector:
        connector = st.session_state.mt5_connector
        
        account = connector.get_account_info()
        if account:
            st.markdown("### 📊 Account Information")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Balance", f"${account.balance:,.2f}")
            with col2:
                st.metric("Equity", f"${account.equity:,.2f}")
            with col3:
                profit_delta = f"{account.profit:+,.2f}" if account.profit != 0 else "0.00"
                st.metric("Floating P/L", f"${account.profit:,.2f}", delta=profit_delta)
            with col4:
                st.metric("Free Margin", f"${account.free_margin:,.2f}")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Account", f"#{account.login}")
            with col2:
                st.metric("Server", account.server[:20] + "..." if len(account.server) > 20 else account.server)
            with col3:
                leverage_text = "Unlimited" if account.leverage == 0 else f"1:{account.leverage}"
                st.metric("Leverage", leverage_text)
            with col4:
                st.metric("Currency", account.currency)
        
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 📝 New Order")
            
            price_info = connector.get_current_price()
            if price_info:
                st.info(f"**Current Price** - Bid: ${price_info['bid']:,.2f} | Ask: ${price_info['ask']:,.2f}")
            
            order_type = st.selectbox("Order Type", ["BUY", "SELL"])
            
            volume = st.number_input(
                "Volume (Lots)",
                min_value=0.01,
                max_value=10.0,
                value=0.01,
                step=0.01
            )
            
            use_sl_tp = st.checkbox("Set SL/TP", value=True)
            
            sl_price = None
            tp_price = None
            
            if use_sl_tp and price_info:
                current_price = price_info['bid'] if order_type == "BUY" else price_info['ask']
                atr = df['atr'].iloc[-1] if 'atr' in df.columns else 10
                
                if order_type == "BUY":
                    default_sl = current_price - (atr * 2)
                    default_tp = current_price + (atr * 3)
                else:
                    default_sl = current_price + (atr * 2)
                    default_tp = current_price - (atr * 3)
                
                sl_price = st.number_input(
                    "Stop Loss ($)",
                    min_value=0.0,
                    value=float(default_sl),
                    step=0.5
                )
                
                tp_price = st.number_input(
                    "Take Profit ($)",
                    min_value=0.0,
                    value=float(default_tp),
                    step=0.5
                )
            
            if st.button(f"🚀 Place {order_type} Order", type="primary"):
                with st.spinner("Placing order..."):
                    ot = OrderType.BUY if order_type == "BUY" else OrderType.SELL
                    result = connector.open_position(
                        order_type=ot,
                        volume=volume,
                        sl=sl_price,
                        tp=tp_price
                    )
                    
                    if result.success:
                        st.success(f"✅ {result.message} - Order #{result.order_id} @ ${result.price:,.2f}")
                    else:
                        st.error(f"❌ {result.message}")
        
        with col2:
            st.markdown("### 📋 Open Positions")
            
            positions = connector.get_positions()
            
            if positions:
                for pos in positions:
                    with st.container():
                        pos_color = "🟢" if pos.profit >= 0 else "🔴"
                        
                        st.markdown(f"""
                        **{pos_color} #{pos.ticket}** | {pos.type} {pos.volume} lots @ ${pos.price_open:,.2f}
                        
                        Current: ${pos.price_current:,.2f} | P/L: **${pos.profit:,.2f}**
                        
                        SL: ${pos.sl:,.2f} | TP: ${pos.tp:,.2f}
                        """)
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"Close #{pos.ticket}", key=f"close_{pos.ticket}"):
                                result = connector.close_position(pos.ticket)
                                if result.success:
                                    st.success(result.message)
                                    st.rerun()
                                else:
                                    st.error(result.message)
                        
                        st.markdown("---")
            else:
                st.info("No open positions")
            
            if st.button("🔄 Refresh Positions"):
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📈 Quick Analysis")
        
        signal_gen = SignalGenerator(df)
        recommendation = signal_gen.get_current_recommendation()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if recommendation['action'] == 'BUY':
                st.success(f"**Signal: {recommendation['action']}**")
            elif recommendation['action'] == 'SELL':
                st.error(f"**Signal: {recommendation['action']}**")
            else:
                st.warning(f"**Signal: {recommendation['action']}**")
        
        with col2:
            st.metric("Confidence", f"{recommendation['confidence']:.1%}")
        
        with col3:
            st.write(f"**Reason:** {recommendation['reason']}")
        
        if isinstance(connector, MT5SimulatorConnector):
            st.markdown("---")
            st.warning("⚠️ **Demo Mode**: This is a simulated trading environment. No real trades are being executed.")
    
    else:
        st.info("👆 Click 'Connect MT5' to start trading")
        
        st.markdown("""
        ### 📋 Connection Info
        
        **Account Details:**
        - Login: `412070670`
        - Server: `Exness-MT5Real8`
        - Account Type: Zero (0.05 USD commission, 0.00 spread)
        - Leverage: Unlimited
        
        **Note:** 
        - MetaTrader5 package only works on Windows
        - Use Demo Mode for testing on other platforms
        - Real trading requires MT5 terminal installed
        """)


def main():
    """Main application entry point"""
    render_header()
    
    settings = render_sidebar()
    
    with st.spinner("Loading data..."):
        df = load_data(
            period=settings['period'],
            interval=settings['interval'],
            use_sample=settings['use_sample']
        )
    
    if df.empty:
        st.error("Unable to load data. Please try again or use sample data.")
        return
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard",
        "📈 Signals",
        "🔍 Analysis",
        "💰 Risk",
        "🔬 Backtest",
        "🤖 Trading"
    ])
    
    with tab1:
        render_dashboard_tab(df, settings)
    
    with tab2:
        render_signals_tab(df)
    
    with tab3:
        render_analysis_tab(df)
    
    with tab4:
        render_risk_tab(df, settings)
    
    with tab5:
        render_backtest_tab(df, settings)
    
    with tab6:
        render_trading_tab(df, settings)
    
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #9E9E9E;'>© 2024 Dona Invest - Professional XAUUSD Trading System</p>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

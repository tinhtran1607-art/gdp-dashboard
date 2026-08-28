"""
Dona Invest - Chart Generation Module
Creates interactive charts using Plotly for trading analysis
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional
from datetime import datetime


def create_candlestick_chart(df: pd.DataFrame, 
                             title: str = "XAUUSD Price Chart",
                             show_volume: bool = True,
                             indicators: List[str] = None) -> go.Figure:
    """
    Create an interactive candlestick chart with optional indicators
    
    Args:
        df: DataFrame with OHLCV data
        title: Chart title
        show_volume: Whether to show volume subplot
        indicators: List of indicator columns to overlay
    
    Returns:
        Plotly Figure object
    """
    rows = 2 if show_volume else 1
    row_heights = [0.7, 0.3] if show_volume else [1]
    
    fig = make_subplots(
        rows=rows, 
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=row_heights
    )
    
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='XAUUSD',
            increasing_line_color='#00C853',
            decreasing_line_color='#FF5252'
        ),
        row=1, col=1
    )
    
    if indicators:
        colors = ['#2196F3', '#FF9800', '#9C27B0', '#00BCD4', '#E91E63']
        for i, indicator in enumerate(indicators):
            if indicator in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df[indicator],
                        name=indicator.upper(),
                        line=dict(color=colors[i % len(colors)], width=1.5)
                    ),
                    row=1, col=1
                )
    
    if show_volume and 'volume' in df.columns:
        colors = ['#00C853' if df['close'].iloc[i] >= df['open'].iloc[i] 
                  else '#FF5252' for i in range(len(df))]
        
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.7
            ),
            row=2, col=1
        )
    
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=20, color='#FFD700')),
        template='plotly_dark',
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        xaxis_rangeslider_visible=False,
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    fig.update_xaxes(
        gridcolor='#1E3A5F',
        showgrid=True
    )
    fig.update_yaxes(
        gridcolor='#1E3A5F',
        showgrid=True
    )
    
    return fig


def create_indicator_chart(df: pd.DataFrame, 
                          indicator_type: str = 'rsi') -> go.Figure:
    """
    Create indicator-specific chart
    
    Args:
        df: DataFrame with indicator data
        indicator_type: Type of indicator ('rsi', 'macd', 'stochastic')
    
    Returns:
        Plotly Figure object
    """
    if indicator_type == 'rsi':
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['rsi'],
            name='RSI',
            line=dict(color='#FFD700', width=2)
        ))
        
        fig.add_hline(y=70, line_dash="dash", line_color="#FF5252", 
                      annotation_text="Overbought (70)")
        fig.add_hline(y=30, line_dash="dash", line_color="#00C853",
                      annotation_text="Oversold (30)")
        fig.add_hline(y=50, line_dash="dot", line_color="#9E9E9E")
        
        fig.update_layout(
            title="RSI (14)",
            yaxis_range=[0, 100],
            template='plotly_dark',
            paper_bgcolor='#0E1117',
            plot_bgcolor='#0E1117',
            height=250
        )
        
    elif indicator_type == 'macd':
        fig = make_subplots(rows=1, cols=1)
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['macd'],
            name='MACD',
            line=dict(color='#2196F3', width=1.5)
        ))
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['macd_signal'],
            name='Signal',
            line=dict(color='#FF9800', width=1.5)
        ))
        
        colors = ['#00C853' if val >= 0 else '#FF5252' 
                  for val in df['macd_histogram']]
        
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['macd_histogram'],
            name='Histogram',
            marker_color=colors,
            opacity=0.7
        ))
        
        fig.update_layout(
            title="MACD (12, 26, 9)",
            template='plotly_dark',
            paper_bgcolor='#0E1117',
            plot_bgcolor='#0E1117',
            height=250,
            barmode='relative'
        )
        
    elif indicator_type == 'stochastic':
        fig = go.Figure()
        
        if 'stoch_k' in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['stoch_k'],
                name='%K',
                line=dict(color='#2196F3', width=1.5)
            ))
        
        if 'stoch_d' in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['stoch_d'],
                name='%D',
                line=dict(color='#FF9800', width=1.5)
            ))
        
        fig.add_hline(y=80, line_dash="dash", line_color="#FF5252")
        fig.add_hline(y=20, line_dash="dash", line_color="#00C853")
        
        fig.update_layout(
            title="Stochastic Oscillator",
            yaxis_range=[0, 100],
            template='plotly_dark',
            paper_bgcolor='#0E1117',
            plot_bgcolor='#0E1117',
            height=250
        )
    
    else:
        fig = go.Figure()
    
    fig.update_xaxes(gridcolor='#1E3A5F')
    fig.update_yaxes(gridcolor='#1E3A5F')
    
    return fig


def create_bollinger_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create chart with Bollinger Bands
    
    Args:
        df: DataFrame with price and Bollinger Bands data
    
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['bb_upper'],
        name='Upper Band',
        line=dict(color='rgba(173, 216, 230, 0.5)', width=1),
        fill=None
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['bb_lower'],
        name='Lower Band',
        line=dict(color='rgba(173, 216, 230, 0.5)', width=1),
        fill='tonexty',
        fillcolor='rgba(173, 216, 230, 0.2)'
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['bb_middle'],
        name='Middle Band',
        line=dict(color='#FFD700', width=1, dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['close'],
        name='Price',
        line=dict(color='#FFFFFF', width=2)
    ))
    
    fig.update_layout(
        title="Bollinger Bands (20, 2)",
        template='plotly_dark',
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        height=400
    )
    
    fig.update_xaxes(gridcolor='#1E3A5F')
    fig.update_yaxes(gridcolor='#1E3A5F')
    
    return fig


def create_equity_curve(equity_curve: List[float], 
                        title: str = "Equity Curve") -> go.Figure:
    """
    Create equity curve chart for backtesting
    
    Args:
        equity_curve: List of equity values over time
        title: Chart title
    
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    
    x = list(range(len(equity_curve)))
    
    fig.add_trace(go.Scatter(
        x=x,
        y=equity_curve,
        name='Equity',
        line=dict(color='#FFD700', width=2),
        fill='tozeroy',
        fillcolor='rgba(255, 215, 0, 0.1)'
    ))
    
    max_equity = max(equity_curve)
    min_equity = min(equity_curve)
    
    fig.add_hline(y=equity_curve[0], line_dash="dash", 
                  line_color="#9E9E9E", 
                  annotation_text="Initial Balance")
    
    peak_idx = equity_curve.index(max_equity)
    fig.add_annotation(
        x=peak_idx, y=max_equity,
        text=f"Peak: ${max_equity:,.2f}",
        showarrow=True,
        arrowhead=1,
        arrowcolor="#00C853",
        font=dict(color="#00C853")
    )
    
    fig.update_layout(
        title=title,
        xaxis_title="Trade Number",
        yaxis_title="Equity ($)",
        template='plotly_dark',
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        height=350
    )
    
    fig.update_xaxes(gridcolor='#1E3A5F')
    fig.update_yaxes(gridcolor='#1E3A5F')
    
    return fig


def create_drawdown_chart(equity_curve: List[float]) -> go.Figure:
    """
    Create drawdown chart
    
    Args:
        equity_curve: List of equity values
    
    Returns:
        Plotly Figure object
    """
    equity = np.array(equity_curve)
    rolling_max = np.maximum.accumulate(equity)
    drawdown = (equity - rolling_max) / rolling_max * 100
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=list(range(len(drawdown))),
        y=drawdown,
        name='Drawdown',
        line=dict(color='#FF5252', width=1),
        fill='tozeroy',
        fillcolor='rgba(255, 82, 82, 0.3)'
    ))
    
    max_dd_idx = np.argmin(drawdown)
    fig.add_annotation(
        x=max_dd_idx, y=drawdown[max_dd_idx],
        text=f"Max DD: {drawdown[max_dd_idx]:.2f}%",
        showarrow=True,
        arrowhead=1,
        arrowcolor="#FF5252",
        font=dict(color="#FF5252")
    )
    
    fig.update_layout(
        title="Drawdown",
        xaxis_title="Time",
        yaxis_title="Drawdown (%)",
        template='plotly_dark',
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        height=250
    )
    
    fig.update_xaxes(gridcolor='#1E3A5F')
    fig.update_yaxes(gridcolor='#1E3A5F')
    
    return fig


def create_trade_distribution(trades: List) -> go.Figure:
    """
    Create trade P&L distribution chart
    
    Args:
        trades: List of BacktestTrade objects
    
    Returns:
        Plotly Figure object
    """
    pnls = [t.pnl for t in trades]
    
    fig = go.Figure()
    
    colors = ['#00C853' if p >= 0 else '#FF5252' for p in pnls]
    
    fig.add_trace(go.Bar(
        x=list(range(len(pnls))),
        y=pnls,
        marker_color=colors,
        name='P&L'
    ))
    
    fig.add_hline(y=0, line_color="#9E9E9E")
    
    if pnls:
        avg_pnl = np.mean(pnls)
        fig.add_hline(y=avg_pnl, line_dash="dash", line_color="#FFD700",
                      annotation_text=f"Avg: ${avg_pnl:.2f}")
    
    fig.update_layout(
        title="Trade P&L Distribution",
        xaxis_title="Trade Number",
        yaxis_title="P&L ($)",
        template='plotly_dark',
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        height=300
    )
    
    fig.update_xaxes(gridcolor='#1E3A5F')
    fig.update_yaxes(gridcolor='#1E3A5F')
    
    return fig


def create_signal_chart(df: pd.DataFrame, signals: List) -> go.Figure:
    """
    Create price chart with trading signals overlaid
    
    Args:
        df: DataFrame with OHLCV data
        signals: List of TradingSignal objects
    
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='XAUUSD',
        increasing_line_color='#00C853',
        decreasing_line_color='#FF5252'
    ))
    
    buy_signals = [s for s in signals if s.type.value == 'BUY']
    sell_signals = [s for s in signals if s.type.value == 'SELL']
    
    if buy_signals:
        fig.add_trace(go.Scatter(
            x=[s.timestamp for s in buy_signals],
            y=[s.price for s in buy_signals],
            mode='markers',
            marker=dict(symbol='triangle-up', size=15, color='#00C853'),
            name='Buy Signal',
            hovertemplate='Buy @ %{y:.2f}<br>%{text}',
            text=[s.reason for s in buy_signals]
        ))
    
    if sell_signals:
        fig.add_trace(go.Scatter(
            x=[s.timestamp for s in sell_signals],
            y=[s.price for s in sell_signals],
            mode='markers',
            marker=dict(symbol='triangle-down', size=15, color='#FF5252'),
            name='Sell Signal',
            hovertemplate='Sell @ %{y:.2f}<br>%{text}',
            text=[s.reason for s in sell_signals]
        ))
    
    fig.update_layout(
        title="XAUUSD with Trading Signals",
        template='plotly_dark',
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        xaxis_rangeslider_visible=False,
        height=500
    )
    
    fig.update_xaxes(gridcolor='#1E3A5F')
    fig.update_yaxes(gridcolor='#1E3A5F')
    
    return fig


def create_heatmap_calendar(df: pd.DataFrame) -> go.Figure:
    """
    Create calendar heatmap of daily returns
    
    Args:
        df: DataFrame with daily price data
    
    Returns:
        Plotly Figure object
    """
    daily_returns = df['close'].pct_change() * 100
    
    df_returns = pd.DataFrame({
        'date': df.index,
        'return': daily_returns.values
    })
    df_returns['weekday'] = pd.to_datetime(df_returns['date']).dt.dayofweek
    df_returns['week'] = pd.to_datetime(df_returns['date']).dt.isocalendar().week
    
    pivot = df_returns.pivot_table(
        values='return',
        index='weekday',
        columns='week',
        aggfunc='mean'
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        colorscale='RdYlGn',
        zmid=0,
        colorbar_title='Return %'
    ))
    
    fig.update_layout(
        title="Daily Returns Heatmap",
        template='plotly_dark',
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        height=300
    )
    
    return fig

"""
Dona Invest - XAUUSD Trading System Configuration
"""

SYMBOL = "GC=F"  # Gold Futures on Yahoo Finance (proxy for XAUUSD)

DEFAULT_TIMEFRAMES = {
    "1D": "1d",
    "1H": "1h",
    "4H": "4h",
    "1W": "1wk",
    "1M": "1mo"
}

DEFAULT_PERIODS = {
    "1 Week": 7,
    "1 Month": 30,
    "3 Months": 90,
    "6 Months": 180,
    "1 Year": 365,
    "2 Years": 730
}

INDICATOR_DEFAULTS = {
    "sma_fast": 20,
    "sma_slow": 50,
    "ema_fast": 12,
    "ema_slow": 26,
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bb_period": 20,
    "bb_std": 2,
    "atr_period": 14
}

RISK_DEFAULTS = {
    "max_risk_per_trade": 2.0,
    "default_stop_loss_pips": 100,
    "default_take_profit_pips": 200,
    "max_positions": 3,
    "leverage": 100
}

COLORS = {
    "primary": "#FFD700",
    "secondary": "#1E3A5F",
    "success": "#00C853",
    "danger": "#FF5252",
    "warning": "#FFB300",
    "info": "#2196F3",
    "background": "#0E1117",
    "text": "#FAFAFA"
}

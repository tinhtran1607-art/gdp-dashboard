# 🥇 Dona Invest - XAUUSD Trading System

A professional trading dashboard for Gold (XAUUSD) analysis built with Streamlit.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

## Features

### 📊 Real-time Dashboard
- Live XAUUSD price data from Yahoo Finance
- Interactive candlestick charts with volume
- Multiple timeframe support (1H, 1D, 1W)
- Customizable technical indicators overlay

### 📈 Technical Analysis
- **Moving Averages**: SMA (20, 50, 200), EMA (12, 26)
- **Oscillators**: RSI, MACD, Stochastic
- **Volatility**: Bollinger Bands, ATR
- **Trend Analysis**: ADX, Ichimoku Cloud
- **Support/Resistance**: Pivot Points (Classic)

### 🎯 Trading Signals
- Automated signal generation from multiple strategies
- Signal strength and confidence scoring
- Entry, Stop Loss, and Take Profit recommendations
- Visual signal markers on charts

### 💰 Risk Management
- Position size calculator based on risk percentage
- Risk/Reward ratio analysis
- Portfolio risk metrics (Volatility, Sharpe Ratio, Max Drawdown, VaR)
- Margin and leverage calculations

### 🔬 Strategy Backtesting
- Test multiple trading strategies:
  - MA Crossover
  - RSI Divergence
  - MACD Crossover
  - Bollinger Band Mean Reversion
- Detailed performance metrics
- Equity curve visualization
- Trade-by-trade analysis

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd dona-invest
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run streamlit_app.py
```

## Project Structure

```
dona-invest/
├── streamlit_app.py      # Main Streamlit application
├── requirements.txt      # Python dependencies
├── README.md            # Documentation
├── config/
│   └── settings.py      # Configuration settings
└── src/
    ├── __init__.py
    ├── data_fetcher.py  # Data fetching module
    ├── indicators.py    # Technical indicators
    ├── signals.py       # Signal generation
    ├── risk_manager.py  # Risk management
    ├── backtester.py    # Backtesting engine
    └── charts.py        # Chart generation
```

## Usage

### Dashboard Tab
View real-time XAUUSD prices with interactive charts. Enable/disable indicators from the sidebar.

### Signals Tab
See automated trading signals generated from technical analysis. Each signal includes:
- Signal type (BUY/SELL)
- Strength (STRONG/MODERATE/WEAK)
- Entry price
- Suggested Stop Loss and Take Profit
- Confidence score

### Analysis Tab
Deep dive into technical analysis with:
- Overall trend assessment
- Individual indicator readings
- Key support/resistance levels (Pivot Points)

### Risk Tab
Calculate optimal position sizes based on:
- Account balance
- Risk per trade (%)
- Entry and Stop Loss prices

Also view portfolio risk metrics calculated from historical data.

### Backtest Tab
Test trading strategies on historical data:
1. Select a strategy
2. Set initial balance
3. Click "Run Backtest"
4. Review performance metrics and equity curve

## Configuration

Adjust settings in `config/settings.py`:

```python
INDICATOR_DEFAULTS = {
    "sma_fast": 20,
    "sma_slow": 50,
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    ...
}

RISK_DEFAULTS = {
    "max_risk_per_trade": 2.0,
    "default_stop_loss_pips": 100,
    "leverage": 100
}
```

## Dependencies

- **streamlit**: Web application framework
- **pandas**: Data manipulation
- **numpy**: Numerical computations
- **plotly**: Interactive charts
- **yfinance**: Market data fetching
- **ta**: Technical analysis library

## Disclaimer

This software is for educational and informational purposes only. It is not financial advice. Trading gold and other financial instruments involves significant risk of loss. Past performance does not guarantee future results. Always do your own research and consider consulting a qualified financial advisor before making investment decisions.

## License

MIT License - See LICENSE file for details.

## Author

Dona Invest Team

---

Made with ❤️ using Streamlit

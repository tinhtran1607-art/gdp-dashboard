"""
Dona Invest - Technical Indicators Module
Implements various technical analysis indicators for XAUUSD trading
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
import ta


class TechnicalIndicators:
    """Technical indicators calculator for trading analysis"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with OHLCV DataFrame
        
        Args:
            df: DataFrame with columns: open, high, low, close, volume
        """
        self.df = df.copy()
    
    def add_sma(self, period: int = 20, column: str = 'close') -> pd.Series:
        """Simple Moving Average"""
        sma = self.df[column].rolling(window=period).mean()
        self.df[f'sma_{period}'] = sma
        return sma
    
    def add_ema(self, period: int = 20, column: str = 'close') -> pd.Series:
        """Exponential Moving Average"""
        ema = self.df[column].ewm(span=period, adjust=False).mean()
        self.df[f'ema_{period}'] = ema
        return ema
    
    def add_rsi(self, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = self.df['close'].diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        self.df['rsi'] = rsi
        return rsi
    
    def add_macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Moving Average Convergence Divergence
        
        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        ema_fast = self.df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = self.df['close'].ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        self.df['macd'] = macd_line
        self.df['macd_signal'] = signal_line
        self.df['macd_histogram'] = histogram
        
        return macd_line, signal_line, histogram
    
    def add_bollinger_bands(self, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands
        
        Returns:
            Tuple of (Upper band, Middle band, Lower band)
        """
        middle = self.df['close'].rolling(window=period).mean()
        std = self.df['close'].rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        self.df['bb_upper'] = upper
        self.df['bb_middle'] = middle
        self.df['bb_lower'] = lower
        
        return upper, middle, lower
    
    def add_atr(self, period: int = 14) -> pd.Series:
        """Average True Range"""
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        self.df['atr'] = atr
        return atr
    
    def add_stochastic(self, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator
        
        Returns:
            Tuple of (%K, %D)
        """
        low_min = self.df['low'].rolling(window=k_period).min()
        high_max = self.df['high'].rolling(window=k_period).max()
        
        stoch_k = 100 * (self.df['close'] - low_min) / (high_max - low_min)
        stoch_d = stoch_k.rolling(window=d_period).mean()
        
        self.df['stoch_k'] = stoch_k
        self.df['stoch_d'] = stoch_d
        
        return stoch_k, stoch_d
    
    def add_adx(self, period: int = 14) -> pd.Series:
        """Average Directional Index"""
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        
        plus_dm = high.diff()
        minus_dm = low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(window=period).mean()
        
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = abs(100 * (minus_dm.rolling(window=period).mean() / atr))
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        self.df['adx'] = adx
        self.df['plus_di'] = plus_di
        self.df['minus_di'] = minus_di
        
        return adx
    
    def add_pivot_points(self) -> dict:
        """Calculate daily pivot points"""
        high = self.df['high'].iloc[-1]
        low = self.df['low'].iloc[-1]
        close = self.df['close'].iloc[-1]
        
        pivot = (high + low + close) / 3
        
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)
        
        return {
            'pivot': pivot,
            'r1': r1, 'r2': r2, 'r3': r3,
            's1': s1, 's2': s2, 's3': s3
        }
    
    def add_ichimoku(self, tenkan: int = 9, kijun: int = 26, senkou_b: int = 52) -> dict:
        """Ichimoku Cloud"""
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        
        tenkan_sen = (high.rolling(window=tenkan).max() + low.rolling(window=tenkan).min()) / 2
        kijun_sen = (high.rolling(window=kijun).max() + low.rolling(window=kijun).min()) / 2
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun)
        senkou_span_b = ((high.rolling(window=senkou_b).max() + low.rolling(window=senkou_b).min()) / 2).shift(kijun)
        chikou_span = close.shift(-kijun)
        
        self.df['tenkan_sen'] = tenkan_sen
        self.df['kijun_sen'] = kijun_sen
        self.df['senkou_span_a'] = senkou_span_a
        self.df['senkou_span_b'] = senkou_span_b
        self.df['chikou_span'] = chikou_span
        
        return {
            'tenkan_sen': tenkan_sen,
            'kijun_sen': kijun_sen,
            'senkou_span_a': senkou_span_a,
            'senkou_span_b': senkou_span_b,
            'chikou_span': chikou_span
        }
    
    def add_all_indicators(self, 
                          sma_periods: list = [20, 50, 200],
                          ema_periods: list = [12, 26],
                          rsi_period: int = 14,
                          macd_params: tuple = (12, 26, 9),
                          bb_params: tuple = (20, 2.0),
                          atr_period: int = 14) -> pd.DataFrame:
        """Add all common indicators to the dataframe"""
        
        for period in sma_periods:
            self.add_sma(period)
        
        for period in ema_periods:
            self.add_ema(period)
        
        self.add_rsi(rsi_period)
        self.add_macd(*macd_params)
        self.add_bollinger_bands(*bb_params)
        self.add_atr(atr_period)
        self.add_stochastic()
        self.add_adx()
        
        return self.df
    
    def get_dataframe(self) -> pd.DataFrame:
        """Return the dataframe with all added indicators"""
        return self.df


def analyze_trend(df: pd.DataFrame) -> dict:
    """
    Analyze overall trend based on multiple indicators
    
    Returns:
        Dictionary with trend analysis results
    """
    analysis = {
        'trend': 'NEUTRAL',
        'strength': 0,
        'signals': []
    }
    
    if df.empty or len(df) < 50:
        return analysis
    
    current_price = df['close'].iloc[-1]
    
    ma_signals = []
    if 'sma_20' in df.columns and 'sma_50' in df.columns:
        sma_20 = df['sma_20'].iloc[-1]
        sma_50 = df['sma_50'].iloc[-1]
        
        if current_price > sma_20 > sma_50:
            ma_signals.append(('SMA', 'BULLISH', 'Price above SMA20 > SMA50'))
        elif current_price < sma_20 < sma_50:
            ma_signals.append(('SMA', 'BEARISH', 'Price below SMA20 < SMA50'))
        else:
            ma_signals.append(('SMA', 'NEUTRAL', 'Mixed MA signals'))
    
    rsi_signal = None
    if 'rsi' in df.columns:
        rsi = df['rsi'].iloc[-1]
        if rsi > 70:
            rsi_signal = ('RSI', 'OVERBOUGHT', f'RSI at {rsi:.1f}')
        elif rsi < 30:
            rsi_signal = ('RSI', 'OVERSOLD', f'RSI at {rsi:.1f}')
        elif rsi > 50:
            rsi_signal = ('RSI', 'BULLISH', f'RSI at {rsi:.1f}')
        else:
            rsi_signal = ('RSI', 'BEARISH', f'RSI at {rsi:.1f}')
    
    macd_signal = None
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        macd = df['macd'].iloc[-1]
        macd_sig = df['macd_signal'].iloc[-1]
        macd_hist = df['macd_histogram'].iloc[-1]
        
        if macd > macd_sig and macd_hist > 0:
            macd_signal = ('MACD', 'BULLISH', 'MACD above signal line')
        elif macd < macd_sig and macd_hist < 0:
            macd_signal = ('MACD', 'BEARISH', 'MACD below signal line')
        else:
            macd_signal = ('MACD', 'NEUTRAL', 'MACD crossing signal')
    
    bb_signal = None
    if all(col in df.columns for col in ['bb_upper', 'bb_lower', 'bb_middle']):
        bb_upper = df['bb_upper'].iloc[-1]
        bb_lower = df['bb_lower'].iloc[-1]
        bb_middle = df['bb_middle'].iloc[-1]
        
        if current_price >= bb_upper:
            bb_signal = ('Bollinger', 'OVERBOUGHT', 'Price at upper band')
        elif current_price <= bb_lower:
            bb_signal = ('Bollinger', 'OVERSOLD', 'Price at lower band')
        elif current_price > bb_middle:
            bb_signal = ('Bollinger', 'BULLISH', 'Price above middle band')
        else:
            bb_signal = ('Bollinger', 'BEARISH', 'Price below middle band')
    
    analysis['signals'] = ma_signals + [s for s in [rsi_signal, macd_signal, bb_signal] if s]
    
    bullish_count = sum(1 for s in analysis['signals'] if s[1] in ['BULLISH', 'OVERSOLD'])
    bearish_count = sum(1 for s in analysis['signals'] if s[1] in ['BEARISH', 'OVERBOUGHT'])
    
    total = len(analysis['signals'])
    if total > 0:
        if bullish_count > bearish_count:
            analysis['trend'] = 'BULLISH'
            analysis['strength'] = int((bullish_count / total) * 100)
        elif bearish_count > bullish_count:
            analysis['trend'] = 'BEARISH'
            analysis['strength'] = int((bearish_count / total) * 100)
        else:
            analysis['trend'] = 'NEUTRAL'
            analysis['strength'] = 50
    
    return analysis

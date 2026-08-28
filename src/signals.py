"""
Dona Invest - Trading Signals Module
Generates buy/sell signals based on technical analysis
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SignalStrength(Enum):
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"


@dataclass
class TradingSignal:
    """Represents a trading signal"""
    type: SignalType
    strength: SignalStrength
    price: float
    timestamp: datetime
    strategy: str
    reason: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    confidence: float = 0.0


class SignalGenerator:
    """Generates trading signals based on various strategies"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with DataFrame containing price data and indicators
        
        Args:
            df: DataFrame with OHLCV data and technical indicators
        """
        self.df = df.copy()
        self.signals = []
    
    def generate_ma_crossover_signals(self, fast_ma: str = 'sma_20', 
                                       slow_ma: str = 'sma_50') -> List[TradingSignal]:
        """
        Generate signals based on Moving Average crossover
        
        Golden Cross: Fast MA crosses above Slow MA = BUY
        Death Cross: Fast MA crosses below Slow MA = SELL
        """
        signals = []
        
        if fast_ma not in self.df.columns or slow_ma not in self.df.columns:
            return signals
        
        self.df['ma_diff'] = self.df[fast_ma] - self.df[slow_ma]
        self.df['ma_diff_prev'] = self.df['ma_diff'].shift(1)
        
        golden_cross = (self.df['ma_diff'] > 0) & (self.df['ma_diff_prev'] <= 0)
        death_cross = (self.df['ma_diff'] < 0) & (self.df['ma_diff_prev'] >= 0)
        
        for idx in self.df[golden_cross].index:
            price = self.df.loc[idx, 'close']
            atr = self.df.loc[idx, 'atr'] if 'atr' in self.df.columns else price * 0.01
            
            signals.append(TradingSignal(
                type=SignalType.BUY,
                strength=SignalStrength.MODERATE,
                price=price,
                timestamp=idx,
                strategy="MA Crossover",
                reason=f"Golden Cross: {fast_ma} crossed above {slow_ma}",
                stop_loss=price - (2 * atr),
                take_profit=price + (3 * atr),
                confidence=0.65
            ))
        
        for idx in self.df[death_cross].index:
            price = self.df.loc[idx, 'close']
            atr = self.df.loc[idx, 'atr'] if 'atr' in self.df.columns else price * 0.01
            
            signals.append(TradingSignal(
                type=SignalType.SELL,
                strength=SignalStrength.MODERATE,
                price=price,
                timestamp=idx,
                strategy="MA Crossover",
                reason=f"Death Cross: {fast_ma} crossed below {slow_ma}",
                stop_loss=price + (2 * atr),
                take_profit=price - (3 * atr),
                confidence=0.65
            ))
        
        return signals
    
    def generate_rsi_signals(self, overbought: int = 70, 
                             oversold: int = 30) -> List[TradingSignal]:
        """Generate signals based on RSI overbought/oversold levels"""
        signals = []
        
        if 'rsi' not in self.df.columns:
            return signals
        
        self.df['rsi_prev'] = self.df['rsi'].shift(1)
        
        oversold_exit = (self.df['rsi'] > oversold) & (self.df['rsi_prev'] <= oversold)
        overbought_exit = (self.df['rsi'] < overbought) & (self.df['rsi_prev'] >= overbought)
        
        for idx in self.df[oversold_exit].index:
            price = self.df.loc[idx, 'close']
            atr = self.df.loc[idx, 'atr'] if 'atr' in self.df.columns else price * 0.01
            rsi_val = self.df.loc[idx, 'rsi']
            
            signals.append(TradingSignal(
                type=SignalType.BUY,
                strength=SignalStrength.MODERATE if rsi_val < 35 else SignalStrength.WEAK,
                price=price,
                timestamp=idx,
                strategy="RSI",
                reason=f"RSI exiting oversold zone (RSI: {rsi_val:.1f})",
                stop_loss=price - (1.5 * atr),
                take_profit=price + (2 * atr),
                confidence=0.60
            ))
        
        for idx in self.df[overbought_exit].index:
            price = self.df.loc[idx, 'close']
            atr = self.df.loc[idx, 'atr'] if 'atr' in self.df.columns else price * 0.01
            rsi_val = self.df.loc[idx, 'rsi']
            
            signals.append(TradingSignal(
                type=SignalType.SELL,
                strength=SignalStrength.MODERATE if rsi_val > 65 else SignalStrength.WEAK,
                price=price,
                timestamp=idx,
                strategy="RSI",
                reason=f"RSI exiting overbought zone (RSI: {rsi_val:.1f})",
                stop_loss=price + (1.5 * atr),
                take_profit=price - (2 * atr),
                confidence=0.60
            ))
        
        return signals
    
    def generate_macd_signals(self) -> List[TradingSignal]:
        """Generate signals based on MACD crossover"""
        signals = []
        
        if 'macd' not in self.df.columns or 'macd_signal' not in self.df.columns:
            return signals
        
        self.df['macd_diff'] = self.df['macd'] - self.df['macd_signal']
        self.df['macd_diff_prev'] = self.df['macd_diff'].shift(1)
        
        bullish_cross = (self.df['macd_diff'] > 0) & (self.df['macd_diff_prev'] <= 0)
        bearish_cross = (self.df['macd_diff'] < 0) & (self.df['macd_diff_prev'] >= 0)
        
        for idx in self.df[bullish_cross].index:
            price = self.df.loc[idx, 'close']
            atr = self.df.loc[idx, 'atr'] if 'atr' in self.df.columns else price * 0.01
            hist = abs(self.df.loc[idx, 'macd_histogram'])
            
            strength = SignalStrength.STRONG if hist > atr * 0.5 else SignalStrength.MODERATE
            
            signals.append(TradingSignal(
                type=SignalType.BUY,
                strength=strength,
                price=price,
                timestamp=idx,
                strategy="MACD",
                reason="MACD crossed above signal line",
                stop_loss=price - (2 * atr),
                take_profit=price + (3 * atr),
                confidence=0.70 if strength == SignalStrength.STRONG else 0.60
            ))
        
        for idx in self.df[bearish_cross].index:
            price = self.df.loc[idx, 'close']
            atr = self.df.loc[idx, 'atr'] if 'atr' in self.df.columns else price * 0.01
            hist = abs(self.df.loc[idx, 'macd_histogram'])
            
            strength = SignalStrength.STRONG if hist > atr * 0.5 else SignalStrength.MODERATE
            
            signals.append(TradingSignal(
                type=SignalType.SELL,
                strength=strength,
                price=price,
                timestamp=idx,
                strategy="MACD",
                reason="MACD crossed below signal line",
                stop_loss=price + (2 * atr),
                take_profit=price - (3 * atr),
                confidence=0.70 if strength == SignalStrength.STRONG else 0.60
            ))
        
        return signals
    
    def generate_bollinger_signals(self) -> List[TradingSignal]:
        """Generate signals based on Bollinger Bands"""
        signals = []
        
        required_cols = ['bb_upper', 'bb_lower', 'bb_middle']
        if not all(col in self.df.columns for col in required_cols):
            return signals
        
        self.df['close_prev'] = self.df['close'].shift(1)
        
        bounce_lower = (
            (self.df['close_prev'] <= self.df['bb_lower'].shift(1)) & 
            (self.df['close'] > self.df['bb_lower'])
        )
        
        bounce_upper = (
            (self.df['close_prev'] >= self.df['bb_upper'].shift(1)) & 
            (self.df['close'] < self.df['bb_upper'])
        )
        
        for idx in self.df[bounce_lower].index:
            price = self.df.loc[idx, 'close']
            atr = self.df.loc[idx, 'atr'] if 'atr' in self.df.columns else price * 0.01
            bb_middle = self.df.loc[idx, 'bb_middle']
            
            signals.append(TradingSignal(
                type=SignalType.BUY,
                strength=SignalStrength.MODERATE,
                price=price,
                timestamp=idx,
                strategy="Bollinger Bands",
                reason="Price bounced from lower Bollinger Band",
                stop_loss=price - (1.5 * atr),
                take_profit=bb_middle,
                confidence=0.55
            ))
        
        for idx in self.df[bounce_upper].index:
            price = self.df.loc[idx, 'close']
            atr = self.df.loc[idx, 'atr'] if 'atr' in self.df.columns else price * 0.01
            bb_middle = self.df.loc[idx, 'bb_middle']
            
            signals.append(TradingSignal(
                type=SignalType.SELL,
                strength=SignalStrength.MODERATE,
                price=price,
                timestamp=idx,
                strategy="Bollinger Bands",
                reason="Price bounced from upper Bollinger Band",
                stop_loss=price + (1.5 * atr),
                take_profit=bb_middle,
                confidence=0.55
            ))
        
        return signals
    
    def generate_combined_signals(self) -> Tuple[List[TradingSignal], Dict]:
        """
        Generate combined signals from all strategies
        
        Returns:
            Tuple of (list of signals, summary statistics)
        """
        all_signals = []
        
        all_signals.extend(self.generate_ma_crossover_signals())
        all_signals.extend(self.generate_rsi_signals())
        all_signals.extend(self.generate_macd_signals())
        all_signals.extend(self.generate_bollinger_signals())
        
        all_signals.sort(key=lambda x: x.timestamp, reverse=True)
        
        summary = {
            'total_signals': len(all_signals),
            'buy_signals': sum(1 for s in all_signals if s.type == SignalType.BUY),
            'sell_signals': sum(1 for s in all_signals if s.type == SignalType.SELL),
            'strong_signals': sum(1 for s in all_signals if s.strength == SignalStrength.STRONG),
            'avg_confidence': np.mean([s.confidence for s in all_signals]) if all_signals else 0
        }
        
        return all_signals, summary
    
    def get_latest_signal(self) -> Optional[TradingSignal]:
        """Get the most recent signal"""
        signals, _ = self.generate_combined_signals()
        return signals[0] if signals else None
    
    def get_current_recommendation(self) -> Dict:
        """
        Get current trading recommendation based on all signals
        
        Returns:
            Dictionary with recommendation details
        """
        signals, summary = self.generate_combined_signals()
        
        if not signals:
            return {
                'action': 'HOLD',
                'confidence': 0,
                'reason': 'No clear signals detected',
                'signals': []
            }
        
        recent_signals = [s for s in signals if s.timestamp >= self.df.index[-5]]
        
        if not recent_signals:
            return {
                'action': 'HOLD',
                'confidence': 0,
                'reason': 'No recent signals',
                'signals': signals[:5]
            }
        
        buy_score = sum(s.confidence for s in recent_signals if s.type == SignalType.BUY)
        sell_score = sum(s.confidence for s in recent_signals if s.type == SignalType.SELL)
        
        if buy_score > sell_score and buy_score > 1.0:
            action = 'BUY'
            confidence = min(buy_score / 2, 1.0)
            reason = f"{summary['buy_signals']} buy signals detected"
        elif sell_score > buy_score and sell_score > 1.0:
            action = 'SELL'
            confidence = min(sell_score / 2, 1.0)
            reason = f"{summary['sell_signals']} sell signals detected"
        else:
            action = 'HOLD'
            confidence = 0.5
            reason = 'Mixed signals, waiting for confirmation'
        
        return {
            'action': action,
            'confidence': confidence,
            'reason': reason,
            'signals': recent_signals[:5]
        }

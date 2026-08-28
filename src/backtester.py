"""
Dona Invest - Backtesting Module
Tests trading strategies on historical data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TradeResult(Enum):
    WIN = "WIN"
    LOSS = "LOSS"
    BREAKEVEN = "BREAKEVEN"


@dataclass
class BacktestTrade:
    """Represents a single trade in backtest"""
    entry_date: datetime
    exit_date: datetime
    entry_price: float
    exit_price: float
    trade_type: str  # "LONG" or "SHORT"
    size: float
    pnl: float
    pnl_percent: float
    result: TradeResult
    reason: str  # "SL", "TP", "SIGNAL", "END"


@dataclass
class BacktestResult:
    """Results from a backtest run"""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_balance: float
    final_balance: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    max_drawdown: float
    max_drawdown_percent: float
    sharpe_ratio: float
    total_return: float
    total_return_percent: float
    avg_trade_pnl: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    trades: List[BacktestTrade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)


class Backtester:
    """Backtests trading strategies on historical data"""
    
    def __init__(self, 
                 df: pd.DataFrame,
                 initial_balance: float = 10000,
                 commission: float = 0.0001,
                 slippage: float = 0.5):
        """
        Initialize backtester
        
        Args:
            df: DataFrame with OHLCV data and indicators
            initial_balance: Starting balance
            commission: Commission per trade as decimal
            slippage: Slippage in price points
        """
        self.df = df.copy()
        self.initial_balance = initial_balance
        self.commission = commission
        self.slippage = slippage
        self.balance = initial_balance
        self.equity_curve = [initial_balance]
        self.trades: List[BacktestTrade] = []
        self.position = None
    
    def run_ma_crossover_strategy(self, 
                                  fast_ma: str = 'sma_20',
                                  slow_ma: str = 'sma_50',
                                  sl_atr_mult: float = 2.0,
                                  tp_atr_mult: float = 3.0) -> BacktestResult:
        """
        Run MA Crossover strategy backtest
        
        Args:
            fast_ma: Column name for fast moving average
            slow_ma: Column name for slow moving average
            sl_atr_mult: Stop loss ATR multiplier
            tp_atr_mult: Take profit ATR multiplier
        
        Returns:
            BacktestResult with strategy performance
        """
        self._reset()
        
        if fast_ma not in self.df.columns or slow_ma not in self.df.columns:
            raise ValueError(f"Required columns not found: {fast_ma}, {slow_ma}")
        
        for i in range(1, len(self.df)):
            current = self.df.iloc[i]
            previous = self.df.iloc[i-1]
            date = self.df.index[i]
            
            self._check_exit(current, date)
            
            if self.position is None:
                if previous[fast_ma] <= previous[slow_ma] and current[fast_ma] > current[slow_ma]:
                    atr = current.get('atr', current['close'] * 0.01)
                    self._open_position(
                        date=date,
                        price=current['close'],
                        trade_type="LONG",
                        stop_loss=current['close'] - (sl_atr_mult * atr),
                        take_profit=current['close'] + (tp_atr_mult * atr)
                    )
                
                elif previous[fast_ma] >= previous[slow_ma] and current[fast_ma] < current[slow_ma]:
                    atr = current.get('atr', current['close'] * 0.01)
                    self._open_position(
                        date=date,
                        price=current['close'],
                        trade_type="SHORT",
                        stop_loss=current['close'] + (sl_atr_mult * atr),
                        take_profit=current['close'] - (tp_atr_mult * atr)
                    )
            
            self.equity_curve.append(self.balance + self._get_unrealized_pnl(current['close']))
        
        if self.position:
            self._close_position(
                date=self.df.index[-1],
                price=self.df.iloc[-1]['close'],
                reason="END"
            )
        
        return self._generate_result("MA Crossover")
    
    def run_rsi_strategy(self,
                         oversold: int = 30,
                         overbought: int = 70,
                         sl_atr_mult: float = 1.5,
                         tp_atr_mult: float = 2.0) -> BacktestResult:
        """
        Run RSI strategy backtest
        
        Args:
            oversold: RSI oversold threshold
            overbought: RSI overbought threshold
        
        Returns:
            BacktestResult with strategy performance
        """
        self._reset()
        
        if 'rsi' not in self.df.columns:
            raise ValueError("RSI column not found in dataframe")
        
        for i in range(1, len(self.df)):
            current = self.df.iloc[i]
            previous = self.df.iloc[i-1]
            date = self.df.index[i]
            
            self._check_exit(current, date)
            
            if self.position is None:
                if previous['rsi'] <= oversold and current['rsi'] > oversold:
                    atr = current.get('atr', current['close'] * 0.01)
                    self._open_position(
                        date=date,
                        price=current['close'],
                        trade_type="LONG",
                        stop_loss=current['close'] - (sl_atr_mult * atr),
                        take_profit=current['close'] + (tp_atr_mult * atr)
                    )
                
                elif previous['rsi'] >= overbought and current['rsi'] < overbought:
                    atr = current.get('atr', current['close'] * 0.01)
                    self._open_position(
                        date=date,
                        price=current['close'],
                        trade_type="SHORT",
                        stop_loss=current['close'] + (sl_atr_mult * atr),
                        take_profit=current['close'] - (tp_atr_mult * atr)
                    )
            
            self.equity_curve.append(self.balance + self._get_unrealized_pnl(current['close']))
        
        if self.position:
            self._close_position(
                date=self.df.index[-1],
                price=self.df.iloc[-1]['close'],
                reason="END"
            )
        
        return self._generate_result("RSI Strategy")
    
    def run_macd_strategy(self,
                          sl_atr_mult: float = 2.0,
                          tp_atr_mult: float = 3.0) -> BacktestResult:
        """
        Run MACD crossover strategy backtest
        
        Returns:
            BacktestResult with strategy performance
        """
        self._reset()
        
        if 'macd' not in self.df.columns or 'macd_signal' not in self.df.columns:
            raise ValueError("MACD columns not found in dataframe")
        
        for i in range(1, len(self.df)):
            current = self.df.iloc[i]
            previous = self.df.iloc[i-1]
            date = self.df.index[i]
            
            self._check_exit(current, date)
            
            if self.position is None:
                if previous['macd'] <= previous['macd_signal'] and \
                   current['macd'] > current['macd_signal']:
                    atr = current.get('atr', current['close'] * 0.01)
                    self._open_position(
                        date=date,
                        price=current['close'],
                        trade_type="LONG",
                        stop_loss=current['close'] - (sl_atr_mult * atr),
                        take_profit=current['close'] + (tp_atr_mult * atr)
                    )
                
                elif previous['macd'] >= previous['macd_signal'] and \
                     current['macd'] < current['macd_signal']:
                    atr = current.get('atr', current['close'] * 0.01)
                    self._open_position(
                        date=date,
                        price=current['close'],
                        trade_type="SHORT",
                        stop_loss=current['close'] + (sl_atr_mult * atr),
                        take_profit=current['close'] - (tp_atr_mult * atr)
                    )
            
            self.equity_curve.append(self.balance + self._get_unrealized_pnl(current['close']))
        
        if self.position:
            self._close_position(
                date=self.df.index[-1],
                price=self.df.iloc[-1]['close'],
                reason="END"
            )
        
        return self._generate_result("MACD Strategy")
    
    def run_bollinger_strategy(self,
                               sl_atr_mult: float = 1.5,
                               tp_mult: float = 1.0) -> BacktestResult:
        """
        Run Bollinger Bands mean reversion strategy
        
        Returns:
            BacktestResult with strategy performance
        """
        self._reset()
        
        required = ['bb_upper', 'bb_lower', 'bb_middle']
        if not all(col in self.df.columns for col in required):
            raise ValueError("Bollinger Bands columns not found")
        
        for i in range(1, len(self.df)):
            current = self.df.iloc[i]
            previous = self.df.iloc[i-1]
            date = self.df.index[i]
            
            self._check_exit(current, date)
            
            if self.position is None:
                if previous['close'] <= previous['bb_lower'] and current['close'] > current['bb_lower']:
                    atr = current.get('atr', current['close'] * 0.01)
                    self._open_position(
                        date=date,
                        price=current['close'],
                        trade_type="LONG",
                        stop_loss=current['close'] - (sl_atr_mult * atr),
                        take_profit=current['bb_middle']
                    )
                
                elif previous['close'] >= previous['bb_upper'] and current['close'] < current['bb_upper']:
                    atr = current.get('atr', current['close'] * 0.01)
                    self._open_position(
                        date=date,
                        price=current['close'],
                        trade_type="SHORT",
                        stop_loss=current['close'] + (sl_atr_mult * atr),
                        take_profit=current['bb_middle']
                    )
            
            self.equity_curve.append(self.balance + self._get_unrealized_pnl(current['close']))
        
        if self.position:
            self._close_position(
                date=self.df.index[-1],
                price=self.df.iloc[-1]['close'],
                reason="END"
            )
        
        return self._generate_result("Bollinger Bands Strategy")
    
    def _reset(self):
        """Reset backtester state"""
        self.balance = self.initial_balance
        self.equity_curve = [self.initial_balance]
        self.trades = []
        self.position = None
    
    def _open_position(self, date, price, trade_type, stop_loss, take_profit):
        """Open a new position"""
        price_with_slippage = price + self.slippage if trade_type == "LONG" else price - self.slippage
        
        risk_amount = self.balance * 0.02
        sl_distance = abs(price_with_slippage - stop_loss)
        
        if sl_distance > 0:
            size = risk_amount / sl_distance
        else:
            size = 0.01
        
        size = max(0.01, min(size, 1.0))
        
        self.position = {
            'entry_date': date,
            'entry_price': price_with_slippage,
            'trade_type': trade_type,
            'size': size,
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
    
    def _close_position(self, date, price, reason):
        """Close current position"""
        if self.position is None:
            return
        
        price_with_slippage = price - self.slippage if self.position['trade_type'] == "LONG" else price + self.slippage
        
        if self.position['trade_type'] == "LONG":
            pnl = (price_with_slippage - self.position['entry_price']) * self.position['size']
        else:
            pnl = (self.position['entry_price'] - price_with_slippage) * self.position['size']
        
        commission_cost = (self.position['entry_price'] + price_with_slippage) * self.position['size'] * self.commission
        pnl -= commission_cost
        
        pnl_percent = (pnl / self.balance) * 100
        
        if pnl > 0:
            result = TradeResult.WIN
        elif pnl < 0:
            result = TradeResult.LOSS
        else:
            result = TradeResult.BREAKEVEN
        
        trade = BacktestTrade(
            entry_date=self.position['entry_date'],
            exit_date=date,
            entry_price=self.position['entry_price'],
            exit_price=price_with_slippage,
            trade_type=self.position['trade_type'],
            size=self.position['size'],
            pnl=pnl,
            pnl_percent=pnl_percent,
            result=result,
            reason=reason
        )
        
        self.trades.append(trade)
        self.balance += pnl
        self.position = None
    
    def _check_exit(self, current, date):
        """Check if position should be closed"""
        if self.position is None:
            return
        
        high = current['high']
        low = current['low']
        
        if self.position['trade_type'] == "LONG":
            if low <= self.position['stop_loss']:
                self._close_position(date, self.position['stop_loss'], "SL")
            elif high >= self.position['take_profit']:
                self._close_position(date, self.position['take_profit'], "TP")
        else:  # SHORT
            if high >= self.position['stop_loss']:
                self._close_position(date, self.position['stop_loss'], "SL")
            elif low <= self.position['take_profit']:
                self._close_position(date, self.position['take_profit'], "TP")
    
    def _get_unrealized_pnl(self, current_price) -> float:
        """Calculate unrealized P&L"""
        if self.position is None:
            return 0
        
        if self.position['trade_type'] == "LONG":
            return (current_price - self.position['entry_price']) * self.position['size']
        else:
            return (self.position['entry_price'] - current_price) * self.position['size']
    
    def _generate_result(self, strategy_name: str) -> BacktestResult:
        """Generate backtest results"""
        winning_trades = [t for t in self.trades if t.result == TradeResult.WIN]
        losing_trades = [t for t in self.trades if t.result == TradeResult.LOSS]
        
        total_trades = len(self.trades)
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        equity = np.array(self.equity_curve)
        rolling_max = np.maximum.accumulate(equity)
        drawdowns = (equity - rolling_max) / rolling_max
        max_drawdown_percent = abs(min(drawdowns)) * 100
        max_drawdown = rolling_max[np.argmin(drawdowns)] - equity[np.argmin(drawdowns)]
        
        returns = np.diff(equity) / equity[:-1]
        sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0
        
        total_return = self.balance - self.initial_balance
        total_return_percent = (total_return / self.initial_balance) * 100
        
        avg_trade_pnl = np.mean([t.pnl for t in self.trades]) if self.trades else 0
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        largest_win = max([t.pnl for t in winning_trades]) if winning_trades else 0
        largest_loss = min([t.pnl for t in losing_trades]) if losing_trades else 0
        
        return BacktestResult(
            strategy_name=strategy_name,
            start_date=self.df.index[0],
            end_date=self.df.index[-1],
            initial_balance=self.initial_balance,
            final_balance=self.balance,
            total_trades=total_trades,
            winning_trades=win_count,
            losing_trades=loss_count,
            win_rate=win_rate,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            max_drawdown_percent=max_drawdown_percent,
            sharpe_ratio=sharpe,
            total_return=total_return,
            total_return_percent=total_return_percent,
            avg_trade_pnl=avg_trade_pnl,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            trades=self.trades,
            equity_curve=self.equity_curve
        )


def compare_strategies(df: pd.DataFrame, initial_balance: float = 10000) -> Dict[str, BacktestResult]:
    """
    Compare multiple trading strategies
    
    Args:
        df: DataFrame with price data and indicators
        initial_balance: Starting balance for each strategy
    
    Returns:
        Dictionary of strategy names to BacktestResult
    """
    results = {}
    
    backtester = Backtester(df, initial_balance)
    
    try:
        results['MA Crossover'] = backtester.run_ma_crossover_strategy()
    except ValueError:
        pass
    
    try:
        results['RSI'] = backtester.run_rsi_strategy()
    except ValueError:
        pass
    
    try:
        results['MACD'] = backtester.run_macd_strategy()
    except ValueError:
        pass
    
    try:
        results['Bollinger Bands'] = backtester.run_bollinger_strategy()
    except ValueError:
        pass
    
    return results

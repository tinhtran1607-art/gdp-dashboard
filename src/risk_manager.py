"""
Dona Invest - Risk Management Module
Handles position sizing, stop loss, take profit, and portfolio risk
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class PositionType(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class Position:
    """Represents an open trading position"""
    id: str
    type: PositionType
    entry_price: float
    size: float  # Lot size
    stop_loss: float
    take_profit: float
    entry_time: datetime
    current_price: float = 0.0
    pnl: float = 0.0
    pnl_percent: float = 0.0
    
    def update_pnl(self, current_price: float):
        """Update P&L based on current price"""
        self.current_price = current_price
        if self.type == PositionType.LONG:
            self.pnl = (current_price - self.entry_price) * self.size * 100
        else:
            self.pnl = (self.entry_price - current_price) * self.size * 100
        
        self.pnl_percent = (self.pnl / (self.entry_price * self.size * 100)) * 100


class RiskManager:
    """Manages trading risk and position sizing"""
    
    def __init__(self, 
                 account_balance: float = 10000,
                 max_risk_per_trade: float = 2.0,
                 max_total_risk: float = 6.0,
                 leverage: int = 100):
        """
        Initialize Risk Manager
        
        Args:
            account_balance: Total account balance in USD
            max_risk_per_trade: Maximum risk per trade as percentage of balance
            max_total_risk: Maximum total portfolio risk as percentage
            leverage: Trading leverage
        """
        self.account_balance = account_balance
        self.max_risk_per_trade = max_risk_per_trade
        self.max_total_risk = max_total_risk
        self.leverage = leverage
        self.positions: List[Position] = []
        self.closed_positions: List[Position] = []
    
    def calculate_position_size(self, 
                                entry_price: float, 
                                stop_loss: float,
                                risk_percent: Optional[float] = None) -> Dict:
        """
        Calculate optimal position size based on risk parameters
        
        Args:
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            risk_percent: Risk percentage (uses default if not provided)
        
        Returns:
            Dictionary with position sizing details
        """
        if risk_percent is None:
            risk_percent = self.max_risk_per_trade
        
        risk_amount = self.account_balance * (risk_percent / 100)
        
        stop_loss_pips = abs(entry_price - stop_loss)
        pip_value = 0.01  # For gold, 1 pip = $0.01 per 0.01 lot
        
        if stop_loss_pips == 0:
            return {
                'lot_size': 0.01,
                'risk_amount': risk_amount,
                'stop_loss_pips': 0,
                'position_value': entry_price * 0.01 * 100,
                'margin_required': (entry_price * 0.01 * 100) / self.leverage
            }
        
        lot_size = risk_amount / (stop_loss_pips * pip_value * 100)
        
        lot_size = max(0.01, round(lot_size, 2))
        lot_size = min(lot_size, 10.0)
        
        position_value = entry_price * lot_size * 100
        margin_required = position_value / self.leverage
        
        if margin_required > self.account_balance * 0.5:
            lot_size = (self.account_balance * 0.5 * self.leverage) / (entry_price * 100)
            lot_size = max(0.01, round(lot_size, 2))
            margin_required = (entry_price * lot_size * 100) / self.leverage
        
        return {
            'lot_size': lot_size,
            'risk_amount': risk_amount,
            'stop_loss_pips': stop_loss_pips,
            'position_value': entry_price * lot_size * 100,
            'margin_required': margin_required,
            'risk_reward_info': self._calculate_risk_reward(entry_price, stop_loss, lot_size)
        }
    
    def _calculate_risk_reward(self, entry: float, stop_loss: float, lot_size: float) -> Dict:
        """Calculate risk/reward metrics"""
        risk = abs(entry - stop_loss)
        
        return {
            '1:1': entry + risk if entry > stop_loss else entry - risk,
            '1:2': entry + (2 * risk) if entry > stop_loss else entry - (2 * risk),
            '1:3': entry + (3 * risk) if entry > stop_loss else entry - (3 * risk),
        }
    
    def calculate_stop_loss(self, 
                           entry_price: float, 
                           atr: float,
                           position_type: PositionType,
                           multiplier: float = 2.0) -> float:
        """
        Calculate stop loss based on ATR
        
        Args:
            entry_price: Entry price
            atr: Current ATR value
            position_type: LONG or SHORT
            multiplier: ATR multiplier for stop loss distance
        
        Returns:
            Stop loss price
        """
        stop_distance = atr * multiplier
        
        if position_type == PositionType.LONG:
            return entry_price - stop_distance
        else:
            return entry_price + stop_distance
    
    def calculate_take_profit(self, 
                              entry_price: float,
                              stop_loss: float,
                              risk_reward_ratio: float = 2.0) -> float:
        """
        Calculate take profit based on risk/reward ratio
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_reward_ratio: Desired risk/reward ratio
        
        Returns:
            Take profit price
        """
        risk = abs(entry_price - stop_loss)
        reward = risk * risk_reward_ratio
        
        if entry_price > stop_loss:  # Long position
            return entry_price + reward
        else:  # Short position
            return entry_price - reward
    
    def open_position(self, 
                      position_type: PositionType,
                      entry_price: float,
                      stop_loss: float,
                      take_profit: float,
                      lot_size: float) -> Optional[Position]:
        """
        Open a new position
        
        Args:
            position_type: LONG or SHORT
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            lot_size: Position size in lots
        
        Returns:
            Position object if successful, None if risk limits exceeded
        """
        current_risk = self._calculate_total_risk()
        new_trade_risk = (abs(entry_price - stop_loss) * lot_size * 100 / self.account_balance) * 100
        
        if current_risk + new_trade_risk > self.max_total_risk:
            return None
        
        position = Position(
            id=f"POS_{len(self.positions) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            type=position_type,
            entry_price=entry_price,
            size=lot_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_time=datetime.now(),
            current_price=entry_price
        )
        
        self.positions.append(position)
        return position
    
    def close_position(self, position_id: str, close_price: float) -> Optional[Dict]:
        """
        Close an existing position
        
        Args:
            position_id: Position ID to close
            close_price: Closing price
        
        Returns:
            Dictionary with closing details
        """
        position = next((p for p in self.positions if p.id == position_id), None)
        
        if position is None:
            return None
        
        position.update_pnl(close_price)
        
        self.positions.remove(position)
        self.closed_positions.append(position)
        
        self.account_balance += position.pnl
        
        return {
            'position_id': position_id,
            'pnl': position.pnl,
            'pnl_percent': position.pnl_percent,
            'new_balance': self.account_balance
        }
    
    def _calculate_total_risk(self) -> float:
        """Calculate total portfolio risk from open positions"""
        total_risk = 0
        for pos in self.positions:
            risk = abs(pos.entry_price - pos.stop_loss) * pos.size * 100
            total_risk += (risk / self.account_balance) * 100
        return total_risk
    
    def update_positions(self, current_price: float) -> List[Dict]:
        """
        Update all positions with current price and check for SL/TP hits
        
        Args:
            current_price: Current market price
        
        Returns:
            List of closed positions (hit SL or TP)
        """
        closed = []
        
        for position in self.positions[:]:
            position.update_pnl(current_price)
            
            if position.type == PositionType.LONG:
                if current_price <= position.stop_loss:
                    result = self.close_position(position.id, position.stop_loss)
                    if result:
                        result['reason'] = 'STOP_LOSS'
                        closed.append(result)
                elif current_price >= position.take_profit:
                    result = self.close_position(position.id, position.take_profit)
                    if result:
                        result['reason'] = 'TAKE_PROFIT'
                        closed.append(result)
            else:  # SHORT
                if current_price >= position.stop_loss:
                    result = self.close_position(position.id, position.stop_loss)
                    if result:
                        result['reason'] = 'STOP_LOSS'
                        closed.append(result)
                elif current_price <= position.take_profit:
                    result = self.close_position(position.id, position.take_profit)
                    if result:
                        result['reason'] = 'TAKE_PROFIT'
                        closed.append(result)
        
        return closed
    
    def get_portfolio_summary(self) -> Dict:
        """Get summary of portfolio status"""
        total_pnl = sum(p.pnl for p in self.positions)
        total_risk = self._calculate_total_risk()
        
        return {
            'account_balance': self.account_balance,
            'floating_pnl': total_pnl,
            'equity': self.account_balance + total_pnl,
            'open_positions': len(self.positions),
            'total_risk_percent': total_risk,
            'available_risk': self.max_total_risk - total_risk,
            'margin_used': sum(
                (p.entry_price * p.size * 100) / self.leverage 
                for p in self.positions
            ),
            'closed_trades': len(self.closed_positions),
            'win_rate': self._calculate_win_rate()
        }
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate from closed positions"""
        if not self.closed_positions:
            return 0.0
        
        wins = sum(1 for p in self.closed_positions if p.pnl > 0)
        return (wins / len(self.closed_positions)) * 100
    
    def get_risk_metrics(self, df: pd.DataFrame) -> Dict:
        """
        Calculate various risk metrics from historical data
        
        Args:
            df: DataFrame with price history
        
        Returns:
            Dictionary with risk metrics
        """
        returns = df['close'].pct_change().dropna()
        
        volatility = returns.std() * np.sqrt(252) * 100
        
        if returns.std() != 0:
            sharpe = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
        else:
            sharpe = 0
        
        cumulative = (1 + returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdowns = (cumulative - rolling_max) / rolling_max
        max_drawdown = drawdowns.min() * 100
        
        var_95 = np.percentile(returns, 5) * 100
        
        return {
            'volatility_annual': volatility,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'var_95': var_95,
            'avg_daily_return': returns.mean() * 100,
            'best_day': returns.max() * 100,
            'worst_day': returns.min() * 100
        }

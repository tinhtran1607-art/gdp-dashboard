"""
Order Blocks Detection Module
Identifies bullish and bearish order blocks based on institutional order flow
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class OrderBlockType(Enum):
    BULLISH = "BULLISH_OB"
    BEARISH = "BEARISH_OB"


class OrderBlockStatus(Enum):
    FRESH = "FRESH"  # Not yet tested
    TESTED = "TESTED"  # Tested but held
    MITIGATED = "MITIGATED"  # Price passed through
    BROKEN = "BROKEN"  # Invalidated


@dataclass
class OrderBlock:
    """Represents an Order Block"""
    type: OrderBlockType
    index: int
    timestamp: pd.Timestamp
    high: float
    low: float
    open_price: float
    close_price: float
    status: OrderBlockStatus = OrderBlockStatus.FRESH
    strength: float = 0.0
    impulse_size: float = 0.0
    tested_count: int = 0


class OrderBlockDetector:
    """Detects and manages Order Blocks"""
    
    def __init__(self, df: pd.DataFrame, atr_period: int = 14, 
                 impulse_threshold: float = 1.5, lookback: int = 10):
        """
        Initialize Order Block detector
        
        Args:
            df: DataFrame with OHLCV data
            atr_period: Period for ATR calculation
            impulse_threshold: Minimum impulse size in ATR units
            lookback: Number of candles to look back for OB
        """
        self.df = df.copy()
        self.atr_period = atr_period
        self.impulse_threshold = impulse_threshold
        self.lookback = lookback
        self.order_blocks: List[OrderBlock] = []
        self._calculate_atr()
    
    def _calculate_atr(self):
        """Calculate ATR for the dataframe"""
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        self.df['atr'] = tr.rolling(window=self.atr_period).mean()
    
    def _is_bullish_candle(self, index: int) -> bool:
        """Check if candle is bullish"""
        return self.df['close'].iloc[index] > self.df['open'].iloc[index]
    
    def _is_bearish_candle(self, index: int) -> bool:
        """Check if candle is bearish"""
        return self.df['close'].iloc[index] < self.df['open'].iloc[index]
    
    def _get_candle_body_size(self, index: int) -> float:
        """Get the body size of a candle"""
        return abs(self.df['close'].iloc[index] - self.df['open'].iloc[index])
    
    def _get_impulse_size(self, start_idx: int, end_idx: int) -> float:
        """Calculate the size of an impulse move"""
        return abs(self.df['close'].iloc[end_idx] - self.df['close'].iloc[start_idx])
    
    def identify_order_blocks(self) -> List[OrderBlock]:
        """
        Identify all order blocks in the data
        
        Returns:
            List of identified order blocks
        """
        self.order_blocks = []
        
        for i in range(self.lookback + 1, len(self.df)):
            atr = self.df['atr'].iloc[i]
            if pd.isna(atr) or atr == 0:
                continue
            
            # Check for bullish impulse (strong up move)
            impulse_move = self.df['close'].iloc[i] - self.df['close'].iloc[i-1]
            
            if impulse_move > atr * self.impulse_threshold:
                # Bullish impulse - look for bearish OB before
                ob = self._find_bearish_ob_before_impulse(i)
                if ob:
                    ob.impulse_size = impulse_move
                    ob.strength = self._calculate_ob_strength(ob, impulse_move, atr)
                    self.order_blocks.append(ob)
            
            elif impulse_move < -atr * self.impulse_threshold:
                # Bearish impulse - look for bullish OB before
                ob = self._find_bullish_ob_before_impulse(i)
                if ob:
                    ob.impulse_size = abs(impulse_move)
                    ob.strength = self._calculate_ob_strength(ob, abs(impulse_move), atr)
                    self.order_blocks.append(ob)
        
        self._update_ob_status()
        return self.order_blocks
    
    def _find_bearish_ob_before_impulse(self, impulse_idx: int) -> Optional[OrderBlock]:
        """Find the last bearish candle before a bullish impulse"""
        for j in range(impulse_idx - 1, max(impulse_idx - self.lookback, 0), -1):
            if self._is_bearish_candle(j):
                return OrderBlock(
                    type=OrderBlockType.BULLISH,
                    index=j,
                    timestamp=self.df.index[j],
                    high=self.df['high'].iloc[j],
                    low=self.df['low'].iloc[j],
                    open_price=self.df['open'].iloc[j],
                    close_price=self.df['close'].iloc[j]
                )
        return None
    
    def _find_bullish_ob_before_impulse(self, impulse_idx: int) -> Optional[OrderBlock]:
        """Find the last bullish candle before a bearish impulse"""
        for j in range(impulse_idx - 1, max(impulse_idx - self.lookback, 0), -1):
            if self._is_bullish_candle(j):
                return OrderBlock(
                    type=OrderBlockType.BEARISH,
                    index=j,
                    timestamp=self.df.index[j],
                    high=self.df['high'].iloc[j],
                    low=self.df['low'].iloc[j],
                    open_price=self.df['open'].iloc[j],
                    close_price=self.df['close'].iloc[j]
                )
        return None
    
    def _calculate_ob_strength(self, ob: OrderBlock, impulse: float, atr: float) -> float:
        """Calculate the strength of an order block (0-1)"""
        body_size = abs(ob.close_price - ob.open_price)
        ob_range = ob.high - ob.low
        
        body_ratio = body_size / ob_range if ob_range > 0 else 0
        impulse_ratio = min(impulse / (atr * 3), 1.0)
        
        strength = (body_ratio * 0.4) + (impulse_ratio * 0.6)
        return min(strength, 1.0)
    
    def _update_ob_status(self):
        """Update the status of all order blocks based on price action"""
        for ob in self.order_blocks:
            for i in range(ob.index + 1, len(self.df)):
                price_low = self.df['low'].iloc[i]
                price_high = self.df['high'].iloc[i]
                price_close = self.df['close'].iloc[i]
                
                if ob.type == OrderBlockType.BULLISH:
                    # Price enters the OB zone
                    if price_low <= ob.high and price_low >= ob.low:
                        if ob.status == OrderBlockStatus.FRESH:
                            ob.status = OrderBlockStatus.TESTED
                            ob.tested_count += 1
                    
                    # Price closes below OB low = mitigated
                    if price_close < ob.low:
                        ob.status = OrderBlockStatus.MITIGATED
                        break
                
                elif ob.type == OrderBlockType.BEARISH:
                    # Price enters the OB zone
                    if price_high >= ob.low and price_high <= ob.high:
                        if ob.status == OrderBlockStatus.FRESH:
                            ob.status = OrderBlockStatus.TESTED
                            ob.tested_count += 1
                    
                    # Price closes above OB high = mitigated
                    if price_close > ob.high:
                        ob.status = OrderBlockStatus.MITIGATED
                        break
    
    def get_active_order_blocks(self) -> List[OrderBlock]:
        """
        Get order blocks that are still active (not mitigated)
        
        Returns:
            List of active order blocks
        """
        if not self.order_blocks:
            self.identify_order_blocks()
        
        return [ob for ob in self.order_blocks 
                if ob.status in [OrderBlockStatus.FRESH, OrderBlockStatus.TESTED]]
    
    def get_nearest_bullish_ob(self, current_price: float) -> Optional[OrderBlock]:
        """
        Get the nearest bullish OB below current price
        
        Args:
            current_price: Current market price
            
        Returns:
            Nearest bullish order block or None
        """
        active_obs = self.get_active_order_blocks()
        bullish_obs = [ob for ob in active_obs 
                      if ob.type == OrderBlockType.BULLISH and ob.high < current_price]
        
        if bullish_obs:
            return max(bullish_obs, key=lambda x: x.high)
        return None
    
    def get_nearest_bearish_ob(self, current_price: float) -> Optional[OrderBlock]:
        """
        Get the nearest bearish OB above current price
        
        Args:
            current_price: Current market price
            
        Returns:
            Nearest bearish order block or None
        """
        active_obs = self.get_active_order_blocks()
        bearish_obs = [ob for ob in active_obs 
                      if ob.type == OrderBlockType.BEARISH and ob.low > current_price]
        
        if bearish_obs:
            return min(bearish_obs, key=lambda x: x.low)
        return None
    
    def check_price_at_ob(self, price: float, tolerance: float = 0.001) -> Optional[OrderBlock]:
        """
        Check if price is at an order block
        
        Args:
            price: Price to check
            tolerance: Price tolerance (percentage)
            
        Returns:
            Order block if price is at one, None otherwise
        """
        active_obs = self.get_active_order_blocks()
        
        for ob in active_obs:
            ob_mid = (ob.high + ob.low) / 2
            ob_range = ob.high - ob.low
            extended_high = ob.high + (ob_range * tolerance)
            extended_low = ob.low - (ob_range * tolerance)
            
            if extended_low <= price <= extended_high:
                return ob
        
        return None
    
    def get_ob_zones_for_chart(self) -> List[Dict]:
        """
        Get order block zones formatted for charting
        
        Returns:
            List of dictionaries with OB zone data
        """
        zones = []
        
        for ob in self.order_blocks:
            color = 'green' if ob.type == OrderBlockType.BULLISH else 'red'
            opacity = 0.3 if ob.status == OrderBlockStatus.MITIGATED else 0.6
            
            zones.append({
                'type': ob.type.value,
                'start_idx': ob.index,
                'start_time': ob.timestamp,
                'high': ob.high,
                'low': ob.low,
                'status': ob.status.value,
                'strength': ob.strength,
                'color': color,
                'opacity': opacity
            })
        
        return zones
    
    def analyze(self) -> Dict:
        """
        Perform complete order block analysis
        
        Returns:
            Dictionary with OB analysis results
        """
        if not self.order_blocks:
            self.identify_order_blocks()
        
        current_price = self.df['close'].iloc[-1]
        active_obs = self.get_active_order_blocks()
        
        bullish_obs = [ob for ob in active_obs if ob.type == OrderBlockType.BULLISH]
        bearish_obs = [ob for ob in active_obs if ob.type == OrderBlockType.BEARISH]
        
        return {
            'total_obs': len(self.order_blocks),
            'active_obs': len(active_obs),
            'bullish_obs': len(bullish_obs),
            'bearish_obs': len(bearish_obs),
            'nearest_bullish': self.get_nearest_bullish_ob(current_price),
            'nearest_bearish': self.get_nearest_bearish_ob(current_price),
            'price_at_ob': self.check_price_at_ob(current_price),
            'all_active_obs': active_obs
        }

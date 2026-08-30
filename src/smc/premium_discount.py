"""
Premium/Discount Zone Analysis Module
Identifies optimal entry zones based on Fibonacci and price range
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
from enum import Enum


class ZoneType(Enum):
    DEEP_DISCOUNT = "DEEP_DISCOUNT"  # 0-25%
    DISCOUNT = "DISCOUNT"  # 25-50%
    EQUILIBRIUM = "EQUILIBRIUM"  # 50%
    PREMIUM = "PREMIUM"  # 50-75%
    DEEP_PREMIUM = "DEEP_PREMIUM"  # 75-100%


@dataclass
class OTEZone:
    """Represents an Optimal Trade Entry zone"""
    swing_high: float
    swing_low: float
    ote_top: float  # 61.8% level
    ote_bottom: float  # 78.6% level
    optimal_entry: float  # 70.5% level
    direction: str  # 'BULLISH' or 'BEARISH'


class PremiumDiscountAnalyzer:
    """Analyzes premium/discount zones and OTE levels"""
    
    def __init__(self, df: pd.DataFrame, lookback: int = 50):
        """
        Initialize Premium/Discount analyzer
        
        Args:
            df: DataFrame with OHLCV data
            lookback: Number of bars for range calculation
        """
        self.df = df.copy()
        self.lookback = lookback
        
    def calculate_range(self) -> Tuple[float, float]:
        """
        Calculate the current swing range
        
        Returns:
            Tuple of (swing_high, swing_low)
        """
        recent_data = self.df.tail(self.lookback)
        swing_high = recent_data['high'].max()
        swing_low = recent_data['low'].min()
        
        return swing_high, swing_low
    
    def get_current_position(self) -> Tuple[float, ZoneType]:
        """
        Get current price position within the range
        
        Returns:
            Tuple of (position_percentage, zone_type)
        """
        swing_high, swing_low = self.calculate_range()
        current_price = self.df['close'].iloc[-1]
        
        range_size = swing_high - swing_low
        if range_size == 0:
            return 0.5, ZoneType.EQUILIBRIUM
        
        position = (current_price - swing_low) / range_size
        
        if position <= 0.25:
            zone = ZoneType.DEEP_DISCOUNT
        elif position <= 0.50:
            zone = ZoneType.DISCOUNT
        elif position <= 0.75:
            zone = ZoneType.PREMIUM
        else:
            zone = ZoneType.DEEP_PREMIUM
        
        return position, zone
    
    def calculate_fibonacci_levels(self) -> Dict[str, float]:
        """
        Calculate Fibonacci retracement levels
        
        Returns:
            Dictionary of Fibonacci levels
        """
        swing_high, swing_low = self.calculate_range()
        range_size = swing_high - swing_low
        
        fib_levels = {
            '0.0': swing_low,
            '0.236': swing_low + (range_size * 0.236),
            '0.382': swing_low + (range_size * 0.382),
            '0.5': swing_low + (range_size * 0.5),
            '0.618': swing_low + (range_size * 0.618),
            '0.705': swing_low + (range_size * 0.705),
            '0.786': swing_low + (range_size * 0.786),
            '1.0': swing_high,
            '-0.272': swing_low - (range_size * 0.272),
            '-0.618': swing_low - (range_size * 0.618),
            '1.272': swing_high + (range_size * 0.272),
            '1.618': swing_high + (range_size * 0.618),
        }
        
        return fib_levels
    
    def get_ote_zone(self, direction: str = 'auto') -> Optional[OTEZone]:
        """
        Get Optimal Trade Entry zone (61.8% - 78.6%)
        
        Args:
            direction: 'BULLISH', 'BEARISH', or 'auto'
            
        Returns:
            OTE zone or None
        """
        swing_high, swing_low = self.calculate_range()
        range_size = swing_high - swing_low
        
        if range_size == 0:
            return None
        
        current_price = self.df['close'].iloc[-1]
        position, zone = self.get_current_position()
        
        if direction == 'auto':
            if zone in [ZoneType.DISCOUNT, ZoneType.DEEP_DISCOUNT]:
                direction = 'BULLISH'
            else:
                direction = 'BEARISH'
        
        if direction == 'BULLISH':
            return OTEZone(
                swing_high=swing_high,
                swing_low=swing_low,
                ote_top=swing_low + (range_size * 0.382),
                ote_bottom=swing_low + (range_size * 0.214),
                optimal_entry=swing_low + (range_size * 0.295),
                direction='BULLISH'
            )
        else:
            return OTEZone(
                swing_high=swing_high,
                swing_low=swing_low,
                ote_top=swing_low + (range_size * 0.786),
                ote_bottom=swing_low + (range_size * 0.618),
                optimal_entry=swing_low + (range_size * 0.705),
                direction='BEARISH'
            )
    
    def check_price_in_ote(self, price: Optional[float] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if price is in OTE zone
        
        Args:
            price: Price to check (uses current price if None)
            
        Returns:
            Tuple of (is_in_ote, direction)
        """
        if price is None:
            price = self.df['close'].iloc[-1]
        
        bullish_ote = self.get_ote_zone('BULLISH')
        bearish_ote = self.get_ote_zone('BEARISH')
        
        if bullish_ote and bullish_ote.ote_bottom <= price <= bullish_ote.ote_top:
            return True, 'BULLISH'
        
        if bearish_ote and bearish_ote.ote_bottom <= price <= bearish_ote.ote_top:
            return True, 'BEARISH'
        
        return False, None
    
    def get_discount_zone(self) -> Tuple[float, float]:
        """
        Get the discount zone (0-50% of range)
        
        Returns:
            Tuple of (discount_top, discount_bottom)
        """
        swing_high, swing_low = self.calculate_range()
        equilibrium = (swing_high + swing_low) / 2
        
        return equilibrium, swing_low
    
    def get_premium_zone(self) -> Tuple[float, float]:
        """
        Get the premium zone (50-100% of range)
        
        Returns:
            Tuple of (premium_top, premium_bottom)
        """
        swing_high, swing_low = self.calculate_range()
        equilibrium = (swing_high + swing_low) / 2
        
        return swing_high, equilibrium
    
    def add_zones_to_dataframe(self) -> pd.DataFrame:
        """
        Add premium/discount zones to the dataframe
        
        Returns:
            DataFrame with zone indicators
        """
        swing_high = self.df['high'].rolling(window=self.lookback).max()
        swing_low = self.df['low'].rolling(window=self.lookback).min()
        
        range_size = swing_high - swing_low
        position = (self.df['close'] - swing_low) / range_size
        
        self.df['pd_position'] = position
        self.df['pd_zone'] = pd.cut(
            position,
            bins=[-np.inf, 0.25, 0.5, 0.75, np.inf],
            labels=['DEEP_DISCOUNT', 'DISCOUNT', 'PREMIUM', 'DEEP_PREMIUM']
        )
        self.df['equilibrium'] = (swing_high + swing_low) / 2
        self.df['range_high'] = swing_high
        self.df['range_low'] = swing_low
        
        return self.df
    
    def get_trading_bias(self) -> Dict:
        """
        Get trading bias based on current zone
        
        Returns:
            Dictionary with trading bias information
        """
        position, zone = self.get_current_position()
        current_price = self.df['close'].iloc[-1]
        swing_high, swing_low = self.calculate_range()
        
        if zone == ZoneType.DEEP_DISCOUNT:
            bias = 'STRONG_BUY'
            recommendation = 'Price in deep discount - look for bullish confirmation'
        elif zone == ZoneType.DISCOUNT:
            bias = 'BUY'
            recommendation = 'Price in discount zone - favorable for longs'
        elif zone == ZoneType.PREMIUM:
            bias = 'SELL'
            recommendation = 'Price in premium zone - favorable for shorts'
        elif zone == ZoneType.DEEP_PREMIUM:
            bias = 'STRONG_SELL'
            recommendation = 'Price in deep premium - look for bearish confirmation'
        else:
            bias = 'NEUTRAL'
            recommendation = 'Price at equilibrium - wait for direction'
        
        return {
            'bias': bias,
            'zone': zone.value,
            'position_pct': position * 100,
            'current_price': current_price,
            'swing_high': swing_high,
            'swing_low': swing_low,
            'equilibrium': (swing_high + swing_low) / 2,
            'recommendation': recommendation
        }
    
    def get_zones_for_chart(self) -> List[Dict]:
        """
        Get zones formatted for charting
        
        Returns:
            List of dictionaries with zone data
        """
        swing_high, swing_low = self.calculate_range()
        fib_levels = self.calculate_fibonacci_levels()
        equilibrium = (swing_high + swing_low) / 2
        
        zones = [
            {
                'name': 'Deep Premium',
                'top': swing_high,
                'bottom': swing_low + ((swing_high - swing_low) * 0.75),
                'color': 'rgba(255, 0, 0, 0.1)',
                'bias': 'SELL'
            },
            {
                'name': 'Premium',
                'top': swing_low + ((swing_high - swing_low) * 0.75),
                'bottom': equilibrium,
                'color': 'rgba(255, 165, 0, 0.1)',
                'bias': 'SELL'
            },
            {
                'name': 'Discount',
                'top': equilibrium,
                'bottom': swing_low + ((swing_high - swing_low) * 0.25),
                'color': 'rgba(144, 238, 144, 0.1)',
                'bias': 'BUY'
            },
            {
                'name': 'Deep Discount',
                'top': swing_low + ((swing_high - swing_low) * 0.25),
                'bottom': swing_low,
                'color': 'rgba(0, 255, 0, 0.1)',
                'bias': 'BUY'
            }
        ]
        
        fib_lines = [
            {'name': 'High (0%)', 'level': swing_high, 'color': 'red'},
            {'name': 'Fib 23.6%', 'level': fib_levels['0.786'], 'color': 'orange'},
            {'name': 'Fib 38.2%', 'level': fib_levels['0.618'], 'color': 'orange'},
            {'name': 'Equilibrium (50%)', 'level': equilibrium, 'color': 'gray'},
            {'name': 'Fib 61.8%', 'level': fib_levels['0.382'], 'color': 'green'},
            {'name': 'OTE (70.5%)', 'level': fib_levels['0.705'], 'color': 'blue'},
            {'name': 'Fib 78.6%', 'level': fib_levels['0.786'], 'color': 'green'},
            {'name': 'Low (100%)', 'level': swing_low, 'color': 'green'},
        ]
        
        return {
            'zones': zones,
            'fib_lines': fib_lines
        }
    
    def analyze(self) -> Dict:
        """
        Perform complete premium/discount analysis
        
        Returns:
            Dictionary with analysis results
        """
        position, zone = self.get_current_position()
        swing_high, swing_low = self.calculate_range()
        fib_levels = self.calculate_fibonacci_levels()
        trading_bias = self.get_trading_bias()
        is_in_ote, ote_direction = self.check_price_in_ote()
        
        bullish_ote = self.get_ote_zone('BULLISH')
        bearish_ote = self.get_ote_zone('BEARISH')
        
        return {
            'current_zone': zone.value,
            'position_percentage': position * 100,
            'swing_high': swing_high,
            'swing_low': swing_low,
            'range': swing_high - swing_low,
            'equilibrium': (swing_high + swing_low) / 2,
            'fib_levels': fib_levels,
            'trading_bias': trading_bias,
            'is_in_ote': is_in_ote,
            'ote_direction': ote_direction,
            'bullish_ote': bullish_ote,
            'bearish_ote': bearish_ote
        }

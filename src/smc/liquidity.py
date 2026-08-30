"""
Liquidity Analysis Module
Identifies liquidity pools, equal highs/lows, and liquidity sweeps
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class LiquidityType(Enum):
    BSL = "BUY_SIDE_LIQUIDITY"  # Above price - stop losses from shorts
    SSL = "SELL_SIDE_LIQUIDITY"  # Below price - stop losses from longs


class SweepType(Enum):
    BSL_SWEEP = "BSL_SWEEP"  # Swept buy-side liquidity
    SSL_SWEEP = "SSL_SWEEP"  # Swept sell-side liquidity


@dataclass
class LiquidityZone:
    """Represents a liquidity zone"""
    type: LiquidityType
    level: float
    strength: int  # Number of touches
    indices: List[int]  # Indices of touches
    timestamps: List[pd.Timestamp]
    swept: bool = False
    sweep_index: Optional[int] = None


@dataclass
class LiquiditySweep:
    """Represents a liquidity sweep event"""
    type: SweepType
    index: int
    timestamp: pd.Timestamp
    level: float
    wick_high: float
    wick_low: float
    close: float
    signal: str  # 'BUY' or 'SELL'


class LiquidityAnalyzer:
    """Analyzes liquidity in the market"""
    
    def __init__(self, df: pd.DataFrame, tolerance: float = 0.001,
                 min_touches: int = 2, lookback: int = 50):
        """
        Initialize Liquidity analyzer
        
        Args:
            df: DataFrame with OHLCV data
            tolerance: Price tolerance for equal levels (percentage)
            min_touches: Minimum touches to form a liquidity zone
            lookback: Number of bars to look back for analysis
        """
        self.df = df.copy()
        self.tolerance = tolerance
        self.min_touches = min_touches
        self.lookback = lookback
        self.liquidity_zones: List[LiquidityZone] = []
        self.sweeps: List[LiquiditySweep] = []
    
    def identify_equal_highs(self) -> List[LiquidityZone]:
        """
        Identify equal highs (buy-side liquidity)
        Equal highs represent stop losses above the market
        
        Returns:
            List of BSL zones
        """
        bsl_zones = []
        processed_highs = set()
        
        for i in range(len(self.df)):
            if i in processed_highs:
                continue
            
            high_i = self.df['high'].iloc[i]
            matching_indices = [i]
            matching_timestamps = [self.df.index[i]]
            
            for j in range(i + 1, min(i + self.lookback, len(self.df))):
                if j in processed_highs:
                    continue
                
                high_j = self.df['high'].iloc[j]
                
                if abs(high_i - high_j) / high_i <= self.tolerance:
                    matching_indices.append(j)
                    matching_timestamps.append(self.df.index[j])
                    processed_highs.add(j)
            
            if len(matching_indices) >= self.min_touches:
                avg_level = np.mean([self.df['high'].iloc[idx] for idx in matching_indices])
                
                bsl_zones.append(LiquidityZone(
                    type=LiquidityType.BSL,
                    level=avg_level,
                    strength=len(matching_indices),
                    indices=matching_indices,
                    timestamps=matching_timestamps
                ))
                
                processed_highs.add(i)
        
        return bsl_zones
    
    def identify_equal_lows(self) -> List[LiquidityZone]:
        """
        Identify equal lows (sell-side liquidity)
        Equal lows represent stop losses below the market
        
        Returns:
            List of SSL zones
        """
        ssl_zones = []
        processed_lows = set()
        
        for i in range(len(self.df)):
            if i in processed_lows:
                continue
            
            low_i = self.df['low'].iloc[i]
            matching_indices = [i]
            matching_timestamps = [self.df.index[i]]
            
            for j in range(i + 1, min(i + self.lookback, len(self.df))):
                if j in processed_lows:
                    continue
                
                low_j = self.df['low'].iloc[j]
                
                if abs(low_i - low_j) / low_i <= self.tolerance:
                    matching_indices.append(j)
                    matching_timestamps.append(self.df.index[j])
                    processed_lows.add(j)
            
            if len(matching_indices) >= self.min_touches:
                avg_level = np.mean([self.df['low'].iloc[idx] for idx in matching_indices])
                
                ssl_zones.append(LiquidityZone(
                    type=LiquidityType.SSL,
                    level=avg_level,
                    strength=len(matching_indices),
                    indices=matching_indices,
                    timestamps=matching_timestamps
                ))
                
                processed_lows.add(i)
        
        return ssl_zones
    
    def identify_liquidity_zones(self) -> List[LiquidityZone]:
        """
        Identify all liquidity zones (BSL and SSL)
        
        Returns:
            List of all liquidity zones
        """
        bsl_zones = self.identify_equal_highs()
        ssl_zones = self.identify_equal_lows()
        
        self.liquidity_zones = bsl_zones + ssl_zones
        self._check_for_sweeps()
        
        return self.liquidity_zones
    
    def _check_for_sweeps(self):
        """Check if any liquidity zones have been swept"""
        for zone in self.liquidity_zones:
            last_touch_idx = max(zone.indices)
            
            for i in range(last_touch_idx + 1, len(self.df)):
                if zone.type == LiquidityType.BSL:
                    # BSL is swept when price goes above and closes below
                    if self.df['high'].iloc[i] > zone.level:
                        zone.swept = True
                        zone.sweep_index = i
                        break
                
                elif zone.type == LiquidityType.SSL:
                    # SSL is swept when price goes below and closes above
                    if self.df['low'].iloc[i] < zone.level:
                        zone.swept = True
                        zone.sweep_index = i
                        break
    
    def detect_liquidity_sweeps(self, wick_threshold: float = 0.3) -> List[LiquiditySweep]:
        """
        Detect liquidity sweep events with reversal signals
        
        Args:
            wick_threshold: Minimum wick size as percentage of candle range
            
        Returns:
            List of liquidity sweep events
        """
        if not self.liquidity_zones:
            self.identify_liquidity_zones()
        
        self.sweeps = []
        
        for zone in self.liquidity_zones:
            if not zone.swept or zone.sweep_index is None:
                continue
            
            i = zone.sweep_index
            candle_range = self.df['high'].iloc[i] - self.df['low'].iloc[i]
            
            if candle_range == 0:
                continue
            
            if zone.type == LiquidityType.BSL:
                # Check for bearish rejection (sweep and close below)
                upper_wick = self.df['high'].iloc[i] - max(self.df['open'].iloc[i], 
                                                          self.df['close'].iloc[i])
                
                if upper_wick / candle_range >= wick_threshold:
                    if self.df['close'].iloc[i] < zone.level:
                        self.sweeps.append(LiquiditySweep(
                            type=SweepType.BSL_SWEEP,
                            index=i,
                            timestamp=self.df.index[i],
                            level=zone.level,
                            wick_high=self.df['high'].iloc[i],
                            wick_low=self.df['low'].iloc[i],
                            close=self.df['close'].iloc[i],
                            signal='SELL'
                        ))
            
            elif zone.type == LiquidityType.SSL:
                # Check for bullish rejection (sweep and close above)
                lower_wick = min(self.df['open'].iloc[i], 
                                self.df['close'].iloc[i]) - self.df['low'].iloc[i]
                
                if lower_wick / candle_range >= wick_threshold:
                    if self.df['close'].iloc[i] > zone.level:
                        self.sweeps.append(LiquiditySweep(
                            type=SweepType.SSL_SWEEP,
                            index=i,
                            timestamp=self.df.index[i],
                            level=zone.level,
                            wick_high=self.df['high'].iloc[i],
                            wick_low=self.df['low'].iloc[i],
                            close=self.df['close'].iloc[i],
                            signal='BUY'
                        ))
        
        return self.sweeps
    
    def get_unswept_liquidity(self) -> List[LiquidityZone]:
        """
        Get liquidity zones that have not been swept
        
        Returns:
            List of unswept liquidity zones
        """
        if not self.liquidity_zones:
            self.identify_liquidity_zones()
        
        return [zone for zone in self.liquidity_zones if not zone.swept]
    
    def get_nearest_bsl(self, current_price: float) -> Optional[LiquidityZone]:
        """
        Get the nearest buy-side liquidity above current price
        
        Args:
            current_price: Current market price
            
        Returns:
            Nearest BSL zone or None
        """
        unswept = self.get_unswept_liquidity()
        bsl_zones = [zone for zone in unswept 
                    if zone.type == LiquidityType.BSL and zone.level > current_price]
        
        if bsl_zones:
            return min(bsl_zones, key=lambda x: x.level)
        return None
    
    def get_nearest_ssl(self, current_price: float) -> Optional[LiquidityZone]:
        """
        Get the nearest sell-side liquidity below current price
        
        Args:
            current_price: Current market price
            
        Returns:
            Nearest SSL zone or None
        """
        unswept = self.get_unswept_liquidity()
        ssl_zones = [zone for zone in unswept 
                    if zone.type == LiquidityType.SSL and zone.level < current_price]
        
        if ssl_zones:
            return max(ssl_zones, key=lambda x: x.level)
        return None
    
    def get_pdh_pdl(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Get Previous Day High and Low (important liquidity levels)
        
        Returns:
            Tuple of (PDH, PDL)
        """
        if len(self.df) < 2:
            return None, None
        
        df_daily = self.df.resample('D').agg({
            'high': 'max',
            'low': 'min'
        }).dropna()
        
        if len(df_daily) >= 2:
            pdh = df_daily['high'].iloc[-2]
            pdl = df_daily['low'].iloc[-2]
            return pdh, pdl
        
        return None, None
    
    def get_pwh_pwl(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Get Previous Week High and Low (important liquidity levels)
        
        Returns:
            Tuple of (PWH, PWL)
        """
        if len(self.df) < 2:
            return None, None
        
        df_weekly = self.df.resample('W').agg({
            'high': 'max',
            'low': 'min'
        }).dropna()
        
        if len(df_weekly) >= 2:
            pwh = df_weekly['high'].iloc[-2]
            pwl = df_weekly['low'].iloc[-2]
            return pwh, pwl
        
        return None, None
    
    def get_liquidity_levels_for_chart(self) -> List[Dict]:
        """
        Get liquidity levels formatted for charting
        
        Returns:
            List of dictionaries with liquidity level data
        """
        levels = []
        
        for zone in self.liquidity_zones:
            color = 'blue' if zone.type == LiquidityType.BSL else 'orange'
            style = 'dashed' if zone.swept else 'solid'
            
            levels.append({
                'type': zone.type.value,
                'level': zone.level,
                'strength': zone.strength,
                'swept': zone.swept,
                'indices': zone.indices,
                'color': color,
                'style': style
            })
        
        pdh, pdl = self.get_pdh_pdl()
        if pdh:
            levels.append({
                'type': 'PDH',
                'level': pdh,
                'strength': 0,
                'swept': False,
                'color': 'purple',
                'style': 'dotted'
            })
        if pdl:
            levels.append({
                'type': 'PDL',
                'level': pdl,
                'strength': 0,
                'swept': False,
                'color': 'purple',
                'style': 'dotted'
            })
        
        return levels
    
    def analyze(self) -> Dict:
        """
        Perform complete liquidity analysis
        
        Returns:
            Dictionary with liquidity analysis results
        """
        if not self.liquidity_zones:
            self.identify_liquidity_zones()
        
        sweeps = self.detect_liquidity_sweeps()
        current_price = self.df['close'].iloc[-1]
        unswept = self.get_unswept_liquidity()
        pdh, pdl = self.get_pdh_pdl()
        pwh, pwl = self.get_pwh_pwl()
        
        bsl_zones = [zone for zone in unswept if zone.type == LiquidityType.BSL]
        ssl_zones = [zone for zone in unswept if zone.type == LiquidityType.SSL]
        
        return {
            'total_zones': len(self.liquidity_zones),
            'unswept_zones': len(unswept),
            'bsl_zones': len(bsl_zones),
            'ssl_zones': len(ssl_zones),
            'total_sweeps': len(sweeps),
            'recent_sweeps': sweeps[-3:] if sweeps else [],
            'nearest_bsl': self.get_nearest_bsl(current_price),
            'nearest_ssl': self.get_nearest_ssl(current_price),
            'pdh': pdh,
            'pdl': pdl,
            'pwh': pwh,
            'pwl': pwl,
            'all_unswept_zones': unswept
        }

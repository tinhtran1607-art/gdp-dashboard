"""
Fair Value Gaps (FVG) Detection Module
Identifies imbalances in price action where institutional orders create gaps
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class FVGType(Enum):
    BULLISH = "BULLISH_FVG"
    BEARISH = "BEARISH_FVG"


class FVGStatus(Enum):
    FRESH = "FRESH"  # Not yet filled
    PARTIALLY_FILLED = "PARTIALLY_FILLED"  # Partially filled
    FILLED = "FILLED"  # Completely filled


@dataclass
class FairValueGap:
    """Represents a Fair Value Gap"""
    type: FVGType
    index: int  # Index of the middle candle
    timestamp: pd.Timestamp
    top: float  # Top of the gap
    bottom: float  # Bottom of the gap
    size: float  # Size of the gap
    status: FVGStatus = FVGStatus.FRESH
    fill_percentage: float = 0.0
    candle1_idx: int = 0
    candle3_idx: int = 0


class FVGDetector:
    """Detects and manages Fair Value Gaps"""
    
    def __init__(self, df: pd.DataFrame, min_gap_atr: float = 0.3, 
                 atr_period: int = 14):
        """
        Initialize FVG detector
        
        Args:
            df: DataFrame with OHLCV data
            min_gap_atr: Minimum gap size in ATR units
            atr_period: Period for ATR calculation
        """
        self.df = df.copy()
        self.min_gap_atr = min_gap_atr
        self.atr_period = atr_period
        self.fvg_list: List[FairValueGap] = []
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
    
    def identify_fvg(self) -> List[FairValueGap]:
        """
        Identify all Fair Value Gaps in the data
        
        FVG is created when there's a gap between:
        - Bullish FVG: Low of candle 1 > High of candle 3
        - Bearish FVG: High of candle 1 < Low of candle 3
        
        Returns:
            List of identified FVGs
        """
        self.fvg_list = []
        
        for i in range(2, len(self.df)):
            atr = self.df['atr'].iloc[i]
            if pd.isna(atr) or atr == 0:
                continue
            
            candle1_low = self.df['low'].iloc[i-2]
            candle1_high = self.df['high'].iloc[i-2]
            candle3_low = self.df['low'].iloc[i]
            candle3_high = self.df['high'].iloc[i]
            
            # Bullish FVG: Gap up
            # Low of candle 1 is higher than high of candle 3
            if candle1_low > candle3_high:
                gap_size = candle1_low - candle3_high
                
                if gap_size >= atr * self.min_gap_atr:
                    self.fvg_list.append(FairValueGap(
                        type=FVGType.BULLISH,
                        index=i-1,
                        timestamp=self.df.index[i-1],
                        top=candle1_low,
                        bottom=candle3_high,
                        size=gap_size,
                        candle1_idx=i-2,
                        candle3_idx=i
                    ))
            
            # Bearish FVG: Gap down
            # High of candle 1 is lower than low of candle 3
            if candle1_high < candle3_low:
                gap_size = candle3_low - candle1_high
                
                if gap_size >= atr * self.min_gap_atr:
                    self.fvg_list.append(FairValueGap(
                        type=FVGType.BEARISH,
                        index=i-1,
                        timestamp=self.df.index[i-1],
                        top=candle3_low,
                        bottom=candle1_high,
                        size=gap_size,
                        candle1_idx=i-2,
                        candle3_idx=i
                    ))
        
        self._update_fvg_status()
        return self.fvg_list
    
    def _update_fvg_status(self):
        """Update the status of all FVGs based on price action"""
        for fvg in self.fvg_list:
            for i in range(fvg.candle3_idx + 1, len(self.df)):
                price_high = self.df['high'].iloc[i]
                price_low = self.df['low'].iloc[i]
                
                if fvg.type == FVGType.BULLISH:
                    # Check if price enters the FVG from above
                    if price_low <= fvg.top:
                        # Calculate fill percentage
                        if price_low <= fvg.bottom:
                            fvg.status = FVGStatus.FILLED
                            fvg.fill_percentage = 100.0
                            break
                        else:
                            filled = (fvg.top - price_low) / fvg.size * 100
                            fvg.fill_percentage = max(fvg.fill_percentage, filled)
                            if fvg.fill_percentage > 0:
                                fvg.status = FVGStatus.PARTIALLY_FILLED
                
                elif fvg.type == FVGType.BEARISH:
                    # Check if price enters the FVG from below
                    if price_high >= fvg.bottom:
                        # Calculate fill percentage
                        if price_high >= fvg.top:
                            fvg.status = FVGStatus.FILLED
                            fvg.fill_percentage = 100.0
                            break
                        else:
                            filled = (price_high - fvg.bottom) / fvg.size * 100
                            fvg.fill_percentage = max(fvg.fill_percentage, filled)
                            if fvg.fill_percentage > 0:
                                fvg.status = FVGStatus.PARTIALLY_FILLED
    
    def get_unfilled_fvg(self) -> List[FairValueGap]:
        """
        Get FVGs that have not been completely filled
        
        Returns:
            List of unfilled FVGs
        """
        if not self.fvg_list:
            self.identify_fvg()
        
        return [fvg for fvg in self.fvg_list 
                if fvg.status in [FVGStatus.FRESH, FVGStatus.PARTIALLY_FILLED]]
    
    def get_fresh_fvg(self) -> List[FairValueGap]:
        """
        Get FVGs that have not been touched at all
        
        Returns:
            List of fresh FVGs
        """
        if not self.fvg_list:
            self.identify_fvg()
        
        return [fvg for fvg in self.fvg_list if fvg.status == FVGStatus.FRESH]
    
    def get_nearest_bullish_fvg(self, current_price: float) -> Optional[FairValueGap]:
        """
        Get the nearest bullish FVG below current price
        
        Args:
            current_price: Current market price
            
        Returns:
            Nearest bullish FVG or None
        """
        unfilled = self.get_unfilled_fvg()
        bullish_fvgs = [fvg for fvg in unfilled 
                       if fvg.type == FVGType.BULLISH and fvg.top < current_price]
        
        if bullish_fvgs:
            return max(bullish_fvgs, key=lambda x: x.top)
        return None
    
    def get_nearest_bearish_fvg(self, current_price: float) -> Optional[FairValueGap]:
        """
        Get the nearest bearish FVG above current price
        
        Args:
            current_price: Current market price
            
        Returns:
            Nearest bearish FVG or None
        """
        unfilled = self.get_unfilled_fvg()
        bearish_fvgs = [fvg for fvg in unfilled 
                       if fvg.type == FVGType.BEARISH and fvg.bottom > current_price]
        
        if bearish_fvgs:
            return min(bearish_fvgs, key=lambda x: x.bottom)
        return None
    
    def check_price_in_fvg(self, price: float) -> Optional[FairValueGap]:
        """
        Check if price is currently inside an FVG
        
        Args:
            price: Price to check
            
        Returns:
            FVG if price is inside one, None otherwise
        """
        unfilled = self.get_unfilled_fvg()
        
        for fvg in unfilled:
            if fvg.bottom <= price <= fvg.top:
                return fvg
        
        return None
    
    def get_consequent_encroachment(self, fvg: FairValueGap) -> float:
        """
        Calculate the consequent encroachment (CE) level - 50% of FVG
        This is often used as entry point
        
        Args:
            fvg: Fair Value Gap to calculate CE for
            
        Returns:
            CE price level
        """
        return (fvg.top + fvg.bottom) / 2
    
    def get_fvg_zones_for_chart(self) -> List[Dict]:
        """
        Get FVG zones formatted for charting
        
        Returns:
            List of dictionaries with FVG zone data
        """
        zones = []
        
        for fvg in self.fvg_list:
            if fvg.type == FVGType.BULLISH:
                color = 'rgba(0, 255, 0, 0.2)' if fvg.status != FVGStatus.FILLED else 'rgba(0, 255, 0, 0.1)'
            else:
                color = 'rgba(255, 0, 0, 0.2)' if fvg.status != FVGStatus.FILLED else 'rgba(255, 0, 0, 0.1)'
            
            zones.append({
                'type': fvg.type.value,
                'start_idx': fvg.candle1_idx,
                'middle_idx': fvg.index,
                'end_idx': fvg.candle3_idx,
                'start_time': fvg.timestamp,
                'top': fvg.top,
                'bottom': fvg.bottom,
                'ce_level': self.get_consequent_encroachment(fvg),
                'size': fvg.size,
                'status': fvg.status.value,
                'fill_percentage': fvg.fill_percentage,
                'color': color
            })
        
        return zones
    
    def analyze(self) -> Dict:
        """
        Perform complete FVG analysis
        
        Returns:
            Dictionary with FVG analysis results
        """
        if not self.fvg_list:
            self.identify_fvg()
        
        current_price = self.df['close'].iloc[-1]
        unfilled = self.get_unfilled_fvg()
        fresh = self.get_fresh_fvg()
        
        bullish_fvgs = [fvg for fvg in unfilled if fvg.type == FVGType.BULLISH]
        bearish_fvgs = [fvg for fvg in unfilled if fvg.type == FVGType.BEARISH]
        
        return {
            'total_fvgs': len(self.fvg_list),
            'unfilled_fvgs': len(unfilled),
            'fresh_fvgs': len(fresh),
            'bullish_fvgs': len(bullish_fvgs),
            'bearish_fvgs': len(bearish_fvgs),
            'nearest_bullish': self.get_nearest_bullish_fvg(current_price),
            'nearest_bearish': self.get_nearest_bearish_fvg(current_price),
            'price_in_fvg': self.check_price_in_fvg(current_price),
            'all_unfilled_fvgs': unfilled
        }

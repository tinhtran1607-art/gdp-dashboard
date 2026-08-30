"""
Market Structure Analysis Module
Identifies swing points, BOS, CHoCH, and overall market structure
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class TrendDirection(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    RANGING = "RANGING"


class StructureType(Enum):
    BOS = "BOS"  # Break of Structure
    CHOCH = "CHOCH"  # Change of Character
    HH = "HH"  # Higher High
    HL = "HL"  # Higher Low
    LH = "LH"  # Lower High
    LL = "LL"  # Lower Low


@dataclass
class SwingPoint:
    """Represents a swing high or swing low"""
    index: int
    price: float
    timestamp: pd.Timestamp
    type: str  # 'HIGH' or 'LOW'
    strength: int  # Number of bars confirming the swing


@dataclass
class StructureBreak:
    """Represents a structure break (BOS or CHoCH)"""
    index: int
    timestamp: pd.Timestamp
    type: StructureType
    direction: str  # 'BULLISH' or 'BEARISH'
    broken_level: float
    close_price: float
    previous_trend: Optional[str] = None


class MarketStructure:
    """Analyzes market structure using SMC concepts"""
    
    def __init__(self, df: pd.DataFrame, left_bars: int = 5, right_bars: int = 5):
        """
        Initialize Market Structure analyzer
        
        Args:
            df: DataFrame with OHLCV data
            left_bars: Number of bars to the left for swing point confirmation
            right_bars: Number of bars to the right for swing point confirmation
        """
        self.df = df.copy()
        self.left_bars = left_bars
        self.right_bars = right_bars
        self.swing_highs: List[SwingPoint] = []
        self.swing_lows: List[SwingPoint] = []
        self.structure_breaks: List[StructureBreak] = []
        self.current_trend = TrendDirection.RANGING
        
    def identify_swing_points(self) -> Tuple[List[SwingPoint], List[SwingPoint]]:
        """
        Identify swing highs and swing lows
        
        Returns:
            Tuple of (swing_highs, swing_lows)
        """
        self.swing_highs = []
        self.swing_lows = []
        
        for i in range(self.left_bars, len(self.df) - self.right_bars):
            # Check for swing high
            is_swing_high = True
            for j in range(1, self.left_bars + 1):
                if self.df['high'].iloc[i] <= self.df['high'].iloc[i - j]:
                    is_swing_high = False
                    break
            if is_swing_high:
                for j in range(1, self.right_bars + 1):
                    if self.df['high'].iloc[i] <= self.df['high'].iloc[i + j]:
                        is_swing_high = False
                        break
            
            if is_swing_high:
                strength = self._calculate_swing_strength(i, 'high')
                self.swing_highs.append(SwingPoint(
                    index=i,
                    price=self.df['high'].iloc[i],
                    timestamp=self.df.index[i],
                    type='HIGH',
                    strength=strength
                ))
            
            # Check for swing low
            is_swing_low = True
            for j in range(1, self.left_bars + 1):
                if self.df['low'].iloc[i] >= self.df['low'].iloc[i - j]:
                    is_swing_low = False
                    break
            if is_swing_low:
                for j in range(1, self.right_bars + 1):
                    if self.df['low'].iloc[i] >= self.df['low'].iloc[i + j]:
                        is_swing_low = False
                        break
            
            if is_swing_low:
                strength = self._calculate_swing_strength(i, 'low')
                self.swing_lows.append(SwingPoint(
                    index=i,
                    price=self.df['low'].iloc[i],
                    timestamp=self.df.index[i],
                    type='LOW',
                    strength=strength
                ))
        
        return self.swing_highs, self.swing_lows
    
    def _calculate_swing_strength(self, index: int, swing_type: str) -> int:
        """Calculate the strength of a swing point based on surrounding bars"""
        strength = 0
        lookback = min(20, index)
        lookforward = min(20, len(self.df) - index - 1)
        
        if swing_type == 'high':
            for i in range(1, lookback + 1):
                if self.df['high'].iloc[index] > self.df['high'].iloc[index - i]:
                    strength += 1
                else:
                    break
            for i in range(1, lookforward + 1):
                if self.df['high'].iloc[index] > self.df['high'].iloc[index + i]:
                    strength += 1
                else:
                    break
        else:
            for i in range(1, lookback + 1):
                if self.df['low'].iloc[index] < self.df['low'].iloc[index - i]:
                    strength += 1
                else:
                    break
            for i in range(1, lookforward + 1):
                if self.df['low'].iloc[index] < self.df['low'].iloc[index + i]:
                    strength += 1
                else:
                    break
        
        return strength
    
    def determine_trend(self) -> TrendDirection:
        """
        Determine the current market trend based on swing points
        
        Returns:
            Current trend direction
        """
        if not self.swing_highs or not self.swing_lows:
            self.identify_swing_points()
        
        if len(self.swing_highs) < 2 or len(self.swing_lows) < 2:
            return TrendDirection.RANGING
        
        recent_highs = sorted(self.swing_highs, key=lambda x: x.index)[-3:]
        recent_lows = sorted(self.swing_lows, key=lambda x: x.index)[-3:]
        
        hh_count = 0
        lh_count = 0
        hl_count = 0
        ll_count = 0
        
        for i in range(1, len(recent_highs)):
            if recent_highs[i].price > recent_highs[i-1].price:
                hh_count += 1
            else:
                lh_count += 1
        
        for i in range(1, len(recent_lows)):
            if recent_lows[i].price > recent_lows[i-1].price:
                hl_count += 1
            else:
                ll_count += 1
        
        if hh_count > lh_count and hl_count > ll_count:
            self.current_trend = TrendDirection.BULLISH
        elif lh_count > hh_count and ll_count > hl_count:
            self.current_trend = TrendDirection.BEARISH
        else:
            self.current_trend = TrendDirection.RANGING
        
        return self.current_trend
    
    def detect_bos(self) -> List[StructureBreak]:
        """
        Detect Break of Structure (BOS)
        BOS confirms trend continuation
        
        Returns:
            List of BOS events
        """
        if not self.swing_highs or not self.swing_lows:
            self.identify_swing_points()
        
        bos_list = []
        
        for i in range(len(self.df)):
            current_close = self.df['close'].iloc[i]
            
            # Bullish BOS - price breaks above recent swing high in uptrend
            recent_swing_highs = [sh for sh in self.swing_highs if sh.index < i]
            if recent_swing_highs:
                last_sh = max(recent_swing_highs, key=lambda x: x.index)
                
                if i > 0:
                    prev_close = self.df['close'].iloc[i-1]
                    if prev_close <= last_sh.price and current_close > last_sh.price:
                        bos_list.append(StructureBreak(
                            index=i,
                            timestamp=self.df.index[i],
                            type=StructureType.BOS,
                            direction='BULLISH',
                            broken_level=last_sh.price,
                            close_price=current_close
                        ))
            
            # Bearish BOS - price breaks below recent swing low in downtrend
            recent_swing_lows = [sl for sl in self.swing_lows if sl.index < i]
            if recent_swing_lows:
                last_sl = max(recent_swing_lows, key=lambda x: x.index)
                
                if i > 0:
                    prev_close = self.df['close'].iloc[i-1]
                    if prev_close >= last_sl.price and current_close < last_sl.price:
                        bos_list.append(StructureBreak(
                            index=i,
                            timestamp=self.df.index[i],
                            type=StructureType.BOS,
                            direction='BEARISH',
                            broken_level=last_sl.price,
                            close_price=current_close
                        ))
        
        return bos_list
    
    def detect_choch(self) -> List[StructureBreak]:
        """
        Detect Change of Character (CHoCH)
        CHoCH signals potential trend reversal
        
        Returns:
            List of CHoCH events
        """
        if not self.swing_highs or not self.swing_lows:
            self.identify_swing_points()
        
        self.determine_trend()
        choch_list = []
        
        all_swings = []
        for sh in self.swing_highs:
            all_swings.append(('HIGH', sh))
        for sl in self.swing_lows:
            all_swings.append(('LOW', sl))
        all_swings.sort(key=lambda x: x[1].index)
        
        local_trend = None
        last_hl = None
        last_lh = None
        
        for i, (swing_type, swing) in enumerate(all_swings):
            if i < 2:
                continue
            
            prev_same_type = None
            for j in range(i-1, -1, -1):
                if all_swings[j][0] == swing_type:
                    prev_same_type = all_swings[j][1]
                    break
            
            if prev_same_type:
                if swing_type == 'HIGH':
                    if swing.price > prev_same_type.price:
                        local_trend = 'BULLISH'
                    else:
                        local_trend = 'BEARISH'
                        last_lh = swing
                else:
                    if swing.price > prev_same_type.price:
                        local_trend = 'BULLISH'
                        last_hl = swing
                    else:
                        local_trend = 'BEARISH'
        
        for i in range(len(self.df)):
            current_close = self.df['close'].iloc[i]
            
            # Bullish CHoCH - break of LH in downtrend
            if local_trend == 'BEARISH' and last_lh:
                if current_close > last_lh.price:
                    choch_list.append(StructureBreak(
                        index=i,
                        timestamp=self.df.index[i],
                        type=StructureType.CHOCH,
                        direction='BULLISH',
                        broken_level=last_lh.price,
                        close_price=current_close,
                        previous_trend='BEARISH'
                    ))
                    last_lh = None
            
            # Bearish CHoCH - break of HL in uptrend
            if local_trend == 'BULLISH' and last_hl:
                if current_close < last_hl.price:
                    choch_list.append(StructureBreak(
                        index=i,
                        timestamp=self.df.index[i],
                        type=StructureType.CHOCH,
                        direction='BEARISH',
                        broken_level=last_hl.price,
                        close_price=current_close,
                        previous_trend='BULLISH'
                    ))
                    last_hl = None
        
        return choch_list
    
    def get_structure_labels(self) -> pd.DataFrame:
        """
        Add structure labels to the dataframe
        
        Returns:
            DataFrame with structure labels
        """
        if not self.swing_highs or not self.swing_lows:
            self.identify_swing_points()
        
        self.df['swing_high'] = None
        self.df['swing_low'] = None
        self.df['structure'] = None
        
        for sh in self.swing_highs:
            self.df.loc[self.df.index[sh.index], 'swing_high'] = sh.price
        
        for sl in self.swing_lows:
            self.df.loc[self.df.index[sl.index], 'swing_low'] = sl.price
        
        sorted_highs = sorted(self.swing_highs, key=lambda x: x.index)
        sorted_lows = sorted(self.swing_lows, key=lambda x: x.index)
        
        for i, sh in enumerate(sorted_highs):
            if i > 0:
                if sh.price > sorted_highs[i-1].price:
                    self.df.loc[self.df.index[sh.index], 'structure'] = 'HH'
                else:
                    self.df.loc[self.df.index[sh.index], 'structure'] = 'LH'
        
        for i, sl in enumerate(sorted_lows):
            if i > 0:
                if sl.price > sorted_lows[i-1].price:
                    self.df.loc[self.df.index[sl.index], 'structure'] = 'HL'
                else:
                    self.df.loc[self.df.index[sl.index], 'structure'] = 'LL'
        
        return self.df
    
    def analyze(self) -> Dict:
        """
        Perform complete market structure analysis
        
        Returns:
            Dictionary with all structure analysis results
        """
        self.identify_swing_points()
        trend = self.determine_trend()
        bos_list = self.detect_bos()
        choch_list = self.detect_choch()
        
        return {
            'trend': trend.value,
            'swing_highs': len(self.swing_highs),
            'swing_lows': len(self.swing_lows),
            'recent_swing_high': self.swing_highs[-1] if self.swing_highs else None,
            'recent_swing_low': self.swing_lows[-1] if self.swing_lows else None,
            'bos_count': len(bos_list),
            'choch_count': len(choch_list),
            'recent_bos': bos_list[-1] if bos_list else None,
            'recent_choch': choch_list[-1] if choch_list else None,
            'all_bos': bos_list,
            'all_choch': choch_list
        }

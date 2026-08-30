"""
SMC Signal Generator Module
Combines all SMC concepts to generate trading signals
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, time

from .market_structure import MarketStructure, TrendDirection, StructureType
from .order_blocks import OrderBlockDetector, OrderBlock, OrderBlockType
from .fair_value_gaps import FVGDetector, FairValueGap, FVGType
from .liquidity import LiquidityAnalyzer, LiquidityZone, LiquiditySweep
from .premium_discount import PremiumDiscountAnalyzer, ZoneType, OTEZone


class SMCSignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SMCSignalStrength(Enum):
    STRONG = "STRONG"  # 3+ confluences
    MODERATE = "MODERATE"  # 2 confluences
    WEAK = "WEAK"  # 1 confluence


class KillZone(Enum):
    ASIAN = "ASIAN"
    LONDON_OPEN = "LONDON_OPEN"
    NEW_YORK = "NEW_YORK"
    LONDON_CLOSE = "LONDON_CLOSE"
    OFF_HOURS = "OFF_HOURS"


@dataclass
class SMCSignal:
    """Represents an SMC trading signal"""
    type: SMCSignalType
    strength: SMCSignalStrength
    price: float
    timestamp: pd.Timestamp
    entry_zone: str
    stop_loss: float
    take_profit: float
    confidence: float
    confluences: List[str]
    kill_zone: KillZone
    risk_reward: float


class SMCSignalGenerator:
    """Generates trading signals based on SMC analysis"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize SMC Signal Generator
        
        Args:
            df: DataFrame with OHLCV data
        """
        self.df = df.copy()
        self.market_structure = MarketStructure(df)
        self.ob_detector = OrderBlockDetector(df)
        self.fvg_detector = FVGDetector(df)
        self.liquidity_analyzer = LiquidityAnalyzer(df)
        self.pd_analyzer = PremiumDiscountAnalyzer(df)
        
        self._analyze_all()
    
    def _analyze_all(self):
        """Run all SMC analyses"""
        self.ms_analysis = self.market_structure.analyze()
        self.ob_analysis = self.ob_detector.analyze()
        self.fvg_analysis = self.fvg_detector.analyze()
        self.liq_analysis = self.liquidity_analyzer.analyze()
        self.pd_analysis = self.pd_analyzer.analyze()
    
    def identify_kill_zone(self, timestamp: Optional[pd.Timestamp] = None) -> KillZone:
        """
        Identify the current kill zone (trading session)
        
        Args:
            timestamp: Timestamp to check (uses latest if None)
            
        Returns:
            Current kill zone
        """
        if timestamp is None:
            timestamp = self.df.index[-1]
        
        hour = timestamp.hour
        
        if 0 <= hour < 8:
            return KillZone.ASIAN
        elif 7 <= hour < 10:
            return KillZone.LONDON_OPEN
        elif 12 <= hour < 15:
            return KillZone.NEW_YORK
        elif 15 <= hour < 17:
            return KillZone.LONDON_CLOSE
        else:
            return KillZone.OFF_HOURS
    
    def _calculate_confluence_score(self, confluences: List[str]) -> Tuple[SMCSignalStrength, float]:
        """
        Calculate signal strength and confidence based on confluences
        
        Args:
            confluences: List of confluence factors
            
        Returns:
            Tuple of (strength, confidence)
        """
        num_confluences = len(confluences)
        
        weights = {
            'market_structure': 0.20,
            'order_block': 0.15,
            'fvg': 0.15,
            'liquidity_sweep': 0.15,
            'premium_discount': 0.15,
            'ote_zone': 0.10,
            'kill_zone': 0.10
        }
        
        confidence = 0.0
        for conf in confluences:
            for key, weight in weights.items():
                if key in conf.lower():
                    confidence += weight
        
        confidence = min(confidence, 1.0)
        
        if num_confluences >= 4:
            strength = SMCSignalStrength.STRONG
        elif num_confluences >= 2:
            strength = SMCSignalStrength.MODERATE
        else:
            strength = SMCSignalStrength.WEAK
        
        return strength, confidence
    
    def generate_buy_signal(self) -> Optional[SMCSignal]:
        """
        Generate a buy signal based on SMC analysis
        
        Returns:
            Buy signal or None if conditions not met
        """
        current_price = self.df['close'].iloc[-1]
        current_time = self.df.index[-1]
        confluences = []
        entry_zone = None
        stop_loss = None
        take_profit = None
        
        # Check market structure
        if self.ms_analysis['trend'] == 'BULLISH':
            confluences.append('market_structure_bullish')
        
        recent_choch = self.ms_analysis.get('recent_choch')
        if recent_choch and recent_choch.direction == 'BULLISH':
            confluences.append('bullish_choch')
        
        # Check order blocks
        nearest_bullish_ob = self.ob_analysis.get('nearest_bullish')
        price_at_ob = self.ob_analysis.get('price_at_ob')
        
        if price_at_ob and price_at_ob.type == OrderBlockType.BULLISH:
            confluences.append('price_at_order_block')
            entry_zone = 'Bullish Order Block'
            stop_loss = price_at_ob.low - (price_at_ob.high - price_at_ob.low) * 0.5
        
        # Check FVG
        price_in_fvg = self.fvg_analysis.get('price_in_fvg')
        nearest_bullish_fvg = self.fvg_analysis.get('nearest_bullish')
        
        if price_in_fvg and price_in_fvg.type == FVGType.BULLISH:
            confluences.append('price_in_fvg')
            if not entry_zone:
                entry_zone = 'Bullish FVG'
        
        # Check liquidity
        recent_sweeps = self.liq_analysis.get('recent_sweeps', [])
        for sweep in recent_sweeps:
            if sweep.signal == 'BUY':
                confluences.append('liquidity_sweep_buy')
                break
        
        # Check premium/discount
        current_zone = self.pd_analysis.get('current_zone')
        if current_zone in ['DEEP_DISCOUNT', 'DISCOUNT']:
            confluences.append('price_in_discount')
        
        # Check OTE
        is_in_ote = self.pd_analysis.get('is_in_ote')
        ote_direction = self.pd_analysis.get('ote_direction')
        if is_in_ote and ote_direction == 'BULLISH':
            confluences.append('price_in_ote_zone')
        
        # Check kill zone
        kill_zone = self.identify_kill_zone(current_time)
        if kill_zone in [KillZone.LONDON_OPEN, KillZone.NEW_YORK]:
            confluences.append('active_kill_zone')
        
        if len(confluences) < 2:
            return None
        
        # Calculate SL and TP
        if not stop_loss:
            nearest_ssl = self.liq_analysis.get('nearest_ssl')
            if nearest_ssl:
                stop_loss = nearest_ssl.level - (current_price * 0.001)
            else:
                atr = self._calculate_atr()
                stop_loss = current_price - (atr * 2)
        
        nearest_bsl = self.liq_analysis.get('nearest_bsl')
        if nearest_bsl:
            take_profit = nearest_bsl.level
        else:
            risk = current_price - stop_loss
            take_profit = current_price + (risk * 2)
        
        if not entry_zone:
            entry_zone = 'Discount Zone'
        
        strength, confidence = self._calculate_confluence_score(confluences)
        risk_reward = (take_profit - current_price) / (current_price - stop_loss) if stop_loss < current_price else 0
        
        return SMCSignal(
            type=SMCSignalType.BUY,
            strength=strength,
            price=current_price,
            timestamp=current_time,
            entry_zone=entry_zone,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=confidence,
            confluences=confluences,
            kill_zone=kill_zone,
            risk_reward=risk_reward
        )
    
    def generate_sell_signal(self) -> Optional[SMCSignal]:
        """
        Generate a sell signal based on SMC analysis
        
        Returns:
            Sell signal or None if conditions not met
        """
        current_price = self.df['close'].iloc[-1]
        current_time = self.df.index[-1]
        confluences = []
        entry_zone = None
        stop_loss = None
        take_profit = None
        
        # Check market structure
        if self.ms_analysis['trend'] == 'BEARISH':
            confluences.append('market_structure_bearish')
        
        recent_choch = self.ms_analysis.get('recent_choch')
        if recent_choch and recent_choch.direction == 'BEARISH':
            confluences.append('bearish_choch')
        
        # Check order blocks
        nearest_bearish_ob = self.ob_analysis.get('nearest_bearish')
        price_at_ob = self.ob_analysis.get('price_at_ob')
        
        if price_at_ob and price_at_ob.type == OrderBlockType.BEARISH:
            confluences.append('price_at_order_block')
            entry_zone = 'Bearish Order Block'
            stop_loss = price_at_ob.high + (price_at_ob.high - price_at_ob.low) * 0.5
        
        # Check FVG
        price_in_fvg = self.fvg_analysis.get('price_in_fvg')
        nearest_bearish_fvg = self.fvg_analysis.get('nearest_bearish')
        
        if price_in_fvg and price_in_fvg.type == FVGType.BEARISH:
            confluences.append('price_in_fvg')
            if not entry_zone:
                entry_zone = 'Bearish FVG'
        
        # Check liquidity
        recent_sweeps = self.liq_analysis.get('recent_sweeps', [])
        for sweep in recent_sweeps:
            if sweep.signal == 'SELL':
                confluences.append('liquidity_sweep_sell')
                break
        
        # Check premium/discount
        current_zone = self.pd_analysis.get('current_zone')
        if current_zone in ['DEEP_PREMIUM', 'PREMIUM']:
            confluences.append('price_in_premium')
        
        # Check OTE
        is_in_ote = self.pd_analysis.get('is_in_ote')
        ote_direction = self.pd_analysis.get('ote_direction')
        if is_in_ote and ote_direction == 'BEARISH':
            confluences.append('price_in_ote_zone')
        
        # Check kill zone
        kill_zone = self.identify_kill_zone(current_time)
        if kill_zone in [KillZone.LONDON_OPEN, KillZone.NEW_YORK]:
            confluences.append('active_kill_zone')
        
        if len(confluences) < 2:
            return None
        
        # Calculate SL and TP
        if not stop_loss:
            nearest_bsl = self.liq_analysis.get('nearest_bsl')
            if nearest_bsl:
                stop_loss = nearest_bsl.level + (current_price * 0.001)
            else:
                atr = self._calculate_atr()
                stop_loss = current_price + (atr * 2)
        
        nearest_ssl = self.liq_analysis.get('nearest_ssl')
        if nearest_ssl:
            take_profit = nearest_ssl.level
        else:
            risk = stop_loss - current_price
            take_profit = current_price - (risk * 2)
        
        if not entry_zone:
            entry_zone = 'Premium Zone'
        
        strength, confidence = self._calculate_confluence_score(confluences)
        risk_reward = (current_price - take_profit) / (stop_loss - current_price) if stop_loss > current_price else 0
        
        return SMCSignal(
            type=SMCSignalType.SELL,
            strength=strength,
            price=current_price,
            timestamp=current_time,
            entry_zone=entry_zone,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=confidence,
            confluences=confluences,
            kill_zone=kill_zone,
            risk_reward=risk_reward
        )
    
    def _calculate_atr(self, period: int = 14) -> float:
        """Calculate ATR for position sizing"""
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        return atr if not pd.isna(atr) else (high.iloc[-1] - low.iloc[-1])
    
    def generate_signals(self) -> Dict:
        """
        Generate trading signals
        
        Returns:
            Dictionary with signal information
        """
        buy_signal = self.generate_buy_signal()
        sell_signal = self.generate_sell_signal()
        
        if buy_signal and sell_signal:
            if buy_signal.confidence > sell_signal.confidence:
                primary_signal = buy_signal
            else:
                primary_signal = sell_signal
        elif buy_signal:
            primary_signal = buy_signal
        elif sell_signal:
            primary_signal = sell_signal
        else:
            primary_signal = None
        
        return {
            'primary_signal': primary_signal,
            'buy_signal': buy_signal,
            'sell_signal': sell_signal,
            'recommendation': self._get_recommendation(primary_signal)
        }
    
    def _get_recommendation(self, signal: Optional[SMCSignal]) -> str:
        """Get trading recommendation based on signal"""
        if not signal:
            return "No clear trading opportunity. Wait for better setup."
        
        if signal.strength == SMCSignalStrength.STRONG:
            strength_text = "STRONG"
        elif signal.strength == SMCSignalStrength.MODERATE:
            strength_text = "MODERATE"
        else:
            strength_text = "WEAK"
        
        return (
            f"{strength_text} {signal.type.value} signal at {signal.price:.2f}. "
            f"Entry zone: {signal.entry_zone}. "
            f"SL: {signal.stop_loss:.2f}, TP: {signal.take_profit:.2f}. "
            f"R:R = 1:{signal.risk_reward:.1f}. "
            f"Confluences: {', '.join(signal.confluences)}."
        )


class SMCAnalyzer:
    """Complete SMC analysis suite"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize SMC Analyzer
        
        Args:
            df: DataFrame with OHLCV data
        """
        self.df = df.copy()
        self.market_structure = MarketStructure(df)
        self.ob_detector = OrderBlockDetector(df)
        self.fvg_detector = FVGDetector(df)
        self.liquidity_analyzer = LiquidityAnalyzer(df)
        self.pd_analyzer = PremiumDiscountAnalyzer(df)
        self.signal_generator = SMCSignalGenerator(df)
    
    def full_analysis(self) -> Dict:
        """
        Perform complete SMC analysis
        
        Returns:
            Dictionary with all SMC analysis results
        """
        ms_analysis = self.market_structure.analyze()
        ob_analysis = self.ob_detector.analyze()
        fvg_analysis = self.fvg_detector.analyze()
        liq_analysis = self.liquidity_analyzer.analyze()
        pd_analysis = self.pd_analyzer.analyze()
        signals = self.signal_generator.generate_signals()
        
        return {
            'market_structure': ms_analysis,
            'order_blocks': ob_analysis,
            'fair_value_gaps': fvg_analysis,
            'liquidity': liq_analysis,
            'premium_discount': pd_analysis,
            'signals': signals,
            'summary': self._generate_summary(
                ms_analysis, ob_analysis, fvg_analysis, 
                liq_analysis, pd_analysis, signals
            )
        }
    
    def _generate_summary(self, ms, ob, fvg, liq, pd, signals) -> Dict:
        """Generate a summary of all analysis"""
        current_price = self.df['close'].iloc[-1]
        
        summary = {
            'current_price': current_price,
            'trend': ms['trend'],
            'zone': pd['current_zone'],
            'active_obs': ob['active_obs'],
            'unfilled_fvgs': fvg['unfilled_fvgs'],
            'unswept_liquidity': liq['unswept_zones'],
            'recommendation': signals['recommendation'],
            'primary_signal': signals['primary_signal']
        }
        
        key_levels = []
        
        if ob['nearest_bullish']:
            key_levels.append({
                'type': 'Support (Bullish OB)',
                'level': ob['nearest_bullish'].high
            })
        if ob['nearest_bearish']:
            key_levels.append({
                'type': 'Resistance (Bearish OB)',
                'level': ob['nearest_bearish'].low
            })
        if liq['nearest_ssl']:
            key_levels.append({
                'type': 'SSL',
                'level': liq['nearest_ssl'].level
            })
        if liq['nearest_bsl']:
            key_levels.append({
                'type': 'BSL',
                'level': liq['nearest_bsl'].level
            })
        if liq['pdh']:
            key_levels.append({
                'type': 'PDH',
                'level': liq['pdh']
            })
        if liq['pdl']:
            key_levels.append({
                'type': 'PDL',
                'level': liq['pdl']
            })
        
        summary['key_levels'] = sorted(key_levels, key=lambda x: x['level'], reverse=True)
        
        return summary
    
    def get_chart_data(self) -> Dict:
        """
        Get all data formatted for charting
        
        Returns:
            Dictionary with chart-ready data
        """
        return {
            'order_blocks': self.ob_detector.get_ob_zones_for_chart(),
            'fvg_zones': self.fvg_detector.get_fvg_zones_for_chart(),
            'liquidity_levels': self.liquidity_analyzer.get_liquidity_levels_for_chart(),
            'premium_discount_zones': self.pd_analyzer.get_zones_for_chart(),
            'structure_labels': self.market_structure.get_structure_labels()
        }

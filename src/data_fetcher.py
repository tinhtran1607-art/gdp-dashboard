"""
Dona Invest - Data Fetcher Module
Handles fetching XAUUSD price data from various sources
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import streamlit as st
from typing import Optional, Tuple
import numpy as np


class XAUUSDDataFetcher:
    """Fetches XAUUSD (Gold) price data"""
    
    SYMBOL = "GC=F"  # Gold Futures
    
    def __init__(self):
        self.ticker = yf.Ticker(self.SYMBOL)
    
    @st.cache_data(ttl=300)
    def get_historical_data(_self, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """
        Fetch historical XAUUSD data
        
        Args:
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo)
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            df = yf.download(
                _self.SYMBOL,
                period=period,
                interval=interval,
                progress=False
            )
            
            if df.empty:
                return pd.DataFrame()
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
            
            df = df.reset_index()
            
            if 'Datetime' in df.columns:
                df = df.rename(columns={'Datetime': 'Date'})
            
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
                'Date': 'date'
            })
            
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            
            return df
            
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=60)
    def get_current_price(_self) -> Optional[dict]:
        """Get current XAUUSD price and basic info"""
        try:
            ticker = yf.Ticker(_self.SYMBOL)
            info = ticker.fast_info
            
            return {
                'price': info.last_price,
                'previous_close': info.previous_close,
                'open': info.open,
                'day_high': info.day_high,
                'day_low': info.day_low,
                'change': info.last_price - info.previous_close,
                'change_percent': ((info.last_price - info.previous_close) / info.previous_close) * 100
            }
        except Exception as e:
            st.error(f"Error fetching current price: {str(e)}")
            return None
    
    def get_date_range_data(self, start_date: datetime, end_date: datetime, 
                           interval: str = "1d") -> pd.DataFrame:
        """Fetch data for a specific date range"""
        try:
            df = yf.download(
                self.SYMBOL,
                start=start_date,
                end=end_date,
                interval=interval,
                progress=False
            )
            
            if df.empty:
                return pd.DataFrame()
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
            
            df = df.reset_index()
            
            if 'Datetime' in df.columns:
                df = df.rename(columns={'Datetime': 'Date'})
            
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
                'Date': 'date'
            })
            
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            
            return df
            
        except Exception as e:
            st.error(f"Error fetching date range data: {str(e)}")
            return pd.DataFrame()


def generate_sample_data(days: int = 365) -> pd.DataFrame:
    """Generate sample XAUUSD data for testing/demo purposes"""
    np.random.seed(42)
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    base_price = 1900
    prices = [base_price]
    
    for i in range(1, days):
        change = np.random.normal(0, 15)
        trend = np.sin(i / 30) * 5
        new_price = max(prices[-1] + change + trend, 1500)
        prices.append(new_price)
    
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        volatility = np.random.uniform(10, 30)
        high = close + np.random.uniform(0, volatility)
        low = close - np.random.uniform(0, volatility)
        open_price = low + np.random.uniform(0, high - low)
        volume = np.random.randint(50000, 200000)
        
        data.append({
            'date': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df = df.set_index('date')
    
    return df

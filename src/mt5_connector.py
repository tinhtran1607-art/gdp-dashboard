"""
Dona Invest - MT5 Connector Module
Connects to MetaTrader 5 for live trading
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None

from dotenv import load_dotenv

load_dotenv()


class OrderType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"


@dataclass
class AccountInfo:
    """MT5 Account information"""
    login: int
    server: str
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    profit: float
    leverage: int
    currency: str
    name: str
    company: str


@dataclass
class Position:
    """Open position information"""
    ticket: int
    symbol: str
    type: str
    volume: float
    price_open: float
    price_current: float
    sl: float
    tp: float
    profit: float
    swap: float
    time: datetime
    comment: str


@dataclass
class TradeResult:
    """Result of a trade operation"""
    success: bool
    order_id: Optional[int]
    message: str
    volume: float
    price: float


class MT5Connector:
    """MetaTrader 5 connection handler"""
    
    SYMBOL = "XAUUSD"
    
    def __init__(self, login: int = None, password: str = None, server: str = None):
        """
        Initialize MT5 connector
        
        Args:
            login: MT5 account login (default from env)
            password: MT5 account password (default from env)
            server: MT5 server name (default from env)
        """
        self.login = login or int(os.getenv('MT5_LOGIN', 0))
        self.password = password or os.getenv('MT5_PASSWORD', '')
        self.server = server or os.getenv('MT5_SERVER', '')
        self.connected = False
        self._initialized = False
    
    def connect(self) -> Tuple[bool, str]:
        """
        Connect to MT5 terminal
        
        Returns:
            Tuple of (success, message)
        """
        if not MT5_AVAILABLE:
            return False, "MetaTrader5 package not installed. Install with: pip install MetaTrader5"
        
        if not self._initialized:
            if not mt5.initialize():
                return False, f"MT5 initialization failed: {mt5.last_error()}"
            self._initialized = True
        
        if not self.login or not self.password or not self.server:
            return False, "Missing MT5 credentials. Check .env file."
        
        authorized = mt5.login(
            login=self.login,
            password=self.password,
            server=self.server
        )
        
        if authorized:
            self.connected = True
            account_info = mt5.account_info()
            return True, f"Connected to {account_info.name} (#{self.login})"
        else:
            error = mt5.last_error()
            return False, f"Login failed: {error}"
    
    def disconnect(self):
        """Disconnect from MT5"""
        if MT5_AVAILABLE and self._initialized:
            mt5.shutdown()
            self.connected = False
            self._initialized = False
    
    def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information"""
        if not self.connected or not MT5_AVAILABLE:
            return None
        
        info = mt5.account_info()
        if info is None:
            return None
        
        return AccountInfo(
            login=info.login,
            server=info.server,
            balance=info.balance,
            equity=info.equity,
            margin=info.margin,
            free_margin=info.margin_free,
            margin_level=info.margin_level if info.margin_level else 0,
            profit=info.profit,
            leverage=info.leverage,
            currency=info.currency,
            name=info.name,
            company=info.company
        )
    
    def get_symbol_info(self, symbol: str = None) -> Optional[Dict]:
        """Get symbol information"""
        if not self.connected or not MT5_AVAILABLE:
            return None
        
        symbol = symbol or self.SYMBOL
        info = mt5.symbol_info(symbol)
        
        if info is None:
            return None
        
        return {
            'symbol': info.name,
            'bid': info.bid,
            'ask': info.ask,
            'spread': info.spread,
            'digits': info.digits,
            'volume_min': info.volume_min,
            'volume_max': info.volume_max,
            'volume_step': info.volume_step,
            'trade_mode': info.trade_mode,
            'swap_long': info.swap_long,
            'swap_short': info.swap_short
        }
    
    def get_current_price(self, symbol: str = None) -> Optional[Dict]:
        """Get current bid/ask price"""
        if not self.connected or not MT5_AVAILABLE:
            return None
        
        symbol = symbol or self.SYMBOL
        tick = mt5.symbol_info_tick(symbol)
        
        if tick is None:
            return None
        
        return {
            'symbol': symbol,
            'bid': tick.bid,
            'ask': tick.ask,
            'last': tick.last,
            'volume': tick.volume,
            'time': datetime.fromtimestamp(tick.time)
        }
    
    def get_historical_data(self, symbol: str = None, timeframe: str = "D1",
                           count: int = 100) -> pd.DataFrame:
        """
        Get historical OHLCV data
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (M1, M5, M15, M30, H1, H4, D1, W1, MN1)
            count: Number of bars to fetch
        
        Returns:
            DataFrame with OHLCV data
        """
        if not self.connected or not MT5_AVAILABLE:
            return pd.DataFrame()
        
        symbol = symbol or self.SYMBOL
        
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
            'MN1': mt5.TIMEFRAME_MN1
        }
        
        tf = timeframe_map.get(timeframe, mt5.TIMEFRAME_D1)
        
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
        
        if rates is None or len(rates) == 0:
            return pd.DataFrame()
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df = df.rename(columns={
            'time': 'date',
            'tick_volume': 'volume'
        })
        df = df.set_index('date')
        
        return df[['open', 'high', 'low', 'close', 'volume']]
    
    def get_positions(self, symbol: str = None) -> List[Position]:
        """Get open positions"""
        if not self.connected or not MT5_AVAILABLE:
            return []
        
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()
        
        if positions is None:
            return []
        
        result = []
        for pos in positions:
            result.append(Position(
                ticket=pos.ticket,
                symbol=pos.symbol,
                type="BUY" if pos.type == 0 else "SELL",
                volume=pos.volume,
                price_open=pos.price_open,
                price_current=pos.price_current,
                sl=pos.sl,
                tp=pos.tp,
                profit=pos.profit,
                swap=pos.swap,
                time=datetime.fromtimestamp(pos.time),
                comment=pos.comment
            ))
        
        return result
    
    def open_position(self, order_type: OrderType, volume: float,
                     symbol: str = None, sl: float = None, tp: float = None,
                     comment: str = "Dona Invest") -> TradeResult:
        """
        Open a new position
        
        Args:
            order_type: BUY or SELL
            volume: Lot size
            symbol: Trading symbol
            sl: Stop loss price
            tp: Take profit price
            comment: Order comment
        
        Returns:
            TradeResult with operation status
        """
        if not self.connected or not MT5_AVAILABLE:
            return TradeResult(False, None, "Not connected to MT5", 0, 0)
        
        symbol = symbol or self.SYMBOL
        
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return TradeResult(False, None, f"Symbol {symbol} not found", 0, 0)
        
        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                return TradeResult(False, None, f"Failed to select {symbol}", 0, 0)
        
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return TradeResult(False, None, "Failed to get current price", 0, 0)
        
        if order_type == OrderType.BUY:
            price = tick.ask
            trade_type = mt5.ORDER_TYPE_BUY
        else:
            price = tick.bid
            trade_type = mt5.ORDER_TYPE_SELL
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": trade_type,
            "price": price,
            "deviation": 20,
            "magic": 202408,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        if sl:
            request["sl"] = sl
        if tp:
            request["tp"] = tp
        
        result = mt5.order_send(request)
        
        if result is None:
            return TradeResult(False, None, f"Order failed: {mt5.last_error()}", 0, 0)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return TradeResult(False, None, f"Order failed: {result.comment}", 0, 0)
        
        return TradeResult(
            success=True,
            order_id=result.order,
            message=f"Order executed successfully",
            volume=result.volume,
            price=result.price
        )
    
    def close_position(self, ticket: int) -> TradeResult:
        """
        Close a position by ticket
        
        Args:
            ticket: Position ticket number
        
        Returns:
            TradeResult with operation status
        """
        if not self.connected or not MT5_AVAILABLE:
            return TradeResult(False, None, "Not connected to MT5", 0, 0)
        
        position = mt5.positions_get(ticket=ticket)
        if not position:
            return TradeResult(False, None, f"Position {ticket} not found", 0, 0)
        
        position = position[0]
        symbol = position.symbol
        volume = position.volume
        
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return TradeResult(False, None, "Failed to get price", 0, 0)
        
        if position.type == 0:  # BUY position
            price = tick.bid
            trade_type = mt5.ORDER_TYPE_SELL
        else:  # SELL position
            price = tick.ask
            trade_type = mt5.ORDER_TYPE_BUY
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": trade_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 202408,
            "comment": "Close by Dona Invest",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result is None:
            return TradeResult(False, None, f"Close failed: {mt5.last_error()}", 0, 0)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return TradeResult(False, None, f"Close failed: {result.comment}", 0, 0)
        
        return TradeResult(
            success=True,
            order_id=result.order,
            message=f"Position closed successfully",
            volume=result.volume,
            price=result.price
        )
    
    def modify_position(self, ticket: int, sl: float = None, tp: float = None) -> TradeResult:
        """
        Modify position SL/TP
        
        Args:
            ticket: Position ticket
            sl: New stop loss
            tp: New take profit
        
        Returns:
            TradeResult with operation status
        """
        if not self.connected or not MT5_AVAILABLE:
            return TradeResult(False, None, "Not connected to MT5", 0, 0)
        
        position = mt5.positions_get(ticket=ticket)
        if not position:
            return TradeResult(False, None, f"Position {ticket} not found", 0, 0)
        
        position = position[0]
        
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position.symbol,
            "position": ticket,
            "sl": sl if sl else position.sl,
            "tp": tp if tp else position.tp,
        }
        
        result = mt5.order_send(request)
        
        if result is None:
            return TradeResult(False, None, f"Modify failed: {mt5.last_error()}", 0, 0)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return TradeResult(False, None, f"Modify failed: {result.comment}", 0, 0)
        
        return TradeResult(
            success=True,
            order_id=ticket,
            message="Position modified successfully",
            volume=position.volume,
            price=position.price_current
        )
    
    def get_trade_history(self, days: int = 30) -> List[Dict]:
        """Get trade history for the past N days"""
        if not self.connected or not MT5_AVAILABLE:
            return []
        
        from_date = datetime.now() - timedelta(days=days)
        to_date = datetime.now()
        
        deals = mt5.history_deals_get(from_date, to_date)
        
        if deals is None:
            return []
        
        history = []
        for deal in deals:
            history.append({
                'ticket': deal.ticket,
                'order': deal.order,
                'time': datetime.fromtimestamp(deal.time),
                'type': 'BUY' if deal.type == 0 else 'SELL' if deal.type == 1 else 'OTHER',
                'symbol': deal.symbol,
                'volume': deal.volume,
                'price': deal.price,
                'profit': deal.profit,
                'commission': deal.commission,
                'swap': deal.swap,
                'comment': deal.comment
            })
        
        return history


class MT5SimulatorConnector:
    """Simulated MT5 connector for demo/testing without real MT5"""
    
    SYMBOL = "XAUUSD"
    
    def __init__(self):
        self.connected = False
        self.balance = 10000.0
        self.equity = 10000.0
        self.positions = []
        self.next_ticket = 1000
        self.current_price = 2650.0
    
    def connect(self) -> Tuple[bool, str]:
        self.connected = True
        return True, "Connected to Demo Account (Simulated)"
    
    def disconnect(self):
        self.connected = False
    
    def get_account_info(self) -> AccountInfo:
        total_profit = sum(p.profit for p in self.positions)
        self.equity = self.balance + total_profit
        
        return AccountInfo(
            login=412070670,
            server="Exness-MT5Real8 (Demo)",
            balance=self.balance,
            equity=self.equity,
            margin=sum(p.volume * 1000 for p in self.positions),
            free_margin=self.equity - sum(p.volume * 1000 for p in self.positions),
            margin_level=999.99 if self.positions else 0,
            profit=total_profit,
            leverage=0,  # Unlimited
            currency="USD",
            name="Dona Invest Demo",
            company="Exness"
        )
    
    def get_current_price(self, symbol: str = None) -> Dict:
        spread = 0.5
        self.current_price += np.random.uniform(-2, 2)
        
        return {
            'symbol': symbol or self.SYMBOL,
            'bid': self.current_price,
            'ask': self.current_price + spread,
            'last': self.current_price,
            'volume': np.random.randint(100, 1000),
            'time': datetime.now()
        }
    
    def get_positions(self, symbol: str = None) -> List[Position]:
        price_info = self.get_current_price()
        current_price = price_info['bid']
        
        for pos in self.positions:
            if pos.type == "BUY":
                pos.profit = (current_price - pos.price_open) * pos.volume * 100
            else:
                pos.profit = (pos.price_open - current_price) * pos.volume * 100
            pos.price_current = current_price
        
        return self.positions
    
    def open_position(self, order_type: OrderType, volume: float,
                     symbol: str = None, sl: float = None, tp: float = None,
                     comment: str = "Dona Invest") -> TradeResult:
        
        price_info = self.get_current_price()
        
        if order_type == OrderType.BUY:
            price = price_info['ask']
            pos_type = "BUY"
        else:
            price = price_info['bid']
            pos_type = "SELL"
        
        position = Position(
            ticket=self.next_ticket,
            symbol=symbol or self.SYMBOL,
            type=pos_type,
            volume=volume,
            price_open=price,
            price_current=price,
            sl=sl or 0,
            tp=tp or 0,
            profit=0,
            swap=0,
            time=datetime.now(),
            comment=comment
        )
        
        self.positions.append(position)
        self.next_ticket += 1
        
        return TradeResult(
            success=True,
            order_id=position.ticket,
            message=f"Demo {pos_type} order opened",
            volume=volume,
            price=price
        )
    
    def close_position(self, ticket: int) -> TradeResult:
        position = next((p for p in self.positions if p.ticket == ticket), None)
        
        if not position:
            return TradeResult(False, None, "Position not found", 0, 0)
        
        self.balance += position.profit
        self.positions.remove(position)
        
        return TradeResult(
            success=True,
            order_id=ticket,
            message=f"Demo position closed with ${position.profit:.2f} profit",
            volume=position.volume,
            price=position.price_current
        )


def get_mt5_connector(use_simulator: bool = False) -> MT5Connector:
    """
    Get appropriate MT5 connector
    
    Args:
        use_simulator: If True, return simulator instead of real connector
    
    Returns:
        MT5Connector or MT5SimulatorConnector instance
    """
    if use_simulator or not MT5_AVAILABLE:
        return MT5SimulatorConnector()
    return MT5Connector()

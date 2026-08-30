# Smart Money Concepts (SMC) Trading Skill

## Tổng Quan

Smart Money Concepts (SMC) là phương pháp phân tích kỹ thuật dựa trên hành vi của "Smart Money" - các tổ chức tài chính lớn, ngân hàng, và quỹ đầu tư. SMC tập trung vào việc xác định dấu chân của dòng tiền lớn trên thị trường.

---

## 1. Market Structure (Cấu Trúc Thị Trường)

### 1.1 Định nghĩa
Market Structure là xương sống của SMC, xác định xu hướng thị trường thông qua các Higher High (HH), Higher Low (HL), Lower High (LH), và Lower Low (LL).

### 1.2 Bullish Structure (Cấu trúc tăng)
```
         HH
        /  \
       /    \
     HL      \
    /         HH
   /         /
  HL        /
 /         HL
```
- **Higher High (HH)**: Đỉnh mới cao hơn đỉnh trước
- **Higher Low (HL)**: Đáy mới cao hơn đáy trước
- **Xu hướng**: Tăng khi HH và HL liên tiếp

### 1.3 Bearish Structure (Cấu trúc giảm)
```
  LH
 /  \
/    \
      LL
       \
        LH
         \
          LL
```
- **Lower High (LH)**: Đỉnh mới thấp hơn đỉnh trước
- **Lower Low (LL)**: Đáy mới thấp hơn đáy trước
- **Xu hướng**: Giảm khi LH và LL liên tiếp

### 1.4 Code Implementation
```python
def identify_swing_points(df, left_bars=5, right_bars=5):
    """Xác định các swing high và swing low"""
    swing_highs = []
    swing_lows = []
    
    for i in range(left_bars, len(df) - right_bars):
        # Check swing high
        if all(df['high'].iloc[i] > df['high'].iloc[i-j] for j in range(1, left_bars+1)) and \
           all(df['high'].iloc[i] > df['high'].iloc[i+j] for j in range(1, right_bars+1)):
            swing_highs.append((i, df['high'].iloc[i]))
        
        # Check swing low
        if all(df['low'].iloc[i] < df['low'].iloc[i-j] for j in range(1, left_bars+1)) and \
           all(df['low'].iloc[i] < df['low'].iloc[i+j] for j in range(1, right_bars+1)):
            swing_lows.append((i, df['low'].iloc[i]))
    
    return swing_highs, swing_lows
```

---

## 2. Break of Structure (BOS)

### 2.1 Định nghĩa
BOS xảy ra khi giá phá vỡ một swing point quan trọng, xác nhận xu hướng hiện tại tiếp tục.

### 2.2 Bullish BOS
```
        BOS ←── Giá phá vỡ HH trước
         ↑
    HH ──┤
   /     │
  /      │
HL       │
         │
    Previous HH
```
- Giá đóng cửa trên Previous HH
- Xác nhận xu hướng tăng tiếp tục
- Tín hiệu BUY khi pullback về HL

### 2.3 Bearish BOS
```
    Previous LL
         │
         │    LL
         │     \
         │      \
    LL ──┤       LH
         ↓
        BOS ←── Giá phá vỡ LL trước
```
- Giá đóng cửa dưới Previous LL
- Xác nhận xu hướng giảm tiếp tục
- Tín hiệu SELL khi pullback về LH

### 2.4 Code Implementation
```python
def detect_bos(df, swing_highs, swing_lows):
    """Phát hiện Break of Structure"""
    bos_signals = []
    
    for i in range(len(df)):
        # Bullish BOS
        for sh_idx, sh_price in swing_highs:
            if sh_idx < i and df['close'].iloc[i] > sh_price:
                bos_signals.append({
                    'index': i,
                    'type': 'BULLISH_BOS',
                    'broken_level': sh_price,
                    'close': df['close'].iloc[i]
                })
                break
        
        # Bearish BOS
        for sl_idx, sl_price in swing_lows:
            if sl_idx < i and df['close'].iloc[i] < sl_price:
                bos_signals.append({
                    'index': i,
                    'type': 'BEARISH_BOS',
                    'broken_level': sl_price,
                    'close': df['close'].iloc[i]
                })
                break
    
    return bos_signals
```

---

## 3. Change of Character (CHoCH)

### 3.1 Định nghĩa
CHoCH là dấu hiệu đảo chiều xu hướng - khi cấu trúc thị trường thay đổi từ bullish sang bearish hoặc ngược lại.

### 3.2 Bullish CHoCH (Từ giảm sang tăng)
```
    LH
   /  \
  /    LL
 /      \
LH       \    CHoCH
          \   ↑
           └──┼── Giá phá vỡ LH trong xu hướng giảm
              │
              New HL
```
- Trong xu hướng giảm, giá phá vỡ LH gần nhất
- Đánh dấu potential trend reversal
- Entry point: Pullback sau CHoCH

### 3.3 Bearish CHoCH (Từ tăng sang giảm)
```
              New LH
              │
           ┌──┼── Giá phá vỡ HL trong xu hướng tăng
          /   ↓
         /   CHoCH
    HL  /
   /  \/
  /    HH
 /
HL
```
- Trong xu hướng tăng, giá phá vỡ HL gần nhất
- Đánh dấu potential trend reversal
- Entry point: Pullback sau CHoCH

### 3.4 Phân biệt BOS vs CHoCH

| Tiêu chí | BOS | CHoCH |
|----------|-----|-------|
| Ý nghĩa | Tiếp tục xu hướng | Đảo chiều xu hướng |
| Bullish | Phá HH trong uptrend | Phá LH trong downtrend |
| Bearish | Phá LL trong downtrend | Phá HL trong uptrend |
| Trading | Trade theo trend | Trade reversal |

### 3.5 Code Implementation
```python
def detect_choch(df, swing_highs, swing_lows, current_trend):
    """Phát hiện Change of Character"""
    choch_signals = []
    
    for i in range(len(df)):
        if current_trend == 'BEARISH':
            # Look for bullish CHoCH (break of recent LH)
            recent_lh = get_recent_swing(swing_highs, i, 'high')
            if recent_lh and df['close'].iloc[i] > recent_lh['price']:
                choch_signals.append({
                    'index': i,
                    'type': 'BULLISH_CHOCH',
                    'broken_level': recent_lh['price'],
                    'previous_trend': 'BEARISH',
                    'new_trend': 'BULLISH'
                })
        
        elif current_trend == 'BULLISH':
            # Look for bearish CHoCH (break of recent HL)
            recent_hl = get_recent_swing(swing_lows, i, 'low')
            if recent_hl and df['close'].iloc[i] < recent_hl['price']:
                choch_signals.append({
                    'index': i,
                    'type': 'BEARISH_CHOCH',
                    'broken_level': recent_hl['price'],
                    'previous_trend': 'BULLISH',
                    'new_trend': 'BEARISH'
                })
    
    return choch_signals
```

---

## 4. Order Blocks (OB)

### 4.1 Định nghĩa
Order Block là vùng giá nơi Smart Money đặt lệnh lớn. Đây thường là nến cuối cùng trước khi có một đợt tăng/giảm mạnh.

### 4.2 Bullish Order Block
```
                 ┌────────────────
                 │ Impulse Move Up
                 │
    ┌────────┐   │
    │ BULLISH│───┤
    │   OB   │   │
    └────────┘   │
                 │
    Last bearish candle before strong move up
```

**Đặc điểm:**
- Nến giảm cuối cùng trước đợt tăng mạnh
- Thường là nến đỏ với thân lớn
- Vùng hỗ trợ tiềm năng khi giá quay lại
- Entry: Khi giá retest vùng OB

### 4.3 Bearish Order Block
```
    Last bullish candle before strong move down
                 │
    ┌────────┐   │
    │BEARISH │───┤
    │   OB   │   │
    └────────┘   │
                 │
                 │ Impulse Move Down
                 └────────────────
```

**Đặc điểm:**
- Nến tăng cuối cùng trước đợt giảm mạnh
- Thường là nến xanh với thân lớn
- Vùng kháng cự tiềm năng khi giá quay lại
- Entry: Khi giá retest vùng OB

### 4.4 Order Block Mitigation
- **Unmitigated OB**: OB chưa được retest - vẫn valid
- **Mitigated OB**: OB đã được retest - có thể không còn hiệu lực
- **Respect**: Giá phản ứng tại OB = OB vẫn mạnh

### 4.5 Code Implementation
```python
def identify_order_blocks(df, lookback=10, impulse_threshold=2.0):
    """Xác định Order Blocks"""
    order_blocks = []
    atr = calculate_atr(df, 14)
    
    for i in range(lookback, len(df)):
        # Check for impulse move
        impulse_range = abs(df['close'].iloc[i] - df['close'].iloc[i-1])
        
        if impulse_range > atr.iloc[i] * impulse_threshold:
            # Bullish impulse - look for bearish OB before
            if df['close'].iloc[i] > df['open'].iloc[i]:
                for j in range(i-1, max(i-lookback, 0), -1):
                    if df['close'].iloc[j] < df['open'].iloc[j]:  # Bearish candle
                        order_blocks.append({
                            'type': 'BULLISH_OB',
                            'index': j,
                            'high': df['high'].iloc[j],
                            'low': df['low'].iloc[j],
                            'mitigated': False
                        })
                        break
            
            # Bearish impulse - look for bullish OB before
            elif df['close'].iloc[i] < df['open'].iloc[i]:
                for j in range(i-1, max(i-lookback, 0), -1):
                    if df['close'].iloc[j] > df['open'].iloc[j]:  # Bullish candle
                        order_blocks.append({
                            'type': 'BEARISH_OB',
                            'index': j,
                            'high': df['high'].iloc[j],
                            'low': df['low'].iloc[j],
                            'mitigated': False
                        })
                        break
    
    return order_blocks
```

---

## 5. Fair Value Gaps (FVG) / Imbalance

### 5.1 Định nghĩa
FVG là khoảng trống giá tạo ra bởi momentum mạnh, nơi không có giao dịch hai chiều xảy ra. Giá có xu hướng quay lại lấp đầy khoảng trống này.

### 5.2 Bullish FVG
```
    Candle 3   ┌───┐
               │   │
               │   │
               └───┘ ← High of Candle 3
                     
    ════════════════ ← FVG Zone (Gap)
                     
    Candle 1   ┌───┐ ← Low of Candle 1
               │   │
               └───┘
    
    Candle 2 (giữa) tạo gap giữa Candle 1 và 3
```

**Điều kiện:**
- Low của Candle 1 > High của Candle 3
- Tạo ra khoảng trống bullish
- Vùng hỗ trợ khi giá quay lại

### 5.3 Bearish FVG
```
    Candle 1   ┌───┐ ← High of Candle 1
               │   │
               └───┘
                     
    ════════════════ ← FVG Zone (Gap)
                     
    Candle 3   ┌───┐ ← Low of Candle 3
               │   │
               │   │
               └───┘
    
    Candle 2 (giữa) tạo gap giữa Candle 1 và 3
```

**Điều kiện:**
- High của Candle 1 < Low của Candle 3
- Tạo ra khoảng trống bearish
- Vùng kháng cự khi giá quay lại

### 5.4 FVG Trading
- **Fresh FVG**: Chưa được lấp = valid entry zone
- **Filled FVG**: Đã được lấp đầy = không còn valid
- **Partially Filled**: Lấp một phần = có thể vẫn valid

### 5.5 Code Implementation
```python
def identify_fvg(df, min_gap_atr=0.5):
    """Xác định Fair Value Gaps"""
    fvg_zones = []
    atr = calculate_atr(df, 14)
    
    for i in range(2, len(df)):
        candle1_low = df['low'].iloc[i-2]
        candle1_high = df['high'].iloc[i-2]
        candle3_low = df['low'].iloc[i]
        candle3_high = df['high'].iloc[i]
        
        # Bullish FVG
        if candle1_low > candle3_high:
            gap_size = candle1_low - candle3_high
            if gap_size > atr.iloc[i] * min_gap_atr:
                fvg_zones.append({
                    'type': 'BULLISH_FVG',
                    'index': i-1,  # Middle candle index
                    'top': candle1_low,
                    'bottom': candle3_high,
                    'size': gap_size,
                    'filled': False
                })
        
        # Bearish FVG
        if candle1_high < candle3_low:
            gap_size = candle3_low - candle1_high
            if gap_size > atr.iloc[i] * min_gap_atr:
                fvg_zones.append({
                    'type': 'BEARISH_FVG',
                    'index': i-1,
                    'top': candle3_low,
                    'bottom': candle1_high,
                    'size': gap_size,
                    'filled': False
                })
    
    return fvg_zones
```

---

## 6. Liquidity Concepts

### 6.1 Liquidity là gì?
Liquidity trong SMC là nơi tập trung các stop loss và pending orders của retail traders. Smart Money "săn" liquidity này để thực hiện các lệnh lớn.

### 6.2 Liquidity Pools

#### Buy-side Liquidity (BSL)
```
    ═══════════════ ← Previous High (BSL)
    Stop losses của SELL orders
    Buy stops của breakout traders
         │
         │  Smart Money targets this area
         │
    Current Price
```

#### Sell-side Liquidity (SSL)
```
    Current Price
         │
         │  Smart Money targets this area
         │
    Stop losses của BUY orders
    Sell stops của breakout traders
    ═══════════════ ← Previous Low (SSL)
```

### 6.3 Liquidity Sweep / Grab
```
                Liquidity Sweep
                     ↓
    ═════════════════╪══ Previous High
                    / \
                   /   \
                  /     \
                 /       Price reverses
                /        after grabbing liquidity
               │
         Normal Price Action
```

**Đặc điểm:**
- Giá phá vỡ level quan trọng
- Nhanh chóng quay đầu
- Stop losses bị kích hoạt
- Smart Money entry ngược chiều

### 6.4 Equal Highs/Lows (EQH/EQL)
```
    EQH ═══╤═══╤═══╤═══ ← Multiple touches = Strong liquidity
           │   │   │
           │   │   │
```

- Nhiều lần test cùng một level = liquidity tích tụ
- Smart Money sẽ săn những vùng này
- Entry sau khi liquidity được grab

### 6.5 Code Implementation
```python
def identify_liquidity_levels(df, tolerance=0.001):
    """Xác định các vùng liquidity"""
    liquidity_zones = []
    
    # Find equal highs
    for i in range(len(df)):
        for j in range(i+1, min(i+50, len(df))):
            if abs(df['high'].iloc[i] - df['high'].iloc[j]) / df['high'].iloc[i] < tolerance:
                liquidity_zones.append({
                    'type': 'BSL',  # Buy-side liquidity
                    'level': (df['high'].iloc[i] + df['high'].iloc[j]) / 2,
                    'strength': 2,
                    'indices': [i, j]
                })
    
    # Find equal lows
    for i in range(len(df)):
        for j in range(i+1, min(i+50, len(df))):
            if abs(df['low'].iloc[i] - df['low'].iloc[j]) / df['low'].iloc[i] < tolerance:
                liquidity_zones.append({
                    'type': 'SSL',  # Sell-side liquidity
                    'level': (df['low'].iloc[i] + df['low'].iloc[j]) / 2,
                    'strength': 2,
                    'indices': [i, j]
                })
    
    return liquidity_zones

def detect_liquidity_sweep(df, liquidity_zones, wick_threshold=0.3):
    """Phát hiện liquidity sweep"""
    sweeps = []
    
    for zone in liquidity_zones:
        for i in range(max(zone['indices']) + 1, len(df)):
            candle_range = df['high'].iloc[i] - df['low'].iloc[i]
            
            if zone['type'] == 'BSL':
                # Check for sweep above (price wicks above then closes below)
                if df['high'].iloc[i] > zone['level'] and df['close'].iloc[i] < zone['level']:
                    wick_size = df['high'].iloc[i] - max(df['open'].iloc[i], df['close'].iloc[i])
                    if wick_size / candle_range > wick_threshold:
                        sweeps.append({
                            'type': 'BSL_SWEEP',
                            'index': i,
                            'level': zone['level'],
                            'signal': 'SELL'
                        })
            
            elif zone['type'] == 'SSL':
                # Check for sweep below (price wicks below then closes above)
                if df['low'].iloc[i] < zone['level'] and df['close'].iloc[i] > zone['level']:
                    wick_size = min(df['open'].iloc[i], df['close'].iloc[i]) - df['low'].iloc[i]
                    if wick_size / candle_range > wick_threshold:
                        sweeps.append({
                            'type': 'SSL_SWEEP',
                            'index': i,
                            'level': zone['level'],
                            'signal': 'BUY'
                        })
    
    return sweeps
```

---

## 7. Premium và Discount Zones

### 7.1 Định nghĩa
Dựa trên Fibonacci, thị trường chia thành Premium (giá cao) và Discount (giá thấp) để xác định vùng entry tối ưu.

### 7.2 Calculation
```
    Swing High ────── 100% ──────┬── PREMIUM ZONE
                                 │   (Sell Zone)
                      75% ───────┤
                                 │
    Equilibrium ────── 50% ──────┤── EQUILIBRIUM
                                 │
                      25% ───────┤
                                 │   DISCOUNT ZONE
    Swing Low ─────── 0% ────────┴── (Buy Zone)
```

### 7.3 Trading Rules
- **BUY** trong Discount Zone (0-50%)
- **SELL** trong Premium Zone (50-100%)
- **Equilibrium** (50%) = điểm cân bằng, wait for confirmation

### 7.4 Code Implementation
```python
def calculate_premium_discount(df, lookback=50):
    """Tính toán Premium/Discount zones"""
    swing_high = df['high'].rolling(window=lookback).max()
    swing_low = df['low'].rolling(window=lookback).min()
    
    range_size = swing_high - swing_low
    current_position = (df['close'] - swing_low) / range_size
    
    df['premium_discount'] = current_position
    df['zone'] = pd.cut(current_position, 
                        bins=[0, 0.25, 0.5, 0.75, 1.0],
                        labels=['DEEP_DISCOUNT', 'DISCOUNT', 'PREMIUM', 'DEEP_PREMIUM'])
    
    return df
```

---

## 8. Optimal Trade Entry (OTE)

### 8.1 Định nghĩa
OTE là vùng entry tối ưu dựa trên Fibonacci retracement, thường nằm trong khoảng 62-79% retracement.

### 8.2 OTE Zone
```
    Impulse High ──── 0% ────────┐
                                 │
                    23.6% ───────┤
                                 │
                    38.2% ───────┤
                                 │
                    50% ─────────┤
                                 │
    ════════════ 61.8% ══════════╡ ← OTE ZONE START
                                 │
    ════════════ 70.5% ══════════│ ← OPTIMAL ENTRY
                                 │
    ════════════ 78.6% ══════════╡ ← OTE ZONE END
                                 │
    Impulse Low ──── 100% ───────┘
```

### 8.3 OTE Trading Setup
1. Xác định impulse move (swing high to swing low hoặc ngược lại)
2. Vẽ Fibonacci retracement
3. Chờ giá pullback vào OTE zone (61.8% - 78.6%)
4. Entry với confirmation (candlestick pattern, FVG, OB)
5. Stop loss ngoài swing point
6. Take profit tại vùng liquidity đối diện

### 8.4 Code Implementation
```python
def find_ote_zones(df, swing_highs, swing_lows):
    """Xác định OTE zones"""
    ote_zones = []
    
    # For bullish setup (after impulse down, looking for buy)
    for i, (sh_idx, sh_price) in enumerate(swing_highs):
        # Find next swing low after this high
        next_lows = [(idx, price) for idx, price in swing_lows if idx > sh_idx]
        if next_lows:
            sl_idx, sl_price = next_lows[0]
            range_size = sh_price - sl_price
            
            ote_zones.append({
                'type': 'BULLISH_OTE',
                'swing_high': sh_price,
                'swing_low': sl_price,
                'ote_top': sl_price + (range_size * 0.382),     # 61.8% from high
                'ote_bottom': sl_price + (range_size * 0.214),  # 78.6% from high
                'optimal_entry': sl_price + (range_size * 0.295) # 70.5% from high
            })
    
    # For bearish setup (after impulse up, looking for sell)
    for i, (sl_idx, sl_price) in enumerate(swing_lows):
        next_highs = [(idx, price) for idx, price in swing_highs if idx > sl_idx]
        if next_highs:
            sh_idx, sh_price = next_highs[0]
            range_size = sh_price - sl_price
            
            ote_zones.append({
                'type': 'BEARISH_OTE',
                'swing_high': sh_price,
                'swing_low': sl_price,
                'ote_top': sl_price + (range_size * 0.786),     # 78.6% from low
                'ote_bottom': sl_price + (range_size * 0.618),  # 61.8% from low
                'optimal_entry': sl_price + (range_size * 0.705) # 70.5% from low
            })
    
    return ote_zones
```

---

## 9. ICT Kill Zones (Session Times)

### 9.1 Định nghĩa
Kill Zones là các khung giờ giao dịch quan trọng khi Smart Money hoạt động mạnh nhất.

### 9.2 Major Kill Zones (UTC)

| Kill Zone | Thời gian (UTC) | Mô tả |
|-----------|-----------------|-------|
| Asian Session | 00:00 - 08:00 | Range thường hẹp, liquidity building |
| London Open | 07:00 - 10:00 | High volatility, major moves |
| New York Open | 12:00 - 15:00 | Continuation hoặc reversal |
| London Close | 15:00 - 17:00 | Potential reversals |

### 9.3 XAUUSD Specific Kill Zones
```
    Asian Range
    ├─────────────────────────────────────┤
    00:00                              08:00
    
                    London Kill Zone
                    ├───────────────┤
                   07:00          10:00
    
                              NY Kill Zone
                              ├───────────────┤
                             12:00          15:00
    
                                        London Close
                                        ├─────────┤
                                       15:00   17:00
```

### 9.4 Trading Strategy per Kill Zone

**Asian Session:**
- Xác định range (high/low)
- Expect liquidity grab ở London Open

**London Open:**
- Trade breakout from Asian range
- Look for liquidity sweep of Asian high/low
- Strong trend moves

**New York Open:**
- Continuation of London trend OR
- Reversal if London over-extended
- Look for OB/FVG entries

**London Close:**
- Potential reversals
- Take profits
- Reduce position size

### 9.5 Code Implementation
```python
from datetime import datetime, time

def identify_kill_zone(timestamp):
    """Xác định kill zone hiện tại"""
    hour = timestamp.hour
    
    if 0 <= hour < 8:
        return 'ASIAN'
    elif 7 <= hour < 10:
        return 'LONDON_OPEN'
    elif 12 <= hour < 15:
        return 'NEW_YORK'
    elif 15 <= hour < 17:
        return 'LONDON_CLOSE'
    else:
        return 'OFF_HOURS'

def get_asian_range(df):
    """Lấy Asian session range"""
    asian_candles = df[df.index.hour.isin(range(0, 8))]
    
    if len(asian_candles) > 0:
        return {
            'high': asian_candles['high'].max(),
            'low': asian_candles['low'].min(),
            'range': asian_candles['high'].max() - asian_candles['low'].min()
        }
    return None
```

---

## 10. Breaker Blocks

### 10.1 Định nghĩa
Breaker Block là Order Block đã bị fail (bị phá vỡ), sau đó flip thành vùng support/resistance ngược lại.

### 10.2 Bullish Breaker
```
    ┌────────────┐
    │ Old Bearish│ ←─ Original bearish OB
    │     OB     │
    └────────────┘
         │
         │ OB gets broken (failed)
         ↓
    ═════╪═════════ ←─ Price breaks through
         │
         │ Price comes back
         ↓
    ┌────────────┐
    │  BULLISH   │ ←─ Now acts as SUPPORT
    │  BREAKER   │    (Buy zone)
    └────────────┘
```

### 10.3 Bearish Breaker
```
    ┌────────────┐
    │  BEARISH   │ ←─ Now acts as RESISTANCE
    │  BREAKER   │    (Sell zone)
    └────────────┘
         ↑
         │ Price comes back
         │
    ═════╪═════════ ←─ Price breaks through
         ↑
         │ OB gets broken (failed)
         │
    ┌────────────┐
    │ Old Bullish│ ←─ Original bullish OB
    │     OB     │
    └────────────┘
```

### 10.4 Code Implementation
```python
def identify_breaker_blocks(df, order_blocks):
    """Xác định Breaker Blocks từ failed Order Blocks"""
    breaker_blocks = []
    
    for ob in order_blocks:
        ob_broken = False
        broken_index = None
        
        # Check if OB was broken
        for i in range(ob['index'] + 1, len(df)):
            if ob['type'] == 'BULLISH_OB':
                if df['close'].iloc[i] < ob['low']:
                    ob_broken = True
                    broken_index = i
                    break
            elif ob['type'] == 'BEARISH_OB':
                if df['close'].iloc[i] > ob['high']:
                    ob_broken = True
                    broken_index = i
                    break
        
        if ob_broken:
            # Check for price return to the broken OB
            for j in range(broken_index + 1, len(df)):
                if ob['type'] == 'BULLISH_OB':
                    # Failed bullish OB becomes bearish breaker
                    if df['high'].iloc[j] >= ob['low']:
                        breaker_blocks.append({
                            'type': 'BEARISH_BREAKER',
                            'original_ob': ob,
                            'broken_at': broken_index,
                            'retest_at': j,
                            'high': ob['high'],
                            'low': ob['low'],
                            'signal': 'SELL'
                        })
                        break
                        
                elif ob['type'] == 'BEARISH_OB':
                    # Failed bearish OB becomes bullish breaker
                    if df['low'].iloc[j] <= ob['high']:
                        breaker_blocks.append({
                            'type': 'BULLISH_BREAKER',
                            'original_ob': ob,
                            'broken_at': broken_index,
                            'retest_at': j,
                            'high': ob['high'],
                            'low': ob['low'],
                            'signal': 'BUY'
                        })
                        break
    
    return breaker_blocks
```

---

## 11. Mitigation Blocks

### 11.1 Định nghĩa
Mitigation Block là vùng giá nơi Smart Money đã từng thua lỗ và sẽ quay lại để "mitigation" (giảm thiểu tổn thất) bằng cách đóng vị thế ở breakeven.

### 11.2 Concept
```
    Smart Money sells here
              ↓
         ┌────────┐
         │ Entry  │
         └────────┘
              │
              │ Price moves against (SM in loss)
              ↓
         ══════════ Low
              │
              │ Price reverses
              ↓
         ┌────────┐
         │MITIGAT-│ ←─ SM closes at breakeven
         │  ION   │    (Mitigation Block)
         └────────┘
              │
              │ After mitigation, expect continuation
              ↓
```

### 11.3 Trading Mitigation Blocks
1. Xác định vùng SM entry cũ
2. Chờ giá quay lại vùng đó
3. Entry sau khi mitigation xảy ra
4. Expect continuation theo hướng SM

---

## 12. SMC Trading Strategy Template

### 12.1 Checklist trước khi Entry

```
□ 1. MARKET STRUCTURE
   □ Xác định trend (Bullish/Bearish/Ranging)
   □ Identify recent BOS/CHoCH
   
□ 2. HIGHER TIMEFRAME BIAS
   □ Daily/4H trend direction
   □ Key levels from HTF
   
□ 3. LIQUIDITY
   □ Identify BSL/SSL zones
   □ Check for recent liquidity sweeps
   
□ 4. POI (Point of Interest)
   □ Order Blocks
   □ Fair Value Gaps
   □ Breaker Blocks
   
□ 5. PREMIUM/DISCOUNT
   □ Buying in discount (0-50%)
   □ Selling in premium (50-100%)
   
□ 6. KILL ZONE
   □ Trading during active sessions
   □ Avoid off-hours
   
□ 7. CONFLUENCE
   □ Multiple factors align
   □ At least 3 confirmations
```

### 12.2 Entry Model

**Bullish Entry:**
```
1. HTF bullish structure
2. Price sweeps SSL
3. Bullish CHoCH on LTF
4. Entry at:
   - Bullish OB
   - Bullish FVG
   - OTE zone (61.8-78.6%)
5. SL below swing low
6. TP at BSL / next resistance
```

**Bearish Entry:**
```
1. HTF bearish structure
2. Price sweeps BSL
3. Bearish CHoCH on LTF
4. Entry at:
   - Bearish OB
   - Bearish FVG
   - OTE zone (61.8-78.6%)
5. SL above swing high
6. TP at SSL / next support
```

---

## 13. Risk Management với SMC

### 13.1 Position Sizing
```python
def calculate_position_size(account_balance, risk_percent, entry, stop_loss, pip_value=10):
    """Tính position size theo SMC risk management"""
    risk_amount = account_balance * (risk_percent / 100)
    stop_loss_pips = abs(entry - stop_loss) * 10  # Convert to pips for gold
    
    if stop_loss_pips == 0:
        return 0
    
    position_size = risk_amount / (stop_loss_pips * pip_value)
    return round(position_size, 2)
```

### 13.2 Risk:Reward Ratio
- Minimum R:R = 1:2
- Ideal R:R = 1:3 hoặc cao hơn
- Sử dụng liquidity levels làm TP targets

### 13.3 Partial Profit Taking
```
Entry ────────────────────────
   │
   │ Move SL to breakeven at 1R
   ↓
1:1 Target ─────────────────── Take 50% profit
   │
   │ Trail stop loss
   ↓
1:2 Target ─────────────────── Take 30% profit
   │
   │
   ↓
1:3+ Target ────────────────── Let rest run
```

---

## 14. Integration với Dona Invest System

### 14.1 File Structure
```
dona-invest/
├── src/
│   ├── smc/
│   │   ├── __init__.py
│   │   ├── market_structure.py
│   │   ├── order_blocks.py
│   │   ├── fair_value_gaps.py
│   │   ├── liquidity.py
│   │   ├── premium_discount.py
│   │   └── smc_signals.py
│   ├── signals.py (updated with SMC)
│   └── ...
```

### 14.2 Usage Example
```python
from src.smc import SMCAnalyzer

# Initialize
smc = SMCAnalyzer(df)

# Get all SMC analysis
analysis = smc.full_analysis()

# Get trading signals
signals = smc.generate_signals()

# Display on chart
smc.plot_analysis(chart)
```

---

## 15. Glossary

| Thuật ngữ | Định nghĩa |
|-----------|------------|
| **BOS** | Break of Structure - Phá vỡ cấu trúc, xác nhận trend |
| **CHoCH** | Change of Character - Thay đổi tính chất, báo hiệu đảo chiều |
| **OB** | Order Block - Vùng đặt lệnh của Smart Money |
| **FVG** | Fair Value Gap - Khoảng trống giá trị hợp lý |
| **BSL** | Buy-side Liquidity - Thanh khoản phía mua |
| **SSL** | Sell-side Liquidity - Thanh khoản phía bán |
| **OTE** | Optimal Trade Entry - Vùng entry tối ưu |
| **IMB** | Imbalance - Mất cân bằng (= FVG) |
| **PDH/PDL** | Previous Day High/Low |
| **PWH/PWL** | Previous Week High/Low |
| **HTF** | Higher Timeframe |
| **LTF** | Lower Timeframe |
| **POI** | Point of Interest |
| **MSS** | Market Structure Shift (= CHoCH) |
| **EQH/EQL** | Equal Highs/Lows |

---

## Tài liệu tham khảo

1. ICT (Inner Circle Trader) Concepts
2. SMC Trading Community Resources
3. Price Action Trading Principles

---

*Skill này được tạo cho dự án Dona Invest XAUUSD Trading System*

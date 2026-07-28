"""
فیلترادیوم - Technical Indicators
Advanced technical analysis indicators using historical price data

Usage:
    from backend.core.indicators import TechnicalIndicators
    
    ti = TechnicalIndicators(closes, highs, lows, volumes)
    rsi = ti.rsi(14)
    macd = ti.macd()
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class IndicatorResult:
    """Generic indicator result"""
    value: float
    signal: str
    details: Dict


class TechnicalIndicators:
    """
    Comprehensive technical indicators calculator
    
    All methods accept lists of prices and return calculated values.
    Data should be ordered from newest to oldest (index 0 = most recent).
    """
    
    def __init__(self, 
                 closes: List[float],
                 highs: Optional[List[float]] = None,
                 lows: Optional[List[float]] = None,
                 volumes: Optional[List[float]] = None,
                 opens: Optional[List[float]] = None):
        """
        Initialize with price data
        
        Args:
            closes: Closing prices (newest first)
            highs: High prices (optional)
            lows: Low prices (optional)
            volumes: Volume data (optional)
            opens: Open prices (optional)
        """
        self.closes = np.array(closes, dtype=float)
        self.highs = np.array(highs if highs else closes, dtype=float)
        self.lows = np.array(lows if lows else closes, dtype=float)
        self.volumes = np.array(volumes if volumes else [0] * len(closes), dtype=float)
        self.opens = np.array(opens if opens else closes, dtype=float)
    
    # ============================================================
    # Moving Averages
    # ============================================================
    
    def sma(self, period: int) -> float:
        """
        Simple Moving Average
        
        Args:
            period: Number of periods
            
        Returns:
            SMA value
        """
        if len(self.closes) < period:
            return float(self.closes[0]) if len(self.closes) > 0 else 0
        return float(np.mean(self.closes[:period]))
    
    def ema(self, period: int) -> float:
        """
        Exponential Moving Average
        
        Args:
            period: Number of periods
            
        Returns:
            EMA value
        """
        if len(self.closes) < period:
            return float(self.closes[0]) if len(self.closes) > 0 else 0
        
        k = 2 / (period + 1)
        ema = float(np.mean(self.closes[:period]))
        
        for price in self.closes[period:]:
            ema = float(price) * k + ema * (1 - k)
        
        return ema
    
    def wma(self, period: int) -> float:
        """
        Weighted Moving Average
        
        Args:
            period: Number of periods
            
        Returns:
            WMA value
        """
        if len(self.closes) < period:
            return float(self.closes[0]) if len(self.closes) > 0 else 0
        
        weights = np.arange(1, period + 1)
        sum_weights = np.sum(weights)
        
        return float(np.sum(self.closes[:period] * weights) / sum_weights)
    
    def dema(self, period: int) -> float:
        """
        Double Exponential Moving Average
        
        Args:
            period: Number of periods
            
        Returns:
            DEMA value
        """
        ema1 = self.ema(period)
        
        # Calculate second EMA
        k = 2 / (period + 1)
        ema2 = float(np.mean(self.closes[:period]))
        for price in self.closes[period:]:
            ema2 = float(price) * k + ema2 * (1 - k)
        
        return 2 * ema1 - ema2
    
    def tema(self, period: int) -> float:
        """
        Triple Exponential Moving Average
        
        Args:
            period: Number of periods
            
        Returns:
            TEMA value
        """
        ema1 = self.ema(period)
        
        # Calculate second EMA
        k = 2 / (period + 1)
        ema2 = float(np.mean(self.closes[:period]))
        for price in self.closes[period:]:
            ema2 = float(price) * k + ema2 * (1 - k)
        
        # Calculate third EMA
        ema3 = float(np.mean(self.closes[:period]))
        for price in self.closes[period:]:
            ema3 = float(price) * k + ema3 * (1 - k)
        
        return 3 * ema1 - 3 * ema2 + ema3
    
    def hull_ma(self, period: int) -> float:
        """
        Hull Moving Average
        
        Args:
            period: Number of periods
            
        Returns:
            HMA value
        """
        half_period = period // 2
        sqrt_period = int(np.sqrt(period))
        
        # Calculate WMA of half period
        wma_half = self.wma(half_period)
        
        # Calculate WMA of full period
        wma_full = self.wma(period)
        
        # Calculate difference
        diff = 2 * wma_half - wma_full
        
        # Calculate WMA of difference
        if diff > 0:
            return diff
        return float(self.closes[0]) if len(self.closes) > 0 else 0
    
    def ichimoku(self, 
                 tenkan_period: int = 9,
                 kijun_period: int = 26,
                 senkou_b_period: int = 52) -> Dict[str, float]:
        """
        Ichimoku Cloud
        
        Args:
            tenkan_period: Tenkan-sen period (default: 9)
            kijun_period: Kijun-sen period (default: 26)
            senkou_b_period: Senkou Span B period (default: 52)
            
        Returns:
            Dictionary with Ichimoku values
        """
        # Tenkan-sen (Conversion Line)
        tenkan_high = float(np.max(self.highs[:tenkan_period]))
        tenkan_low = float(np.min(self.lows[:tenkan_period]))
        tenkan = (tenkan_high + tenkan_low) / 2
        
        # Kijun-sen (Base Line)
        kijun_high = float(np.max(self.highs[:kijun_period]))
        kijun_low = float(np.min(self.lows[:kijun_period]))
        kijun = (kijun_high + kijun_low) / 2
        
        # Senkou Span A
        senkou_a = (tenkan + kijun) / 2
        
        # Senkou Span B
        senkou_b_high = float(np.max(self.highs[:senkou_b_period]))
        senkou_b_low = float(np.min(self.lows[:senkou_b_period]))
        senkou_b = (senkou_b_high + senkou_b_low) / 2
        
        # Chikou Span (Lagging Span)
        chikou = float(self.closes[min(kijun_period, len(self.closes) - 1)])
        
        return {
            "tenkan": tenkan,
            "kijun": kijun,
            "senkou_a": senkou_a,
            "senkou_b": senkou_b,
            "chikou": chikou
        }
    
    # ============================================================
    # Momentum Indicators
    # ============================================================
    
    def rsi(self, period: int = 14) -> float:
        """
        Relative Strength Index
        
        Args:
            period: RSI period (default: 14)
            
        Returns:
            RSI value (0-100)
        """
        if len(self.closes) < period + 1:
            return 50.0
        
        deltas = np.diff(self.closes[:period + 1])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = float(np.mean(gains))
        avg_loss = float(np.mean(losses))
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return float(100 - (100 / (1 + rs)))
    
    def macd(self, 
             fast_period: int = 12,
             slow_period: int = 26,
             signal_period: int = 9) -> Dict[str, float]:
        """
        MACD (Moving Average Convergence Divergence)
        
        Args:
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line period (default: 9)
            
        Returns:
            Dictionary with MACD line, signal line, and histogram
        """
        if len(self.closes) < slow_period:
            return {"macd": 0, "signal": 0, "histogram": 0}
        
        # Calculate EMAs
        k_fast = 2 / (fast_period + 1)
        k_slow = 2 / (slow_period + 1)
        
        ema_fast = float(np.mean(self.closes[:fast_period]))
        ema_slow = float(np.mean(self.closes[:slow_period]))
        
        macd_values = []
        
        for i in range(slow_period, len(self.closes)):
            # Update EMAs
            if i >= fast_period:
                ema_fast = float(self.closes[i]) * k_fast + ema_fast * (1 - k_fast)
            ema_slow = float(self.closes[i]) * k_slow + ema_slow * (1 - k_slow)
            
            macd_line = ema_fast - ema_slow
            macd_values.append(macd_line)
        
        if not macd_values:
            return {"macd": 0, "signal": 0, "histogram": 0}
        
        # Calculate signal line
        macd_line = macd_values[0]
        
        if len(macd_values) >= signal_period:
            k_signal = 2 / (signal_period + 1)
            signal = float(np.mean(macd_values[:signal_period]))
            for val in macd_values[signal_period:]:
                signal = val * k_signal + signal * (1 - k_signal)
        else:
            signal = float(np.mean(macd_values))
        
        histogram = macd_line - signal
        
        return {
            "macd": macd_line,
            "signal": signal,
            "histogram": histogram
        }
    
    def stochastic(self, 
                   k_period: int = 14,
                   d_period: int = 3) -> Dict[str, float]:
        """
        Stochastic Oscillator
        
        Args:
            k_period: %K period (default: 14)
            d_period: %D period (default: 3)
            
        Returns:
            Dictionary with %K and %D values
        """
        if len(self.highs) < k_period:
            return {"k": 50, "d": 50}
        
        highest = float(np.max(self.highs[:k_period]))
        lowest = float(np.min(self.lows[:k_period]))
        
        if highest == lowest:
            k = 50.0
        else:
            k = ((float(self.closes[0]) - lowest) / (highest - lowest)) * 100
        
        # %D is typically SMA of %K
        d = k  # Simplified
        
        return {"k": k, "d": d}
    
    def williams_r(self, period: int = 14) -> float:
        """
        Williams %R
        
        Args:
            period: Period (default: 14)
            
        Returns:
            Williams %R value (-100 to 0)
        """
        if len(self.highs) < period:
            return -50.0
        
        highest = float(np.max(self.highs[:period]))
        lowest = float(np.min(self.lows[:period]))
        
        if highest == lowest:
            return -50.0
        
        return float(((highest - float(self.closes[0])) / (highest - lowest)) * -100)
    
    def cci(self, period: int = 20) -> float:
        """
        Commodity Channel Index
        
        Args:
            period: Period (default: 20)
            
        Returns:
            CCI value
        """
        if len(self.highs) < period:
            return 0.0
        
        typical_prices = (self.highs[:period] + self.lows[:period] + self.closes[:period]) / 3
        sma = float(np.mean(typical_prices))
        mean_deviation = float(np.mean(np.abs(typical_prices - sma)))
        
        if mean_deviation == 0:
            return 0.0
        
        return float((typical_prices[0] - sma) / (0.015 * mean_deviation))
    
    def mfi(self, period: int = 14) -> float:
        """
        Money Flow Index
        
        Args:
            period: Period (default: 14)
            
        Returns:
            MFI value (0-100)
        """
        if len(self.closes) < period:
            return 50.0
        
        pos_flow = 0
        neg_flow = 0
        
        for i in range(period):
            typical_price = (self.highs[i] + self.lows[i] + self.closes[i]) / 3
            raw_mf = typical_price * self.volumes[i]
            
            if i < len(self.closes) - 1:
                next_tp = (self.highs[i + 1] + self.lows[i + 1] + self.closes[i + 1]) / 3
                if typical_price > next_tp:
                    pos_flow += raw_mf
                else:
                    neg_flow += raw_mf
        
        if neg_flow == 0:
            return 100.0
        
        mfi = 100 - (100 / (1 + pos_flow / neg_flow))
        return float(mfi)
    
    def roc(self, period: int = 12) -> float:
        """
        Rate of Change
        
        Args:
            period: Period (default: 12)
            
        Returns:
            ROC value (%)
        """
        if len(self.closes) < period + 1:
            return 0.0
        
        return float(((self.closes[0] - self.closes[period]) / self.closes[period]) * 100)
    
    def momentum(self, period: int = 10) -> float:
        """
        Momentum
        
        Args:
            period: Period (default: 10)
            
        Returns:
            Momentum value
        """
        if len(self.closes) < period + 1:
            return 0.0
        
        return float(self.closes[0] - self.closes[period])
    
    # ============================================================
    # Volatility Indicators
    # ============================================================
    
    def atr(self, period: int = 14) -> float:
        """
        Average True Range
        
        Args:
            period: Period (default: 14)
            
        Returns:
            ATR value
        """
        if len(self.highs) < period + 1:
            return float(self.highs[0] - self.lows[0]) if len(self.highs) > 0 else 0
        
        tr_list = []
        for i in range(period):
            tr = max(
                self.highs[i] - self.lows[i],
                abs(self.highs[i] - self.closes[i + 1]),
                abs(self.lows[i] - self.closes[i + 1])
            )
            tr_list.append(tr)
        
        return float(np.mean(tr_list))
    
    def bollinger_bands(self, 
                        period: int = 20,
                        std_dev: float = 2.0) -> Dict[str, float]:
        """
        Bollinger Bands
        
        Args:
            period: SMA period (default: 20)
            std_dev: Standard deviation multiplier (default: 2.0)
            
        Returns:
            Dictionary with upper, middle, lower bands
        """
        if len(self.closes) < period:
            return {
                "upper": float(self.closes[0]) if len(self.closes) > 0 else 0,
                "middle": float(self.closes[0]) if len(self.closes) > 0 else 0,
                "lower": float(self.closes[0]) if len(self.closes) > 0 else 0
            }
        
        middle = float(np.mean(self.closes[:period]))
        std = float(np.std(self.closes[:period]))
        
        return {
            "upper": middle + (std * std_dev),
            "middle": middle,
            "lower": middle - (std * std_dev)
        }
    
    def keltner_channels(self,
                         ema_period: int = 20,
                         atr_period: int = 10,
                         multiplier: float = 2.0) -> Dict[str, float]:
        """
        Keltner Channels
        
        Args:
            ema_period: EMA period (default: 20)
            atr_period: ATR period (default: 10)
            multiplier: ATR multiplier (default: 2.0)
            
        Returns:
            Dictionary with upper, middle, lower channels
        """
        middle = self.ema(ema_period)
        atr_value = self.atr(atr_period)
        
        return {
            "upper": middle + (atr_value * multiplier),
            "middle": middle,
            "lower": middle - (atr_value * multiplier)
        }
    
    def donchian_channels(self, period: int = 20) -> Dict[str, float]:
        """
        Donchian Channels
        
        Args:
            period: Period (default: 20)
            
        Returns:
            Dictionary with upper, middle, lower channels
        """
        if len(self.highs) < period:
            return {
                "upper": float(self.highs[0]) if len(self.highs) > 0 else 0,
                "middle": float(self.closes[0]) if len(self.closes) > 0 else 0,
                "lower": float(self.lows[0]) if len(self.lows) > 0 else 0
            }
        
        upper = float(np.max(self.highs[:period]))
        lower = float(np.min(self.lows[:period]))
        
        return {
            "upper": upper,
            "middle": (upper + lower) / 2,
            "lower": lower
        }
    
    # ============================================================
    # Trend Indicators
    # ============================================================
    
    def adx(self, period: int = 14) -> Dict[str, float]:
        """
        Average Directional Index
        
        Args:
            period: Period (default: 14)
            
        Returns:
            Dictionary with ADX, +DI, -DI
        """
        if len(self.highs) < period + 1:
            return {"adx": 25, "plus_di": 25, "minus_di": 25}
        
        plus_dm = 0
        minus_dm = 0
        tr_sum = 0
        
        for i in range(period):
            high_diff = self.highs[i] - self.highs[i + 1]
            low_diff = self.lows[i + 1] - self.lows[i]
            
            plus_dm += high_diff if (high_diff > low_diff and high_diff > 0) else 0
            minus_dm += low_diff if (low_diff > high_diff and low_diff > 0) else 0
            
            tr = max(
                self.highs[i] - self.lows[i],
                abs(self.highs[i] - self.closes[i + 1]),
                abs(self.lows[i] - self.closes[i + 1])
            )
            tr_sum += tr
        
        atr_value = tr_sum / period
        plus_di = (plus_dm / period) / atr_value * 100 if atr_value > 0 else 0
        minus_di = (minus_dm / period) / atr_value * 100 if atr_value > 0 else 0
        
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0
        
        return {"adx": dx, "plus_di": plus_di, "minus_di": minus_di}
    
    def aroon(self, period: int = 25) -> Dict[str, float]:
        """
        Aroon Indicator
        
        Args:
            period: Period (default: 25)
            
        Returns:
            Dictionary with Aroon Up, Aroon Down, Oscillator
        """
        if len(self.highs) < period:
            return {"up": 50, "down": 50, "oscillator": 0}
        
        # Find highest high and lowest low positions
        high_idx = 0
        low_idx = 0
        max_high = self.highs[0]
        min_low = self.lows[0]
        
        for i in range(period):
            if self.highs[i] >= max_high:
                max_high = self.highs[i]
                high_idx = i
            if self.lows[i] <= min_low:
                min_low = self.lows[i]
                low_idx = i
        
        aroon_up = ((period - high_idx) / period) * 100
        aroon_down = ((period - low_idx) / period) * 100
        
        return {
            "up": aroon_up,
            "down": aroon_down,
            "oscillator": aroon_up - aroon_down
        }
    
    def dpo(self, period: int = 20) -> float:
        """
        Detrended Price Oscillator
        
        Args:
            period: Period (default: 20)
            
        Returns:
            DPO value
        """
        if len(self.closes) < period:
            return 0.0
        
        sma = float(np.mean(self.closes[:period]))
        shift = period // 2 + 1
        
        if shift < len(self.closes):
            return float(self.closes[0] - self.closes[shift])
        return float(self.closes[0] - sma)
    
    def mass_index(self, period: int = 25) -> float:
        """
        Mass Index
        
        Args:
            period: Period (default: 25)
            
        Returns:
            Mass Index value
        """
        if len(self.highs) < period:
            return 1.0
        
        diffs = self.highs[:period] - self.lows[:period]
        
        # Simple moving averages for ratio
        ema1 = float(np.mean(diffs))
        ema2 = float(np.mean(diffs))
        
        if ema2 == 0:
            return 1.0
        
        return ema1 / ema2
    
    # ============================================================
    # Volume Indicators
    # ============================================================
    
    def obv(self) -> float:
        """
        On Balance Volume
        
        Returns:
            OBV value
        """
        obv = 0
        
        for i in range(min(len(self.closes) - 1, 50)):
            if self.closes[i] > self.closes[i + 1]:
                obv += self.volumes[i]
            elif self.closes[i] < self.closes[i + 1]:
                obv -= self.volumes[i]
        
        return float(obv)
    
    def vwap(self) -> float:
        """
        Volume Weighted Average Price
        
        Returns:
            VWAP value
        """
        typical_prices = (self.highs + self.lows + self.closes) / 3
        cumulative_tp_vol = np.sum(typical_prices[:min(20, len(typical_prices))] * 
                                   self.volumes[:min(20, len(self.volumes))])
        cumulative_vol = np.sum(self.volumes[:min(20, len(self.volumes))])
        
        if cumulative_vol == 0:
            return float(self.closes[0]) if len(self.closes) > 0 else 0
        
        return float(cumulative_tp_vol / cumulative_vol)
    
    def vwma(self, period: int = 20) -> float:
        """
        Volume Weighted Moving Average
        
        Args:
            period: Period (default: 20)
            
        Returns:
            VWMA value
        """
        if len(self.closes) < period:
            return float(self.closes[0]) if len(self.closes) > 0 else 0
        
        pv_sum = np.sum(self.closes[:period] * self.volumes[:period])
        v_sum = np.sum(self.volumes[:period])
        
        if v_sum == 0:
            return float(self.closes[0])
        
        return float(pv_sum / v_sum)
    
    def adl(self) -> float:
        """
        Accumulation/Distribution Line
        
        Returns:
            ADL value
        """
        ad = 0
        
        for i in range(min(len(self.closes), 50)):
            clv = 0
            if self.highs[i] != self.lows[i]:
                clv = ((self.closes[i] - self.lows[i]) - 
                       (self.highs[i] - self.closes[i])) / (self.highs[i] - self.lows[i])
            ad += clv * self.volumes[i]
        
        return float(ad)
    
    def cmf(self, period: int = 20) -> float:
        """
        Chaikin Money Flow
        
        Args:
            period: Period (default: 20)
            
        Returns:
            CMF value
        """
        if len(self.closes) < period:
            return 0.0
        
        ad_sum = 0
        vol_sum = 0
        
        for i in range(period):
            clv = 0
            if self.highs[i] != self.lows[i]:
                clv = ((self.closes[i] - self.lows[i]) - 
                       (self.highs[i] - self.closes[i])) / (self.highs[i] - self.lows[i])
            ad_sum += clv * self.volumes[i]
            vol_sum += self.volumes[i]
        
        return float(ad_sum / vol_sum) if vol_sum > 0 else 0.0
    
    def force_index(self, period: int = 13) -> float:
        """
        Force Index
        
        Args:
            period: EMA period (default: 13)
            
        Returns:
            Force Index value
        """
        if len(self.closes) < 2:
            return 0.0
        
        fi = (self.closes[0] - self.closes[1]) * self.volumes[0]
        
        # Simple EMA of Force Index
        k = 2 / (period + 1)
        ema_fi = fi
        
        return float(ema_fi)
    
    def eom(self, period: int = 14) -> float:
        """
        Ease of Movement
        
        Args:
            period: Period (default: 14)
            
        Returns:
            EOM value
        """
        if len(self.highs) < period:
            return 0.0
        
        eom_values = []
        
        for i in range(min(period, len(self.highs) - 1)):
            high_low_range = self.highs[i] - self.lows[i]
            distance_moved = ((self.highs[i] + self.lows[i]) / 2) - \
                            ((self.highs[i + 1] + self.lows[i + 1]) / 2)
            
            box_ratio = (self.volumes[i] / 1000000) / high_low_range if high_low_range > 0 else 1
            
            eom_values.append(distance_moved / box_ratio if box_ratio > 0 else 0)
        
        return float(np.mean(eom_values)) if eom_values else 0.0
    
    # ============================================================
    # Volatility Measure
    # ============================================================
    
    def volatility(self, period: int = 20) -> float:
        """
        Calculate volatility (%)
        
        Args:
            period: Period (default: 20)
            
        Returns:
            Volatility percentage
        """
        if len(self.closes) < period + 1:
            return 0.0
        
        returns = []
        for i in range(min(len(self.closes) - 1, period)):
            ret = (self.closes[i] - self.closes[i + 1]) / self.closes[i + 1]
            returns.append(ret)
        
        return float(np.std(returns) * 100)
    
    def max_drawdown(self) -> float:
        """
        Maximum Drawdown
        
        Returns:
            Max drawdown percentage
        """
        if len(self.closes) == 0:
            return 0.0
        
        peak = self.closes[0]
        max_dd = 0
        
        for price in self.closes:
            if price > peak:
                peak = price
            dd = (peak - price) / peak
            if dd > max_dd:
                max_dd = dd
        
        return float(max_dd * 100)
    
    # ============================================================
    # Support & Resistance
    # ============================================================
    
    def pivot_points(self) -> Dict[str, float]:
        """
        Classic Pivot Points
        
        Returns:
            Dictionary with pivot, support, resistance levels
        """
        if len(self.highs) == 0 or len(self.lows) == 0 or len(self.closes) == 0:
            return {"pivot": 0, "s1": 0, "s2": 0, "r1": 0, "r2": 0}
        
        pivot = (self.highs[0] + self.lows[0] + self.closes[0]) / 3
        s1 = 2 * pivot - self.highs[0]
        s2 = pivot - (self.highs[0] - self.lows[0])
        r1 = 2 * pivot - self.lows[0]
        r2 = pivot + (self.highs[0] - self.lows[0])
        
        return {
            "pivot": pivot,
            "s1": s1,
            "s2": s2,
            "r1": r1,
            "r2": r2
        }
    
    def fibonacci_levels(self) -> Dict[str, float]:
        """
        Fibonacci Retracement Levels
        
        Returns:
            Dictionary with Fibonacci levels
        """
        if len(self.highs) == 0 or len(self.lows) == 0:
            return {}
        
        high = float(np.max(self.highs[:50])) if len(self.highs) >= 50 else float(self.highs[0])
        low = float(np.min(self.lows[:50])) if len(self.lows) >= 50 else float(self.lows[0])
        
        diff = high - low
        
        return {
            "0": high,
            "0.236": high - diff * 0.236,
            "0.382": high - diff * 0.382,
            "0.5": high - diff * 0.5,
            "0.618": high - diff * 0.618,
            "0.786": high - diff * 0.786,
            "1": low
        }
    
    # ============================================================
    # Signal Generation
    # ============================================================
    
    def rsi_signal(self, period: int = 14) -> IndicatorResult:
        """Generate RSI signal"""
        rsi = self.rsi(period)
        
        if rsi < 30:
            signal = "OVERSOLD_BUY"
        elif rsi < 40:
            signal = "APPROACHING_OVERSOLD"
        elif rsi > 70:
            signal = "OVERBOUGHT_SELL"
        elif rsi > 60:
            signal = "APPROACHING_OVERBOUGHT"
        else:
            signal = "NEUTRAL"
        
        return IndicatorResult(value=rsi, signal=signal, details={"period": period})
    
    def macd_signal(self) -> IndicatorResult:
        """Generate MACD signal"""
        macd = self.macd()
        
        if macd["macd"] > macd["signal"] and macd["histogram"] > 0:
            signal = "BULLISH"
        elif macd["macd"] < macd["signal"] and macd["histogram"] < 0:
            signal = "BEARISH"
        elif macd["histogram"] > 0:
            signal = "WEAK_BULLISH"
        elif macd["histogram"] < 0:
            signal = "WEAK_BEARISH"
        else:
            signal = "NEUTRAL"
        
        return IndicatorResult(
            value=macd["macd"],
            signal=signal,
            details=macd
        )
    
    def bollinger_signal(self) -> IndicatorResult:
        """Generate Bollinger Bands signal"""
        boll = self.bollinger_bands()
        
        if self.closes[0] < boll["lower"]:
            signal = "OVERSOLD_BUY"
        elif self.closes[0] > boll["upper"]:
            signal = "OVERBOUGHT_SELL"
        elif self.closes[0] < boll["middle"]:
            signal = "BELOW_AVG"
        elif self.closes[0] > boll["middle"]:
            signal = "ABOVE_AVG"
        else:
            signal = "NEUTRAL"
        
        return IndicatorResult(
            value=self.closes[0],
            signal=signal,
            details=boll
        )
    
    def adx_signal(self, period: int = 14) -> IndicatorResult:
        """Generate ADX signal"""
        adx = self.adx(period)
        
        if adx["adx"] > 40:
            if adx["plus_di"] > adx["minus_di"]:
                signal = "STRONG_UPTREND"
            else:
                signal = "STRONG_DOWNTREND"
        elif adx["adx"] > 25:
            if adx["plus_di"] > adx["minus_di"]:
                signal = "UPTREND"
            else:
                signal = "DOWNTREND"
        elif adx["adx"] > 15:
            signal = "WEAK_TREND"
        else:
            signal = "RANGING"
        
        return IndicatorResult(
            value=adx["adx"],
            signal=signal,
            details=adx
        )
    
    # ============================================================
    # Combined Analysis
    # ============================================================
    
    def all_indicators(self) -> Dict:
        """
        Calculate all indicators at once
        
        Returns:
            Dictionary with all indicator values
        """
        return {
            "sma_20": self.sma(20),
            "sma_50": self.sma(50) if len(self.closes) >= 50 else None,
            "ema_12": self.ema(12),
            "ema_26": self.ema(26),
            "rsi_14": self.rsi(14),
            "macd": self.macd(),
            "stochastic": self.stochastic(),
            "bollinger": self.bollinger_bands(),
            "adx": self.adx(),
            "atr_14": self.atr(14),
            "cci_20": self.cci(20),
            "williams_r": self.williams_r(),
            "mfi_14": self.mfi(14),
            "obv": self.obv(),
            "vwap": self.vwap(),
            "ichimoku": self.ichimoku(),
            "pivot_points": self.pivot_points(),
            "fibonacci": self.fibonacci_levels(),
            "volatility": self.volatility(),
            "max_drawdown": self.max_drawdown()
        }
    
    def trend_score(self) -> float:
        """
        Calculate trend score (0-100)
        
        Returns:
            Trend score
        """
        score = 50
        
        # Price vs SMAs
        if self.closes[0] > self.sma(20):
            score += 10
        if self.closes[0] > self.sma(50) if len(self.closes) >= 50 else False:
            score += 10
        
        # RSI
        rsi = self.rsi()
        if rsi > 50:
            score += 5
        if rsi > 60:
            score += 5
        
        # MACD
        macd = self.macd()
        if macd["macd"] > macd["signal"]:
            score += 10
        
        # ADX
        adx = self.adx()
        if adx["adx"] > 25 and adx["plus_di"] > adx["minus_di"]:
            score += 10
        
        return max(0, min(100, score))
    
    def momentum_score(self) -> float:
        """
        Calculate momentum score (0-100)
        
        Returns:
            Momentum score
        """
        score = 50
        
        # Price change
        if len(self.closes) >= 2:
            change = (self.closes[0] - self.closes[1]) / self.closes[1]
            if change > 0:
                score += 10
            if change > 0.02:
                score += 10
        
        # RSI
        rsi = self.rsi()
        if 40 < rsi < 70:
            score += 10
        
        # ROC
        roc = self.roc()
        if roc > 0:
            score += 10
        
        # Stochastic
        stoch = self.stochastic()
        if stoch["k"] > 50:
            score += 10
        
        return max(0, min(100, score))

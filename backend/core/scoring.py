"""
فیلترادیوم - Scoring Engine
Advanced stock analysis and scoring system
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class Signal(Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class Regime(Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"


@dataclass
class ScoreResult:
    """Result of scoring analysis"""
    total_score: float
    signal: Signal
    confidence: float
    regime: Regime
    technical: float
    fundamental: float
    moneyflow: float
    risk: float
    momentum: float
    details: Dict


class TechnicalAnalyzer:
    """Technical analysis calculations"""
    
    @staticmethod
    def sma(data: List[float], period: int) -> float:
        """Simple Moving Average"""
        if len(data) < period:
            return data[0] if data else 0
        return np.mean(data[:period])
    
    @staticmethod
    def ema(data: List[float], period: int) -> float:
        """Exponential Moving Average"""
        if len(data) < period:
            return data[0] if data else 0
        k = 2 / (period + 1)
        ema = np.mean(data[:period])
        for price in data[period:]:
            ema = price * k + ema * (1 - k)
        return ema
    
    @staticmethod
    def rsi(data: List[float], period: int = 14) -> float:
        """Relative Strength Index"""
        if len(data) < period + 1:
            return 50
        
        deltas = np.diff(data[:period + 1])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(data: List[float]) -> Dict[str, float]:
        """MACD indicator"""
        if len(data) < 26:
            return {"macd": 0, "signal": 0, "histogram": 0}
        
        k12 = 2 / 13
        k26 = 2 / 27
        
        ema12 = np.mean(data[:12])
        ema26 = np.mean(data[:26])
        
        for price in data[12:]:
            ema12 = price * k12 + ema12 * (1 - k12)
        for price in data[26:]:
            ema26 = price * k26 + ema26 * (1 - k26)
        
        macd_line = ema12 - ema26
        
        return {
            "macd": macd_line,
            "signal": 0,
            "histogram": macd_line
        }
    
    @staticmethod
    def bollinger_bands(data: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
        """Bollinger Bands"""
        if len(data) < period:
            return {"upper": data[0], "middle": data[0], "lower": data[0]}
        
        sma = np.mean(data[:period])
        std = np.std(data[:period])
        
        return {
            "upper": sma + (std * std_dev),
            "middle": sma,
            "lower": sma - (std * std_dev)
        }
    
    @staticmethod
    def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """Average True Range"""
        if len(highs) < period + 1:
            return highs[0] - lows[0] if highs and lows else 0
        
        tr_list = []
        for i in range(period):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i + 1]),
                abs(lows[i] - closes[i + 1])
            )
            tr_list.append(tr)
        
        return np.mean(tr_list)
    
    @staticmethod
    def stochastic(highs: List[float], lows: List[float], closes: List[float], 
                   k_period: int = 14, d_period: int = 3) -> Dict[str, float]:
        """Stochastic Oscillator"""
        if len(highs) < k_period:
            return {"k": 50, "d": 50}
        
        highest = max(highs[:k_period])
        lowest = min(lows[:k_period])
        
        if highest == lowest:
            k = 50
        else:
            k = ((closes[0] - lowest) / (highest - lowest)) * 100
        
        return {"k": k, "d": 50}
    
    @staticmethod
    def adx(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Dict[str, float]:
        """Average Directional Index"""
        if len(highs) < period + 1:
            return {"adx": 25, "plus_di": 25, "minus_di": 25}
        
        plus_dm = 0
        minus_dm = 0
        tr_sum = 0
        
        for i in range(period):
            high_diff = highs[i] - highs[i + 1]
            low_diff = lows[i + 1] - lows[i]
            
            plus_dm += high_diff if (high_diff > low_diff and high_diff > 0) else 0
            minus_dm += low_diff if (low_diff > high_diff and low_diff > 0) else 0
            
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i + 1]),
                abs(lows[i] - closes[i + 1])
            )
            tr_sum += tr
        
        atr = tr_sum / period
        plus_di = (plus_dm / period) / atr * 100 if atr > 0 else 0
        minus_di = (minus_dm / period) / atr * 100 if atr > 0 else 0
        
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0
        
        return {"adx": dx, "plus_di": plus_di, "minus_di": minus_di}
    
    @staticmethod
    def cci(highs: List[float], lows: List[float], closes: List[float], period: int = 20) -> float:
        """Commodity Channel Index"""
        if len(highs) < period:
            return 0
        
        typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs[:period], lows[:period], closes[:period])]
        sma = np.mean(typical_prices)
        mean_deviation = np.mean([abs(tp - sma) for tp in typical_prices])
        
        if mean_deviation == 0:
            return 0
        
        return (typical_prices[0] - sma) / (0.015 * mean_deviation)
    
    @staticmethod
    def williams_r(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """Williams %R"""
        if len(highs) < period:
            return -50
        
        highest = max(highs[:period])
        lowest = min(lows[:period])
        
        if highest == lowest:
            return -50
        
        return ((highest - closes[0]) / (highest - lowest)) * -100


class PatternAnalyzer:
    """Pattern recognition"""
    
    @staticmethod
    def detect_candle_patterns(opens: List[float], highs: List[float], 
                               lows: List[float], closes: List[float]) -> List[Dict]:
        """Detect candlestick patterns"""
        patterns = []
        
        if len(opens) < 3:
            return patterns
        
        o, h, l, c = opens[0], highs[0], lows[0], closes[0]
        body = abs(c - o)
        range_ = h - l
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        is_bullish = c > o
        
        # Doji
        if body < range_ * 0.1 and range_ > 0:
            patterns.append({"name": "DOJI", "type": "neutral", "reliability": 0.6})
        
        # Hammer
        if lower_wick > body * 2 and upper_wick < body * 0.5 and is_bullish:
            patterns.append({"name": "HAMMER", "type": "bullish", "reliability": 0.65})
        
        # Shooting Star
        if upper_wick > body * 2 and lower_wick < body * 0.5 and not is_bullish:
            patterns.append({"name": "SHOOTING_STAR", "type": "bearish", "reliability": 0.6})
        
        # Engulfing
        o1, c1 = opens[1], closes[1]
        if o1 > c1 and c > o and c > o1 and o < c1:
            patterns.append({"name": "BULLISH_ENGULFING", "type": "bullish", "reliability": 0.75})
        if o1 < c1 and c < o and c < o1 and o > c1:
            patterns.append({"name": "BEARISH_ENGULFING", "type": "bearish", "reliability": 0.75})
        
        # Three White Soldiers / Three Black Crows
        o2, c2 = opens[2], closes[2]
        if c > o and c1 > o1 and c2 > o2 and c > c1 and c1 > c2:
            patterns.append({"name": "THREE_WHITE_SOLDIERS", "type": "bullish", "reliability": 0.85})
        if c < o and c1 < o1 and c2 < o2 and c < c1 and c1 < c2:
            patterns.append({"name": "THREE_BLACK_CROWS", "type": "bearish", "reliability": 0.85})
        
        return patterns
    
    @staticmethod
    def detect_chart_patterns(closes: List[float], highs: List[float], 
                              lows: List[float]) -> List[Dict]:
        """Detect chart patterns"""
        patterns = []
        
        if len(closes) < 20:
            return patterns
        
        # Double Top / Double Bottom
        recent_highs = highs[:10]
        recent_lows = lows[:10]
        
        max1 = max(recent_highs[:5])
        max2 = max(recent_highs[5:10])
        
        if abs(max1 - max2) / max1 < 0.02:
            patterns.append({"name": "DOUBLE_TOP", "type": "bearish", "reliability": 0.7})
        
        min1 = min(recent_lows[:5])
        min2 = min(recent_lows[5:10])
        
        if abs(min1 - min2) / min1 < 0.02:
            patterns.append({"name": "DOUBLE_BOTTOM", "type": "bullish", "reliability": 0.7})
        
        # Triangle
        highs_slope = (highs[0] - highs[10]) / 10
        lows_slope = (lows[0] - lows[10]) / 10
        
        if highs_slope < 0 and lows_slope > 0:
            patterns.append({"name": "SYMMETRICAL_TRIANGLE", "type": "neutral", "reliability": 0.65})
        elif highs_slope < 0 and abs(lows_slope) < 0.01:
            patterns.append({"name": "ASCENDING_TRIANGLE", "type": "bullish", "reliability": 0.7})
        
        return patterns


class MoneyFlowAnalyzer:
    """Money flow analysis"""
    
    @staticmethod
    def calculate_adl(highs: List[float], lows: List[float], 
                      closes: List[float], volumes: List[float]) -> float:
        """Accumulation/Distribution Line"""
        ad = 0
        for i in range(min(len(closes), 50)):
            clv = 0
            if highs[i] != lows[i]:
                clv = ((closes[i] - lows[i]) - (highs[i] - closes[i])) / (highs[i] - lows[i])
            ad += clv * volumes[i]
        return ad
    
    @staticmethod
    def calculate_cmf(highs: List[float], lows: List[float], 
                      closes: List[float], volumes: List[float], period: int = 20) -> float:
        """Chaikin Money Flow"""
        ad_sum = 0
        vol_sum = 0
        
        for i in range(min(len(closes), period)):
            clv = 0
            if highs[i] != lows[i]:
                clv = ((closes[i] - lows[i]) - (highs[i] - closes[i])) / (highs[i] - lows[i])
            ad_sum += clv * volumes[i]
            vol_sum += volumes[i]
        
        return ad_sum / vol_sum if vol_sum > 0 else 0
    
    @staticmethod
    def calculate_mfi(highs: List[float], lows: List[float], 
                      closes: List[float], volumes: List[float], period: int = 14) -> float:
        """Money Flow Index"""
        if len(closes) < period:
            return 50
        
        pos_flow = 0
        neg_flow = 0
        
        for i in range(period):
            typical_price = (highs[i] + lows[i] + closes[i]) / 3
            raw_mf = typical_price * volumes[i]
            
            if i < len(closes) - 1:
                if typical_price > (highs[i + 1] + lows[i + 1] + closes[i + 1]) / 3:
                    pos_flow += raw_mf
                else:
                    neg_flow += raw_mf
        
        if neg_flow == 0:
            return 100
        
        mfi = 100 - (100 / (1 + pos_flow / neg_flow))
        return mfi


class RiskAnalyzer:
    """Risk analysis"""
    
    @staticmethod
    def calculate_volatility(closes: List[float], period: int = 20) -> float:
        """Calculate volatility"""
        if len(closes) < period:
            return 0
        
        returns = []
        for i in range(min(len(closes) - 1, period)):
            returns.append((closes[i] - closes[i + 1]) / closes[i + 1])
        
        return np.std(returns) * 100
    
    @staticmethod
    def calculate_max_drawdown(closes: List[float]) -> float:
        """Calculate maximum drawdown"""
        if not closes:
            return 0
        
        peak = closes[0]
        max_dd = 0
        
        for price in closes:
            if price > peak:
                peak = price
            dd = (peak - price) / peak
            if dd > max_dd:
                max_dd = dd
        
        return max_dd * 100
    
    @staticmethod
    def calculate_sharpe(closes: List[float], risk_free_rate: float = 0.15) -> float:
        """Calculate Sharpe Ratio"""
        if len(closes) < 20:
            return 0
        
        returns = []
        for i in range(min(len(closes) - 1, 252)):
            returns.append((closes[i] - closes[i + 1]) / closes[i + 1])
        
        mean_return = np.mean(returns)
        std = np.std(returns)
        
        if std == 0:
            return 0
        
        annualized_return = mean_return * 252
        annualized_std = std * np.sqrt(252)
        
        return (annualized_return - risk_free_rate) / annualized_std
    
    @staticmethod
    def calculate_kelly(closes: List[float]) -> Dict[str, float]:
        """Calculate Kelly Criterion"""
        if len(closes) < 20:
            return {"full_kelly": 0, "half_kelly": 0, "win_rate": 0}
        
        wins = 0
        losses = 0
        total_win = 0
        total_loss = 0
        
        for i in range(min(len(closes) - 1, 100)):
            change = closes[i] - closes[i + 1]
            if change > 0:
                wins += 1
                total_win += change
            else:
                losses += 1
                total_loss += abs(change)
        
        win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0
        avg_win = total_win / wins if wins > 0 else 0
        avg_loss = total_loss / losses if losses > 0 else 1
        win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        kelly = win_rate - ((1 - win_rate) / win_loss_ratio) if win_loss_ratio > 0 else 0
        
        return {
            "full_kelly": kelly * 100,
            "half_kelly": (kelly / 2) * 100,
            "win_rate": win_rate * 100,
            "win_loss_ratio": win_loss_ratio
        }


class ScoringEngine:
    """Main scoring engine"""
    
    def __init__(self):
        self.tech_analyzer = TechnicalAnalyzer()
        self.pattern_analyzer = PatternAnalyzer()
        self.moneyflow_analyzer = MoneyFlowAnalyzer()
        self.risk_analyzer = RiskAnalyzer()
    
    def calculate_score(self, 
                       opens: List[float],
                       highs: List[float],
                       lows: List[float],
                       closes: List[float],
                       volumes: List[float],
                       client_type: Optional[Dict] = None) -> ScoreResult:
        """
        Calculate comprehensive stock score
        
        Returns:
            ScoreResult with all analysis data
        """
        # Technical Analysis
        tech_score = self._calculate_technical_score(highs, lows, closes, volumes)
        
        # Pattern Analysis
        pattern_score = self._calculate_pattern_score(opens, highs, lows, closes)
        
        # Money Flow Analysis
        mf_score = self._calculate_moneyflow_score(highs, lows, closes, volumes, client_type)
        
        # Risk Analysis
        risk_score = self._calculate_risk_score(closes)
        
        # Momentum Analysis
        momentum_score = self._calculate_momentum_score(closes, highs, lows, volumes)
        
        # Detect regime
        regime = self._detect_regime(closes, volumes)
        
        # Calculate weights based on regime
        weights = self._get_weights(regime)
        
        # Calculate total score
        total_score = (
            tech_score * weights["technical"] +
            pattern_score * weights["pattern"] +
            mf_score * weights["moneyflow"] +
            risk_score * weights["risk"] +
            momentum_score * weights["momentum"]
        )
        
        # Normalize to 0-100
        total_score = max(0, min(100, total_score))
        
        # Generate signal
        signal, confidence = self._generate_signal(total_score, tech_score, mf_score)
        
        return ScoreResult(
            total_score=total_score,
            signal=signal,
            confidence=confidence,
            regime=regime,
            technical=tech_score,
            fundamental=0,  # Would need fundamental data
            moneyflow=mf_score,
            risk=risk_score,
            momentum=momentum_score,
            details={
                "weights": weights,
                "regime": regime.value,
                "signal": signal.value
            }
        )
    
    def _calculate_technical_score(self, highs, lows, closes, volumes) -> float:
        """Calculate technical score"""
        score = 50  # Base score
        
        # RSI
        rsi = self.tech_analyzer.rsi(closes)
        if rsi < 30:
            score += 15
        elif rsi > 70:
            score -= 10
        
        # MACD
        macd = self.tech_analyzer.macd(closes)
        if macd["macd"] > 0:
            score += 10
        
        # Bollinger
        boll = self.tech_analyzer.bollinger_bands(closes)
        if closes[0] < boll["lower"]:
            score += 10
        elif closes[0] > boll["upper"]:
            score -= 5
        
        # ADX
        adx = self.tech_analyzer.adx(highs, lows, closes)
        if adx["adx"] > 25:
            if adx["plus_di"] > adx["minus_di"]:
                score += 10
            else:
                score -= 5
        
        # CCI
        cci = self.tech_analyzer.cci(highs, lows, closes)
        if cci < -100:
            score += 10
        elif cci > 100:
            score -= 5
        
        return max(0, min(100, score))
    
    def _calculate_pattern_score(self, opens, highs, lows, closes) -> float:
        """Calculate pattern score"""
        score = 50
        
        # Candle patterns
        candle_patterns = self.pattern_analyzer.detect_candle_patterns(opens, highs, lows, closes)
        for p in candle_patterns:
            if p["type"] == "bullish":
                score += 10
            elif p["type"] == "bearish":
                score -= 10
        
        # Chart patterns
        chart_patterns = self.pattern_analyzer.detect_chart_patterns(closes, highs, lows)
        for p in chart_patterns:
            if p["type"] == "bullish":
                score += 10
            elif p["type"] == "bearish":
                score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_moneyflow_score(self, highs, lows, closes, volumes, client_type) -> float:
        """Calculate money flow score"""
        score = 50
        
        # ADL
        adl = self.moneyflow_analyzer.calculate_adl(highs, lows, closes, volumes)
        if adl > 0:
            score += 10
        
        # CMF
        cmf = self.moneyflow_analyzer.calculate_cmf(highs, lows, closes, volumes)
        if cmf > 0.05:
            score += 10
        elif cmf < -0.05:
            score -= 10
        
        # MFI
        mfi = self.moneyflow_analyzer.calculate_mfi(highs, lows, closes, volumes)
        if mfi < 20:
            score += 15
        elif mfi > 80:
            score -= 10
        
        # Client type
        if client_type:
            buy_vol = client_type.get("individual_buy_volume", 0)
            sell_vol = client_type.get("individual_sell_volume", 0)
            if sell_vol > 0 and buy_vol > sell_vol * 1.2:
                score += 15
        
        return max(0, min(100, score))
    
    def _calculate_risk_score(self, closes) -> float:
        """Calculate risk score (inverted: lower risk = higher score)"""
        score = 70
        
        # Volatility
        vol = self.risk_analyzer.calculate_volatility(closes)
        if vol > 5:
            score -= 20
        elif vol > 3:
            score -= 10
        
        # Max Drawdown
        dd = self.risk_analyzer.calculate_max_drawdown(closes)
        if dd > 20:
            score -= 20
        elif dd > 10:
            score -= 10
        
        # Sharpe
        sharpe = self.risk_analyzer.calculate_sharpe(closes)
        if sharpe < 0:
            score -= 15
        elif sharpe > 1:
            score += 10
        
        return max(0, min(100, score))
    
    def _calculate_momentum_score(self, closes, highs, lows, volumes) -> float:
        """Calculate momentum score"""
        score = 50
        
        # Short-term trend
        if len(closes) >= 5:
            sma5 = np.mean(closes[:5])
            if closes[0] > sma5:
                score += 10
        
        # Medium-term trend
        if len(closes) >= 20:
            sma20 = np.mean(closes[:20])
            if closes[0] > sma20:
                score += 10
        
        # Price change
        if len(closes) >= 2:
            change = (closes[0] - closes[1]) / closes[1]
            if change > 0:
                score += 10
            elif change < -0.03:
                score -= 10
        
        # Volume trend
        if len(volumes) >= 5:
            avg_vol = np.mean(volumes[:5])
            if volumes[0] > avg_vol * 1.5:
                score += 10
        
        return max(0, min(100, score))
    
    def _detect_regime(self, closes, volumes) -> Regime:
        """Detect market regime"""
        if len(closes) < 20:
            return Regime.SIDEWAYS
        
        # Volatility
        vol = self.risk_analyzer.calculate_volatility(closes)
        
        # Trend
        sma20 = np.mean(closes[:20])
        sma50 = np.mean(closes[:50]) if len(closes) >= 50 else sma20
        trend = (sma20 - sma50) / sma50 * 100
        
        if vol > 4:
            return Regime.VOLATILE
        elif trend > 2:
            return Regime.BULL
        elif trend < -2:
            return Regime.BEAR
        else:
            return Regime.SIDEWAYS
    
    def _get_weights(self, regime: Regime) -> Dict[str, float]:
        """Get weights based on regime"""
        weights = {
            Regime.BULL: {"technical": 0.30, "pattern": 0.15, "moneyflow": 0.25, "risk": 0.15, "momentum": 0.15},
            Regime.BEAR: {"technical": 0.20, "pattern": 0.10, "moneyflow": 0.15, "risk": 0.30, "momentum": 0.25},
            Regime.SIDEWAYS: {"technical": 0.25, "pattern": 0.20, "moneyflow": 0.20, "risk": 0.20, "momentum": 0.15},
            Regime.VOLATILE: {"technical": 0.15, "pattern": 0.10, "moneyflow": 0.15, "risk": 0.35, "momentum": 0.25},
        }
        return weights.get(regime, weights[Regime.SIDEWAYS])
    
    def _generate_signal(self, total_score: float, tech_score: float, mf_score: float) -> Tuple[Signal, float]:
        """Generate trading signal"""
        if total_score >= 80:
            return Signal.STRONG_BUY, 0.9
        elif total_score >= 65:
            return Signal.BUY, 0.75
        elif total_score >= 50:
            return Signal.HOLD, 0.5
        elif total_score >= 35:
            return Signal.SELL, 0.75
        else:
            return Signal.STRONG_SELL, 0.9

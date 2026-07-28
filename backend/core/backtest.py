"""
فیلترادیوم - Backtest Engine
Strategy backtesting using historical price data
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class StrategyType(Enum):
    """Strategy types"""
    RSI_OVERSOLD = "rsi_oversold"
    MACD_CROSS = "macd_cross"
    BOLLINGER_BOUNCE = "bollinger_bounce"
    MOVING_AVERAGE_CROSS = "ma_cross"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    CUSTOM = "custom"


@dataclass
class Trade:
    """Single trade record"""
    entry_date: datetime
    exit_date: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    quantity: int
    side: str  # "long" or "short"
    pnl: float = 0
    pnl_pct: float = 0
    exit_reason: str = ""


@dataclass
class BacktestResult:
    """Backtest results"""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    
    # Performance metrics
    total_return: float
    annual_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    
    # Trade list
    trades: List[Trade] = field(default_factory=list)
    
    # Equity curve
    equity_curve: List[float] = field(default_factory=list)


class BacktestEngine:
    """
    Backtesting engine for trading strategies
    
    Tests strategies against historical price data
    """
    
    def __init__(self, initial_capital: float = 100000000):
        """
        Initialize backtest engine
        
        Args:
            initial_capital: Starting capital in Rials
        """
        self.initial_capital = initial_capital
    
    def run_backtest(self,
                     closes: List[float],
                     highs: List[float],
                     lows: List[float],
                     volumes: List[float],
                     strategy: StrategyType,
                     params: Optional[Dict] = None) -> BacktestResult:
        """
        Run backtest with given strategy
        
        Args:
            closes: Closing prices (oldest first)
            highs: High prices
            lows: Low prices
            volumes: Volume data
            strategy: Strategy type
            params: Strategy parameters
            
        Returns:
            BacktestResult with all metrics
        """
        params = params or {}
        
        # Get signals based on strategy
        signals = self._generate_signals(
            closes, highs, lows, volumes, strategy, params
        )
        
        # Simulate trades
        trades = self._simulate_trades(closes, signals, params)
        
        # Calculate metrics
        return self._calculate_metrics(trades, closes, strategy.value)
    
    def _generate_signals(self,
                          closes: List[float],
                          highs: List[float],
                          lows: List[float],
                          volumes: List[float],
                          strategy: StrategyType,
                          params: Dict) -> List[int]:
        """
        Generate trading signals
        
        Returns:
            List of signals: 1=buy, -1=sell, 0=hold
        """
        n = len(closes)
        signals = [0] * n
        
        if strategy == StrategyType.RSI_OVERSOLD:
            period = params.get("rsi_period", 14)
            oversold = params.get("oversold", 30)
            overbought = params.get("overbought", 70)
            
            for i in range(period + 1, n):
                rsi = self._calculate_rsi(closes[i-period:i+1], period)
                if rsi < oversold:
                    signals[i] = 1  # Buy
                elif rsi > overbought:
                    signals[i] = -1  # Sell
        
        elif strategy == StrategyType.MACD_CROSS:
            fast = params.get("fast_period", 12)
            slow = params.get("slow_period", 26)
            
            for i in range(slow + 1, n):
                macd, signal = self._calculate_macd(closes[i-slow:i+1], fast, slow)
                if macd > signal and macd > 0:
                    signals[i] = 1
                elif macd < signal and macd < 0:
                    signals[i] = -1
        
        elif strategy == StrategyType.BOLLINGER_BOUNCE:
            period = params.get("period", 20)
            std_dev = params.get("std_dev", 2.0)
            
            for i in range(period, n):
                sma = np.mean(closes[i-period:i])
                std = np.std(closes[i-period:i])
                lower = sma - (std * std_dev)
                upper = sma + (std * std_dev)
                
                if closes[i] < lower:
                    signals[i] = 1  # Buy at lower band
                elif closes[i] > upper:
                    signals[i] = -1  # Sell at upper band
        
        elif strategy == StrategyType.MOVING_AVERAGE_CROSS:
            fast_period = params.get("fast_period", 10)
            slow_period = params.get("slow_period", 50)
            
            for i in range(slow_period, n):
                fast_ma = np.mean(closes[i-fast_period:i])
                slow_ma = np.mean(closes[i-slow_period:i])
                prev_fast = np.mean(closes[i-fast_period-1:i-1])
                prev_slow = np.mean(closes[i-slow_period-1:i-1])
                
                # Golden cross
                if fast_ma > slow_ma and prev_fast <= prev_slow:
                    signals[i] = 1
                # Death cross
                elif fast_ma < slow_ma and prev_fast >= prev_slow:
                    signals[i] = -1
        
        elif strategy == StrategyType.MOMENTUM:
            period = params.get("period", 10)
            threshold = params.get("threshold", 0.02)
            
            for i in range(period, n):
                momentum = (closes[i] - closes[i-period]) / closes[i-period]
                if momentum > threshold:
                    signals[i] = 1
                elif momentum < -threshold:
                    signals[i] = -1
        
        elif strategy == StrategyType.MEAN_REVERSION:
            period = params.get("period", 20)
            threshold = params.get("threshold", 2.0)
            
            for i in range(period, n):
                sma = np.mean(closes[i-period:i])
                std = np.std(closes[i-period:i])
                z_score = (closes[i] - sma) / std if std > 0 else 0
                
                if z_score < -threshold:
                    signals[i] = 1  # Buy when oversold
                elif z_score > threshold:
                    signals[i] = -1  # Sell when overbought
        
        return signals
    
    def _calculate_rsi(self, prices: List[float], period: int) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50
        
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_macd(self, prices: List[float], fast: int, slow: int) -> Tuple[float, float]:
        """Calculate MACD"""
        if len(prices) < slow:
            return 0, 0
        
        k_fast = 2 / (fast + 1)
        k_slow = 2 / (slow + 1)
        
        ema_fast = np.mean(prices[:fast])
        ema_slow = np.mean(prices[:slow])
        
        for price in prices[fast:]:
            ema_fast = price * k_fast + ema_fast * (1 - k_fast)
        for price in prices[slow:]:
            ema_slow = price * k_slow + ema_slow * (1 - k_slow)
        
        macd = ema_fast - ema_slow
        
        # Simplified signal line
        signal = macd * 0.8
        
        return macd, signal
    
    def _simulate_trades(self,
                        closes: List[float],
                        signals: List[int],
                        params: Dict) -> List[Trade]:
        """
        Simulate trades based on signals
        
        Returns:
            List of Trade objects
        """
        trades = []
        position = 0  # 0=no position, 1=long, -1=short
        entry_price = 0
        entry_date = datetime.utcnow()
        quantity = 0
        
        stop_loss = params.get("stop_loss", 0.05)  # 5%
        take_profit = params.get("take_profit", 0.10)  # 10%
        
        for i in range(len(closes)):
            price = closes[i]
            
            if signals[i] == 1 and position == 0:  # Buy signal
                # Enter long position
                quantity = int(self.initial_capital * 0.9 / price)
                entry_price = price
                entry_date = datetime.utcnow() - timedelta(days=len(closes) - i)
                position = 1
                
            elif signals[i] == -1 and position == 1:  # Sell signal
                # Exit long position
                pnl = (price - entry_price) * quantity
                pnl_pct = (price - entry_price) / entry_price * 100
                
                trade = Trade(
                    entry_date=entry_date,
                    exit_date=datetime.utcnow() - timedelta(days=len(closes) - i),
                    entry_price=entry_price,
                    exit_price=price,
                    quantity=quantity,
                    side="long",
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    exit_reason="signal"
                )
                trades.append(trade)
                
                position = 0
                quantity = 0
            
            # Check stop loss and take profit
            if position == 1:
                pnl_pct = (price - entry_price) / entry_price
                
                if pnl_pct <= -stop_loss:
                    # Stop loss hit
                    pnl = (price - entry_price) * quantity
                    trade = Trade(
                        entry_date=entry_date,
                        exit_date=datetime.utcnow() - timedelta(days=len(closes) - i),
                        entry_price=entry_price,
                        exit_price=price,
                        quantity=quantity,
                        side="long",
                        pnl=pnl,
                        pnl_pct=pnl_pct * 100,
                        exit_reason="stop_loss"
                    )
                    trades.append(trade)
                    position = 0
                    quantity = 0
                
                elif pnl_pct >= take_profit:
                    # Take profit hit
                    pnl = (price - entry_price) * quantity
                    trade = Trade(
                        entry_date=entry_date,
                        exit_date=datetime.utcnow() - timedelta(days=len(closes) - i),
                        entry_price=entry_price,
                        exit_price=price,
                        quantity=quantity,
                        side="long",
                        pnl=pnl,
                        pnl_pct=pnl_pct * 100,
                        exit_reason="take_profit"
                    )
                    trades.append(trade)
                    position = 0
                    quantity = 0
        
        return trades
    
    def _calculate_metrics(self,
                          trades: List[Trade],
                          closes: List[float],
                          strategy_name: str) -> BacktestResult:
        """
        Calculate backtest metrics
        
        Returns:
            BacktestResult with all metrics
        """
        if not trades:
            return BacktestResult(
                strategy_name=strategy_name,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow(),
                initial_capital=self.initial_capital,
                final_capital=self.initial_capital,
                total_return=0,
                annual_return=0,
                sharpe_ratio=0,
                sortino_ratio=0,
                max_drawdown=0,
                calmar_ratio=0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0,
                avg_win=0,
                avg_loss=0,
                profit_factor=0,
                trades=[],
                equity_curve=[self.initial_capital]
            )
        
        # Calculate PnL
        total_pnl = sum(t.pnl for t in trades)
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl <= 0]
        
        # Win rate
        win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
        
        # Average win/loss
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        # Profit factor
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Returns
        final_capital = self.initial_capital + total_pnl
        total_return = (final_capital - self.initial_capital) / self.initial_capital * 100
        
        # Annual return (assuming 252 trading days)
        days = len(closes)
        annual_return = ((final_capital / self.initial_capital) ** (252 / max(days, 1)) - 1) * 100
        
        # Sharpe ratio
        returns = [t.pnl_pct / 100 for t in trades]
        if returns:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe = (avg_return * 252) / (std_return * np.sqrt(252)) if std_return > 0 else 0
        else:
            sharpe = 0
        
        # Sortino ratio
        downside_returns = [r for r in returns if r < 0]
        if downside_returns:
            downside_std = np.std(downside_returns)
            sortino = (np.mean(returns) * 252) / (downside_std * np.sqrt(252)) if downside_std > 0 else 0
        else:
            sortino = sharpe
        
        # Max drawdown
        equity = [self.initial_capital]
        for t in trades:
            equity.append(equity[-1] + t.pnl)
        
        peak = equity[0]
        max_dd = 0
        for e in equity:
            if e > peak:
                peak = e
            dd = (peak - e) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        # Calmar ratio
        calmar = annual_return / max_dd if max_dd > 0 else 0
        
        return BacktestResult(
            strategy_name=strategy_name,
            start_date=trades[0].entry_date if trades else datetime.utcnow(),
            end_date=trades[-1].exit_date or datetime.utcnow() if trades else datetime.utcnow(),
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_dd,
            calmar_ratio=calmar,
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=win_rate,
            avg_win=float(avg_win),
            avg_loss=float(avg_loss),
            profit_factor=profit_factor,
            trades=trades,
            equity_curve=equity
        )
    
    def optimize_strategy(self,
                         closes: List[float],
                         highs: List[float],
                         lows: List[float],
                         volumes: List[float],
                         strategy: StrategyType,
                         param_grid: Dict[str, List]) -> Tuple[Dict, BacktestResult]:
        """
        Optimize strategy parameters
        
        Args:
            closes, highs, lows, volumes: Price data
            strategy: Strategy type
            param_grid: Parameter grid to search
            
        Returns:
            Best parameters and corresponding result
        """
        best_params = {}
        best_result = None
        best_sharpe = -float('inf')
        
        # Generate all parameter combinations
        import itertools
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        
        for combo in itertools.product(*values):
            params = dict(zip(keys, combo))
            
            result = self.run_backtest(
                closes, highs, lows, volumes, strategy, params
            )
            
            if result.sharpe_ratio > best_sharpe:
                best_sharpe = result.sharpe_ratio
                best_params = params
                best_result = result
        
        return best_params, best_result


class StrategyLibrary:
    """
    Pre-built trading strategies
    """
    
    @staticmethod
    def rsi_oversold(period: int = 14, oversold: int = 30, overbought: int = 70) -> Dict:
        """RSI Oversold/Overbought strategy"""
        return {
            "name": "RSI Oversold",
            "type": StrategyType.RSI_OVERSOLD,
            "params": {
                "rsi_period": period,
                "oversold": oversold,
                "overbought": overbought
            }
        }
    
    @staticmethod
    def macd_cross(fast: int = 12, slow: int = 26) -> Dict:
        """MACD Crossover strategy"""
        return {
            "name": "MACD Crossover",
            "type": StrategyType.MACD_CROSS,
            "params": {
                "fast_period": fast,
                "slow_period": slow
            }
        }
    
    @staticmethod
    def bollinger_bounce(period: int = 20, std_dev: float = 2.0) -> Dict:
        """Bollinger Band Bounce strategy"""
        return {
            "name": "Bollinger Bounce",
            "type": StrategyType.BOLLINGER_BOUNCE,
            "params": {
                "period": period,
                "std_dev": std_dev
            }
        }
    
    @staticmethod
    def ma_cross(fast: int = 10, slow: int = 50) -> Dict:
        """Moving Average Crossover strategy"""
        return {
            "name": "MA Crossover",
            "type": StrategyType.MOVING_AVERAGE_CROSS,
            "params": {
                "fast_period": fast,
                "slow_period": slow
            }
        }
    
    @staticmethod
    def momentum(period: int = 10, threshold: float = 0.02) -> Dict:
        """Momentum strategy"""
        return {
            "name": "Momentum",
            "type": StrategyType.MOMENTUM,
            "params": {
                "period": period,
                "threshold": threshold
            }
        }
    
    @staticmethod
    def mean_reversion(period: int = 20, threshold: float = 2.0) -> Dict:
        """Mean Reversion strategy"""
        return {
            "name": "Mean Reversion",
            "type": StrategyType.MEAN_REVERSION,
            "params": {
                "period": period,
                "threshold": threshold
            }
        }

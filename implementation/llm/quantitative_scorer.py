"""
RemDarwin Quantitative Scoring Pipeline - Integration with existing quantitative components

This module provides the interface between RemDarwin's existing quantitative scoring
(Greeks, IV surfaces, fundamental analysis) and the LLM decision matrix.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

from .decision_matrix import QuantitativeScore

logger = logging.getLogger(__name__)


@dataclass
class GreeksData:
    """Container for options Greeks data"""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    option_type: str  # 'call' or 'put'
    strike_price: float
    expiration_date: str
    days_to_expiration: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delta": self.delta,
            "gamma": self.gamma,
            "theta": self.theta,
            "vega": self.vega,
            "rho": self.rho,
            "option_type": self.option_type,
            "strike_price": self.strike_price,
            "expiration_date": self.expiration_date,
            "days_to_expiration": self.days_to_expiration
        }


@dataclass
class VolatilityData:
    """Container for volatility analysis data"""
    implied_volatility: float
    realized_volatility: float
    iv_percentile: float  # Percentile vs historical IV
    skew: float  # Volatility skew
    term_structure: str  # 'normal', 'backwardation', 'contango'
    volatility_regime: str  # 'low', 'normal', 'high', 'extreme'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "implied_volatility": self.implied_volatility,
            "realized_volatility": self.realized_volatility,
            "iv_percentile": self.iv_percentile,
            "skew": self.skew,
            "term_structure": self.term_structure,
            "volatility_regime": self.volatility_regime
        }


@dataclass
class FundamentalData:
    """Container for fundamental analysis data"""
    sector: str
    market_cap: float
    beta: float
    pe_ratio: Optional[float]
    dividend_yield: float
    debt_to_equity: Optional[float]
    roa: Optional[float]
    roe: Optional[float]
    profit_margin: Optional[float]
    revenue_growth: Optional[float]
    earnings_growth: Optional[float]
    analyst_rating: Optional[str]  # 'buy', 'hold', 'sell'
    analyst_target_price: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sector": self.sector,
            "market_cap": self.market_cap,
            "beta": self.beta,
            "pe_ratio": self.pe_ratio,
            "dividend_yield": self.dividend_yield,
            "debt_to_equity": self.debt_to_equity,
            "roa": self.roa,
            "roe": self.roe,
            "profit_margin": self.profit_margin,
            "revenue_growth": self.revenue_growth,
            "earnings_growth": self.earnings_growth,
            "analyst_rating": self.analyst_rating,
            "analyst_target_price": self.analyst_target_price
        }


@dataclass
class TechnicalData:
    """Container for technical analysis data"""
    trend_direction: str  # 'bullish', 'bearish', 'sideways'
    trend_strength: float  # 0-1 scale
    support_levels: list[float]
    resistance_levels: list[float]
    rsi: Optional[float]
    macd_signal: Optional[str]  # 'bullish', 'bearish', 'neutral'
    volume_profile: str  # 'above_average', 'average', 'below_average'
    relative_strength: float  # vs market/benchmark

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trend_direction": self.trend_direction,
            "trend_strength": self.trend_strength,
            "support_levels": self.support_levels,
            "resistance_levels": self.resistance_levels,
            "rsi": self.rsi,
            "macd_signal": self.macd_signal,
            "volume_profile": self.volume_profile,
            "relative_strength": self.relative_strength
        }


class QuantitativeScorer:
    """
    Main quantitative scoring engine that integrates with existing RemDarwin components

    This class provides the interface between RemDarwin's quantitative analysis
    (Greeks, IV surfaces, fundamentals, technicals) and the LLM decision matrix.
    """

    def __init__(self):
        # Scoring weights for different components
        self.weights = {
            "greeks": 0.40,      # 40% - Most important for options
            "volatility": 0.30,  # 30% - Critical for pricing and risk
            "fundamental": 0.20, # 20% - Company health and growth
            "technical": 0.10    # 10% - Market timing and momentum
        }

        # Greeks scoring thresholds (for covered calls/cash-secured puts)
        self.greeks_thresholds = {
            "delta": {"ideal_range": (0.15, 0.35), "weight": 0.3},
            "gamma": {"max_acceptable": 0.10, "weight": 0.2},
            "theta": {"min_desirable": 0.15, "weight": 0.3},  # Positive theta decay
            "vega": {"max_acceptable": 0.20, "weight": 0.2}
        }

        # Volatility scoring parameters
        self.volatility_params = {
            "iv_percentile": {"optimal_range": (30, 70), "weight": 0.4},
            "realized_vs_implied": {"max_ratio": 1.5, "weight": 0.3},
            "skew": {"neutral_range": (-0.1, 0.1), "weight": 0.3}
        }

        # Fundamental scoring parameters
        self.fundamental_params = {
            "beta": {"optimal_range": (0.8, 1.3), "weight": 0.2},
            "pe_ratio": {"max_acceptable": 25, "weight": 0.2},
            "debt_to_equity": {"max_acceptable": 1.5, "weight": 0.2},
            "roe": {"min_desirable": 0.10, "weight": 0.2},
            "analyst_rating": {"weight": 0.2}
        }

        # Technical scoring parameters
        self.technical_params = {
            "trend_strength": {"min_desirable": 0.6, "weight": 0.4},
            "rsi": {"neutral_range": (40, 60), "weight": 0.3},
            "relative_strength": {"min_desirable": 0.0, "weight": 0.3}
        }

        logger.info("QuantitativeScorer initialized with standard institutional parameters")

    def calculate_composite_score(self,
                                 greeks_data: GreeksData,
                                 volatility_data: VolatilityData,
                                 fundamental_data: FundamentalData,
                                 technical_data: TechnicalData) -> QuantitativeScore:
        """
        Calculate comprehensive quantitative score from all data sources

        Args:
            greeks_data: Options Greeks data
            volatility_data: Volatility analysis data
            fundamental_data: Fundamental analysis data
            technical_data: Technical analysis data

        Returns:
            Complete QuantitativeScore object
        """
        # Calculate component scores
        greeks_score = self._score_greeks(greeks_data)
        volatility_score = self._score_volatility(volatility_data)
        fundamental_score = self._score_fundamentals(fundamental_data)
        technical_score = self._score_technical(technical_data)

        # Calculate risk-adjusted score
        risk_adjusted_score = self._calculate_risk_adjustment(
            greeks_score, volatility_score, fundamental_score, technical_score
        )

        # Calculate weighted composite score
        composite_score = (
            greeks_score * self.weights["greeks"] +
            volatility_score * self.weights["volatility"] +
            fundamental_score * self.weights["fundamental"] +
            technical_score * self.weights["technical"]
        )

        # Create comprehensive components dict
        components = {
            "greeks_data": greeks_data.to_dict(),
            "volatility_data": volatility_data.to_dict(),
            "fundamental_data": fundamental_data.to_dict(),
            "technical_data": technical_data.to_dict(),
            "component_scores": {
                "greeks_score": greeks_score,
                "volatility_score": volatility_score,
                "fundamental_score": fundamental_score,
                "technical_score": technical_score,
                "risk_adjusted_score": risk_adjusted_score
            },
            "scoring_metadata": {
                "weights": self.weights,
                "scoring_version": "1.0",
                "calculation_timestamp": datetime.utcnow().isoformat()
            }
        }

        return QuantitativeScore(
            total_score=composite_score,
            greeks_score=greeks_score,
            volatility_score=volatility_score,
            fundamental_score=fundamental_score,
            technical_score=technical_score,
            risk_adjusted_score=risk_adjusted_score,
            components=components
        )

    def _score_greeks(self, greeks: GreeksData) -> float:
        """Score options Greeks for covered call/cash-secured put suitability"""
        score = 0.0

        # Delta scoring (want moderate positive delta)
        delta_params = self.greeks_thresholds["delta"]
        if delta_params["ideal_range"][0] <= abs(greeks.delta) <= delta_params["ideal_range"][1]:
            score += 100 * delta_params["weight"]
        elif abs(greeks.delta) < delta_params["ideal_range"][0]:
            # Too low delta, reduce score
            score += (abs(greeks.delta) / delta_params["ideal_range"][0]) * 100 * delta_params["weight"]
        else:
            # Too high delta, reduce score
            excess = abs(greeks.delta) - delta_params["ideal_range"][1]
            score += max(0, 100 - excess * 200) * delta_params["weight"]

        # Gamma scoring (prefer lower gamma for stability)
        gamma_params = self.greeks_thresholds["gamma"]
        if abs(greeks.gamma) <= gamma_params["max_acceptable"]:
            gamma_score = 100 * (1 - abs(greeks.gamma) / gamma_params["max_acceptable"])
            score += gamma_score * gamma_params["weight"]
        else:
            score += 0  # Too high gamma, no points

        # Theta scoring (want positive theta for premium decay)
        theta_params = self.greeks_thresholds["theta"]
        if greeks.theta >= theta_params["min_desirable"]:
            score += 100 * theta_params["weight"]
        elif greeks.theta > 0:
            score += (greeks.theta / theta_params["min_desirable"]) * 100 * theta_params["weight"]
        else:
            score += 0  # Negative theta is bad

        # Vega scoring (lower vega preferred for volatility stability)
        vega_params = self.greeks_thresholds["vega"]
        if abs(greeks.vega) <= vega_params["max_acceptable"]:
            vega_score = 100 * (1 - abs(greeks.vega) / vega_params["max_acceptable"])
            score += vega_score * vega_params["weight"]
        else:
            score += 0

        return min(100.0, max(0.0, score))

    def _score_volatility(self, volatility: VolatilityData) -> float:
        """Score volatility characteristics"""
        score = 0.0

        # IV percentile scoring (moderate IV preferred)
        iv_params = self.volatility_params["iv_percentile"]
        if iv_params["optimal_range"][0] <= volatility.iv_percentile <= iv_params["optimal_range"][1]:
            score += 100 * iv_params["weight"]
        elif volatility.iv_percentile < iv_params["optimal_range"][0]:
            # Too low IV
            score += (volatility.iv_percentile / iv_params["optimal_range"][0]) * 100 * iv_params["weight"]
        else:
            # Too high IV
            excess = volatility.iv_percentile - iv_params["optimal_range"][1]
            score += max(0, 100 - excess) * iv_params["weight"]

        # Realized vs Implied volatility ratio
        rv_iv_params = self.volatility_params["realized_vs_implied"]
        if volatility.realized_volatility > 0:
            ratio = volatility.implied_volatility / volatility.realized_volatility
            if ratio <= rv_iv_params["max_ratio"]:
                ratio_score = 100 * (1 - ratio / rv_iv_params["max_ratio"])
                score += ratio_score * rv_iv_params["weight"]
            else:
                score += 0

        # Volatility skew scoring
        skew_params = self.volatility_params["skew"]
        if skew_params["neutral_range"][0] <= volatility.skew <= skew_params["neutral_range"][1]:
            score += 100 * skew_params["weight"]
        else:
            # Penalize extreme skew
            skew_distance = min(abs(volatility.skew - skew_params["neutral_range"][0]),
                              abs(volatility.skew - skew_params["neutral_range"][1]))
            skew_score = max(0, 100 - skew_distance * 500)
            score += skew_score * skew_params["weight"]

        return min(100.0, max(0.0, score))

    def _score_fundamentals(self, fundamentals: FundamentalData) -> float:
        """Score fundamental characteristics"""
        score = 0.0

        # Beta scoring (moderate beta preferred)
        beta_params = self.fundamental_params["beta"]
        if beta_params["optimal_range"][0] <= fundamentals.beta <= beta_params["optimal_range"][1]:
            score += 100 * beta_params["weight"]
        elif fundamentals.beta < beta_params["optimal_range"][0]:
            score += (fundamentals.beta / beta_params["optimal_range"][0]) * 100 * beta_params["weight"]
        else:
            excess = fundamentals.beta - beta_params["optimal_range"][1]
            score += max(0, 100 - excess * 50) * beta_params["weight"]

        # P/E ratio scoring
        pe_params = self.fundamental_params["pe_ratio"]
        if fundamentals.pe_ratio and fundamentals.pe_ratio <= pe_params["max_acceptable"]:
            pe_score = 100 * (1 - fundamentals.pe_ratio / pe_params["max_acceptable"])
            score += pe_score * pe_params["weight"]
        elif fundamentals.pe_ratio:
            score += 0  # Too expensive

        # Debt-to-equity scoring
        de_params = self.fundamental_params["debt_to_equity"]
        if fundamentals.debt_to_equity is not None and fundamentals.debt_to_equity <= de_params["max_acceptable"]:
            de_score = 100 * (1 - fundamentals.debt_to_equity / de_params["max_acceptable"])
            score += de_score * de_params["weight"]
        elif fundamentals.debt_to_equity is not None:
            score += 0  # Too leveraged

        # ROE scoring
        roe_params = self.fundamental_params["roe"]
        if fundamentals.roe and fundamentals.roe >= roe_params["min_desirable"]:
            score += 100 * roe_params["weight"]
        elif fundamentals.roe and fundamentals.roe > 0:
            score += (fundamentals.roe / roe_params["min_desirable"]) * 100 * roe_params["weight"]

        # Analyst rating scoring
        rating_params = self.fundamental_params["analyst_rating"]
        if fundamentals.analyst_rating:
            rating_score = {"buy": 100, "hold": 60, "sell": 20}.get(fundamentals.analyst_rating.lower(), 50)
            score += rating_score * rating_params["weight"]

        return min(100.0, max(0.0, score))

    def _score_technical(self, technical: TechnicalData) -> float:
        """Score technical characteristics"""
        score = 0.0

        # Trend strength scoring
        trend_params = self.technical_params["trend_strength"]
        if technical.trend_strength >= trend_params["min_desirable"]:
            score += 100 * trend_params["weight"]
        else:
            score += (technical.trend_strength / trend_params["min_desirable"]) * 100 * trend_params["weight"]

        # RSI scoring (prefer neutral readings)
        rsi_params = self.technical_params["rsi"]
        if technical.rsi and rsi_params["neutral_range"][0] <= technical.rsi <= rsi_params["neutral_range"][1]:
            score += 100 * rsi_params["weight"]
        elif technical.rsi:
            # Penalize extreme RSI readings
            distance = min(abs(technical.rsi - rsi_params["neutral_range"][0]),
                         abs(technical.rsi - rsi_params["neutral_range"][1]))
            rsi_score = max(0, 100 - distance * 2)
            score += rsi_score * rsi_params["weight"]

        # Relative strength scoring
        rs_params = self.technical_params["relative_strength"]
        if technical.relative_strength >= rs_params["min_desirable"]:
            rs_score = min(100, technical.relative_strength * 100)
            score += rs_score * rs_params["weight"]
        else:
            score += 0  # Below minimum threshold

        return min(100.0, max(0.0, score))

    def _calculate_risk_adjustment(self, greeks_score: float, volatility_score: float,
                                 fundamental_score: float, technical_score: float) -> float:
        """Calculate risk-adjusted composite score"""
        # Simple risk adjustment: reduce score based on volatility and fundamental risk
        base_score = (greeks_score + volatility_score + fundamental_score + technical_score) / 4

        # Risk factors that reduce confidence
        volatility_risk = max(0, 100 - volatility_score) * 0.3
        fundamental_risk = max(0, 100 - fundamental_score) * 0.2
        greeks_risk = max(0, 100 - greeks_score) * 0.2
        technical_risk = max(0, 100 - technical_score) * 0.1

        total_risk = volatility_risk + fundamental_risk + greeks_risk + technical_risk

        # Apply risk adjustment (reduce score by up to 30% based on risk)
        risk_adjustment = min(30, total_risk * 0.3)

        return max(0, base_score - risk_adjustment)


def create_quantitative_scorer() -> QuantitativeScorer:
    """
    Factory function to create quantitative scorer

    Returns:
        Configured QuantitativeScorer instance
    """
    return QuantitativeScorer()


# Integration point for existing RemDarwin quantitative components
def integrate_existing_scores(existing_scores: Dict[str, Any]) -> QuantitativeScore:
    """
    Integrate scores from existing RemDarwin quantitative components

    This function serves as the bridge between current quantitative analysis
    and the new LLM-enhanced decision matrix.

    Args:
        existing_scores: Dictionary containing scores from existing components

    Returns:
        Standardized QuantitativeScore object
    """
    # This would map existing component outputs to the new scoring structure
    # Placeholder implementation - would be customized based on existing interfaces

    scorer = create_quantitative_scorer()

    # Mock data for integration - replace with actual component integration
    greeks = GreeksData(
        delta=existing_scores.get("delta", 0.25),
        gamma=existing_scores.get("gamma", 0.05),
        theta=existing_scores.get("theta", 0.20),
        vega=existing_scores.get("vega", 0.15),
        rho=existing_scores.get("rho", 0.10),
        option_type=existing_scores.get("option_type", "call"),
        strike_price=existing_scores.get("strike_price", 100.0),
        expiration_date=existing_scores.get("expiration_date", "2024-02-01"),
        days_to_expiration=existing_scores.get("days_to_expiration", 30)
    )

    volatility = VolatilityData(
        implied_volatility=existing_scores.get("implied_volatility", 0.25),
        realized_volatility=existing_scores.get("realized_volatility", 0.20),
        iv_percentile=existing_scores.get("iv_percentile", 60.0),
        skew=existing_scores.get("volatility_skew", 0.05),
        term_structure=existing_scores.get("term_structure", "normal"),
        volatility_regime=existing_scores.get("volatility_regime", "normal")
    )

    fundamentals = FundamentalData(
        sector=existing_scores.get("sector", "Technology"),
        market_cap=existing_scores.get("market_cap", 1000000000),
        beta=existing_scores.get("beta", 1.2),
        pe_ratio=existing_scores.get("pe_ratio", 20.0),
        dividend_yield=existing_scores.get("dividend_yield", 0.02),
        debt_to_equity=existing_scores.get("debt_to_equity", 0.5),
        roa=existing_scores.get("roa", 0.08),
        roe=existing_scores.get("roe", 0.12),
        profit_margin=existing_scores.get("profit_margin", 0.15),
        revenue_growth=existing_scores.get("revenue_growth", 0.10),
        earnings_growth=existing_scores.get("earnings_growth", 0.08),
        analyst_rating=existing_scores.get("analyst_rating", "buy"),
        analyst_target_price=existing_scores.get("analyst_target_price")
    )

    technical = TechnicalData(
        trend_direction=existing_scores.get("trend_direction", "bullish"),
        trend_strength=existing_scores.get("trend_strength", 0.7),
        support_levels=existing_scores.get("support_levels", [95.0, 90.0]),
        resistance_levels=existing_scores.get("resistance_levels", [110.0, 115.0]),
        rsi=existing_scores.get("rsi", 55.0),
        macd_signal=existing_scores.get("macd_signal", "bullish"),
        volume_profile=existing_scores.get("volume_profile", "above_average"),
        relative_strength=existing_scores.get("relative_strength", 0.1)
    )

    return scorer.calculate_composite_score(greeks, volatility, fundamentals, technical)


if __name__ == "__main__":
    # Test the quantitative scorer
    scorer = create_quantitative_scorer()

    # Mock data for testing
    greeks = GreeksData(
        delta=0.25, gamma=0.05, theta=0.20, vega=0.15, rho=0.10,
        option_type="call", strike_price=100.0, expiration_date="2024-02-01", days_to_expiration=30
    )

    volatility = VolatilityData(
        implied_volatility=0.25, realized_volatility=0.20, iv_percentile=60.0,
        skew=0.05, term_structure="normal", volatility_regime="normal"
    )

    fundamentals = FundamentalData(
        sector="Technology", market_cap=1000000000, beta=1.2,
        pe_ratio=20.0, dividend_yield=0.02, debt_to_equity=0.5,
        roa=0.08, roe=0.12, profit_margin=0.15,
        revenue_growth=0.10, earnings_growth=0.08,
        analyst_rating="buy", analyst_target_price=120.0
    )

    technical = TechnicalData(
        trend_direction="bullish", trend_strength=0.7,
        support_levels=[95.0, 90.0], resistance_levels=[110.0, 115.0],
        rsi=55.0, macd_signal="bullish",
        volume_profile="above_average", relative_strength=0.1
    )

    score = scorer.calculate_composite_score(greeks, volatility, fundamentals, technical)

    print(f"Quantitative Score: {score.total_score:.1f}/100")
    print(f"Components: Greeks={score.greeks_score:.1f}, Volatility={score.volatility_score:.1f}, "
          f"Fundamental={score.fundamental_score:.1f}, Technical={score.technical_score:.1f}")
    print(f"Risk-Adjusted Score: {score.risk_adjusted_score:.1f}")
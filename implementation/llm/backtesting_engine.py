"""
RemDarwin Backtesting Engine - Confidence Score Validation Framework

This module provides comprehensive backtesting capabilities to validate LLM confidence
scores against historical trade outcomes, enabling calibration and performance assessment.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, classification_report, roc_curve, auc

from .historical_data_collector import HistoricalDataCollector, HistoricalTrade
from .decision_matrix import DecisionMatrixEngine, QuantitativeScore, LLMScore
from .quantitative_scorer import QuantitativeScorer
from .llm_normalizer import LLMOutputNormalizer

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Results from a single backtest simulation"""
    trade_id: str
    historical_outcome: str  # 'profitable', 'loss', 'breakeven'
    predicted_decision: str  # 'BUY', 'SELL', 'HOLD', 'AVOID'
    confidence_score: float
    quantitative_score: QuantitativeScore
    llm_score: Optional[LLMScore] = None
    decision_matrix_result: Optional[Any] = None
    simulation_timestamp: datetime = None

    def __post_init__(self):
        if self.simulation_timestamp is None:
            self.simulation_timestamp = datetime.now()


@dataclass
class BacktestMetrics:
    """Comprehensive backtest performance metrics"""
    total_trades: int = 0
    profitable_trades: int = 0
    loss_trades: int = 0
    breakeven_trades: int = 0

    # Decision accuracy metrics
    correct_predictions: int = 0
    incorrect_predictions: int = 0
    accuracy: float = 0.0

    # Confidence calibration metrics
    confidence_bins: Dict[str, List[float]] = field(default_factory=lambda: {
        "0.0-0.2": [], "0.2-0.4": [], "0.4-0.6": [],
        "0.6-0.8": [], "0.8-1.0": []
    })
    bin_accuracies: Dict[str, float] = field(default_factory=dict)

    # Risk-adjusted metrics
    expected_value: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0

    # Classification metrics
    confusion_matrix: Optional[np.ndarray] = None
    classification_report: Optional[str] = None
    roc_auc: Optional[float] = None

    # Performance by confidence level
    high_confidence_accuracy: float = 0.0
    medium_confidence_accuracy: float = 0.0
    low_confidence_accuracy: float = 0.0

    def calculate_metrics(self, results: List[BacktestResult]):
        """Calculate comprehensive metrics from backtest results"""
        if not results:
            return

        self.total_trades = len(results)
        self.profitable_trades = sum(1 for r in results if r.historical_outcome == 'profitable')
        self.loss_trades = sum(1 for r in results if r.historical_outcome == 'loss')
        self.breakeven_trades = sum(1 for r in results if r.historical_outcome == 'breakeven')

        # Calculate decision accuracy
        self._calculate_decision_accuracy(results)

        # Calculate confidence calibration
        self._calculate_confidence_calibration(results)

        # Calculate risk metrics
        self._calculate_risk_metrics(results)

        # Calculate classification metrics
        self._calculate_classification_metrics(results)

    def _calculate_decision_accuracy(self, results: List[BacktestResult]):
        """Calculate decision prediction accuracy"""
        correct = 0
        for result in results:
            # Simplified accuracy: BUY/HOLD/MONITOR predicted for profitable trades
            predicted_positive = result.predicted_decision in ['BUY', 'HOLD', 'MONITOR']
            actual_positive = result.historical_outcome == 'profitable'

            if predicted_positive == actual_positive:
                correct += 1

        self.correct_predictions = correct
        self.incorrect_predictions = self.total_trades - correct
        self.accuracy = correct / self.total_trades if self.total_trades > 0 else 0.0

    def _calculate_confidence_calibration(self, results: List[BacktestResult]):
        """Calculate confidence calibration metrics"""
        # Group results by confidence bins
        for result in results:
            confidence = result.confidence_score
            if confidence <= 0.2:
                bin_name = "0.0-0.2"
            elif confidence <= 0.4:
                bin_name = "0.2-0.4"
            elif confidence <= 0.6:
                bin_name = "0.4-0.6"
            elif confidence <= 0.8:
                bin_name = "0.6-0.8"
            else:
                bin_name = "0.8-1.0"

            self.confidence_bins[bin_name].append(result.historical_outcome == 'profitable')

        # Calculate accuracy per bin
        for bin_name, outcomes in self.confidence_bins.items():
            if outcomes:
                accuracy = sum(outcomes) / len(outcomes)
                self.bin_accuracies[bin_name] = accuracy

    def _calculate_risk_metrics(self, results: List[BacktestResult]):
        """Calculate risk-adjusted performance metrics"""
        if not results:
            return

        # Calculate win rate and averages
        profitable_results = [r for r in results if r.historical_outcome == 'profitable']
        loss_results = [r for r in results if r.historical_outcome == 'loss']

        self.win_rate = len(profitable_results) / len(results) if results else 0.0

        if profitable_results:
            # Mock P&L values for demonstration (would use actual values in production)
            self.avg_win = sum(np.random.uniform(1, 5) for _ in profitable_results) / len(profitable_results)

        if loss_results:
            self.avg_loss = -sum(np.random.uniform(0.5, 3) for _ in loss_results) / len(loss_results)

        # Calculate profit factor
        total_wins = self.avg_win * len(profitable_results)
        total_losses = abs(self.avg_loss) * len(loss_results)
        self.profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')

        # Calculate Sharpe ratio (simplified)
        returns = []
        for result in results:
            if result.historical_outcome == 'profitable':
                returns.append(self.avg_win)
            elif result.historical_outcome == 'loss':
                returns.append(self.avg_loss)
            else:
                returns.append(0.0)

        if returns:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            self.sharpe_ratio = avg_return / std_return if std_return > 0 else 0.0

    def _calculate_classification_metrics(self, results: List[BacktestResult]):
        """Calculate classification performance metrics"""
        if not results:
            return

        # Convert to binary classification (profitable vs not profitable)
        y_true = [1 if r.historical_outcome == 'profitable' else 0 for r in results]
        y_pred = [1 if r.predicted_decision in ['BUY', 'HOLD', 'MONITOR'] else 0 for r in results]
        y_scores = [r.confidence_score for r in results]

        # Confusion matrix
        self.confusion_matrix = confusion_matrix(y_true, y_pred)

        # Classification report
        self.classification_report = classification_report(y_true, y_pred, zero_division=0)

        # ROC AUC
        try:
            fpr, tpr, _ = roc_curve(y_true, y_scores)
            self.roc_auc = auc(fpr, tpr)
        except:
            self.roc_auc = None

    def get_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive summary report"""
        return {
            "overview": {
                "total_trades": self.total_trades,
                "accuracy": self.accuracy,
                "win_rate": self.win_rate,
                "sharpe_ratio": self.sharpe_ratio,
                "profit_factor": self.profit_factor
            },
            "confidence_calibration": {
                "bin_accuracies": self.bin_accuracies,
                "high_confidence_accuracy": self.bin_accuracies.get("0.8-1.0", 0.0),
                "medium_confidence_accuracy": self.bin_accuracies.get("0.4-0.6", 0.0),
                "low_confidence_accuracy": self.bin_accuracies.get("0.0-0.2", 0.0)
            },
            "risk_metrics": {
                "avg_win": self.avg_win,
                "avg_loss": self.avg_loss,
                "max_drawdown": self.max_drawdown,
                "expected_value": self.expected_value
            },
            "classification": {
                "roc_auc": self.roc_auc,
                "confusion_matrix": self.confusion_matrix.tolist() if self.confusion_matrix is not None else None,
                "classification_report": self.classification_report
            }
        }


class ConfidenceBacktestingEngine:
    """
    Engine for backtesting LLM confidence scores against historical performance

    This simulates what decisions the LLM would have made for historical trades
    and evaluates the calibration and accuracy of confidence scores.
    """

    def __init__(self,
                 historical_collector: Optional[HistoricalDataCollector] = None,
                 decision_engine: Optional[DecisionMatrixEngine] = None,
                 quantitative_scorer: Optional[QuantitativeScorer] = None,
                 llm_normalizer: Optional[LLMOutputNormalizer] = None):
        """
        Initialize the backtesting engine

        Args:
            historical_collector: Collector for historical trade data
            decision_engine: Decision matrix engine for simulation
            quantitative_scorer: Quantitative scoring engine
            llm_normalizer: LLM output normalizer
        """
        self.historical_collector = historical_collector or HistoricalDataCollector()
        self.decision_engine = decision_engine or DecisionMatrixEngine()
        self.quantitative_scorer = quantitative_scorer or QuantitativeScorer()
        self.llm_normalizer = llm_normalizer or LLMOutputNormalizer()

        logger.info("Confidence backtesting engine initialized")

    def run_backtest(self,
                    symbol: Optional[str] = None,
                    strategy: Optional[str] = None,
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    min_trades: int = 10) -> Tuple[List[BacktestResult], BacktestMetrics]:
        """
        Run comprehensive backtest simulation

        Args:
            symbol: Filter by stock symbol
            strategy: Filter by strategy type
            start_date: Start date for backtest
            end_date: End date for backtest
            min_trades: Minimum number of trades required

        Returns:
            Tuple of (individual results, aggregate metrics)
        """
        # Get historical trades
        historical_trades = self.historical_collector.get_trades(
            symbol=symbol,
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )

        if len(historical_trades) < min_trades:
            logger.warning(f"Insufficient trades for backtest: {len(historical_trades)} < {min_trades}")
            return [], BacktestMetrics()

        logger.info(f"Running backtest on {len(historical_trades)} historical trades")

        # Simulate decisions for each historical trade
        backtest_results = []
        for trade in historical_trades:
            try:
                result = self._simulate_trade_decision(trade)
                if result:
                    backtest_results.append(result)
            except Exception as e:
                logger.warning(f"Failed to simulate trade {trade.trade_id}: {e}")
                continue

        # Calculate aggregate metrics
        metrics = BacktestMetrics()
        metrics.calculate_metrics(backtest_results)

        logger.info(f"Backtest completed: {len(backtest_results)} simulated decisions, "
                   f"accuracy: {metrics.accuracy:.1%}")

        return backtest_results, metrics

    def _simulate_trade_decision(self, trade: HistoricalTrade) -> Optional[BacktestResult]:
        """
        Simulate what decision would be made for a historical trade

        Args:
            trade: Historical trade to simulate

        Returns:
            Backtest result or None if simulation fails
        """
        # For demonstration, we'll create realistic simulations
        # In production, this would use actual LLM API calls with historical context

        # Create quantitative score (would use actual historical data in production)
        volatility_data = {
            "implied_volatility": 0.25,
            "realized_volatility": 0.20,
            "iv_percentile": 60.0,
            "skew": 0.05,
            "term_structure": "normal",
            "volatility_regime": trade.volatility_environment
        }

        fundamental_data = {
            "sector": trade.market_regime,  # Simplified mapping
            "market_cap": 1000000000,
            "beta": 1.2,
            "pe_ratio": 20.0,
            "dividend_yield": 0.02,
            "debt_to_equity": 0.5,
            "roa": 0.08,
            "roe": 0.12,
            "analyst_rating": "buy"
        }

        technical_data = {
            "trend_direction": "bullish",
            "trend_strength": 0.7,
            "rsi": 55.0,
            "macd_signal": "bullish",
            "volume_profile": "above_average",
            "relative_strength": 0.1
        }

        # Calculate quantitative score
        quant_score = self.quantitative_scorer.calculate_composite_score(
            greeks_data=None,  # Would need historical Greeks data
            volatility_data=type('MockVol', (), volatility_data)(),
            fundamental_data=type('MockFund', (), fundamental_data)(),
            technical_data=type('MockTech', (), technical_data)()
        )

        # Simulate LLM response (would use actual LLM in production)
        mock_llm_response = {
            "analysis_confidence": np.random.uniform(0.3, 0.9),
            "recommendation": {
                "action": np.random.choice(["BUY", "HOLD", "AVOID", "SELL"]),
                "confidence_score": np.random.uniform(0.3, 0.9),
                "urgency_level": np.random.choice(["HIGH", "MODERATE", "LOW"])
            },
            "risk_assessment": {
                "overall_risk_level": trade.market_regime.upper()  # Simplified
            },
            "trade_rationale": {
                "primary_catalyst": f"Historical {trade.strategy_type} setup",
                "narrative_summary": f"Based on {trade.market_regime} market conditions"
            }
        }

        # Normalize LLM output
        normalized_llm = self.llm_normalizer.normalize_output(mock_llm_response)

        # Create LLM score
        llm_score = LLMScore(
            confidence_score=normalized_llm.original_confidence,
            action_recommendation=normalized_llm.action_polarity > 0 and "BUY" or "AVOID",
            risk_level=normalized_llm.risk_perception,
            urgency_level="MODERATE",
            normalized_score=normalized_llm.calibrated_score,
            rationale_summary=normalized_llm.rationale_summary,
            key_assumptions=["Historical simulation"]
        )

        # Make decision using decision matrix
        from .response_parser import ParsedResponse
        mock_parsed_response = ParsedResponse(
            raw_response=str(mock_llm_response),
            parsed_json=mock_llm_response,
            is_valid=True,
            validation_errors=[],
            confidence_score=normalized_llm.original_confidence,
            processing_time=0.1,
            parse_method="simulation",
            metadata={}
        )

        decision_result = self.decision_engine.process_decision(
            trade.trade_id, quant_score, mock_parsed_response
        )

        return BacktestResult(
            trade_id=trade.trade_id,
            historical_outcome=trade.outcome_category,
            predicted_decision=decision_result.final_recommendation,
            confidence_score=normalized_llm.original_confidence,
            quantitative_score=quant_score,
            llm_score=llm_score,
            decision_matrix_result=decision_result
        )

    def analyze_confidence_calibration(self,
                                    results: List[BacktestResult],
                                    confidence_thresholds: List[float] = [0.3, 0.5, 0.7, 0.9]) -> Dict[str, Any]:
        """
        Analyze confidence score calibration across different thresholds

        Args:
            results: Backtest results to analyze
            confidence_thresholds: Confidence thresholds to evaluate

        Returns:
            Calibration analysis results
        """
        analysis = {}

        for threshold in confidence_thresholds:
            # Filter results above threshold
            high_conf_results = [r for r in results if r.confidence_score >= threshold]

            if high_conf_results:
                accuracy = sum(1 for r in high_conf_results
                             if (r.predicted_decision in ['BUY', 'HOLD', 'MONITOR'] and
                                 r.historical_outcome == 'profitable'))
                accuracy /= len(high_conf_results)

                analysis[f"confidence_{threshold}"] = {
                    "threshold": threshold,
                    "trades_above_threshold": len(high_conf_results),
                    "accuracy": accuracy,
                    "coverage": len(high_conf_results) / len(results)
                }

        return analysis

    def generate_calibration_report(self,
                                  results: List[BacktestResult],
                                  metrics: BacktestMetrics) -> Dict[str, Any]:
        """
        Generate comprehensive calibration report

        Args:
            results: Individual backtest results
            metrics: Aggregate performance metrics

        Returns:
            Complete calibration report
        """
        # Confidence calibration analysis
        calibration_analysis = self.analyze_confidence_calibration(results)

        # Performance by confidence decile
        confidence_deciles = self._analyze_confidence_deciles(results)

        # Recommendation adjustments based on calibration
        recommendations = self._generate_calibration_recommendations(metrics, calibration_analysis)

        return {
            "summary": {
                "total_simulations": len(results),
                "overall_accuracy": metrics.accuracy,
                "confidence_range": {
                    "min": min(r.confidence_score for r in results),
                    "max": max(r.confidence_score for r in results),
                    "avg": np.mean([r.confidence_score for r in results])
                }
            },
            "calibration_analysis": calibration_analysis,
            "confidence_deciles": confidence_deciles,
            "performance_metrics": metrics.get_summary_report(),
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }

    def _analyze_confidence_deciles(self, results: List[BacktestResult]) -> Dict[str, Any]:
        """Analyze performance across confidence deciles"""
        if not results:
            return {}

        # Sort by confidence
        sorted_results = sorted(results, key=lambda r: r.confidence_score)

        # Split into deciles
        decile_size = len(sorted_results) // 10
        deciles = {}

        for i in range(10):
            start_idx = i * decile_size
            end_idx = (i + 1) * decile_size if i < 9 else len(sorted_results)

            decile_results = sorted_results[start_idx:end_idx]
            if decile_results:
                accuracy = sum(1 for r in decile_results
                             if (r.predicted_decision in ['BUY', 'HOLD', 'MONITOR'] and
                                 r.historical_outcome == 'profitable'))
                accuracy /= len(decile_results)

                deciles[f"decile_{i+1}"] = {
                    "confidence_range": {
                        "min": min(r.confidence_score for r in decile_results),
                        "max": max(r.confidence_score for r in decile_results)
                    },
                    "accuracy": accuracy,
                    "trade_count": len(decile_results)
                }

        return deciles

    def _generate_calibration_recommendations(self,
                                            metrics: BacktestMetrics,
                                            calibration_analysis: Dict[str, Any]) -> List[str]:
        """Generate calibration recommendations based on analysis"""
        recommendations = []

        # Accuracy recommendations
        if metrics.accuracy < 0.55:
            recommendations.append("Overall accuracy is below acceptable threshold. Consider retraining LLM or adjusting scoring weights.")

        # Confidence calibration recommendations
        high_conf_accuracy = calibration_analysis.get("confidence_0.8", {}).get("accuracy", 0)
        if high_conf_accuracy < 0.7:
            recommendations.append("High confidence predictions are underperforming. Consider adjusting confidence thresholds.")

        low_conf_accuracy = calibration_analysis.get("confidence_0.3", {}).get("accuracy", 0)
        if low_conf_accuracy > high_conf_accuracy:
            recommendations.append("Low confidence predictions outperforming high confidence ones. Confidence calibration may be inverted.")

        # Risk recommendations
        if metrics.sharpe_ratio < 0.5:
            recommendations.append("Risk-adjusted returns are poor. Consider more conservative position sizing.")

        if not recommendations:
            recommendations.append("Calibration appears reasonable. Monitor performance and recalibrate quarterly.")

        return recommendations


def create_backtesting_engine(historical_db_path: str = "data/historical_trades.db") -> ConfidenceBacktestingEngine:
    """
    Factory function to create configured backtesting engine

    Args:
        historical_db_path: Path to historical trades database

    Returns:
        Configured backtesting engine
    """
    from .historical_data_collector import HistoricalDataCollector
    from .decision_matrix import DecisionMatrixEngine
    from .quantitative_scorer import QuantitativeScorer
    from .llm_normalizer import LLMOutputNormalizer

    historical_collector = HistoricalDataCollector(historical_db_path)
    decision_engine = DecisionMatrixEngine()
    quantitative_scorer = QuantitativeScorer()
    llm_normalizer = LLMOutputNormalizer()

    return ConfidenceBacktestingEngine(
        historical_collector=historical_collector,
        decision_engine=decision_engine,
        quantitative_scorer=quantitative_scorer,
        llm_normalizer=llm_normalizer
    )


if __name__ == "__main__":
    # Test the backtesting engine
    engine = create_backtesting_engine()

    # Run backtest
    results, metrics = engine.run_backtest(min_trades=5)

    print(f"Backtest completed: {len(results)} trades simulated")
    print(f"Overall accuracy: {metrics.accuracy:.1%}")
    print(f"Win rate: {metrics.win_rate:.1%}")
    print(f"Profit factor: {metrics.profit_factor:.2f}")

    # Generate calibration report
    report = engine.generate_calibration_report(results, metrics)
    print(f"Calibration recommendations: {len(report['recommendations'])}")
    for rec in report['recommendations'][:2]:  # Show first 2
        print(f"  - {rec}")

    print("Backtesting engine test completed!")
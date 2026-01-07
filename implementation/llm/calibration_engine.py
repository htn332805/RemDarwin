"""
RemDarwin Calibration Engine - Automatic Parameter Optimization

This module provides automated calibration of LLM decision parameters based on
historical performance, including threshold optimization, weight adjustment,
and continuous model improvement.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import scipy.optimize as opt

from .backtesting_engine import ConfidenceBacktestingEngine, BacktestResult, BacktestMetrics
from .decision_matrix import DecisionMatrixEngine

logger = logging.getLogger(__name__)


@dataclass
class CalibrationParameters:
    """Parameters that can be calibrated"""
    quantitative_weight: float = 0.80
    llm_weight: float = 0.20
    risk_adjustment_factor: float = 0.15
    confidence_threshold_high: float = 0.8
    confidence_threshold_low: float = 0.3
    decision_thresholds: Dict[str, float] = None

    def __post_init__(self):
        if self.decision_thresholds is None:
            self.decision_thresholds = {
                "STRONG_BUY": 85.0,
                "BUY": 70.0,
                "HOLD": 55.0,
                "AVOID": 40.0,
                "STRONG_AVOID": 25.0
            }

    def to_vector(self) -> np.ndarray:
        """Convert parameters to optimization vector"""
        return np.array([
            self.quantitative_weight,
            self.confidence_threshold_high,
            self.confidence_threshold_low,
            self.risk_adjustment_factor,
            self.decision_thresholds["BUY"],
            self.decision_thresholds["HOLD"],
            self.decision_thresholds["AVOID"]
        ])

    @classmethod
    def from_vector(cls, vector: np.ndarray) -> 'CalibrationParameters':
        """Create parameters from optimization vector"""
        return cls(
            quantitative_weight=vector[0],
            llm_weight=1.0 - vector[0],  # Ensure weights sum to 1
            confidence_threshold_high=vector[1],
            confidence_threshold_low=vector[2],
            risk_adjustment_factor=vector[3],
            decision_thresholds={
                "STRONG_BUY": 85.0,  # Keep fixed
                "BUY": vector[4],
                "HOLD": vector[5],
                "AVOID": vector[6],
                "STRONG_AVOID": 25.0  # Keep fixed
            }
        )


@dataclass
class CalibrationResult:
    """Results of calibration process"""
    optimal_parameters: CalibrationParameters
    baseline_metrics: BacktestMetrics
    optimized_metrics: BacktestMetrics
    improvement_percentage: float
    calibration_method: str
    confidence_intervals: Dict[str, Tuple[float, float]]
    feature_importance: Dict[str, float]
    convergence_status: str
    iterations_performed: int

    def get_summary_report(self) -> Dict[str, Any]:
        """Generate calibration summary"""
        return {
            "calibration_method": self.calibration_method,
            "improvement": {
                "percentage": self.improvement_percentage,
                "baseline_accuracy": self.baseline_metrics.accuracy,
                "optimized_accuracy": self.optimized_metrics.accuracy,
                "baseline_sharpe": self.baseline_metrics.sharpe_ratio,
                "optimized_sharpe": self.optimized_metrics.sharpe_ratio
            },
            "optimal_parameters": {
                "quantitative_weight": self.optimal_parameters.quantitative_weight,
                "llm_weight": self.optimal_parameters.llm_weight,
                "confidence_threshold_high": self.optimal_parameters.confidence_threshold_high,
                "confidence_threshold_low": self.optimal_parameters.confidence_threshold_low,
                "risk_adjustment_factor": self.optimal_parameters.risk_adjustment_factor
            },
            "decision_thresholds": self.optimal_parameters.decision_thresholds,
            "convergence": {
                "status": self.convergence_status,
                "iterations": self.iterations_performed
            },
            "confidence_intervals": self.confidence_intervals
        }


class CalibrationEngine:
    """
    Automated parameter calibration engine using machine learning and optimization

    Features:
    - Bayesian optimization for parameter tuning
    - Machine learning-based threshold calibration
    - Statistical significance testing
    - Confidence interval estimation
    - Feature importance analysis
    """

    def __init__(self,
                 backtesting_engine: Optional[ConfidenceBacktestingEngine] = None,
                 calibration_method: str = "bayesian_optimization"):
        """
        Initialize calibration engine

        Args:
            backtesting_engine: Engine for running backtests
            calibration_method: Optimization method ('bayesian_optimization', 'grid_search', 'random_search')
        """
        self.backtesting_engine = backtesting_engine or ConfidenceBacktestingEngine()
        self.calibration_method = calibration_method

        # Parameter bounds for optimization
        self.parameter_bounds = {
            "quantitative_weight": (0.5, 0.95),  # 50-95% quantitative
            "confidence_threshold_high": (0.7, 0.9),  # 70-90%
            "confidence_threshold_low": (0.2, 0.4),  # 20-40%
            "risk_adjustment_factor": (0.05, 0.3),  # 5-30%
            "buy_threshold": (60.0, 80.0),  # 60-80 score
            "hold_threshold": (45.0, 65.0),  # 45-65 score
            "avoid_threshold": (25.0, 45.0)  # 25-45 score
        }

        # Performance history for learning
        self.performance_history: List[Dict[str, Any]] = []

        logger.info(f"Calibration engine initialized with method: {calibration_method}")

    def calibrate_parameters(self,
                           baseline_params: CalibrationParameters,
                           max_iterations: int = 50,
                           confidence_level: float = 0.95,
                           target_metric: str = "sharpe_ratio") -> CalibrationResult:
        """
        Perform comprehensive parameter calibration

        Args:
            baseline_params: Starting parameters for optimization
            max_iterations: Maximum optimization iterations
            confidence_level: Statistical confidence level for intervals
            target_metric: Metric to optimize ('accuracy', 'sharpe_ratio', 'profit_factor')

        Returns:
            Complete calibration results
        """
        logger.info(f"Starting parameter calibration with target: {target_metric}")

        # Run baseline backtest
        baseline_results, baseline_metrics = self._run_backtest_with_params(baseline_params)
        baseline_score = self._extract_metric_score(baseline_metrics, target_metric)

        logger.info(f"Baseline {target_metric}: {baseline_score:.4f}")

        # Perform optimization
        if self.calibration_method == "bayesian_optimization":
            optimal_params, optimization_results = self._bayesian_optimization(
                baseline_params, max_iterations, target_metric
            )
        elif self.calibration_method == "grid_search":
            optimal_params, optimization_results = self._grid_search_optimization(
                baseline_params, target_metric
            )
        else:  # random_search
            optimal_params, optimization_results = self._random_search_optimization(
                baseline_params, max_iterations, target_metric
            )

        # Run final backtest with optimal parameters
        optimal_results, optimal_metrics = self._run_backtest_with_params(optimal_params)
        optimal_score = self._extract_metric_score(optimal_metrics, target_metric)

        # Calculate improvement
        improvement_percentage = ((optimal_score - baseline_score) / abs(baseline_score)) * 100

        # Estimate confidence intervals
        confidence_intervals = self._estimate_confidence_intervals(
            optimal_params, confidence_level, target_metric
        )

        # Analyze feature importance
        feature_importance = self._analyze_feature_importance()

        # Create result
        result = CalibrationResult(
            optimal_parameters=optimal_params,
            baseline_metrics=baseline_metrics,
            optimized_metrics=optimal_metrics,
            improvement_percentage=improvement_percentage,
            calibration_method=self.calibration_method,
            confidence_intervals=confidence_intervals,
            feature_importance=feature_importance,
            convergence_status=optimization_results.get("convergence", "completed"),
            iterations_performed=optimization_results.get("iterations", max_iterations)
        )

        logger.info(f"Calibration completed. Improvement: {improvement_percentage:.1f}%")
        logger.info(f"Optimal parameters: quant_weight={optimal_params.quantitative_weight:.2f}, "
                   f"high_conf={optimal_params.confidence_threshold_high:.2f}")

        return result

    def _bayesian_optimization(self, baseline_params: CalibrationParameters,
                             max_iterations: int, target_metric: str) -> Tuple[CalibrationParameters, Dict[str, Any]]:
        """Bayesian optimization for parameter tuning"""
        def objective_function(param_vector: np.ndarray) -> float:
            """Objective function for optimization (negative because we minimize)"""
            try:
                params = CalibrationParameters.from_vector(param_vector)
                _, metrics = self._run_backtest_with_params(params)
                score = self._extract_metric_score(metrics, target_metric)

                # Store for learning
                self.performance_history.append({
                    "parameters": params.to_vector(),
                    "score": score,
                    "metric": target_metric
                })

                return -score  # Negative because scipy minimizes
            except Exception as e:
                logger.warning(f"Error in objective function: {e}")
                return 1000.0  # Large penalty for failures

        # Parameter bounds for optimization
        bounds = [
            self.parameter_bounds["quantitative_weight"],
            self.parameter_bounds["confidence_threshold_high"],
            self.parameter_bounds["confidence_threshold_low"],
            self.parameter_bounds["risk_adjustment_factor"],
            self.parameter_bounds["buy_threshold"],
            self.parameter_bounds["hold_threshold"],
            self.parameter_bounds["avoid_threshold"]
        ]

        # Initial guess
        x0 = baseline_params.to_vector()

        # Run optimization
        try:
            result = opt.minimize(
                objective_function,
                x0,
                method='L-BFGS-B',
                bounds=bounds,
                options={'maxiter': max_iterations, 'disp': False}
            )

            optimal_params = CalibrationParameters.from_vector(result.x)
            optimization_results = {
                "convergence": "success" if result.success else "failed",
                "iterations": result.nit,
                "function_evaluations": result.nfev,
                "final_score": -result.fun
            }

        except Exception as e:
            logger.warning(f"Bayesian optimization failed: {e}, using baseline")
            optimal_params = baseline_params
            optimization_results = {
                "convergence": "failed",
                "iterations": 0,
                "error": str(e)
            }

        return optimal_params, optimization_results

    def _grid_search_optimization(self, baseline_params: CalibrationParameters,
                                target_metric: str) -> Tuple[CalibrationParameters, Dict[str, Any]]:
        """Grid search optimization for parameter tuning"""
        # Define grid points
        quant_weights = np.linspace(0.6, 0.9, 7)  # 7 points
        conf_high_thresholds = np.linspace(0.75, 0.85, 5)  # 5 points
        conf_low_thresholds = np.linspace(0.25, 0.35, 5)  # 5 points

        best_score = float('-inf')
        best_params = baseline_params

        total_combinations = len(quant_weights) * len(conf_high_thresholds) * len(conf_low_thresholds)
        logger.info(f"Grid search: evaluating {total_combinations} parameter combinations")

        iteration = 0
        for quant_weight in quant_weights:
            for conf_high in conf_high_thresholds:
                for conf_low in conf_low_thresholds:
                    iteration += 1
                    if iteration % 10 == 0:
                        logger.debug(f"Grid search iteration {iteration}/{total_combinations}")

                    try:
                        params = CalibrationParameters(
                            quantitative_weight=quant_weight,
                            llm_weight=1.0 - quant_weight,
                            confidence_threshold_high=conf_high,
                            confidence_threshold_low=conf_low,
                            risk_adjustment_factor=baseline_params.risk_adjustment_factor,
                            decision_thresholds=baseline_params.decision_thresholds.copy()
                        )

                        _, metrics = self._run_backtest_with_params(params)
                        score = self._extract_metric_score(metrics, target_metric)

                        if score > best_score:
                            best_score = score
                            best_params = params

                    except Exception as e:
                        logger.debug(f"Grid search parameter combination failed: {e}")
                        continue

        optimization_results = {
            "convergence": "completed",
            "iterations": total_combinations,
            "method": "grid_search"
        }

        return best_params, optimization_results

    def _random_search_optimization(self, baseline_params: CalibrationParameters,
                                  max_iterations: int, target_metric: str) -> Tuple[CalibrationParameters, Dict[str, Any]]:
        """Random search optimization"""
        best_score = float('-inf')
        best_params = baseline_params

        logger.info(f"Random search: evaluating {max_iterations} random parameter combinations")

        for iteration in range(max_iterations):
            # Generate random parameters within bounds
            quant_weight = np.random.uniform(*self.parameter_bounds["quantitative_weight"])
            conf_high = np.random.uniform(*self.parameter_bounds["confidence_threshold_high"])
            conf_low = np.random.uniform(*self.parameter_bounds["confidence_threshold_low"])
            risk_factor = np.random.uniform(*self.parameter_bounds["risk_adjustment_factor"])

            try:
                params = CalibrationParameters(
                    quantitative_weight=quant_weight,
                    llm_weight=1.0 - quant_weight,
                    confidence_threshold_high=conf_high,
                    confidence_threshold_low=conf_low,
                    risk_adjustment_factor=risk_factor,
                    decision_thresholds=baseline_params.decision_thresholds.copy()
                )

                _, metrics = self._run_backtest_with_params(params)
                score = self._extract_metric_score(metrics, target_metric)

                if score > best_score:
                    best_score = score
                    best_params = params

            except Exception as e:
                logger.debug(f"Random search parameter combination failed: {e}")
                continue

        optimization_results = {
            "convergence": "completed",
            "iterations": max_iterations,
            "method": "random_search"
        }

        return best_params, optimization_results

    def _run_backtest_with_params(self, params: CalibrationParameters) -> Tuple[List[BacktestResult], BacktestMetrics]:
        """Run backtest with specific parameters"""
        # Create decision engine with these parameters
        decision_engine = DecisionMatrixEngine(
            quantitative_weight=params.quantitative_weight,
            llm_weight=params.llm_weight,
            risk_adjustment_factor=params.risk_adjustment_factor,
            confidence_threshold_high=params.confidence_threshold_high,
            confidence_threshold_low=params.confidence_threshold_low
        )

        # Update decision thresholds
        decision_engine.decision_thresholds = params.decision_thresholds

        # Create new backtesting engine with this decision engine
        backtesting_engine = ConfidenceBacktestingEngine(
            decision_engine=decision_engine,
            quantitative_scorer=self.backtesting_engine.quantitative_scorer,
            llm_normalizer=self.backtesting_engine.llm_normalizer
        )

        # Run backtest (limit to smaller sample for speed during optimization)
        results, metrics = backtesting_engine.run_backtest(min_trades=20, limit=100)

        return results, metrics

    def _extract_metric_score(self, metrics: BacktestMetrics, target_metric: str) -> float:
        """Extract the target metric score from backtest results"""
        if target_metric == "accuracy":
            return metrics.accuracy
        elif target_metric == "sharpe_ratio":
            return metrics.sharpe_ratio
        elif target_metric == "profit_factor":
            return metrics.profit_factor
        elif target_metric == "win_rate":
            return metrics.win_rate
        else:
            return metrics.accuracy  # Default fallback

    def _estimate_confidence_intervals(self, optimal_params: CalibrationParameters,
                                     confidence_level: float, target_metric: str) -> Dict[str, Tuple[float, float]]:
        """Estimate confidence intervals for optimal parameters using bootstrapping"""
        if len(self.performance_history) < 10:
            # Not enough data for reliable intervals
            return {}

        # Bootstrap resampling
        n_bootstrap = 100
        bootstrap_scores = []

        for _ in range(n_bootstrap):
            # Sample with replacement from performance history
            sample_indices = np.random.choice(len(self.performance_history), size=len(self.performance_history), replace=True)
            sample_scores = [self.performance_history[i]["score"] for i in sample_indices]
            bootstrap_scores.append(np.mean(sample_scores))

        # Calculate confidence interval
        bootstrap_scores.sort()
        lower_idx = int((1 - confidence_level) / 2 * n_bootstrap)
        upper_idx = int((1 + confidence_level) / 2 * n_bootstrap)

        confidence_interval = (bootstrap_scores[lower_idx], bootstrap_scores[upper_idx])

        return {
            target_metric: confidence_interval,
            "confidence_level": confidence_level,
            "bootstrap_samples": n_bootstrap
        }

    def _analyze_feature_importance(self) -> Dict[str, float]:
        """Analyze which parameters are most important for performance"""
        if len(self.performance_history) < 20:
            return {"insufficient_data": 1.0}

        # Prepare data for analysis
        X = np.array([entry["parameters"] for entry in self.performance_history])
        y = np.array([entry["score"] for entry in self.performance_history])

        # Train a simple model to understand feature importance
        try:
            model = RandomForestClassifier(n_estimators=10, random_state=42)
            model.fit(X, y > np.median(y))  # Binary classification: above/below median

            # Parameter names
            param_names = [
                "quantitative_weight", "confidence_threshold_high", "confidence_threshold_low",
                "risk_adjustment_factor", "buy_threshold", "hold_threshold", "avoid_threshold"
            ]

            importance_dict = {}
            for name, importance in zip(param_names, model.feature_importances_):
                importance_dict[name] = float(importance)

            return importance_dict

        except Exception as e:
            logger.warning(f"Feature importance analysis failed: {e}")
            return {"analysis_failed": 1.0}

    def generate_calibration_report(self, result: CalibrationResult) -> str:
        """Generate detailed calibration report"""
        report = ".2f"".2f"".1f"f"""
CALIBRATION REPORT
==================

Calibration Method: {result.calibration_method}
Target Metric: Sharpe Ratio
Convergence Status: {result.convergence_status}
Iterations Performed: {result.iterations_performed}

IMPROVEMENT SUMMARY
-------------------
Baseline Performance: {result.baseline_metrics.sharpe_ratio:.3f}
Optimized Performance: {result.optimized_metrics.sharpe_ratio:.3f}
Improvement: {result.improvement_percentage:.1f}%

OPTIMAL PARAMETERS
------------------
Quantitative Weight: {result.optimal_parameters.quantitative_weight:.2f}
LLM Weight: {result.optimal_parameters.llm_weight:.2f}
High Confidence Threshold: {result.optimal_parameters.confidence_threshold_high:.2f}
Low Confidence Threshold: {result.optimal_parameters.confidence_threshold_low:.2f}
Risk Adjustment Factor: {result.optimal_parameters.risk_adjustment_factor:.3f}

Decision Thresholds:
- Strong Buy: {result.optimal_parameters.decision_thresholds['STRONG_BUY']:.1f}
- Buy: {result.optimal_parameters.decision_thresholds['BUY']:.1f}
- Hold: {result.optimal_parameters.decision_thresholds['HOLD']:.1f}
- Avoid: {result.optimal_parameters.decision_thresholds['AVOID']:.1f}
- Strong Avoid: {result.optimal_parameters.decision_thresholds['STRONG_AVOID']:.1f}

PERFORMANCE METRICS
-------------------
Accuracy: {result.optimized_metrics.accuracy:.1%}
Win Rate: {result.optimized_metrics.win_rate:.1%}
Profit Factor: {result.optimized_metrics.profit_factor:.2f}
Sharpe Ratio: {result.optimized_metrics.sharpe_ratio:.3f}

CONFIDENCE CALIBRATION
----------------------
High Confidence Accuracy: {result.optimized_metrics.high_confidence_accuracy:.1%}
Medium Confidence Accuracy: {result.optimized_metrics.medium_confidence_accuracy:.1%}
Low Confidence Accuracy: {result.optimized_metrics.low_confidence_accuracy:.1%}
        """

        return report


def create_calibration_engine(backtesting_engine: Optional[ConfidenceBacktestingEngine] = None,
                            method: str = "bayesian_optimization") -> CalibrationEngine:
    """
    Factory function to create configured calibration engine

    Args:
        backtesting_engine: Backtesting engine instance
        method: Calibration method

    Returns:
        Configured calibration engine
    """
    return CalibrationEngine(
        backtesting_engine=backtesting_engine,
        calibration_method=method
    )


if __name__ == "__main__":
    # Test calibration engine
    from implementation.llm.backtesting_engine import ConfidenceBacktestingEngine

    backtesting_engine = ConfidenceBacktestingEngine()
    calibration_engine = create_calibration_engine(backtesting_engine, method="random_search")

    # Baseline parameters
    baseline_params = CalibrationParameters()

    print("Starting parameter calibration...")
    result = calibration_engine.calibrate_parameters(
        baseline_params=baseline_params,
        max_iterations=10,  # Reduced for testing
        target_metric="sharpe_ratio"
    )

    print("Calibration completed!")
    print(f"Improvement: {result.improvement_percentage:.1f}%")
    print(f"Optimal quant weight: {result.optimal_parameters.quantitative_weight:.2f}")
    print(f"Optimal high conf threshold: {result.optimal_parameters.confidence_threshold_high:.2f}")

    # Generate report
    report = calibration_engine.generate_calibration_report(result)
    print("\n" + "="*50)
    print(report)
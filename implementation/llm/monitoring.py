"""
RemDarwin LLM Monitoring System - Comprehensive logging and metrics collection

This module provides enterprise-grade monitoring for LLM operations including:
- API performance metrics (latency, throughput, error rates)
- Cost tracking and budget monitoring
- Quality metrics and drift detection
- Alerting and health checks
"""

import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import threading
import json

logger = logging.getLogger(__name__)


@dataclass
class APIMetrics:
    """Real-time API performance metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0.0
    total_tokens: int = 0
    total_cost_usd: float = 0.0

    # Rolling averages (last 100 requests)
    recent_latencies: deque = field(default_factory=lambda: deque(maxlen=100))
    recent_successes: deque = field(default_factory=lambda: deque(maxlen=100))

    def add_request(self, latency_ms: float, tokens: int, cost_usd: float, success: bool):
        """Add a request to metrics"""
        self.total_requests += 1
        self.total_latency_ms += latency_ms
        self.total_tokens += tokens
        self.total_cost_usd += cost_usd

        if success:
            self.successful_requests += 1
            self.recent_successes.append(1)
        else:
            self.failed_requests += 1
            self.recent_successes.append(0)

        self.recent_latencies.append(latency_ms)

        # Update min/max
        self.min_latency_ms = min(self.min_latency_ms, latency_ms)
        self.max_latency_ms = max(self.max_latency_ms, latency_ms)

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        return self.successful_requests / max(self.total_requests, 1)

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency"""
        return self.total_latency_ms / max(self.total_requests, 1)

    @property
    def recent_success_rate(self) -> float:
        """Calculate recent success rate (last 100 requests)"""
        if not self.recent_successes:
            return 1.0
        return sum(self.recent_successes) / len(self.recent_successes)

    @property
    def recent_avg_latency_ms(self) -> float:
        """Calculate recent average latency"""
        if not self.recent_latencies:
            return 0.0
        return sum(self.recent_latencies) / len(self.recent_latencies)


@dataclass
class QualityMetrics:
    """LLM output quality metrics"""
    total_evaluations: int = 0
    quality_scores: deque = field(default_factory=lambda: deque(maxlen=1000))
    confidence_scores: deque = field(default_factory=lambda: deque(maxlen=1000))
    quality_flags: Dict[str, int] = field(default_factory=dict)

    def add_evaluation(self, quality_score: float, confidence_score: float, flags: List[str]):
        """Add quality evaluation"""
        self.total_evaluations += 1
        self.quality_scores.append(quality_score)
        self.confidence_scores.append(confidence_score)

        for flag in flags:
            self.quality_flags[flag] = self.quality_flags.get(flag, 0) + 1

    @property
    def avg_quality_score(self) -> float:
        """Average quality score"""
        if not self.quality_scores:
            return 0.0
        return sum(self.quality_scores) / len(self.quality_scores)

    @property
    def avg_confidence_score(self) -> float:
        """Average confidence score"""
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores) / len(self.confidence_scores)


class LLMMonitoringSystem:
    """
    Comprehensive monitoring system for LLM operations

    Features:
    - Real-time API metrics collection
    - Quality monitoring and drift detection
    - Cost tracking and alerting
    - Health checks and status reporting
    """

    def __init__(self,
                 enable_prometheus: bool = False,
                 metrics_retention_hours: int = 24,
                 alert_thresholds: Optional[Dict[str, Any]] = None):
        """
        Initialize monitoring system

        Args:
            enable_prometheus: Enable Prometheus metrics export
            metrics_retention_hours: How long to retain detailed metrics
            alert_thresholds: Custom alert thresholds
        """
        self.enable_prometheus = enable_prometheus
        self.metrics_retention_hours = metrics_retention_hours

        # Core metrics
        self.api_metrics = APIMetrics()
        self.quality_metrics = QualityMetrics()

        # Model-specific metrics
        self.model_metrics: Dict[str, APIMetrics] = {}

        # Time-series data for trending
        self.metrics_history: deque = deque(maxlen=1000)  # Last 1000 metric snapshots

        # Alert thresholds
        self.alert_thresholds = alert_thresholds or {
            "max_error_rate": 0.05,      # 5% error rate
            "max_avg_latency_ms": 5000,  # 5 second average latency
            "max_cost_per_hour": 10.0,   # $10/hour budget
            "min_quality_score": 0.6     # Minimum quality threshold
        }

        # Active alerts
        self.active_alerts: List[Dict[str, Any]] = []

        # Background monitoring thread
        self.monitoring_thread = None
        self.stop_monitoring = False

        # Logging queue for async processing
        self.log_queue: deque = deque(maxlen=10000)
        self.log_thread = None

        logger.info("LLM Monitoring System initialized")

    def start_monitoring(self):
        """Start background monitoring threads"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return

        self.stop_monitoring = False
        self.monitoring_thread = threading.Thread(target=self._background_monitoring, daemon=True)
        self.monitoring_thread.start()

        self.log_thread = threading.Thread(target=self._process_log_queue, daemon=True)
        self.log_thread.start()

        logger.info("LLM monitoring started")

    def stop_monitoring(self):
        """Stop background monitoring"""
        self.stop_monitoring = True
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        logger.info("LLM monitoring stopped")

    def record_api_call(self, model: str, latency_ms: float, tokens: int,
                       cost_usd: float, success: bool, error_type: Optional[str] = None):
        """
        Record an API call for monitoring

        Args:
            model: Model name used
            latency_ms: Response latency in milliseconds
            tokens: Tokens consumed
            cost_usd: Cost in USD
            success: Whether the call was successful
            error_type: Error type if failed
        """
        # Record in global metrics
        self.api_metrics.add_request(latency_ms, tokens, cost_usd, success)

        # Record in model-specific metrics
        if model not in self.model_metrics:
            self.model_metrics[model] = APIMetrics()
        self.model_metrics[model].add_request(latency_ms, tokens, cost_usd, success)

        # Queue for async logging
        log_entry = {
            "timestamp": datetime.now(),
            "type": "api_call",
            "model": model,
            "latency_ms": latency_ms,
            "tokens": tokens,
            "cost_usd": cost_usd,
            "success": success,
            "error_type": error_type
        }
        self.log_queue.append(log_entry)

        # Check for alerts
        self._check_alerts()

    def record_quality_evaluation(self, quality_score: float, confidence_score: float,
                                flags: List[str], model: str):
        """
        Record LLM output quality evaluation

        Args:
            quality_score: Overall quality score (0-1)
            confidence_score: LLM confidence score (0-1)
            flags: Quality flags/issues identified
            model: Model that generated the output
        """
        self.quality_metrics.add_evaluation(quality_score, confidence_score, flags)

        # Queue for async logging
        log_entry = {
            "timestamp": datetime.now(),
            "type": "quality_evaluation",
            "model": model,
            "quality_score": quality_score,
            "confidence_score": confidence_score,
            "flags": flags
        }
        self.log_queue.append(log_entry)

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        now = datetime.now()

        # Calculate recent metrics (last 5 minutes)
        recent_cutoff = now - timedelta(minutes=5)
        recent_requests = [m for m in self.metrics_history
                          if m["timestamp"] > recent_cutoff]

        status = {
            "timestamp": now.isoformat(),
            "overall_health": self._calculate_overall_health(),
            "api_metrics": {
                "total_requests": self.api_metrics.total_requests,
                "success_rate": round(self.api_metrics.success_rate * 100, 2),
                "recent_success_rate": round(self.api_metrics.recent_success_rate * 100, 2),
                "avg_latency_ms": round(self.api_metrics.avg_latency_ms, 1),
                "recent_avg_latency_ms": round(self.api_metrics.recent_avg_latency_ms, 1),
                "total_cost_usd": round(self.api_metrics.total_cost_usd, 4),
                "cost_per_request_usd": round(self.api_metrics.total_cost_usd / max(self.api_metrics.total_requests, 1), 6)
            },
            "quality_metrics": {
                "total_evaluations": self.quality_metrics.total_evaluations,
                "avg_quality_score": round(self.quality_metrics.avg_quality_score, 3),
                "avg_confidence_score": round(self.quality_metrics.avg_confidence_score, 3),
                "quality_flags": self.quality_metrics.quality_flags
            },
            "model_performance": {
                model: {
                    "requests": metrics.total_requests,
                    "success_rate": round(metrics.success_rate * 100, 2),
                    "avg_latency_ms": round(metrics.avg_latency_ms, 1),
                    "total_cost_usd": round(metrics.total_cost_usd, 4)
                }
                for model, metrics in self.model_metrics.items()
            },
            "active_alerts": self.active_alerts,
            "monitoring_status": "active" if not self.stop_monitoring else "stopped"
        }

        return status

    def _calculate_overall_health(self) -> str:
        """Calculate overall system health"""
        issues = []

        # Check error rate
        if self.api_metrics.recent_success_rate < (1 - self.alert_thresholds["max_error_rate"]):
            issues.append("high_error_rate")

        # Check latency
        if self.api_metrics.recent_avg_latency_ms > self.alert_thresholds["max_avg_latency_ms"]:
            issues.append("high_latency")

        # Check quality
        if self.quality_metrics.avg_quality_score < self.alert_thresholds["min_quality_score"]:
            issues.append("low_quality")

        # Determine health status
        if not issues:
            return "healthy"
        elif len(issues) == 1:
            return "degraded"
        else:
            return "unhealthy"

    def _check_alerts(self):
        """Check for alert conditions"""
        alerts_to_remove = []

        # Error rate alert
        error_rate = 1 - self.api_metrics.recent_success_rate
        if error_rate > self.alert_thresholds["max_error_rate"]:
            self._add_alert("high_error_rate", f"Error rate: {error_rate:.1%}")

        # Latency alert
        if self.api_metrics.recent_avg_latency_ms > self.alert_thresholds["max_avg_latency_ms"]:
            self._add_alert("high_latency",
                          f"Average latency: {self.api_metrics.recent_avg_latency_ms:.0f}ms")

        # Cost alert (hourly)
        recent_cost = sum(m["cost_usd"] for m in list(self.metrics_history)[-60:])  # Last hour approx
        if recent_cost > self.alert_thresholds["max_cost_per_hour"]:
            self._add_alert("high_cost", f"Hourly cost: ${recent_cost:.2f}")

        # Quality alert
        if self.quality_metrics.avg_quality_score < self.alert_thresholds["min_quality_score"]:
            self._add_alert("low_quality",
                          f"Quality score: {self.quality_metrics.avg_quality_score:.2f}")

        # Remove expired alerts (older than 5 minutes)
        now = datetime.now()
        for alert in self.active_alerts[:]:
            if (now - alert["timestamp"]).total_seconds() > 300:  # 5 minutes
                self.active_alerts.remove(alert)

    def _add_alert(self, alert_type: str, message: str):
        """Add an alert if not already active"""
        for alert in self.active_alerts:
            if alert["type"] == alert_type:
                # Update existing alert
                alert["message"] = message
                alert["timestamp"] = datetime.now()
                return

        # Add new alert
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": datetime.now(),
            "severity": "warning"
        }
        self.active_alerts.append(alert)
        logger.warning(f"Alert triggered: {alert_type} - {message}")

    def _background_monitoring(self):
        """Background monitoring thread"""
        while not self.stop_monitoring:
            try:
                # Snapshot current metrics
                snapshot = {
                    "timestamp": datetime.now(),
                    "api_metrics": {
                        "total_requests": self.api_metrics.total_requests,
                        "success_rate": self.api_metrics.success_rate,
                        "avg_latency_ms": self.api_metrics.avg_latency_ms,
                        "total_cost_usd": self.api_metrics.total_cost_usd
                    },
                    "quality_metrics": {
                        "avg_quality_score": self.quality_metrics.avg_quality_score,
                        "avg_confidence_score": self.quality_metrics.avg_confidence_score
                    }
                }

                self.metrics_history.append(snapshot)

                # Clean old history
                cutoff = datetime.now() - timedelta(hours=self.metrics_retention_hours)
                while self.metrics_history and self.metrics_history[0]["timestamp"] < cutoff:
                    self.metrics_history.popleft()

                # Sleep for monitoring interval
                time.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in background monitoring: {e}")
                time.sleep(60)  # Wait longer on errors

    def _process_log_queue(self):
        """Process queued log entries asynchronously"""
        while not self.stop_monitoring:
            try:
                if self.log_queue:
                    # Process in batches of 10
                    batch = []
                    for _ in range(min(10, len(self.log_queue))):
                        batch.append(self.log_queue.popleft())

                    # Write batch to structured log
                    for entry in batch:
                        self._write_structured_log(entry)

                time.sleep(1)  # Process every second

            except Exception as e:
                logger.error(f"Error processing log queue: {e}")
                time.sleep(5)

    def _write_structured_log(self, entry: Dict[str, Any]):
        """Write structured log entry"""
        # In production, this would write to a structured logging system
        # For now, use JSON logging
        log_line = json.dumps({
            "timestamp": entry["timestamp"].isoformat(),
            "level": "INFO",
            "component": "llm_monitoring",
            **entry
        })

        # Write to dedicated log file
        try:
            with open("logs/llm_monitoring.log", "a") as f:
                f.write(log_line + "\n")
        except Exception:
            # Fallback to regular logging
            logger.info(f"LLM Monitoring: {log_line}")


# Global monitoring instance
_monitoring_instance = None

def get_monitoring_system() -> LLMMonitoringSystem:
    """Get global monitoring system instance"""
    global _monitoring_instance
    if _monitoring_instance is None:
        _monitoring_instance = LLMMonitoringSystem()
    return _monitoring_instance

def start_monitoring():
    """Start the global monitoring system"""
    get_monitoring_system().start_monitoring()

def stop_monitoring():
    """Stop the global monitoring system"""
    if _monitoring_instance:
        _monitoring_instance.stop_monitoring()
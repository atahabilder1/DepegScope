"""Historical validation module for comparing model predictions with actual events."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger

from src.models.depeg_event import DepegEvent, HISTORICAL_EVENTS, get_all_historical_events


@dataclass
class ValidationResult:
    """Result of validating model against historical event."""

    event_id: str
    event_date: datetime
    stablecoin: str

    # Actual outcomes
    actual_low_price: float
    actual_tvl_loss: float
    actual_affected_protocols: int
    actual_cascade_stablecoins: int

    # Predicted outcomes
    predicted_tvl_loss: float
    predicted_affected_protocols: int
    predicted_cascade_stablecoins: int

    # Accuracy metrics
    tvl_loss_error: float = 0.0
    protocol_count_error: float = 0.0
    cascade_error: float = 0.0

    def calculate_errors(self):
        """Calculate prediction errors."""
        if self.actual_tvl_loss > 0:
            self.tvl_loss_error = abs(
                self.predicted_tvl_loss - self.actual_tvl_loss
            ) / self.actual_tvl_loss
        else:
            self.tvl_loss_error = 0 if self.predicted_tvl_loss == 0 else 1.0

        if self.actual_affected_protocols > 0:
            self.protocol_count_error = abs(
                self.predicted_affected_protocols - self.actual_affected_protocols
            ) / self.actual_affected_protocols
        else:
            self.protocol_count_error = 0 if self.predicted_affected_protocols == 0 else 1.0

        if self.actual_cascade_stablecoins > 0:
            self.cascade_error = abs(
                self.predicted_cascade_stablecoins - self.actual_cascade_stablecoins
            ) / self.actual_cascade_stablecoins
        else:
            self.cascade_error = 0 if self.predicted_cascade_stablecoins == 0 else 1.0

    @property
    def overall_accuracy(self) -> float:
        """Calculate overall prediction accuracy."""
        errors = [self.tvl_loss_error, self.protocol_count_error, self.cascade_error]
        avg_error = np.mean([e for e in errors if not np.isnan(e)])
        return max(0, 1 - avg_error)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_date": self.event_date.isoformat(),
            "stablecoin": self.stablecoin,
            "actual_low_price": self.actual_low_price,
            "actual_tvl_loss": self.actual_tvl_loss,
            "actual_affected_protocols": self.actual_affected_protocols,
            "actual_cascade_stablecoins": self.actual_cascade_stablecoins,
            "predicted_tvl_loss": self.predicted_tvl_loss,
            "predicted_affected_protocols": self.predicted_affected_protocols,
            "predicted_cascade_stablecoins": self.predicted_cascade_stablecoins,
            "tvl_loss_error": self.tvl_loss_error,
            "protocol_count_error": self.protocol_count_error,
            "cascade_error": self.cascade_error,
            "overall_accuracy": self.overall_accuracy
        }


class HistoricalValidator:
    """Validate model predictions against historical depeg events."""

    def __init__(self, contagion_analyzer):
        """
        Initialize historical validator.

        Args:
            contagion_analyzer: ContagionAnalyzer instance
        """
        self.analyzer = contagion_analyzer
        self.validation_results: List[ValidationResult] = []

    def validate_event(
        self,
        event: DepegEvent,
        use_simulation: bool = True
    ) -> ValidationResult:
        """
        Validate model predictions against a historical event.

        Args:
            event: Historical depeg event
            use_simulation: Whether to use simulation (vs static analysis)

        Returns:
            ValidationResult with comparison metrics
        """
        logger.info(f"Validating against event: {event.event_id}")

        # Calculate depeg severity from actual low price
        severity = 1.0 - event.low_price

        # Get model predictions
        if use_simulation:
            # Note: This would need the stablecoin to be in the model
            # For historical events, we might not have the exact state
            try:
                sim_result = self.analyzer.simulate_contagion(
                    event.stablecoin,
                    severity=severity,
                    seed=42
                )
                predicted_tvl_loss = sim_result["total_tvl_lost"]
                predicted_protocols = sim_result["distressed_protocols"]
                predicted_stablecoins = sim_result["depegged_stablecoins"] - 1  # Exclude trigger
            except Exception as e:
                logger.warning(f"Simulation failed for {event.stablecoin}: {e}")
                # Fall back to static analysis
                use_simulation = False

        if not use_simulation:
            static_result = self.analyzer.analyze_static_contagion(
                event.stablecoin,
                severity
            )
            predicted_tvl_loss = static_result["blast_radius"]["total_tvl_at_risk"]
            predicted_protocols = static_result["blast_radius"]["protocols_affected"]
            predicted_stablecoins = static_result["blast_radius"]["stablecoins_affected"]

        # Create validation result
        result = ValidationResult(
            event_id=event.event_id,
            event_date=event.date,
            stablecoin=event.stablecoin,
            actual_low_price=event.low_price,
            actual_tvl_loss=event.total_loss_usd,
            actual_affected_protocols=len(event.affected_protocols),
            actual_cascade_stablecoins=len(event.affected_stablecoins()) - 1,
            predicted_tvl_loss=predicted_tvl_loss,
            predicted_affected_protocols=predicted_protocols,
            predicted_cascade_stablecoins=predicted_stablecoins
        )

        result.calculate_errors()
        self.validation_results.append(result)

        return result

    def validate_all_events(
        self,
        events: Optional[List[DepegEvent]] = None
    ) -> List[ValidationResult]:
        """
        Validate against all historical events.

        Args:
            events: List of events (defaults to all historical events)

        Returns:
            List of validation results
        """
        events = events or get_all_historical_events()
        results = []

        for event in events:
            try:
                result = self.validate_event(event)
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to validate event {event.event_id}: {e}")

        return results

    def calculate_model_accuracy(self) -> Dict[str, Any]:
        """
        Calculate overall model accuracy across all validated events.

        Returns:
            Accuracy metrics
        """
        if not self.validation_results:
            return {"error": "No validation results available"}

        accuracies = [r.overall_accuracy for r in self.validation_results]
        tvl_errors = [r.tvl_loss_error for r in self.validation_results]
        protocol_errors = [r.protocol_count_error for r in self.validation_results]
        cascade_errors = [r.cascade_error for r in self.validation_results]

        return {
            "overall_accuracy": {
                "mean": np.mean(accuracies),
                "std": np.std(accuracies),
                "min": np.min(accuracies),
                "max": np.max(accuracies)
            },
            "tvl_prediction": {
                "mean_error": np.mean(tvl_errors),
                "std_error": np.std(tvl_errors)
            },
            "protocol_prediction": {
                "mean_error": np.mean(protocol_errors),
                "std_error": np.std(protocol_errors)
            },
            "cascade_prediction": {
                "mean_error": np.mean(cascade_errors),
                "std_error": np.std(cascade_errors)
            },
            "n_events_validated": len(self.validation_results),
            "events": [r.event_id for r in self.validation_results]
        }

    def generate_validation_report(self) -> pd.DataFrame:
        """
        Generate validation report as DataFrame.

        Returns:
            DataFrame with validation results
        """
        return pd.DataFrame([r.to_dict() for r in self.validation_results])

    def identify_model_weaknesses(self) -> Dict[str, Any]:
        """
        Identify where the model performs poorly.

        Returns:
            Analysis of model weaknesses
        """
        if not self.validation_results:
            return {"error": "No validation results available"}

        # Group by error type
        high_tvl_error = [
            r for r in self.validation_results
            if r.tvl_loss_error > 0.5
        ]
        high_protocol_error = [
            r for r in self.validation_results
            if r.protocol_count_error > 0.5
        ]
        high_cascade_error = [
            r for r in self.validation_results
            if r.cascade_error > 0.5
        ]

        # Identify patterns
        underestimated = [
            r for r in self.validation_results
            if r.predicted_tvl_loss < r.actual_tvl_loss * 0.5
        ]
        overestimated = [
            r for r in self.validation_results
            if r.predicted_tvl_loss > r.actual_tvl_loss * 2
        ]

        return {
            "high_tvl_errors": [r.event_id for r in high_tvl_error],
            "high_protocol_errors": [r.event_id for r in high_protocol_error],
            "high_cascade_errors": [r.event_id for r in high_cascade_error],
            "underestimated_events": [r.event_id for r in underestimated],
            "overestimated_events": [r.event_id for r in overestimated],
            "recommendations": self._generate_improvement_recommendations(
                high_tvl_error, high_protocol_error, high_cascade_error
            )
        }

    def _generate_improvement_recommendations(
        self,
        tvl_errors: List[ValidationResult],
        protocol_errors: List[ValidationResult],
        cascade_errors: List[ValidationResult]
    ) -> List[str]:
        """Generate model improvement recommendations."""
        recommendations = []

        if len(tvl_errors) > len(self.validation_results) * 0.3:
            recommendations.append(
                "TVL loss predictions have high error rate. "
                "Consider refining exposure weight calculations."
            )

        if len(protocol_errors) > len(self.validation_results) * 0.3:
            recommendations.append(
                "Protocol count predictions have high error rate. "
                "Consider adjusting distress thresholds."
            )

        if len(cascade_errors) > len(self.validation_results) * 0.3:
            recommendations.append(
                "Cascade predictions have high error rate. "
                "Consider adding more stablecoin-to-stablecoin dependencies."
            )

        if not recommendations:
            recommendations.append(
                "Model performs within acceptable bounds. "
                "Continue monitoring with new events."
            )

        return recommendations

    def backtest_early_warnings(
        self,
        price_data: Dict[str, pd.DataFrame],
        events: Optional[List[DepegEvent]] = None
    ) -> Dict[str, Any]:
        """
        Backtest early warning system against historical events.

        Args:
            price_data: Historical price data by stablecoin
            events: Events to test (defaults to all)

        Returns:
            Backtest results
        """
        from src.analysis.early_warning import EarlyWarningSystem

        events = events or get_all_historical_events()
        ews = EarlyWarningSystem()

        results = []
        for event in events:
            if event.stablecoin not in price_data:
                continue

            prices = price_data[event.stablecoin]

            # Get prices before the event
            pre_event_prices = prices[prices.index < event.date]
            if len(pre_event_prices) < 48:  # Need at least 48 hours
                continue

            # Check warnings in the 24 hours before event
            warning_window = pre_event_prices.iloc[-24:]

            # Simulate warning check
            signal = ews.check_price_deviation(warning_window["price"])

            # Check if we would have detected warning
            detected = signal.warning
            hours_before = (event.date - warning_window.index[-1]).total_seconds() / 3600

            results.append({
                "event_id": event.event_id,
                "stablecoin": event.stablecoin,
                "warning_detected": detected,
                "warning_severity": signal.severity,
                "hours_before_event": hours_before,
                "actual_severity": event.max_deviation
            })

        # Calculate detection rate
        detection_rate = sum(r["warning_detected"] for r in results) / max(len(results), 1)

        return {
            "detection_rate": detection_rate,
            "events_tested": len(results),
            "true_positives": sum(r["warning_detected"] for r in results),
            "false_negatives": sum(not r["warning_detected"] for r in results),
            "details": results
        }

    def compare_severity_predictions(
        self,
        events: Optional[List[DepegEvent]] = None
    ) -> pd.DataFrame:
        """
        Compare predicted vs actual severity across events.

        Args:
            events: Events to compare

        Returns:
            DataFrame with severity comparison
        """
        events = events or get_all_historical_events()
        comparisons = []

        for event in events:
            actual_severity = 1.0 - event.low_price

            # Get model prediction for severity
            try:
                result = self.analyzer.simulate_contagion(
                    event.stablecoin,
                    severity=0.1,  # Start with moderate severity
                    seed=42
                )

                # Find final price in simulation
                final_states = result.get("stablecoin_final_states", [])
                predicted_price = 1.0
                for state in final_states:
                    if state.get("symbol") == event.stablecoin:
                        predicted_price = state.get("price", 1.0)
                        break

                predicted_severity = 1.0 - predicted_price

            except Exception:
                predicted_severity = None

            comparisons.append({
                "event_id": event.event_id,
                "stablecoin": event.stablecoin,
                "actual_severity": actual_severity,
                "predicted_severity": predicted_severity,
                "severity_error": (
                    abs(predicted_severity - actual_severity)
                    if predicted_severity is not None else None
                )
            })

        return pd.DataFrame(comparisons)

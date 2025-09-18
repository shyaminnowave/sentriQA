from typing import List, Dict, Optional, Union
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from django.db.models import QuerySet
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScoreWeights:
    """Configuration class for score calculation weights"""
    risk_weight: float = 1.0
    failure_rate_weight: float = 1.0
    change_weight: float = 1.0
    defect_weight: float = 1.0
    execution_time_penalty: float = 1.0

    def __post_init__(self):
        """Validate weights are non-negative"""
        for field_name, value in self.__dict__.items():
            if value < 0:
                raise ValueError(f"{field_name} must be non-negative, got {value}")


@dataclass
class TestCaseScoreResult:
    """Result object containing score and breakdown"""
    testcase_id: int
    total_score: Decimal
    risk_component: Decimal
    failure_rate_component: Decimal
    change_impact_component: Decimal
    defect_component: Decimal
    execution_penalty_component: Decimal
    normalized_score: Optional[Decimal] = None

    def to_dict(self) -> Dict[str, Union[int, float]]:
        """Convert to dictionary for serialization"""
        return {
            'testcase_id': self.testcase_id,
            'total_score': float(self.total_score),
            'risk_component': float(self.risk_component),
            'failure_rate_component': float(self.failure_rate_component),
            'change_impact_component': float(self.change_impact_component),
            'defect_component': float(self.defect_component),
            'execution_penalty_component': float(self.execution_penalty_component),
            'normalized_score': float(self.normalized_score) if self.normalized_score else None
        }


class TestCaseScore:
    """
    Enterprise-grade test case scoring system implementing risk-based prioritization.

    Calculates comprehensive scores based on:
    - Risk metrics (impact × likelihood)
    - Historical failure rates
    - Code change impact
    - Defect analysis
    - Execution time penalties
    """

    # Constants for score calculation
    MAX_RPN = 10000  # Maximum possible RPN (100 * 100)
    PRECISION = 2
    DEFAULT_MAX_EXECUTION_TIME = Decimal('300.00')  # 5 minutes default

    def __init__(self, weights: Optional[ScoreWeights] = None):
        """
        Initialize scorer with configurable weights.

        Args:
            weights: Custom weight configuration. Uses defaults if None.
        """
        self.weights = weights or ScoreWeights()
        self._validation_errors: List[str] = []

    def calculate_scores(
            self,
            testcase_metrics: QuerySet,
            normalize: bool = True,
            max_execution_time: Optional[Decimal] = None
    ) -> List[TestCaseScoreResult]:
        """
        Calculate scores for a queryset of TestCaseMetric objects.

        Args:
            testcase_metrics: QuerySet of TestCaseMetric objects
            normalize: Whether to normalize scores to 0-100 range
            max_execution_time: Custom max execution time for penalty calculation

        Returns:
            List of TestCaseScoreResult objects sorted by score (highest first)

        Raises:
            ValidationError: If critical validation errors occur
        """
        if not testcase_metrics.exists():
            logger.warning("Empty testcase metrics queryset provided")
            return []

        max_exec_time = max_execution_time or self.DEFAULT_MAX_EXECUTION_TIME
        results = []

        # Calculate raw scores
        for metric in testcase_metrics.select_related('testcase'):
            try:
                score_result = self._calculate_single_score(metric, max_exec_time)
                results.append(score_result)
            except Exception as e:
                logger.error(f"Error calculating score for testcase {metric.testcase.id}: {e}")
                continue

        if not results:
            raise ValidationError("No valid scores could be calculated")

        # Normalize scores if requested
        if normalize:
            results = self._normalize_scores(results)

        # Sort by total score (descending)
        results.sort(key=lambda x: x.total_score, reverse=True)

        return results

    def _calculate_single_score(
            self,
            metric,
            max_execution_time: Decimal
    ) -> TestCaseScoreResult:
        """Calculate score for a single test case metric."""

        # Risk Calculation (RPN)
        risk_component = self._calculate_risk_component(metric)

        # Historical Failure Rate
        failure_rate_component = self._calculate_failure_rate_component(metric)

        # Code Change Impact
        change_impact_component = self._calculate_change_impact_component(metric)

        # Defect Analysis
        defect_component = self._calculate_defect_component(metric)

        # Execution Time Penalty
        execution_penalty = self._calculate_execution_penalty(metric, max_execution_time)

        # Total Score Calculation
        total_score = (
                (risk_component * self.weights.risk_weight) +
                (failure_rate_component * self.weights.failure_rate_weight) +
                (change_impact_component * self.weights.change_weight) +
                (defect_component * self.weights.defect_weight) -
                (execution_penalty * self.weights.execution_time_penalty)
        )

        # Ensure score is non-negative
        total_score = max(total_score, Decimal('0'))

        return TestCaseScoreResult(
            testcase_id=metric.testcase.id,
            total_score=self._round_decimal(total_score),
            risk_component=self._round_decimal(risk_component),
            failure_rate_component=self._round_decimal(failure_rate_component),
            change_impact_component=self._round_decimal(change_impact_component),
            defect_component=self._round_decimal(defect_component),
            execution_penalty_component=self._round_decimal(execution_penalty)
        )

    def _calculate_risk_component(self, metric) -> Decimal:
        """Calculate Risk Priority Number (RPN) component."""
        impact = metric.impact or 0
        likelihood = metric.likelihood or 0

        rpn = Decimal(str(impact * likelihood))

        # Normalize RPN to a 0-100 scale
        if self.MAX_RPN > 0:
            risk_weight = rpn / Decimal(str(self.MAX_RPN))
            return risk_weight * Decimal('100')

        return Decimal('0')

    def _calculate_failure_rate_component(self, metric) -> Decimal:
        """Calculate failure rate component."""
        if metric.total_runs and metric.total_runs > 0:
            failure_rate = Decimal(str(metric.failure or 0)) / Decimal(str(metric.total_runs))
        else:
            failure_rate = metric.failure_rate or Decimal('0')

        # Convert to percentage and weight it
        return failure_rate * Decimal('100')

    def _calculate_change_impact_component(self, metric) -> Decimal:
        """Calculate code change impact component."""
        direct_impact = Decimal(str(metric.direct_impact or 0))

        # Direct impact = 1, Indirect impact = 0.5 (as per diagram)
        if direct_impact == 1:
            return Decimal('100')  # High impact
        elif direct_impact > 0:
            return Decimal('50')  # Medium impact
        else:
            return Decimal('0')  # No impact

    def _calculate_defect_component(self, metric) -> Decimal:
        """Calculate defect analysis component."""
        defects = metric.defects or 0
        severity = metric.severity or 0
        feature_size = max(metric.feature_size or 1, 1)  # Prevent division by zero

        # Defect Density = Total Defects / Feature Size
        defect_density = Decimal(str(defects)) / Decimal(str(feature_size))

        # Defect Weight = Severity × Defect Density
        defect_weight = Decimal(str(severity)) * defect_density

        # Normalize to 0-100 scale (assuming max severity = 10, max reasonable density = 10)
        max_defect_weight = Decimal('100')  # 10 * 10
        if max_defect_weight > 0:
            return min((defect_weight / max_defect_weight) * Decimal('100'), Decimal('100'))

        return Decimal('0')

    def _calculate_execution_penalty(self, metric, max_execution_time: Decimal) -> Decimal:
        """Calculate execution time penalty."""
        execution_time = metric.execution_time or Decimal('0')

        if max_execution_time <= 0 or execution_time <= 0:
            return Decimal('0')

        # Penalty = (Execution Time / Max Execution Time) * 100
        penalty_ratio = execution_time / max_execution_time
        return min(penalty_ratio * Decimal('100'), Decimal('100'))

    def _normalize_scores(self, results: List[TestCaseScoreResult]) -> List[TestCaseScoreResult]:
        """Normalize scores to 0-100 range."""
        if not results:
            return results

        scores = [result.total_score for result in results]
        max_score = max(scores)
        min_score = min(scores)

        # Avoid division by zero
        score_range = max_score - min_score
        if score_range == 0:
            for result in results:
                result.normalized_score = Decimal('100')
            return results

        # Normalize each score
        for result in results:
            normalized = ((result.total_score - min_score) / score_range) * Decimal('100')
            result.normalized_score = self._round_decimal(normalized)

        return results

    def _round_decimal(self, value: Decimal) -> Decimal:
        """Round decimal to configured precision."""
        return value.quantize(
            Decimal(10) ** -self.PRECISION,
            rounding=ROUND_HALF_UP
        )

    def get_score_summary(self, results: List[TestCaseScoreResult]) -> Dict[str, Union[int, float]]:
        """Get statistical summary of calculated scores."""
        if not results:
            return {}

        scores = [float(result.total_score) for result in results]
        normalized_scores = [float(result.normalized_score or 0) for result in results]

        return {
            'total_testcases': len(results),
            'avg_score': sum(scores) / len(scores),
            'max_score': max(scores),
            'min_score': min(scores),
            'avg_normalized_score': sum(normalized_scores) / len(normalized_scores) if normalized_scores else 0,
            'high_priority_count': len([s for s in normalized_scores if s >= 80]),
            'medium_priority_count': len([s for s in normalized_scores if 40 <= s < 80]),
            'low_priority_count': len([s for s in normalized_scores if s < 40])
        }
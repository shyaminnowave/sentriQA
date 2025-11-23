from typing import List, Dict, Optional, Union, Any
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from django.db.models import QuerySet
from apps.core.models import RPNValue
from django.core.exceptions import ValidationError
from apps.core.models import TestCaseMetric
from apps.core.datacls import TestCaseScoreResult
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
    PRECISION = 2
    DEFAULT_MAX_EXECUTION_TIME = 0
    # TestCaseMetric.get_max_time() # 5 minutes default

    def get_max_rpn(self, value: Decimal) -> Decimal:
        get_max = RPNValue.get_solo()

        if get_max.max_value is None or get_max.max_value < value:
            get_max.max_value = value
            get_max.save()
            return Decimal(value)

        return get_max.max_value

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
        # if normalize:
        #     results = self._normalize_scores(results)

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
        risk_component = Decimal(self._calculate_risk_component(metric))
        # Historical Failure Rate
        failure_rate_component = Decimal(self._calculate_failure_rate_component(metric))
        # Code Change Impact
        change_impact_component = Decimal(self._calculate_change_impact_component(metric))
        # Defect Analysis
        defect_component = Decimal(self._calculate_defect_component(metric))
        # Execution Time Penalty
        execution_penalty = Decimal(self._calculate_execution_penalty(metric, max_execution_time))
        # Total Score Calculation
        total_score = (
                (risk_component +
                failure_rate_component +
                change_impact_component) +
                (defect_component -
                execution_penalty)
        )

        # Ensure score is non-negative
        # total_score = max(total_score, Decimal('0'))

        return TestCaseScoreResult(
            testcase_id=metric.testcase.id,
            testcase_name=metric.testcase.name,
            testcase_type=metric.testcase.testcase_type,
            failure_rate = metric.failure_rate,
            defects = metric.defects,
            module=metric.testcase.module.name if metric.testcase.module else "N/A",
            priority=metric.testcase.priority,
            total_score=self._round_decimal(total_score),
            risk_component=self._round_decimal(risk_component),
            failure_rate_component=self._round_decimal(failure_rate_component),
            change_impact_component=self._round_decimal(change_impact_component),
            defect_component=self._round_decimal(defect_component),
            execution_penalty_component=self._round_decimal(execution_penalty)
        )

    def _calculate_priority(self, value):
        if value == 'class_1':
            return Decimal(3)
        elif value == 'class_2':
            return Decimal(2)
        elif value == 'class_3':
            return Decimal(1)
        else:
            return Decimal(value)

    def _calculate_risk_component(self, metric) -> Decimal:
        """Calculate Risk Priority Number (RPN) component."""
        impact = metric.impact or 0
        likelihood = metric.likelihood or 0
        rpn = Decimal(impact * likelihood)
        max_rpn = self.get_max_rpn(rpn)
        if max_rpn > 0:
            risk_weight = Decimal(rpn / max_rpn)
            return Decimal(risk_weight * self._calculate_priority(metric.testcase.priority))
        return Decimal(0)

    def _calculate_failure_rate_component(self, metric) -> Decimal:
        """Calculate failure rate component."""
        if metric.total_runs and metric.total_runs > 0:
            failure_rate = Decimal(str(metric.failure or 0)) / Decimal(str(metric.total_runs))
            return failure_rate * metric.failure_rate
        else:
            failure_rate = metric.failure_rate or Decimal('0')

        # Convert to percentage and weight it
        return failure_rate * Decimal('100')

    def _calculate_change_impact_component(self, metric) -> Decimal:
        """Calculate code change impact component."""
        direct_impact = Decimal(str(metric.direct_impact or 0))

        if direct_impact >= 1:
            return Decimal('1')  # High impact
        else:
            return Decimal('0.5')  # No impact

    def _calculate_defect_component(self, metric) -> Decimal:
        """Calculate defect analysis component."""
        defects = metric.defects or 0
        severity = metric.severity or 0
        feature_size = metric.feature_size
        if not feature_size or feature_size == 0:
            return Decimal('0')
        defect_density = Decimal(defects) / Decimal(feature_size)
        defect_weight = Decimal(str(severity)) * defect_density
        return defect_weight

    def _calculate_execution_penalty(self, metric, max_execution_time: Decimal) -> Decimal:
        """Calculate execution time penalty."""
        execution_time = metric.execution_time or Decimal('0')
        max_execution_time = max_execution_time or self.DEFAULT_MAX_EXECUTION_TIME
        if max_execution_time:
            get_execution_time = Decimal(str(execution_time)) / Decimal(str(max_execution_time))
            return get_execution_time
        return Decimal(0)

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
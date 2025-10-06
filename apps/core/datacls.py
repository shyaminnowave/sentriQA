from decimal import Decimal
from typing import Optional, Dict, Union
from pydantic import BaseModel, Field


class TestCaseScoreResult(BaseModel):
    """Result object containing score and breakdown"""
    testcase_id: int
    testcase_name: str
    total_score: Decimal
    module: str
    priority: str
    risk_component: Decimal
    failure_rate_component: Decimal
    change_impact_component: Decimal
    defect_component: Decimal
    execution_penalty_component: Decimal
    normalized_score: Optional[Decimal] = None

    class Config:
        # Allow arbitrary types like Decimal
        arbitrary_types_allowed = True
        # Use enum values instead of enum objects
        use_enum_values = True

    def to_dict(self) -> Dict[str, Union[int, float]]:
        """Convert to dictionary for serialization"""
        return {
            'testcase_id': self.testcase_id,
            'total_score': float(self.total_score),
            'testcase_name': self.testcase_name,
            'module': self.module,
            'priority': self.priority,
        }
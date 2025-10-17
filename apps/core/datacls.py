import uuid
from decimal import Decimal
from typing import Optional, Dict, Union, List
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

class TestPlanInput(BaseModel):

    name: str
    description: str
    output_counts: str
    module_names: Optional[List[str]]
    priority: str
    project: str = None


class TestcaseData(BaseModel):

    id: int
    testcase: str
    modules: str
    mode: str
    generated: bool
    priority: str
    testscore: float


class Session(BaseModel):

    session: uuid.UUID
    context: str
    version: str
    name: str
    description: str
    modules: List[str]
    output_counts: int
    testcase_data: List[TestcaseData] = Field(default_factory=list)
    status: Optional[str] = None

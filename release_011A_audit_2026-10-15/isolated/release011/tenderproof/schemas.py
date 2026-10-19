from dataclasses import dataclass, field


@dataclass
class RuleResult:
    rule_code: str
    rule_name: str
    status: str
    severity: str
    message: str
    blocker: bool = False


@dataclass
class VerificationSummary:
    overall_status: str
    blockers: list[RuleResult] = field(default_factory=list)
    warnings: list[RuleResult] = field(default_factory=list)
    readiness_label: str = "DRAFT_ONLY"
    rule_results: list[RuleResult] = field(default_factory=list)
    quality_metrics: dict = field(default_factory=dict)


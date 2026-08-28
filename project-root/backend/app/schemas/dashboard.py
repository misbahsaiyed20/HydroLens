from pydantic import BaseModel


class DashboardSummary(BaseModel):
    """
    High-level counts for the dashboard landing view. All computed live
    from the database (no hardcoded numbers, no caching yet — see README
    limitations for the perf tradeoff at scale).
    """
    total_reports: int
    pending_review: int  # status in (SUBMITTED, ANALYZING) — AI hasn't finished yet
    analyzed_reports: int  # status == ANALYZED (i.e. eligible to be a "case")
    high_confidence_cases: int  # analyzed reports whose evidence-fusion confidence_level == HIGH
    verified_cases: int  # verification_status == VERIFIED
    rejected_cases: int  # verification_status == REJECTED
    cases_requiring_review: int  # actionability action_level in (REVIEW_RECOMMENDED, PRIORITY_REVIEW)

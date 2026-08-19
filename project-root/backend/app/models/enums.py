import enum


class ReportStatus(str, enum.Enum):
    """
    Lifecycle of a citizen report.

    SUBMITTED    -> just created, nothing has processed it yet
    ANALYZING    -> AI vision service is currently extracting indicators (Sprint 3+)
    ANALYZED     -> AI extraction finished, indicators exist on the Observation
    UNDER_REVIEW -> case/evidence-fusion layer has flagged it for an officer (later sprint)
    VERIFIED     -> an officer confirmed the environmental risk signal
    DISMISSED    -> an officer reviewed it and rejected it (false positive, duplicate, etc.)
    """
    SUBMITTED = "SUBMITTED"
    ANALYZING = "ANALYZING"
    ANALYZED = "ANALYZED"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    DISMISSED = "DISMISSED"

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


class VerificationStatus(str, enum.Enum):
    """
    Whether a HUMAN has reviewed this report's AI-generated observation.
    Deliberately separate from ReportStatus: ReportStatus answers "has the
    image been analyzed by AI yet?" (SUBMITTED/ANALYZING/ANALYZED/...),
    while VerificationStatus answers "has a person reviewed/confirmed that
    AI output?". Conflating the two was a real risk here — ReportStatus
    already has unused VERIFIED/DISMISSED values left over from an earlier
    design; this enum exists specifically so verification isn't bolted onto
    that AI-status enum. See README's "Trust architecture" section.

    UNVERIFIED -> default state; no human has reviewed this report yet
    VERIFIED   -> a human confirmed the AI observation is a reasonable read of the photo
    REJECTED   -> a human reviewed it and determined it should not be treated as valid evidence
    """
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

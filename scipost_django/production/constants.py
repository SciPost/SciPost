__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


PRODUCTION_STREAM_INITIATED = "initiated"
PRODUCTION_STREAM_COMPLETED = "completed"
PROOFS_SOURCE_REQUESTED = "source_requested"
PROOFS_TASKED = "tasked"
PROOFS_PRODUCED = "produced"
PROOFS_CHECKED = "checked"
PROOFS_SENT = "sent"
PROOFS_RETURNED = "returned"
PROOFS_CORRECTED = "corrected"
PROOFS_ACCEPTED = "accepted"
PROOFS_PUBLISHED = "published"
PROOFS_CITED = "cited"
PRODUCTION_STREAM_STATUS = (
    (PRODUCTION_STREAM_INITIATED, "New Stream started"),
    (PROOFS_SOURCE_REQUESTED, "Source files requested"),
    (PROOFS_TASKED, "Supervisor tasked officer with proofs production"),
    (PROOFS_PRODUCED, "Proofs have been produced"),
    (PROOFS_CHECKED, "Proofs have been checked by Supervisor"),
    (PROOFS_SENT, "Proofs sent to Authors"),
    (PROOFS_RETURNED, "Proofs returned by Authors"),
    (PROOFS_CORRECTED, "Corrections implemented"),
    (PROOFS_ACCEPTED, "Authors have accepted proofs"),
    (PROOFS_PUBLISHED, "Paper has been published"),
    (PROOFS_CITED, "Cited people have been notified/invited to SciPost"),
    (PRODUCTION_STREAM_COMPLETED, "Completed"),
)

EVENT_MESSAGE = "message"
EVENT_HOUR_REGISTRATION = "registration"
PRODUCTION_EVENTS = (
    ("assignment", "Assignment"),
    ("status", "Status change"),
    (EVENT_MESSAGE, "Message"),
    (EVENT_HOUR_REGISTRATION, "Hour registration"),
)

PROOFS_UPLOADED = "uploaded"
PROOFS_SENT = "sent"
PROOFS_ACCEPTED_SUP = "accepted_sup"
PROOFS_DECLINED_SUP = "declined_sup"
PROOFS_DECLINED = "declined"
PROOFS_RENEWED = "renewed"
PROOFS_STATUSES = (
    (PROOFS_UPLOADED, "Proofs uploaded"),
    (PROOFS_SENT, "Proofs sent to authors"),
    (PROOFS_ACCEPTED_SUP, "Proofs accepted by supervisor"),
    (PROOFS_DECLINED_SUP, "Proofs declined by supervisor"),
    (PROOFS_ACCEPTED, "Proofs accepted by authors"),
    (PROOFS_DECLINED, "Proofs declined by authors"),
    (PROOFS_RENEWED, "Proofs renewed"),
)

WORK_LOG_TYPE_TIME_OFF = "time_off"
WORK_LOG_TYPE_PROOFS_PRODUCED = "production_proofs_produced"
WORK_LOG_TYPE_CORRECTIONS_IMPLEMENTED = "production_corrections_implemented"
WORK_LOG_TYPE_CITED_PEOPLE_NOTIFIED = "production_cited_people_notified"
WORK_LOG_TYPE_PROOFS_CHECKED = "production_proofs_checked"
WORK_LOG_TYPE_PAPER_PUBLISHED = "production_paper_published"
WORK_LOG_TYPE_METADATA_UPDATED = "maintenance_metadata_updated"

WORK_LOG_TYPE_OFFICER_CHOICES = (
    (WORK_LOG_TYPE_PROOFS_PRODUCED, "Proofs have been produced"),
    (WORK_LOG_TYPE_CORRECTIONS_IMPLEMENTED, "Corrections implemented"),
    (
        WORK_LOG_TYPE_CITED_PEOPLE_NOTIFIED,
        "Cited people have been notified/invited to SciPost",
    ),
)
WORK_LOG_TYPE_SUPERVISOR_CHOICES = (
    (WORK_LOG_TYPE_PROOFS_PRODUCED, "Proofs have been produced"),
    (
        WORK_LOG_TYPE_PROOFS_CHECKED,
        "Proofs have been checked by Supervisor",
    ),
    (WORK_LOG_TYPE_CORRECTIONS_IMPLEMENTED, "Corrections implemented"),
    (WORK_LOG_TYPE_PAPER_PUBLISHED, "Paper has been published"),
    (WORK_LOG_TYPE_METADATA_UPDATED, "Metadata has been updated"),
    (
        WORK_LOG_TYPE_CITED_PEOPLE_NOTIFIED,
        "Cited people have been notified/invited to SciPost",
    ),
)
WORK_LOG_TYPE_CHOICES = [
    (WORK_LOG_TYPE_TIME_OFF, "Time off"),
] + list(WORK_LOG_TYPE_SUPERVISOR_CHOICES)

PROOFS_REPO_UNINITIALIZED = "uninitialized"
PROOFS_REPO_CREATED = "created"
PROOFS_REPO_TEMPLATE_ONLY = "template_only"
PROOFS_REPO_TEMPLATE_FORMATTED = "template_formatted"
PROOFS_REPO_PRODUCTION_READY = "production_ready"
PROOFS_REPO_STATUSES = (
    (PROOFS_REPO_UNINITIALIZED, "The repository does not exist"),
    (PROOFS_REPO_CREATED, "The repository exists but is empty"),
    (PROOFS_REPO_TEMPLATE_ONLY, "The repository contains the bare template"),
    (
        PROOFS_REPO_TEMPLATE_FORMATTED,
        "The repository contains the automatically formatted template",
    ),
    (PROOFS_REPO_PRODUCTION_READY, "The repository is ready for production"),
)

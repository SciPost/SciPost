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

PRODUCTION_OFFICERS_WORK_LOG_TYPES = (
    ("Production: Proofs have been produced", "Proofs have been produced"),
    ("Production: Corrections implemented", "Corrections implemented"),
    (
        "Production: Cited people have been notified/invited to SciPost",
        "Cited people have been notified/invited to SciPost",
    ),
)
PRODUCTION_ALL_WORK_LOG_TYPES = (
    ("Production: Proofs have been produced", "Proofs have been produced"),
    (
        "Production: Proofs have been checked by Supervisor",
        "Proofs have been checked by Supervisor",
    ),
    ("Production: Corrections implemented", "Corrections implemented"),
    ("Production: Paper has been published", "Paper has been published"),
    ("Maintaince: Metadata has been updated", "Metadata has been updated"),
    (
        "Production: Cited people have been notified/invited to SciPost",
        "Cited people have been notified/invited to SciPost",
    ),
)

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

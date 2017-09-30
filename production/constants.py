PRODUCTION_STREAM_INITIATED = 'initiated'
PRODUCTION_STREAM_COMPLETED = 'completed'
PROOFS_TASKED = 'tasked'
PROOFS_PRODUCED = 'produced'
PROOFS_CHECKED = 'checked'
PROOFS_SENT = 'sent'
PROOFS_RETURNED = 'returned'
PROOFS_CORRECTED = 'corrected'
PROOFS_ACCEPTED = 'accepted'
PROOFS_PUBLISHED = 'published'
PROOFS_CITED = 'cited'
PRODUCTION_STREAM_STATUS = (
    (PRODUCTION_STREAM_INITIATED, 'New Stream started'),
    (PROOFS_TASKED, 'Supervisor tasked officer with proofs production'),
    (PROOFS_PRODUCED, 'Proofs have been produced'),
    (PROOFS_CHECKED, 'Proofs have been checked by Supervisor'),
    (PROOFS_SENT, 'Proofs sent to Authors'),
    (PROOFS_RETURNED, 'Proofs returned by Authors'),
    (PROOFS_CORRECTED, 'Corrections implemented'),
    (PROOFS_ACCEPTED, 'Authors have accepted proofs'),
    (PROOFS_PUBLISHED, 'Paper has been published'),
    (PROOFS_CITED, 'Cited people have been notified/invited to SciPost'),
    (PRODUCTION_STREAM_COMPLETED, 'Completed'),
)

EVENT_MESSAGE = 'message'
EVENT_HOUR_REGISTRATION = 'registration'
PRODUCTION_EVENTS = (
    ('assignment', 'Assignment'),
    ('status', 'Status change'),
    (EVENT_MESSAGE, 'Message'),
    (EVENT_HOUR_REGISTRATION, 'Hour registration'),
)

PROOF_UPLOADED = 'uploaded'
PROOF_SENT = 'sent'
PROOF_ACCEPTED_SUP = 'accepted_sup'
PROOF_DECLINED_SUP = 'declined_sup'
PROOF_ACCEPTED = 'accepted'
PROOF_DECLINED = 'declined'
PROOF_RENEWED = 'renewed'
PROOF_STATUSES = (
    (PROOF_UPLOADED, 'Proofs uploaded'),
    (PROOF_SENT, 'Proofs sent to authors'),
    (PROOF_ACCEPTED_SUP, 'Proofs accepted by supervisor'),
    (PROOF_DECLINED_SUP, 'Proofs declined by supervisor'),
    (PROOF_ACCEPTED, 'Proofs accepted by authors'),
    (PROOF_DECLINED, 'Proofs declined by authors'),
    (PROOF_RENEWED, 'Proofs renewed'),
)

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
    # ('assigned_to_supervisor', 'Assigned by EdAdmin to Supervisor'),
    # ('message_edadmin_to_supervisor', 'Message from EdAdmin to Supervisor'),
    # ('message_supervisor_to_edadmin', 'Message from Supervisor to EdAdmin'),
    # ('officer_tasked_with_proof_production', 'Supervisor tasked officer with proofs production'),
    # ('message_supervisor_to_officer', 'Message from Supervisor to Officer'),
    # ('message_officer_to_supervisor', 'Message from Officer to Supervisor'),
    # ('proofs_produced', 'Proofs have been produced'),
    # ('proofs_checked_by_supervisor', 'Proofs have been checked by Supervisor'),
    # ('proofs_sent_to_authors', 'Proofs sent to Authors'),
    # ('proofs_returned_by_authors', 'Proofs returned by Authors'),
    # ('corrections_implemented', 'Corrections implemented'),
    # ('authors_have_accepted_proofs', 'Authors have accepted proofs'),
    # ('paper_published', 'Paper has been published'),
    # ('cited_notified', 'Cited people have been notified/invited to SciPost'),
)

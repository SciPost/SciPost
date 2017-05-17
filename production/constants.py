

PRODUCTION_STREAM_STATUS = (
    ('ongoing', 'Ongoing'),
    ('completed', 'Completed'),
)


PRODUCTION_EVENTS = (
    ('assigned_to_supervisor', 'Assigned by EdAdmin to Supervisor'),
    ('message_edadmin_to_supervisor', 'Message from EdAdmin to Supervisor'),
    ('message_supervisor_to_edadmin', 'Message from Supervisor to EdAdmin'),
    ('officer_tasked_with_proof_production', 'Supervisor tasked officer with proofs production'),
    ('message_supervisor_to_officer', 'Message from Supervisor to Officer'),
    ('message_officer_to_supervisor', 'Message from Officer to Supervisor'),
    ('proofs_produced', 'Proofs have been produced'),
    ('proofs_sent_to_authors', 'Proofs sent to Authors'),
    ('proofs_returned_by_authors', 'Proofs returned by Authors'),
    ('corrections_implemented', 'Corrections implemented'),
    ('authors_have_accepted_proofs', 'Authors have accepted proofs'),
)

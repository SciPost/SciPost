import datetime


PARTNER_KIND_UNI_LIBRARY = 'Univ. Library'
PARTNER_KINDS = (
    ('Res. Inst.', 'Research Institute'),
    ('Int. Fund. Agency', 'International Funding Agency'),
    ('Nat. Fund. Agency', 'National Funding Agency'),
    ('Nat. Lab.', 'National Laboratory'),
    ('Nat. Library', 'National Library'),
    ('Nat. Acad.', 'National Academy'),
    (PARTNER_KIND_UNI_LIBRARY, 'University (and its Library)'),
    ('Res. Library', 'Research Library'),
    ('Prof. Soc.', 'Professional Society'),
    ('Foundation', 'Foundation'),
    ('Individual', 'Individual'),
)

PROSPECTIVE_PARTNER_REQUESTED = 'requested'
PROSPECTIVE_PARTNER_ADDED = 'added'
PROSPECTIVE_PARTNER_APPROACHED = 'approached'
PROSPECTIVE_PARTNER_NEGOTIATING = 'negotiating'
PROSPECTIVE_PARTNER_UNINTERESTED = 'uninterested'
PROSPECTIVE_PARTNER_PROCESSED = 'processed'
PROSPECTIVE_PARTNER_STATUS = (
    (PROSPECTIVE_PARTNER_REQUESTED, 'Requested (from online form)'),
    (PROSPECTIVE_PARTNER_ADDED, 'Added internally'),
    (PROSPECTIVE_PARTNER_APPROACHED, 'Approached'),
    (PROSPECTIVE_PARTNER_NEGOTIATING, 'Negotiating'),
    (PROSPECTIVE_PARTNER_UNINTERESTED, 'Uninterested'),
    (PROSPECTIVE_PARTNER_PROCESSED, 'Processed into Partner'),
)

PROSPECTIVE_PARTNER_EVENT_REQUESTED = 'requested'
PROSPECTIVE_PARTNER_EVENT_COMMENT = 'comment'
PROSPECTIVE_PARTNER_EVENT_EMAIL_SENT = 'email_sent'
PROSPECTIVE_PARTNER_EVENT_INITIATE_NEGOTIATION = 'negotiating'
PROSPECTIVE_PARTNER_EVENT_MARKED_AS_UNINTERESTED = 'marked_as_uninterested'
PROSPECTIVE_PARTNER_EVENT_PROMOTED = 'promoted'
PROSPECTIVE_PARTNER_EVENTS = (
    (PROSPECTIVE_PARTNER_EVENT_REQUESTED, 'Requested (from online form)'),
    (PROSPECTIVE_PARTNER_EVENT_COMMENT, 'Comment added'),
    (PROSPECTIVE_PARTNER_EVENT_EMAIL_SENT, 'Email sent'),
    (PROSPECTIVE_PARTNER_EVENT_INITIATE_NEGOTIATION, 'Initiated negotiation'),
    (PROSPECTIVE_PARTNER_EVENT_MARKED_AS_UNINTERESTED, 'Marked as uninterested'),
    (PROSPECTIVE_PARTNER_EVENT_PROMOTED, 'Promoted to Partner'),
)


PARTNER_STATUS = (
    ('Initiated', 'Initiated'),
    ('Contacted', 'Contacted'),
    ('Negotiating', 'Negotiating'),
    ('Uninterested', 'Uninterested'),
    ('Active', 'Active'),
    ('Inactive', 'Inactive'),
)


CONSORTIUM_STATUS = (
    ('Prospective', 'Prospective'),
    ('Active', 'Active'),
    ('Inactive', 'Inactive'),
)


PARTNER_EVENTS = (
    ('initial', 'Contacted (initial)'),
    ('status_update', 'Status updated'),
    ('comment', 'Comment added'),
)


CONTACT_TYPES = (
    ('tech', 'Technical Contact'),
    ('fin', 'Financial Contact'),
)


MEMBERSHIP_SUBMITTED = 'Submitted'
MEMBERSHIP_AGREEMENT_STATUS = (
    (MEMBERSHIP_SUBMITTED, 'Request submitted by Partner'),
    ('Pending', 'Sent to Partner, response pending'),
    ('Signed', 'Signed by Partner'),
    ('Honoured', 'Honoured: payment of Partner received'),
    ('Completed', 'Completed: agreement has been fulfilled'),
)

MEMBERSHIP_DURATION = (
    (datetime.timedelta(days=365), '1 year'),
    (datetime.timedelta(days=730), '2 years'),
    (datetime.timedelta(days=1095), '3 years'),
    (datetime.timedelta(days=1460), '4 years'),
    (datetime.timedelta(days=1825), '5 years'),
)

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
    ('Nat. Consor.', 'National Consortium'),
    ('Foundation', 'Foundation'),
    ('Individual', 'Individual'),
)

PROSPECTIVE_PARTNER_REQUESTED = 'requested'
PROSPECTIVE_PARTNER_ADDED = 'added'
PROSPECTIVE_PARTNER_APPROACHED = 'approached'
PROSPECTIVE_PARTNER_FOLLOWED_UP = 'followuped'
PROSPECTIVE_PARTNER_NEGOTIATING = 'negotiating'
PROSPECTIVE_PARTNER_UNINTERESTED = 'uninterested'
PROSPECTIVE_PARTNER_PROCESSED = 'processed'
PROSPECTIVE_PARTNER_STATUS = (
    (PROSPECTIVE_PARTNER_REQUESTED, 'Requested (from online form)'),
    (PROSPECTIVE_PARTNER_ADDED, 'Added internally'),
    (PROSPECTIVE_PARTNER_APPROACHED, 'Approached'),
    (PROSPECTIVE_PARTNER_FOLLOWED_UP, 'Followed-up'),
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


PARTNER_INITIATED = 'Initiated'
PARTNER_STATUS = (
    (PARTNER_INITIATED, 'Initiated'),
    ('Contacted', 'Contacted'),
    ('Negotiating', 'Negotiating'),
    ('Uninterested', 'Uninterested'),
    ('Active', 'Active'),
    ('Inactive', 'Inactive'),
)

REQUEST_INITIATED = 'init'
REQUEST_PROCESSED = 'proc'
REQUEST_DECLINED = 'decl'
REQUEST_STATUSES = (
    (REQUEST_INITIATED, 'Request submitted by Contact'),
    (REQUEST_PROCESSED, 'Processed'),
    (REQUEST_DECLINED, 'Declined'),
)


CONSORTIUM_STATUS = (
    ('Prospective', 'Prospective'),
    ('Active', 'Active'),
    ('Inactive', 'Inactive'),
)

PARTNER_STATUS_UPDATE = 'status_update'
PARTNER_EVENTS = (
    ('initial', 'Contacted (initial)'),
    (PARTNER_STATUS_UPDATE, 'Status updated'),
    ('comment', 'Comment added'),
)

CONTACT_GENERAL = 'gen'
CONTACT_TYPES = (
    (CONTACT_GENERAL, 'General Contact'),
    ('tech', 'Technical Contact'),
    ('fin', 'Financial Contact'),
    ('leg', 'Legal Contact')
)


MEMBERSHIP_SUBMITTED = 'Submitted'
MEMBERSHIP_SIGNED = 'Signed'
MEMBERSHIP_HONOURED = 'Honoured'
MEMBERSHIP_COMPLETED = 'Completed'
MEMBERSHIP_AGREEMENT_STATUS = (
    (MEMBERSHIP_SUBMITTED, 'Request submitted by Partner'),
    ('Pending', 'Sent to Partner, response pending'),
    (MEMBERSHIP_SIGNED, 'Signed by Partner'),
    (MEMBERSHIP_HONOURED, 'Honoured: payment of Partner received'),
    (MEMBERSHIP_COMPLETED, 'Completed: agreement has been fulfilled'),
)

MEMBERSHIP_DURATION = (
    (datetime.timedelta(days=365), '1 year'),
    (datetime.timedelta(days=730), '2 years'),
    (datetime.timedelta(days=1095), '3 years'),
    (datetime.timedelta(days=1460), '4 years'),
    (datetime.timedelta(days=1825), '5 years'),
)

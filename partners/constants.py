import datetime


PARTNER_KINDS = (
    ('Res. Inst.', 'Research Institute'),
    ('Int. Fund. Agency', 'International Funding Agency'),
    ('Nat. Fund. Agency', 'National Funding Agency'),
    ('Nat. Lab.', 'National Laboratory'),
    ('Nat. Library', 'National Library'),
    ('Nat. Acad.', 'National Academy'),
    ('Univ. Library', 'University (and its Library)'),
    ('Res. Library', 'Research Library'),
    ('Prof. Soc.', 'Professional Society'),
    ('Foundation', 'Foundation'),
    ('Individual', 'Individual'),
)


PROSPECTIVE_PARTNER_STATUS = (
    ('requested', 'Requested (from online form)'),
    ('added', 'Added internally'),
    ('processed', 'Processed into Partner object'),
)

PROSPECTIVE_PARTNER_EVENTS = (
    ('comment', 'Comment added'),
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


MEMBERSHIP_AGREEMENT_STATUS = (
    ('Submitted', 'Request submitted by Partner'),
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

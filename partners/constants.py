import datetime


PARTNER_TYPES = (
    ('Int. Fund. Agency', 'International Funding Agency'),
    ('Nat. Fund. Agency', 'National Funding Agency'),
    ('Nat. Library', 'National Library'),
    ('Univ. Library', 'University Library'),
    ('Res. Library', 'Research Library'),
    ('Foundation', 'Foundation'),
    ('Individual', 'Individual'),
)

PARTNER_STATUS = (
    ('Prospective', 'Prospective'),
    ('Negotiating', 'Negotiating'),
    ('Active', 'Active'),
    ('Inactive', 'Inactive'),
)


CONSORTIUM_STATUS = (
    ('Prospective', 'Prospective'),
    ('Active', 'Active'),
    ('Inactive', 'Inactive'),
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

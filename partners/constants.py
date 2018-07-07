__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

ORGTYPE_RESEARCH_INSTITUTE = 'ResearchRnstitute'
ORGTYPE_INTERNATIONAL_FUNDING_AGENCY = 'InternationalFundingAgency'
ORGTYPE_NATIONAL_FUNDING_AGENCY = 'NationalFundingAgency'
ORGTYPE_NATIONAL_LABORATORY = 'NationalLaboratory'
ORGTYPE_NATIONAL_LIBRARY = 'NationalLibrary'
ORGTYPE_NATIONAL_ACADEMY = 'NationalAcademy'
ORGTYPE_UNIVERSITY_LIBRARY = 'UniversityLibrary'
ORGTYPE_RESEARCH_LIBRARY = 'ResearchLibrary'
ORGTYPE_PROFESSIONAL_SOCIETY = 'ProfessionalSociety'
ORGTYPE_INTERNATIONAL_CONSORTIUM = 'InternationalConsortium'
ORGTYPE_NATIONAL_CONSORTIUM = 'NationalConsortium'
ORGTYPE_FOUNDATION = 'Foundation'
ORGTYPE_GOVERNMENTAL_MINISTRY = 'GovernmentalMinistry'
ORGTYPE_GOVERNMENTAL_OFFICE = 'GovernmentalOffice'
ORGTYPE_BUSINESS_CORPORATION = 'BusinessCorporation'
ORGTYPE_INDIVIDUAL_BENEFACTOR = 'IndividualBenefactor'
ORGTYPE_PRIVATE_BENEFACTOR = 'PrivateBenefactor'

ORGANIZATION_TYPES = (
    (ORGTYPE_RESEARCH_INSTITUTE, 'Research Institute'),
    (ORGTYPE_INTERNATIONAL_FUNDING_AGENCY, 'International Funding Agency'),
    (ORGTYPE_NATIONAL_FUNDING_AGENCY, 'Funding Agency'),
    (ORGTYPE_NATIONAL_LABORATORY, 'National Laboratory'),
    (ORGTYPE_NATIONAL_LIBRARY, 'National Library'),
    (ORGTYPE_NATIONAL_ACADEMY, 'National Academy'),
    (ORGTYPE_UNIVERSITY_LIBRARY, 'University (and its Library)'),
    (ORGTYPE_RESEARCH_LIBRARY, 'Research Library'),
    (ORGTYPE_PROFESSIONAL_SOCIETY, 'Professional Society'),
    (ORGTYPE_INTERNATIONAL_CONSORTIUM, 'International Consortium'),
    (ORGTYPE_NATIONAL_CONSORTIUM, 'National Consortium'),
    (ORGTYPE_FOUNDATION, 'Foundation'),
    (ORGTYPE_GOVERNMENTAL_MINISTRY, 'Governmental Ministry'),
    (ORGTYPE_GOVERNMENTAL_OFFICE, 'Governmental Office'),
    (ORGTYPE_BUSINESS_CORPORATION, 'Business Corporation'),
    (ORGTYPE_INDIVIDUAL_BENEFACTOR, 'Individual Benefactor'),
    (ORGTYPE_PRIVATE_BENEFACTOR, 'Private Benefactor'),
)

ORGSTATUS_ACTIVE = 'Active'
ORGSTATUS_SUPERSEDED = 'Superseded'
ORGSTATUS_OBSOLETE = 'Obsolete'

ORGANIZATION_STATUSES = (
    (ORGSTATUS_ACTIVE, 'Active'),
    (ORGSTATUS_SUPERSEDED, 'Superseded'),
    (ORGSTATUS_OBSOLETE, 'Obsolete'),
)



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

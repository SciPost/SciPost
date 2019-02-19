__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

ORGTYPE_RESEARCH_INSTITUTE = 'ResearchRnstitute'
ORGTYPE_INTERNATIONAL_FUNDING_AGENCY = 'InternationalFundingAgency'
ORGTYPE_NATIONAL_FUNDING_AGENCY = 'NationalFundingAgency'
ORGTYPE_FUNDING_AGENCY_INITIATIVE = 'FundingAgencyInitiative'
ORGTYPE_NATIONAL_LABORATORY = 'NationalLaboratory'
ORGTYPE_NATIONAL_LIBRARY = 'NationalLibrary'
ORGTYPE_NATIONAL_ACADEMY = 'NationalAcademy'
ORGTYPE_UNIVERSITY_LIBRARY = 'UniversityLibrary'
ORGTYPE_RESEARCH_LIBRARY = 'ResearchLibrary'
ORGTYPE_PROFESSIONAL_SOCIETY = 'ProfessionalSociety'
ORGTYPE_INTERNATIONAL_CONSORTIUM = 'InternationalConsortium'
ORGTYPE_NATIONAL_CONSORTIUM = 'NationalConsortium'
ORGTYPE_FOUNDATION = 'Foundation'
ORGTYPE_GOVERNMENT_INTERNATIONAL = 'GovernmentInternational'
ORGTYPE_GOVERNMENT_NATIONAL = 'GovernmentNational'
ORGTYPE_GOVERNMENT_PROVINCIAL = 'GovernmentProvincial'
ORGTYPE_GOVERNMENT_REGIONAL = 'GovernmentRegional'
ORGTYPE_GOVERNMENT_MUNICIPAL = 'GovernmentMunicipal'
ORGTYPE_GOVERNMENTAL_MINISTRY = 'GovernmentalMinistry'
ORGTYPE_GOVERNMENTAL_OFFICE = 'GovernmentalOffice'
ORGTYPE_BUSINESS_CORPORATION = 'BusinessCorporation'
ORGTYPE_INDIVIDUAL_BENEFACTOR = 'IndividualBenefactor'
ORGTYPE_PRIVATE_BENEFACTOR = 'PrivateBenefactor'

ORGANIZATION_TYPES = (
    (ORGTYPE_RESEARCH_INSTITUTE, 'Research Institute'),
    (ORGTYPE_INTERNATIONAL_FUNDING_AGENCY, 'International Funding Agency'),
    (ORGTYPE_NATIONAL_FUNDING_AGENCY, 'National Funding Agency'),
    (ORGTYPE_FUNDING_AGENCY_INITIATIVE, 'Funding Agency Initiative'),
    (ORGTYPE_NATIONAL_LABORATORY, 'National Laboratory'),
    (ORGTYPE_NATIONAL_LIBRARY, 'National Library'),
    (ORGTYPE_NATIONAL_ACADEMY, 'National Academy'),
    (ORGTYPE_UNIVERSITY_LIBRARY, 'University (and its Library)'),
    (ORGTYPE_RESEARCH_LIBRARY, 'Research Library'),
    (ORGTYPE_PROFESSIONAL_SOCIETY, 'Professional Society'),
    (ORGTYPE_INTERNATIONAL_CONSORTIUM, 'International Consortium'),
    (ORGTYPE_NATIONAL_CONSORTIUM, 'National Consortium'),
    (ORGTYPE_FOUNDATION, 'Foundation'),
    (ORGTYPE_GOVERNMENT_INTERNATIONAL, 'Government (international)'),
    (ORGTYPE_GOVERNMENT_NATIONAL, 'Government (national)'),
    (ORGTYPE_GOVERNMENT_PROVINCIAL, 'Government (provincial)'),
    (ORGTYPE_GOVERNMENT_REGIONAL, 'Government (regional)'),
    (ORGTYPE_GOVERNMENT_MUNICIPAL, 'Government (municipal)'),
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


ORGANIZATION_EVENT_REQUESTED = 'requested'
ORGANIZATION_EVENT_COMMENT = 'comment'
ORGANIZATION_EVENT_EMAIL_SENT = 'email_sent'
ORGANIZATION_EVENT_INITIATE_NEGOTIATION = 'negotiating'
ORGANIZATION_EVENT_MARKED_AS_UNINTERESTED = 'marked_as_uninterested'
ORGANIZATION_EVENT_PROMOTED = 'promoted'
ORGANIZATION_STATUS_UPDATED = 'status_updated'
ORGANIZATION_EVENTS = (
    (ORGANIZATION_EVENT_REQUESTED, 'Requested (from online form)'),
    (ORGANIZATION_EVENT_COMMENT, 'Comment added'),
    (ORGANIZATION_EVENT_EMAIL_SENT, 'Email sent'),
    (ORGANIZATION_EVENT_INITIATE_NEGOTIATION, 'Initiated negotiation'),
    (ORGANIZATION_EVENT_MARKED_AS_UNINTERESTED, 'Marked as uninterested'),
    (ORGANIZATION_EVENT_PROMOTED, 'Promoted to Sponsor'),
    (ORGANIZATION_STATUS_UPDATED, 'Status updated'),
)

ROLE_GENERAL = 'gen'
ROLE_TECH = 'tech'
ROLE_FIN = 'fin'
ROLE_LEG = 'leg'
ROLE_KINDS = (
    (ROLE_GENERAL, 'General Contact'),
    (ROLE_TECH, 'Technical Contact'),
    (ROLE_FIN, 'Financial Contact'),
    (ROLE_LEG, 'Legal Contact')
)

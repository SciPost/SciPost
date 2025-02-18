__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


# Preprint-related regexes
scipost_regex_wo_vn = "scipost_[0-9]{4,}_[0-9]{4,}"
scipost_regex_w_vn = "scipost_[0-9]{4,}_[0-9]{4,}v[0-9]{1,2}"
arxiv_regex_wo_vn = "[0-9]{4,}.[0-9]{4,}"
arxiv_regex_w_vn = "[0-9]{4,}.[0-9]{4,}v[0-9]{1,2}"
# pre-2021-07 ChemRxiv: to be removed/deprecated
chemrxiv_regex_wo_vn = "chemrxiv_[0-9]+"
chemrxiv_regex_w_vn = "chemrxiv_[0-9]+.v[0-9]{1,2}"
# post-2021-07 ChemRxiv: fits both 10.####(#)/chemrxiv.#####(.v#)? and 10.####(#)/chemrxiv-YYYY-****(-v#)?
CHEMRXIV_DOI_PATTERN = "10.[0-9]{4,5}/chemrxiv([.-][0-9]{4,})?[.-][\w]+([.-]v[0-9]+)?"
techrxiv_regex_wo_vn = "techrxiv_[0-9]+"
techrxiv_regex_w_vn = "techrxiv_[0-9]+.v[0-9]{1,2}"
advance_regex_wo_vn = "advance_[0-9]+"
advance_regex_w_vn = "advance_[0-9]+.v[0-9]{1,2}"
socarxiv_regex = r"socarxiv_[a-z0-9]+(_v\d{1,2})?"

# Preprints with structurally no version number
# (like OSFPreprints-based ones: SocArXiv, ...)
# must not match IDENTIFIER_REGEX to avoid ambiguities.
IDENTIFIER_WO_VN_NR_REGEX = "|".join(
    [
        scipost_regex_wo_vn,
        arxiv_regex_wo_vn,
        chemrxiv_regex_wo_vn,
        techrxiv_regex_wo_vn,
        advance_regex_wo_vn,
    ]
)

IDENTIFIER_REGEX = "|".join(
    [
        scipost_regex_w_vn,
        arxiv_regex_w_vn,
        chemrxiv_regex_w_vn,
        CHEMRXIV_DOI_PATTERN,
        techrxiv_regex_w_vn,
        advance_regex_w_vn,
        socarxiv_regex,
    ]
)

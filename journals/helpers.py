__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re

from .exceptions import JournalNameError, PaperNumberError


def issue_doi_label_from_doi_label(doi_label):
    """
    Strip the last digits block from the label.
    """
    m = re.match(r'[a-zA-Z]+.[0-9]+.[0-9]+', doi_label)
    s = m.start()
    e = m.end()
    return doi_label[s:e]


def journal_name_abbrev_citation(journal_name):
    if journal_name == 'SciPostPhys':
        return 'SciPost Phys.'
    elif journal_name == 'SciPostPhysSel':
        return 'SciPost Phys. Sel.'
    elif journal_name == 'SciPostPhysLectNotes':
        return 'SciPost Phys. Lect. Notes'
    elif journal_name == 'SciPostPhysProc':
        return 'SciPost Phys. Proc.'
    else:
        raise JournalNameError(journal_name)


def paper_nr_string(nr):
    if nr < 10:
        return '00' + str(nr)
    elif nr < 100:
        return '0' + str(nr)
    elif nr < 1000:
        return str(nr)
    else:
        raise PaperNumberError(nr)

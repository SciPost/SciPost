from .exceptions import JournalNameError, PaperNumberError


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

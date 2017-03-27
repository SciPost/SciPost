from .exceptions import JournalNameError, PaperNumberError


def journal_name_abbrev_citation(journal_name):
    if journal_name == 'SciPost Physics':
        return 'SciPost Phys.'
    elif journal_name == 'SciPost Physics Select':
        return 'SciPost Phys. Sel.'
    elif journal_name == 'SciPost Physics Lecture Notes':
        return 'SciPost Phys. Lect. Notes'
    else:
        raise JournalNameError(journal_name)


def journal_name_abbrev_doi(journal_name):
    if journal_name == 'SciPost Physics':
        return 'SciPostPhys'
    elif journal_name == 'SciPost Physics Select':
        return 'SciPostPhysSel'
    elif journal_name == 'SciPost Physics Lecture Notes':
        return 'SciPostPhysLectNotes'
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

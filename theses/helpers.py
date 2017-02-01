import datetime


def past_years(n):
    '''
    Gives back list of integers representing a range of n years, counting down from current year.
    '''
    this_year = datetime.datetime.now().year
    return range(this_year, this_year - n, -1)

from .forms import SearchForm


def searchform(request):
    return {'search_form': SearchForm()}

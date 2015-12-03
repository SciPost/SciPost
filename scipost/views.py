import datetime
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.db.models import Avg

from .models import *
from .forms import *


#############
# Main view
#############

def index(request):
    return render(request, 'scipost/index.html')


###############
# Information
###############

def about(request):
    return render(request, 'scipost/about.html')

def description(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="SciPost_Description.pdf"'
    return response
#    return HttpResponse("scipost/SciPost_Description.pdf", content_type="application/pdf")

def peer_witnessed_refereeing(request):
    return render(request, 'scipost/peer_witnessed_refereeing.html')




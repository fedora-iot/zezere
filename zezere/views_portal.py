from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from zezere.models import Device


@login_required
def index(request):
    return render(
        request,
        'portal/index.html',
    )


@login_required
def claim(request):
    if request.method == "POST":
        return HttpResponse("POST response")

    context = {
        "unclaimed_devices": Device.objects.filter(owner__isnull=True),
    }
    return render(
        request,
        'portal/claim.html',
        context,
    )

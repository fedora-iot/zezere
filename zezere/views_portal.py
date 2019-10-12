from django.contrib.auth.models import User, Group
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
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
        with transaction.atomic():
            device = get_object_or_404(
                Device,
                mac_address=request.POST['mac_address'],
                owner__isnull=True,
            )
            device.owner = request.user
            device.save()
        return redirect("/portal/claim/")

    context = {
        "unclaimed_devices": Device.objects.filter(owner__isnull=True),
    }
    return render(
        request,
        'portal/claim.html',
        context,
    )

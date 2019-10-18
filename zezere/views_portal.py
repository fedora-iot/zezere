from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from rules.contrib.views import permission_required

from zezere.models import Device, RunRequest, device_getter


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
            if not request.user.has_perm(Device.get_perm("claim"), device):
                raise Exception("Not allowed to claim")

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


@login_required
def devices(request):
    devices = Device.objects.filter(owner=request.user)
    return render(
        request,
        'portal/devices.html',
        {
            'devices': devices,
        },
    )


@permission_required(Device.get_perm("provision"), fn=device_getter)
def new_runreq(request, mac_addr):
    device = get_object_or_404(Device, mac_address=mac_addr.upper())

    if request.method == "POST":
        rrid = request.POST["runrequest"]
        runreq = get_object_or_404(RunRequest, id=rrid)
        device.run_request = runreq
        device.full_clean()
        device.save()
        return redirect("portal_devices")

    runreqs = RunRequest.objects.filter(auto_generated_id__isnull=False)

    return render(
        request,
        'portal/runreq.html',
        {
            'device': device,
            'runreqs': runreqs,
        },
    )


@permission_required(Device.get_perm("provision"), fn=device_getter)
def clean_runreq(request, mac_addr):
    device = get_object_or_404(Device, mac_address=mac_addr.upper())

    if request.method != "POST":
        raise Exception("Invalid request method")

    if device.run_request is None:
        raise Exception("Device did not have runrequest")

    device.run_request = None
    device.full_clean()
    device.save()
    return redirect("portal_devices")

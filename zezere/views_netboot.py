import logging
import os

from django.http import (
    FileResponse,
    HttpResponse,
    HttpResponseNotFound,
)
from django.shortcuts import render, get_object_or_404

from ipware import get_client_ip

from .models import Device


ARCHES = {
    "x86_64": {
        "initial": "shimx64.efi",
        "grubx64.efi": "grubx64.efi",
    }
}


def index(request):
    context = {
        'service_url': request.build_absolute_uri('/netboot'),
        'arches': ARCHES.keys(),
    }
    return render(
        request,
        "netboot/index.html",
        context,
    )


def arch_file(request, arch, filetype):
    archfiles = ARCHES.get(arch)
    if not archfiles:
        return HttpResponseNotFound("Architecture not found")
    filename = archfiles.get(filetype)
    if not filename:
        return HttpResponseNotFound("File not found for architecture")
    app_root = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(app_root, "efi_binaries", arch, filename)
    return FileResponse(open(path, 'rb'), content_type="application/efi")


def static_grub_cfg(request, arch):
    return HttpResponse(
        'configfile "/netboot/grubcfg/${net_default_mac}"',
        content_type="text/plain",
    )


def static_proxy(request, mac_addr, filetype):
    device = get_object_or_404(Device, mac_address=mac_addr.upper())
    return HttpResponse(
        'Returning file "%s" for mac addr "%s": %s' %
        (filetype, mac_addr, device),
        content_type="application/octet-stream",
    )


def dynamic_grub_cfg(request, arch, mac_addr):
    context = {
        'service_url': request.build_absolute_uri('/'),
    }

    try:
        remote_ip, _ = get_client_ip(request)

        try:
            device = Device.objects.get(
                mac_address=mac_addr.upper(),
                architecture=arch,
            )
            if device.last_ip_address != remote_ip:
                device.last_ip_address = remote_ip
                device.save()
        except Device.DoesNotExist:
            # Create new Device
            device = Device(
                mac_address=mac_addr.upper(),
                architecture=arch,
                last_ip_address=remote_ip,
            )
            device.full_clean()
            device.save()
        context['device'] = device
        return render(
            request,
            'netboot/grubcfg',
            context,
            content_type='text/plain',
        )

    except Exception:
        logging.getLogger(__name__).error(
            "Error generating grubcfg for '%s', serving fallback: ",
            mac_addr,
            exc_info=True,
        )
        return render(
            request,
            'netboot/grubcfg_fallback',
            context,
            content_type='text/plain',
        )


def kickstart(request, mac_addr):
    device = get_object_or_404(Device, mac_address=mac_addr.upper())
    return HttpResponse(
        'Returning kickstart for "%s": %s' % (mac_addr, device),
        content_type="text/plain",
    )


def ignition_cfg(request, mac_addr):
    device = get_object_or_404(Device, mac_address=mac_addr.upper())
    return HttpResponse(
        'Returning ignitioncfg for "%s": %s' % (mac_addr, device),
        content_type="text/plain",
    )

import logging
import os

from django.http import (
    FileResponse,
    HttpResponse,
    HttpResponseNotFound,
    StreamingHttpResponse,
)
from django.shortcuts import get_object_or_404
from django.template import loader
import requests

from ipware import get_client_ip

from .models import Device, RunRequest
from .runreqs import replace_device_strings


ARCHES = {
    "x86_64": {
        "initial": "shimx64.efi",
        "grubx64.efi": "grubx64.efi",
    },
    "aarch64": {
        "initial": "BOOTAA64.EFI",
    },
}


def render_for_device(device, request, template_name, context=None,
                      content_type=None, status=None, using=None):
    content = loader.render_to_string(
        template_name,
        context,
        request, using=using,
    )

    # Make replacements
    content = content.replace(
        ":urls.base:",
        request.build_absolute_uri("/"),
    )
    if device:
        content = content.replace(
            ":urls.kickstart:",
            request.build_absolute_uri(
                f'/netboot/kickstart/{device.mac_address}'),
        )
        content = content.replace(
            ":arch:",
            device.architecture,
        )
        content = content.replace(
            ":mac_addr:",
            device.mac_address,
        )

    return HttpResponse(content, content_type, status)


def index(request):
    context = {
        'service_url': request.build_absolute_uri('/netboot'),
        'arches': ARCHES.keys(),
    }
    return render_for_device(
        None,
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
        'configfile "${http_path}/grubcfg/${net_default_mac}"',
        content_type="text/plain",
    )


def static_proxy(request, arch, mac_addr, filetype):
    device = get_object_or_404(Device, mac_address=mac_addr.upper())

    if device.run_request is None:
        raise Exception("No run request for device")
    elif device.run_request.type == RunRequest.TYPE_EFI:
        raise Exception("Invalid runreq type for proxydl")

    dlurl = None
    if filetype == "kernel":
        dlurl = device.run_request.kernel_url
    elif filetype == "initrd":
        dlurl = device.run_request.initrd_url

    if not dlurl:
        raise Exception("Invalid filetype")

    dlurl = replace_device_strings(request, dlurl, device)

    resp = requests.get(dlurl, stream=True)
    resp.raise_for_status()

    ourresp = StreamingHttpResponse(
        resp.iter_content(chunk_size=8192),
        content_type='application/octet-stream',
    )
    ourresp['Content-Length'] = resp.headers['Content-Length']
    return ourresp


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
        return render_for_device(
            device,
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
        return render_for_device(
            device,
            request,
            'netboot/grubcfg_fallback',
            context,
            content_type='text/plain',
        )


def kickstart(request, mac_addr):
    device = get_object_or_404(Device, mac_address=mac_addr.upper())
    context = {
        "device": device,
    }
    return render_for_device(
        device,
        request,
        'netboot/kickstart',
        context,
        content_type='text/plain',
    )


def ignition_cfg(request, mac_addr):
    device = get_object_or_404(Device, mac_address=mac_addr.upper())
    context = {
        "device": device,
    }
    return render_for_device(
        device,
        request,
        'netboot/ignition_cfg',
        context,
        content_type='text/plain',
    )


def postboot(request, mac_addr):
    device = get_object_or_404(Device, mac_address=mac_addr.upper())
    if not device.run_request:
        raise ValueError("Device has no run request")
    if 'next' not in device.run_request.settings:
        raise ValueError("Current runrequest does not have a next state")

    nextrunreq = get_object_or_404(
        RunRequest,
        auto_generated_id=device.run_request.settings['next'],
    )
    device.run_request = nextrunreq
    device.save()
    return HttpResponse("Set device %s to %s" % (device, nextrunreq))

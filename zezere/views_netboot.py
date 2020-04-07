from typing import Dict, Any

import logging
import os

from django.http import (
    HttpRequest,
    JsonResponse,
    FileResponse,
    HttpResponse,
    Http404,
    StreamingHttpResponse,
)
from django.shortcuts import get_object_or_404
from django.template import loader
import requests

from ipware import get_client_ip

from .models import Device, RunRequest
from .runreqs import replace_device_strings


ARCHES = {
    "x86_64": {"initial": "shimx64.efi", "grubx64.efi": "grubx64.efi"},
    "aarch64": {"initial": "BOOTAA64.EFI"},
}


def render_for_device(
    device: Device,
    request: HttpRequest,
    template_name: str,
    context: Dict[str, Any] = None,
    content_type: str = None,
    status: int = None,
) -> HttpResponse:

    content = loader.render_to_string(template_name, context, request)

    # Make replacements
    content = content.replace(":urls.base:", request.build_absolute_uri("/"))
    if device:
        content = content.replace(
            ":urls.kickstart:",
            request.build_absolute_uri(f"/netboot/kickstart/{device.mac_address}"),
        )
        content = content.replace(":arch:", device.architecture)
        content = content.replace(":mac_addr:", device.mac_address)

    return HttpResponse(content, content_type, status)


def index(request):
    context = {
        "service_url": request.build_absolute_uri("/netboot"),
        "arches": ARCHES.keys(),
    }
    return render_for_device(None, request, "netboot/index.html", context)


def arch_file(request, arch, filetype, flags=None):
    archfiles = ARCHES.get(arch)
    if not archfiles:
        raise Http404("Architecture not found")
    filename = archfiles.get(filetype)
    if not filename:
        raise Http404("File not found for architecture")
    app_root = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(app_root, "efi_binaries", arch, filename)
    if request.method == "HEAD":
        resp = HttpResponse(b"", content_type="application/efi")
        resp["Content-Length"] = os.path.getsize(path)
        return resp
    return FileResponse(open(path, "rb"), content_type="application/efi")


def static_grub_cfg(request, arch, flags=None):
    if flags:
        flags = flags.split("+")
    else:
        flags = []

    contents = 'configfile "${http_path}/grubcfg/${net_default_mac}"'
    if "debug" in flags:
        contents += "\nset debug=all"
    content_len = len(contents)
    if request.method == "HEAD":
        contents = b""

    resp = HttpResponse(contents, content_type="text/plain",)
    resp["Content-Length"] = content_len
    return resp


def get_or_create_device(request, arch, mac_addr):
    remote_ip, _ = get_client_ip(request)

    try:
        device = Device.objects.get(mac_address=mac_addr.upper(), architecture=arch)
        if device.last_ip_address != remote_ip:
            device.last_ip_address = remote_ip
            device.save()
    except Device.DoesNotExist:
        # Create new Device
        device = Device(
            mac_address=mac_addr.upper(), architecture=arch, last_ip_address=remote_ip,
        )
        device.full_clean()
        device.save()

    return device


def dynamic_grub_cfg(request, arch, mac_addr, flags=None):
    if flags:
        flags = flags.split("+")
    else:
        flags = []
    context = {
        "service_url": request.build_absolute_uri("/"),
        "flags": flags,
    }

    try:
        device = get_or_create_device(request, arch, mac_addr)

        context["device"] = device
        return render_for_device(
            device, request, "netboot/grubcfg", context, content_type="text/plain"
        )

    except Exception:
        logging.getLogger(__name__).error(
            "Error generating grubcfg for '%s', serving fallback: ",
            mac_addr,
            exc_info=True,
        )
        return render_for_device(
            None,
            request,
            "netboot/grubcfg_fallback",
            context,
            content_type="text/plain",
        )


def kickstart(request, mac_addr):
    device = get_object_or_404(Device, mac_address=mac_addr.upper())
    context = {"device": device}

    if device.run_request is None:
        raise Http404()
    elif device.run_request.type == RunRequest.TYPE_EFI:
        raise Http404()

    return render_for_device(
        device, request, "netboot/kickstart", context, content_type="text/plain"
    )


def ignition_cfg(request, arch, mac_addr):
    device = get_or_create_device(request, arch, mac_addr)

    if device.run_request is None:
        raise Http404()

    return JsonResponse(device.get_ignition_config(request).generate_config())


def postboot(request, mac_addr):
    device = get_object_or_404(Device, mac_address=mac_addr.upper())
    if not device.run_request:
        raise Http404()
    if "next" not in device.run_request.settings:
        raise Http404()

    nextrunreq = get_object_or_404(
        RunRequest, auto_generated_id=device.run_request.settings["next"]
    )
    device.run_request = nextrunreq
    device.save()
    return HttpResponse("Set device %s to %s" % (device, nextrunreq))

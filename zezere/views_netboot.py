import logging
import os

from django.http import FileResponse, HttpResponse
from django.template import loader
from django.shortcuts import render, get_object_or_404

from ipware import get_client_ip

from .models import Device

def efi_static_server(filename):
    app_root = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(app_root, "efi_binaries", filename)

    def perform(request):
        return FileResponse(open(path, 'rb'), content_type="application/efi")

    return perform

def static_grub_cfg(request):
    return HttpResponse('configfile "/netboot/grubcfg/${net_default_mac}"', content_type="text/plain")

def static_proxy(request, mac_addr, filetype):
    device = get_object_or_404(Device, mac_address=mac_addr.upper())
    return HttpResponse('Returning file "%s" for mac addr "%s"' % (filetype, mac_addr))

def dynamic_grub_cfg(request, mac_addr):
    context = {
        'service_url': request.build_absolute_uri('/'),
    }

    try:
        remote_ip, _ = get_client_ip(request)

        try:
            device = Device.objects.get(mac_address=mac_addr.upper())
            if device.last_ip_address != remote_ip:
                device.last_ip_address = remote_ip
                device.save()
        except Device.DoesNotExist:
            # Create new Device
            device = Device(
                mac_address=mac_addr.upper(),
                last_ip_address=remote_ip,
            )
            device.full_clean()
            device.save()
        context['device'] = device
        return render(request, 'grubcfg', context, content_type='text/plain')

    except:
        logging.getLogger(__name__).error("Error generating grubcfg for '%s', serving fallback: ", mac_addr, exc_info=True)
        return render(request, 'grubcfg_fallback', context, content_type='text/plain')

def kickstart(request, mac_addr):
    device = get_object_or_404(Device, mac_address=mac_addr.upper())
    return HttpResponse('Returning kickstart for "%s"' % mac_addr, content_type="text/plain")

def ignition_cfg(request, mac_addr):
    device = get_object_or_404(Device, mac_address=mac_addr.upper())
    return HttpResponse('Returning ignitioncfg for "%s"' % mac_addr, content_type="text/plain")
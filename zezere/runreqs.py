from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from . import models


KOJI_ROOT = "https://kojipkgs.fedoraproject.org/compose"

AUTO_RUNREQS = {
    "fedora-iot-stable": {
        "type": "ok",
        "next": "fedora-installed",
        "compose_root": f"{KOJI_ROOT}/iot/latest-Fedora-IoT-31",
        "compose_name": "IoT",
        "clear_parts": True,
        "install_type": "ostree",
        "ostree": {
            "osname": "fedora-iot-stable",
            "remote": "fedora-iot",
            "repo": "https://kojipkgs.fedoraproject.org/compose/iot/repo/",
            "ref": "fedora/stable/:arch:/iot",
        },
    },
    "fedora-iot-rawhide": {
        "type": "ok",
        "next": "fedora-installed",
        "compose_root": f"{KOJI_ROOT}/iot/latest-Fedora-IoT-32",
        "compose_name": "IoT",
        "clear_parts": True,
        "install_type": "ostree",
        "ostree": {
            "osname": "fedora-iot-rawhide",
            "remote": "fedora-iot",
            "repo": "https://kojipkgs.fedoraproject.org/compose/iot/repo/",
            "ref": "fedora/rawhide/:arch:/iot",
        },
    },
    "fedora-installed": {"type": "ef", "efi_path": "/EFI/fedora/grubx64.efi"},
}


def validate_runreq_autoid(autoid):
    if autoid not in AUTO_RUNREQS.keys():
        raise ValidationError(
            _("%(value)s is not a valid runreq autoid"), params={"value": autoid}
        )


def generate_auto_runreq(sender, instance, **kwargs):
    if not instance.auto_generated_id:
        # Nothing to auto-generate
        return
    info = AUTO_RUNREQS[instance.auto_generated_id]
    instance.type = info["type"]

    if "compose_root" in info:
        compose_url = f"{info['compose_root']}/compose/{info['compose_name']}/:arch:/os"
        instance.kernel_url = f"{compose_url}/isolinux/vmlinuz"
        instance.kernel_cmd = " ".join(
            [
                f"inst.repo={compose_url}",
                "inst.ks=:urls.kickstart:",
                "inst.ks.sendmac",
                "noshell",
                "inst.cmdline",
                "inst.sshd=0",
                "ip=dhcp",
            ]
        )
        instance.initrd_url = f"{compose_url}/isolinux/initrd.img"

    settings = {"clear_parts": info.get("clear_parts"), "raw": info}

    if "next" in info:
        settings["next"] = info["next"]

    if info.get("install_type") == "ostree":
        settings["type"] = "ostree"
        settings["ostree"] = info["ostree"]

    if info["type"] == models.RunRequest.TYPE_EFI:
        settings["efi_path"] = info["efi_path"]

    instance._settings = settings


def replace_device_strings(request, value, device):
    value = value.replace(
        ":urls.kickstart:",
        request.build_absolute_uri(f"/netboot/kickstart/{device.mac_address}"),
    )
    value = value.replace(":arch:", device.architecture)
    value = value.replace(":mac_addr:", device.mac_address)

    return value


def generate_runreq_grubcfg(request, device, runreq):
    if runreq.type == models.RunRequest.TYPE_ONLINE_KERNEL:
        proxy_kernel_url = "static/netboot/:arch:/vmlinuz"
        proxy_initrd_url = "static/netboot/:arch:/initrd"

        return f"""
linux {proxy_kernel_url} {runreq.kernel_cmd}
initrd {proxy_initrd_url}
boot
        """

    elif runreq.type == models.RunRequest.TYPE_EFI:
        return f"""
insmod part_gpt
insmod chain
set root='(hd0,gpt1)'
chainloader {runreq.settings.efi_path}
boot
        """

    else:
        raise Exception("Invalid runreq type")

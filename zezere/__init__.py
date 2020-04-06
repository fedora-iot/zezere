from django.contrib.staticfiles.finders import BaseFinder
import requests

from pathlib import Path
import os
import os.path
import sys


def run_django_management():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zezere.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


EFI_FILE_URL_BASE = (
    "https://kojipkgs.fedoraproject.org/compose/iot/latest-Fedora-IoT-32/compose/IoT"
)


EFI_FILES = [
    {
        "url": EFI_FILE_URL_BASE + "/x86_64/os/isolinux/initrd.img",
        "destination": "netboot/x86_64/initrd",
    },
    {
        "url": EFI_FILE_URL_BASE + "/x86_64/os/isolinux/vmlinuz",
        "destination": "netboot/x86_64/vmlinuz",
    },
    {
        "url": EFI_FILE_URL_BASE + "/aarch64/os/images/pxeboot/initrd.img",
        "destination": "netboot/aarch64/initrd",
    },
    {
        "url": EFI_FILE_URL_BASE + "/aarch64/os/images/pxeboot/vmlinuz",
        "destination": "netboot/aarch64/vmlinuz",
    },
]


def download_netboot_files(destroot=None):  # pragma: no cover
    if not destroot:
        destroot = os.getcwd()

    for file in EFI_FILES:
        dir, destfile = os.path.split(file["destination"])
        destdir = os.path.join("zezere/static/", dir)
        url = file["url"]

        destfile = os.path.join(destdir, destfile)

        destfile = os.path.join(destroot, destfile)

        print("Downloading %s to %s" % (url, destfile))

        if not os.path.exists(destfile):
            Path(destdir).mkdir(parents=True, exist_ok=True)

            with requests.get(url, stream=True) as dlf:
                dlf.raise_for_status()
                with open(destfile, "wb") as f:
                    for chunk in dlf.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)


class django_staticfiles_netboot_finder(BaseFinder):  # pragma: no cover
    def list(self, ignore_patterns):
        download_netboot_files()
        return []

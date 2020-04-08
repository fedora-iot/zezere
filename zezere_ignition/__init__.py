#!/usr/bin/python3
from typing import Optional, List

import argparse
import json
import platform
from subprocess import run as sp_run
from tempfile import NamedTemporaryFile
import sys
import os


IGNITION_BINARY_PATH = "/usr/lib/dracut/modules.d/30ignition/ignition"


def get_primary_interface() -> Optional[str]:
    mask_to_iface = {}

    with open("/proc/net/route", "r") as routefile:
        for line in routefile.readlines():
            if not line.strip():
                # Pass over empty lines
                continue
            split = line.split()
            interface = split[0]
            mask = split[7]
            if split[0] == "Iface":
                # Pass over the file header
                continue
            mask_to_iface[mask] = interface

    # If there are no routes at all, just exit
    if len(mask_to_iface) == 0:
        # No routes at all
        return None
    # Determine the smallest mask in the table.
    # This will default to the default route, or go further down
    return mask_to_iface[min(mask_to_iface, key=lambda x: int(x, 16))]


def get_interface_mac(interface: Optional[str]) -> str:
    if interface is None:
        return None
    with open("/sys/class/net/%s/address" % interface, "r") as addrfile:
        return addrfile.read().strip()


def get_zezere_url_cmdline() -> Optional[str]:
    cmdline = None
    with open("/proc/cmdline", "r") as cmdlinefile:
        cmdline = cmdlinefile.read().strip()
    for arg in cmdline.split(" "):
        args = arg.split("=", 2)
        if len(args) != 2:
            continue
        key, val = args
        if key == "zezere.url":
            return val.strip()


def get_zezere_url():
    cmdline_url = get_zezere_url_cmdline()
    if cmdline_url is not None:
        return cmdline_url

    paths = [
        "/usr/lib/zezere-ignition-url",
        "/etc/zezere-ignition-url",
        "./zezere-ignition-url",
    ]
    for path in paths:
        if os.path.exists(path):
            with open(path, "r") as urlfile:
                return urlfile.read().strip()


def run_ignition_stage(config_file: str, stage: str):
    print("Running stage %s with config file %s" % (stage, config_file))
    cmd = [
        IGNITION_BINARY_PATH,
        "--platform",
        "file",
        "--stage",
        stage,
        "--log-to-stdout",
    ]
    procenv = os.environ.copy()
    procenv["IGNITION_CONFIG_FILE"] = config_file
    procenv["IGNITION_WRITE_AUTHORIZED_KEYS_FRAGMENT"] = "false"

    sp_run(cmd, env=procenv)


def run_ignition(config_url: str):
    with NamedTemporaryFile(
        "w", encoding="utf-8", prefix="zezere-ignition-config-", suffix=".ign"
    ) as ignfile:
        cfgobj = {
            "ignition": {
                "version": "3.0.0",
                "config": {"replace": {"source": config_url}},
            }
        }
        ignfile.write(json.dumps(cfgobj))
        ignfile.flush()
        for stage in ["fetch", "disks", "mount", "files", "umount"]:
            run_ignition_stage(ignfile.name, stage)


def update_banner(url: str, device_id: Optional[str]):
    if device_id is None:
        device_id = "device ID not yet known"
    with open("/run/zezere-ignition-banner", "w") as bannerfile:
        bannerfile.write(
            f"Browse to {url} to claim this device ({device_id}) "
            f"and configure SSH keys deployed\n\n"
        )


def main(args: argparse.Namespace):
    zezere_url = get_zezere_url()
    if zezere_url is None:
        print("No Zezere URL configured, exiting", file=sys.stderr)
        return
    if zezere_url.endswith("/"):
        zezere_url = zezere_url[:-1]

    def_intf = get_primary_interface()
    def_intf_mac = get_interface_mac(def_intf)

    # We still want to put the banner in place if there's no default mac addr yet
    if args.update_banner:
        update_banner(zezere_url, def_intf_mac)
        if args.only_update_banner:
            print("Updated issue banner")
            return

    if def_intf_mac is None:
        print("Unable to determine default interface, exiting", file=sys.stderr)
        return

    arch = platform.machine()

    url = "%s/netboot/%s/ignition/%s" % (zezere_url, arch, def_intf_mac)

    run_ignition(url)


def get_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Ignition from Zezere config")

    parser.add_argument(
        "--no-update-banner",
        dest="update_banner",
        action="store_false",
        help="Skip updating the TTY banner",
    )
    parser.add_argument(
        "--only-update-banner",
        dest="only_update_banner",
        action="store_true",
        help="Stop after updating TTY banner",
    )

    return parser.parse_args(argv)


if __name__ == "__main__":
    main(get_args(sys.argv[1:]))

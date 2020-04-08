from unittest import TestCase
from unittest.mock import patch, mock_open, call

import zezere_ignition


CMDLINE_NO_URL = (
    "BOOT_IMAGE=(hd0,gpt2)/vmlinuz-5.6.0-0.rc3.git0.1.fc32.x86_64 "
    "root=/dev/mapper/fedora_localhost--live-root "
    "ro "
    "resume=/dev/mapper/fedora_localhost--live-swap "
    "rd.lvm.lv=fedora_localhost-live/root "
    "rd.luks.uuid=luks-fb53079c-4b5e-491a-9d54-4a9f13ce028a "
    "rd.lvm.lv=fedora_localhost-live/swap "
    "rhgb "
    "quiet "
)

CMDLINE_WITH_URL = CMDLINE_NO_URL + "zezere.url=http://myserver.com"


class ZezereIgnitionTest(TestCase):
    def test_get_primary_interface_no_routes(self):
        with patch("zezere_ignition.open", mock_open(read_data="")) as p:
            intf = zezere_ignition.get_primary_interface()
            p.assert_called_once_with("/proc/net/route", "r")
            self.assertIsNone(intf)

    def test_get_primary_interface(self):
        ROUTE_CTS = """
Iface	Destination	Gateway 	Flags	RefCnt	Use	Metric	Mask	MTU	Window	IRTT
enp0s31f6	00000000	010010AC	0003	0	0	100	00000000	0	0	0
enp0s31f6	000010AC	00000000	0001	0	0	100	00FFFFFF	0	0	0
virbr0	007AA8C0	00000000	0001	0	0	0	00FFFFF0

"""
        with patch("zezere_ignition.open", mock_open(read_data=ROUTE_CTS)) as p:
            intf = zezere_ignition.get_primary_interface()
            p.assert_called_once_with("/proc/net/route", "r")
            self.assertEqual(intf, "enp0s31f6")

    def test_get_interface_mac_no_intf(self):
        with patch(
            "zezere_ignition.open", mock_open(read_data="52:54:00:2d:fb:49\n")
        ) as p:
            mac = zezere_ignition.get_interface_mac(None)
            p.assert_not_called()
            self.assertIsNone(mac)

    def test_get_interface_mac(self):
        with patch(
            "zezere_ignition.open", mock_open(read_data="52:54:00:2d:fb:49\n")
        ) as p:
            mac = zezere_ignition.get_interface_mac("someintf")
            p.assert_called_once_with("/sys/class/net/someintf/address", "r")
            self.assertEqual(mac, "52:54:00:2d:fb:49")

    def test_get_zezere_url_cmdline_no_cmd(self):
        with patch("zezere_ignition.open", mock_open(read_data=CMDLINE_NO_URL)) as p:
            url = zezere_ignition.get_zezere_url_cmdline()
            p.assert_called_once_with("/proc/cmdline", "r")
            self.assertIsNone(url)

    def test_get_zezere_url_cmdline(self):
        with patch("zezere_ignition.open", mock_open(read_data=CMDLINE_WITH_URL)) as p:
            url = zezere_ignition.get_zezere_url_cmdline()
            p.assert_called_once_with("/proc/cmdline", "r")
            self.assertEqual(url, "http://myserver.com")

    def test_get_zezere_url_from_cmdline(self):
        with patch("zezere_ignition.open", mock_open(read_data=CMDLINE_WITH_URL)) as p:
            url = zezere_ignition.get_zezere_url()
            p.assert_called_once_with("/proc/cmdline", "r")
            self.assertEqual(url, "http://myserver.com")

    def test_get_zezere_url_no_files(self):
        with patch("zezere_ignition.open", mock_open(read_data=CMDLINE_NO_URL)):
            with patch("zezere_ignition.os.path.exists", return_value=False) as ep:
                url = zezere_ignition.get_zezere_url()
                ep.assert_has_calls(
                    [
                        call("/usr/lib/zezere-ignition-url"),
                        call("/etc/zezere-ignition-url"),
                        call("./zezere-ignition-url"),
                    ]
                )
                self.assertIsNone(url)

    def test_get_zezere_url(self):
        def get_file_cts(filename, mode):
            self.assertEqual(mode, "r")
            if filename == "/proc/cmdline":
                return mock_open(read_data=CMDLINE_NO_URL)()
            if filename == "/etc/zezere-ignition-url":
                return mock_open(read_data="http://someserver.com")()

        with patch("zezere_ignition.open", side_effect=get_file_cts) as op:
            with patch(
                "zezere_ignition.os.path.exists", side_effect=[False, True]
            ) as ep:
                url = zezere_ignition.get_zezere_url()
                ep.assert_has_calls(
                    [
                        call("/usr/lib/zezere-ignition-url"),
                        call("/etc/zezere-ignition-url"),
                    ]
                )
                op.assert_has_calls(
                    [call("/proc/cmdline", "r"), call("/etc/zezere-ignition-url", "r")]
                )
                self.assertEqual(url, "http://someserver.com")

    def test_run_ignition_stage(self):
        with patch("zezere_ignition.print") as pp:
            with patch("zezere_ignition.sp_run") as spp:
                zezere_ignition.run_ignition_stage("/some/config", "fetch")

        pp.assert_called_once()
        self.assertListEqual(
            spp.call_args[0][0],
            [
                zezere_ignition.IGNITION_BINARY_PATH,
                "--platform",
                "file",
                "--stage",
                "fetch",
                "--log-to-stdout",
            ],
        )

    def test_run_ignition(self):
        with patch("zezere_ignition.NamedTemporaryFile", mock_open()) as ntfp:
            ntfp.return_value.name = "/some/file"
            with patch("zezere_ignition.run_ignition_stage") as risp:
                zezere_ignition.run_ignition("http://someurl")

        ntfp.assert_called_once()
        risp.assert_has_calls(
            [
                call("/some/file", "disks"),
                call("/some/file", "fetch"),
                call("/some/file", "files"),
                call("/some/file", "mount"),
                call("/some/file", "umount"),
            ],
            any_order=True,
        )

    def test_update_banner_no_devid(self):
        with patch("zezere_ignition.open", mock_open()) as bp:
            zezere_ignition.update_banner("http://someserver.com", None)

        bp.assert_called_once_with("/run/zezere-ignition-banner", "w")
        bp.return_value.write.assert_called_once_with(
            "Browse to http://someserver.com to claim this device "
            "(device ID not yet known) and configure SSH keys deployed\n\n"
        )

    def test_update_banner(self):
        with patch("zezere_ignition.open", mock_open()) as bp:
            zezere_ignition.update_banner("http://someserver.com", "mydevice")

        bp.assert_called_once_with("/run/zezere-ignition-banner", "w")
        bp.return_value.write.assert_called_once_with(
            "Browse to http://someserver.com to claim this device (mydevice) "
            "and configure SSH keys deployed\n\n"
        )

    def test_get_args_no_args(self):
        args = zezere_ignition.get_args([])
        self.assertEqual(args.update_banner, True)
        self.assertEqual(args.only_update_banner, False)

    def test_get_args(self):
        args = zezere_ignition.get_args(["--no-update-banner"])
        self.assertEqual(args.update_banner, False)
        self.assertEqual(args.only_update_banner, False)

    @patch("zezere_ignition.print")
    @patch("zezere_ignition.get_zezere_url", return_value=None)
    @patch("zezere_ignition.get_primary_interface")
    def test_main_no_url(self, gpip, *mocks):
        zezere_ignition.main(zezere_ignition.get_args([]))

        gpip.assert_not_called()

    @patch("zezere_ignition.get_zezere_url", return_value="http://someserver")
    @patch("zezere_ignition.get_primary_interface", return_value="defintf")
    @patch("zezere_ignition.get_interface_mac", return_value="defmac")
    @patch("zezere_ignition.print")
    @patch("zezere_ignition.run_ignition")
    @patch("zezere_ignition.update_banner")
    def test_main_only_banner(self, ubp, rip, *mocks):
        zezere_ignition.main(zezere_ignition.get_args(["--only-update-banner"]))

        ubp.assert_called_once_with("http://someserver", "defmac")
        rip.assert_not_called()

    @patch("zezere_ignition.get_zezere_url", return_value="http://someserver/")
    @patch("zezere_ignition.get_primary_interface", return_value="defintf")
    @patch("zezere_ignition.get_interface_mac", return_value="defmac")
    @patch("zezere_ignition.print")
    @patch("zezere_ignition.run_ignition")
    @patch("zezere_ignition.update_banner")
    def test_main_only_banner_with_trailing_slash(self, ubp, rip, *mocks):
        zezere_ignition.main(zezere_ignition.get_args(["--only-update-banner"]))

        ubp.assert_called_once_with("http://someserver", "defmac")
        rip.assert_not_called()

    @patch("zezere_ignition.get_zezere_url", return_value="http://someserver")
    @patch("zezere_ignition.get_primary_interface", return_value="defintf")
    @patch("zezere_ignition.get_interface_mac", return_value=None)
    @patch("zezere_ignition.print")
    @patch("zezere_ignition.run_ignition")
    @patch("zezere_ignition.update_banner")
    def test_main_no_defmac(self, ubp, rip, *mocks):
        zezere_ignition.main(zezere_ignition.get_args([]))

        ubp.assert_called_once_with("http://someserver", None)
        rip.assert_not_called()

    @patch("zezere_ignition.get_zezere_url", return_value="http://someserver")
    @patch("zezere_ignition.get_primary_interface", return_value="defintf")
    @patch("zezere_ignition.get_interface_mac", return_value="defmac")
    @patch("zezere_ignition.print")
    @patch("zezere_ignition.platform.machine", return_value="x86_64")
    @patch("zezere_ignition.run_ignition")
    @patch("zezere_ignition.update_banner")
    def test_main_x86_64(self, ubp, rip, *mocks):
        zezere_ignition.main(zezere_ignition.get_args([]))

        ubp.assert_called_once_with("http://someserver", "defmac")
        rip.assert_called_once_with("http://someserver/netboot/x86_64/ignition/defmac")

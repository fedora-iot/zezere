from unittest.mock import patch

from . import TestCase

from zezere import models


class NetbootTest(TestCase):
    fixtures = ["fedora_installed.json", "fedora_iot_runreqs.json"]

    def test_index(self):
        resp = self.client.get("/netboot")
        self.assertContains(resp, "x86_64")
        self.assertContains(resp, "aarch64")

    def test_static_grub_cfg(self):
        resp = self.client.get("/netboot/x86_64/grub.cfg")
        # NOTE: This URL will be the one configured in DHCP
        # Changing this URL is a solid API break.
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'configfile "')
        self.assertNotContains(resp, "set debug=all")

    def test_static_grub_cfg_head(self):
        resp = self.client.head("/netboot/x86_64/grub.cfg")
        # NOTE: This URL will be the one configured in DHCP
        # Changing this URL is a solid API break.
        self.assertEqual(resp.status_code, 200)

    def test_static_grub_debug_cfg(self):
        resp = self.client.get("/netboot/debug/x86_64/grub.cfg")
        # NOTE: This URL will be the one configured in DHCP
        # Changing this URL is a solid API break.
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'configfile "')
        self.assertContains(resp, "set debug=all")

    def test_dynamic_grub_cfg_ok(self):
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1) as dev:
                with self.device_with_runreq(dev, self.RUNREQ_RAWHIDE):
                    devurl = "/netboot/x86_64/grubcfg/%s" % self.DEVICE_1
                    resp = self.client.get(devurl)
                    self.assertTemplateUsed(resp, "netboot/grubcfg")
                    self.assertIsNotNone(resp.context["device"])
                    self.assertContains(resp, "\nboot")
                    self.assertNotContains(resp, "set debug=all")

    def test_dynamic_grub_noboot_cfg_ok(self):
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1) as dev:
                with self.device_with_runreq(dev, self.RUNREQ_RAWHIDE):
                    devurl = "/netboot/noboot/x86_64/grubcfg/%s" % self.DEVICE_1
                    resp = self.client.get(devurl)
                    self.assertTemplateUsed(resp, "netboot/grubcfg")
                    self.assertIsNotNone(resp.context["device"])
                    self.assertNotContains(resp, "\nboot")
                    self.assertNotContains(resp, "set debug=all")

    def test_dynamic_grub_debug_cfg_ok(self):
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1) as dev:
                with self.device_with_runreq(dev, self.RUNREQ_RAWHIDE):
                    devurl = "/netboot/debug/x86_64/grubcfg/%s" % self.DEVICE_1
                    resp = self.client.get(devurl)
                    self.assertTemplateUsed(resp, "netboot/grubcfg")
                    self.assertIsNotNone(resp.context["device"])
                    self.assertContains(resp, "\nboot")
                    self.assertContains(resp, "set debug=all")

    def test_dynamic_grub_debug_noboot_cfg_ok(self):
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1) as dev:
                with self.device_with_runreq(dev, self.RUNREQ_RAWHIDE):
                    devurl = "/netboot/debug+noboot/x86_64/grubcfg/%s" % self.DEVICE_1
                    resp = self.client.get(devurl)
                    self.assertTemplateUsed(resp, "netboot/grubcfg")
                    self.assertIsNotNone(resp.context["device"])
                    self.assertNotContains(resp, "\nboot")
                    self.assertContains(resp, "set debug=all")

    def test_dynamic_grub_cfg_ok_ip_change(self):
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1) as dev:
                with self.device_with_runreq(dev, self.RUNREQ_RAWHIDE):
                    with patch(
                        "zezere.views_netboot.get_client_ip",
                        return_value=("127.0.0.2", None),
                    ):
                        devurl = "/netboot/x86_64/grubcfg/%s" % self.DEVICE_1
                        resp = self.client.get(devurl)
                        self.assertTemplateUsed(resp, "netboot/grubcfg")
                        self.assertIsNotNone(resp.context["device"])
                    dev.refresh_from_db()
                    self.assertEqual(dev.last_ip_address, "127.0.0.2")

                    with patch(
                        "zezere.views_netboot.get_client_ip",
                        return_value=("127.0.0.3", None),
                    ):
                        devurl = "/netboot/x86_64/grubcfg/%s" % self.DEVICE_1
                        resp = self.client.get(devurl)
                        self.assertTemplateUsed(resp, "netboot/grubcfg")
                        self.assertIsNotNone(resp.context["device"])
                    dev.refresh_from_db()
                    self.assertEqual(dev.last_ip_address, "127.0.0.3")

    def test_dynamic_grub_cfg_ef(self):
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1) as dev:
                with self.device_with_runreq(dev, self.RUNREQ_INSTALLED):
                    devurl = "/netboot/x86_64/grubcfg/%s" % self.DEVICE_1
                    resp = self.client.get(devurl)
                    self.assertTemplateUsed(resp, "netboot/grubcfg")
                    self.assertIsNotNone(resp.context["device"])

    @patch("logging.Logger.error")
    def test_dynamic_grub_cfg_invalid_runreq(self, logging_mock):
        rreq = models.RunRequest(
            auto_generated_id=None,
            owner=self.get_user(self.USER_1),
            type="--",
            efi_application="/somewhere.efi",
        )
        rreq.save()

        self.assertIsNone(rreq.typestr)

        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1) as dev:
                dev.run_request = rreq
                dev.save()
                devurl = "/netboot/x86_64/grubcfg/%s" % self.DEVICE_1
                resp = self.client.get(devurl)
                self.assertTemplateUsed(resp, "netboot/grubcfg")
                self.assertIsNotNone(resp.context["device"])
                self.assertContains(resp, "Something has gone wrong")
                dev.run_request = None
                dev.save()

        logging_mock.assert_called_once()

    def test_dynamic_grub_cfg_no_runreq(self):
        devurl = "/netboot/x86_64/grubcfg/%s" % self.DEVICE_1
        resp = self.client.get(devurl)
        self.assertTemplateUsed(resp, "netboot/grubcfg")
        self.assertIsNotNone(resp.context["device"])

    def test_dynamic_grub_cfg_new_device(self):
        devurl = "/netboot/x86_64/grubcfg/FF:FF:FF:FF:FF:FF"
        resp = self.client.get(devurl)
        self.assertTemplateUsed(resp, "netboot/grubcfg")
        self.assertIsNotNone(resp.context["device"])

    @patch("logging.Logger.error")
    def test_dynamic_grub_cfg_same_mac_diff_arch(self, mock_error):
        # This returns a ValidationError because the MAC already exists
        # but was not found (different architecture)
        devurl = "/netboot/aarch64/grubcfg/%s" % self.DEVICE_1
        resp = self.client.get(devurl)
        self.assertTemplateUsed(resp, "netboot/grubcfg_fallback")
        mock_error.assert_called_once()

    def test_kickstart(self):
        ksurl = "/netboot/kickstart/%s" % self.DEVICE_1
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1) as dev:
                with self.device_with_runreq(dev, self.RUNREQ_RAWHIDE):
                    resp = self.client.get(ksurl)
                    self.assertTemplateUsed(resp, "netboot/kickstart")
                    self.assertIsNotNone(resp.context["device"])

    def test_kickstart_no_runreq(self):
        ksurl = "/netboot/kickstart/%s" % self.DEVICE_1
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1):
                resp = self.client.get(ksurl)
                self.assertEqual(resp.status_code, 404)

    def test_kickstart_non_install_runreq(self):
        ksurl = "/netboot/kickstart/%s" % self.DEVICE_1
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1) as dev:
                with self.device_with_runreq(dev, self.RUNREQ_INSTALLED):
                    resp = self.client.get(ksurl)
                    self.assertEqual(resp.status_code, 404)

    def test_postboot(self):
        pburl = "/netboot/postboot/%s" % self.DEVICE_1
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1) as dev:
                with self.device_with_runreq(dev, self.RUNREQ_RAWHIDE):
                    resp = self.client.get(pburl)
                    self.assertEqual(resp.status_code, 200)
                    dev.refresh_from_db()
                    self.assertEqual(
                        dev.run_request.auto_generated_id, self.RUNREQ_INSTALLED
                    )

    def test_postboot_no_runreq(self):
        pburl = "/netboot/postboot/%s" % self.DEVICE_1
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1):
                resp = self.client.get(pburl)
                self.assertEqual(resp.status_code, 404)

    def test_postboot_runreq_no_next(self):
        pburl = "/netboot/postboot/%s" % self.DEVICE_1
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1) as dev:
                with self.device_with_runreq(dev, self.RUNREQ_INSTALLED):
                    resp = self.client.get(pburl)
                    self.assertEqual(resp.status_code, 404)

    def test_arch_file(self, *mocks):
        resp = self.client.get("/netboot/x86_64/initial")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/efi")

    def test_arch_file_head(self, *mocks):
        resp = self.client.head("/netboot/x86_64/initial")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/efi")

    def test_arch_file_double_slash(self, *mocks):
        resp = self.client.get("/netboot/x86_64//initial")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/efi")

    def test_arch_file_invalid_arch(self):
        resp = self.client.get("/netboot/myarch/initial")
        self.assertEqual(resp.status_code, 404)

    def test_arch_file_invalid_arch_file(self):
        resp = self.client.get("/netboot/aarch64/grubx64.efi")
        self.assertEqual(resp.status_code, 404)

    def test_ignition_cfg_no_runreq(self):
        ignurl = "/netboot/x86_64/ignition/%s" % self.DEVICE_1
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1):
                resp = self.client.get(ignurl)
                self.assertEqual(resp.status_code, 404)

    def ign_cfg_sanity_check(self, value):
        seenusers = set()
        for userobj in value["passwd"]["users"]:
            self.assertFalse(
                userobj["name"] in seenusers,
                "User %s twice in ign config" % userobj["name"],
            )
            seenusers.add(userobj["name"])

    def test_ignition_cfg(self):
        ignurl = "/netboot/x86_64/ignition/%s" % self.DEVICE_1
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1) as dev:
                with self.device_with_runreq(dev, self.RUNREQ_INSTALLED):
                    resp = self.client.get(ignurl)
                    self.assertEqual(resp.status_code, 200)
                    resp = resp.json()
                    self.ign_cfg_sanity_check(resp)
                    self.assertEqual(resp["passwd"]["users"][0]["name"], "root")
                    self.assertEqual(
                        resp["passwd"]["users"][0]["sshAuthorizedKeys"], []
                    )

    def test_ignition_cfg_with_keys(self):
        ignurl = "/netboot/x86_64/ignition/%s" % self.DEVICE_1
        with self.loggedin_as() as user:
            models.SSHKey(owner=user, key="mykeycontents").save()

            with self.claimed_device(self.DEVICE_1) as dev:
                with self.device_with_runreq(dev, self.RUNREQ_INSTALLED):
                    resp = self.client.get(ignurl)
                    self.assertEqual(resp.status_code, 200)
                    resp = resp.json()
                    self.ign_cfg_sanity_check(resp)
                    self.assertEqual(resp["passwd"]["users"][0]["name"], "root")
                    self.assertEqual(
                        resp["passwd"]["users"][0]["sshAuthorizedKeys"],
                        ["mykeycontents"],
                    )

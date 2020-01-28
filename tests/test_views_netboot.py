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

    def test_static_grub_cfg_head(self):
        resp = self.client.head("/netboot/x86_64/grub.cfg")
        # NOTE: This URL will be the one configured in DHCP
        # Changing this URL is a solid API break.
        self.assertEqual(resp.status_code, 200)

    def test_dynamic_grub_cfg_ok(self):
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1) as dev:
                with self.device_with_runreq(dev, self.RUNREQ_RAWHIDE):
                    devurl = "/netboot/x86_64/grubcfg/%s" % self.DEVICE_1
                    resp = self.client.get(devurl)
                    self.assertTemplateUsed(resp, "netboot/grubcfg")
                    self.assertIsNotNone(resp.context["device"])

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

    def test_static_proxy_no_runreq(self):
        dlurl = "/netboot/x86_64/proxydl/%s/kernel" % self.DEVICE_1
        resp = self.client.head(dlurl)
        self.assertEqual(resp.status_code, 404)

    def test_static_proxy_efi_runreq(self):
        dlurl = "/netboot/x86_64/proxydl/%s/kernel" % self.DEVICE_1
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1) as dev:
                with self.device_with_runreq(dev, self.RUNREQ_INSTALLED):
                    resp = self.client.head(dlurl)
                    self.assertEqual(resp.status_code, 404)

    @patch("requests.get")
    def test_static_proxy_invalid_filetype(self, mock_get):
        dlurl = "/netboot/x86_64/proxydl/%s/nosuchfile" % self.DEVICE_1
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1) as dev:
                with self.device_with_runreq(dev, self.RUNREQ_RAWHIDE):
                    resp = self.client.head(dlurl)
                    self.assertEqual(resp.status_code, 404)

    @patch("requests.get")
    def test_static_proxy_kernel(self, mock_get):
        dlurl = "/netboot/x86_64/proxydl/%s/kernel" % self.DEVICE_1
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1) as dev:
                with self.device_with_runreq(dev, self.RUNREQ_RAWHIDE):
                    resp = self.client.head(dlurl)
                    self.assertEqual(resp.status_code, 200)
                    self.assertIn("get().headers.__getitem__", resp["Content-Length"])
                    self.assertEqual(resp["Content-Type"], "application/octet-stream")

        mock_get.assert_called_once_with(
            "https://kojipkgs.fedoraproject.org/compose/iot/"
            "latest-Fedora-IoT-32/compose/IoT/x86_64/os/isolinux/vmlinuz",
            stream=True,
        )

    @patch("requests.get")
    def test_static_proxy_initrd(self, mock_get):
        dlurl = "/netboot/x86_64/proxydl/%s/initrd" % self.DEVICE_1
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1) as dev:
                with self.device_with_runreq(dev, self.RUNREQ_RAWHIDE):
                    resp = self.client.head(dlurl)
                    self.assertEqual(resp.status_code, 200)
                    self.assertIn("get().headers.__getitem__", resp["Content-Length"])
                    self.assertEqual(resp["Content-Type"], "application/octet-stream")

        mock_get.assert_called_once_with(
            "https://kojipkgs.fedoraproject.org/compose/iot/"
            "latest-Fedora-IoT-32/compose/IoT/x86_64/os/isolinux/initrd.img",
            stream=True,
        )

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

        # Hacky fix to silence warning. If this causes failure, the internal
        # django test client API probably changed. This can be safely removed.
        resp._closable_objects[0].close()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/efi")

    def test_arch_file_head(self, *mocks):
        resp = self.client.head("/netboot/x86_64/initial")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/efi")

    def test_arch_file_double_slash(self, *mocks):
        resp = self.client.get("/netboot/x86_64//initial")

        # Hacky fix to silence warning. If this causes failure, the internal
        # django test client API probably changed. This can be safely removed.
        resp._closable_objects[0].close()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/efi")

    def test_arch_file_invalid_arch(self):
        resp = self.client.get("/netboot/myarch/initial")
        self.assertEqual(resp.status_code, 404)

    def test_arch_file_invalid_arch_file(self):
        resp = self.client.get("/netboot/aarch64/grubx64.efi")
        self.assertEqual(resp.status_code, 404)

    def test_ignition_cfg_no_runreq(self):
        ignurl = "/netboot/ignition/%s" % self.DEVICE_1
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
        ignurl = "/netboot/ignition/%s" % self.DEVICE_1
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
        ignurl = "/netboot/ignition/%s" % self.DEVICE_1
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

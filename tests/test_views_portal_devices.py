from unittest.mock import patch

from . import TestCase

from zezere import models


class PortalDevicesTest(TestCase):
    fixtures = ["fedora_installed.json", "fedora_iot_runreqs.json"]

    def test_list_no_devices(self):
        with self.loggedin_as():
            resp = self.client.get("/portal/devices/")
            self.assertTemplateUsed(resp, "portal/devices.html")
            self.assertEqual(len(resp.context["devices"]), 0)

    def test_list_claimable_devices(self):
        with self.loggedin_as():
            resp = self.client.get("/portal/claim/")
            self.assertTemplateUsed(resp, "portal/claim.html")
            self.assertEqual(len(resp.context["unclaimed_devices"]), 3)
            self.assertNotContains(resp, self.REMOTE_DEVICE_1)
        with self.loggedin_as(self.ADMIN_1):
            resp = self.client.get("/portal/claim/")
            self.assertTemplateUsed(resp, "portal/claim.html")
            self.assertEqual(len(resp.context["unclaimed_devices"]), 4)
            self.assertContains(resp, self.REMOTE_DEVICE_1)

    def test_claim_device(self):
        with self.loggedin_as():
            with patch(
                "zezere.views_portal.get_client_ip", return_value=("127.0.0.1", None),
            ):
                resp = self.client.post(
                    "/portal/claim/", {"mac_address": self.DEVICE_1}, follow=True
                )
                self.assertTemplateUsed(resp, "portal/claim.html")
                self.assertEqual(len(resp.context["unclaimed_devices"]), 2)
                self.assertNotContains(resp, self.DEVICE_1)

    def test_claim_claimed_device(self):
        self.claim_device(self.DEVICE_1, self.USER_2)
        with self.loggedin_as(self.USER_1):
            with patch(
                "zezere.views_netboot.get_client_ip", return_value=("127.0.0.1", None),
            ):
                resp = self.client.post(
                    "/portal/claim/", {"mac_address": self.DEVICE_1}, follow=True
                )
                self.assertTemplateNotUsed(resp, "portal/claim.html")
                self.assertEqual(resp.status_code, 403)

    def test_list_runreqs_unowned_device(self):
        dev1url = "/portal/devices/runreq/%s/" % self.DEVICE_1
        with self.loggedin_as():
            resp = self.client.get(dev1url)
            self.assertEqual(resp.status_code, 302)

    def test_list_runreqs_misowned_device(self):
        self.claim_device(self.DEVICE_1, self.USER_2)

        dev1url = "/portal/devices/runreq/%s/" % self.DEVICE_1
        with self.loggedin_as(self.USER_1):
            resp = self.client.get(dev1url)
            self.assertEqual(resp.status_code, 302)

    def test_list_runreqs(self):
        dev1url = "/portal/devices/runreq/%s/" % self.DEVICE_1
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1):
                resp = self.client.get(dev1url)
                self.assertContains(resp, self.RUNREQ_INSTALLED)
                self.assertContains(resp, self.RUNREQ_RAWHIDE)

    def test_apply_runreq(self):
        dev1url = "/portal/devices/runreq/%s/" % self.DEVICE_1
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1):
                rreq = models.RunRequest.objects.get(
                    auto_generated_id=self.RUNREQ_RAWHIDE
                )
                resp = self.client.post(dev1url, {"runrequest": rreq.id}, follow=True)
                self.assertTemplateUsed("portal/devices.html")
                self.assertIsNotNone(resp.context["devices"][0].run_request)

    def test_apply_nonowned_runreq(self):
        rreq = models.RunRequest(
            owner=self.get_user(self.USER_2),
            type=models.RunRequest.TYPE_EFI,
            efi_application="/nowhere.efi",
        )
        rreq.full_clean()
        rreq.save()

        dev1url = "/portal/devices/runreq/%s/" % self.DEVICE_1
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1):
                resp = self.client.post(dev1url, {"runrequest": rreq.id}, follow=True)
                self.assertEqual(resp.status_code, 404)

    def test_apply_nonexisting_runreq(self):
        dev1url = "/portal/devices/runreq/%s/" % self.DEVICE_1
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1):
                resp = self.client.post(dev1url, {"runrequest": 500}, follow=True)
                self.assertEqual(resp.status_code, 404)

    def test_clean_runreq(self):
        dev1url = "/portal/devices/runreq/%s/clean/" % self.DEVICE_1
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1) as dev:
                with self.device_with_runreq(dev, self.RUNREQ_INSTALLED):
                    resp = self.client.post(dev1url, follow=True)
                    self.assertTemplateUsed("portal/devices.html")
                    self.assertIsNone(resp.context["devices"][0].run_request)

    def test_clean_runreq_without_runreq(self):
        dev1url = "/portal/devices/runreq/%s/clean/" % self.DEVICE_1
        with self.loggedin_as():
            with self.claimed_device(self.DEVICE_1):
                resp = self.client.post(dev1url, follow=True)
                self.assertEqual(resp.status_code, 400)

from contextlib import contextmanager

from django.test import TestCase as djangoTestCase
from django.contrib.auth.models import User

from zezere import models


class TestCase(djangoTestCase):
    # Some test users
    USER_1: str = "testuser1"
    USER_2: str = "testuser2"
    ADMIN_1: str = "admin1"

    # Some test devices
    DEVICE_1: str = "00:00:00:00:00:00"
    DEVICE_2: str = "11:11:11:11:11:11"
    DEVICE_3: str = "22:22:22:22:22:22"
    REMOTE_DEVICE_1: str = "33:33:33:33:33:33"

    # The initial runreq auto-ids installed by fixtures
    RUNREQ_INSTALLED = "fedora-installed"
    RUNREQ_RAWHIDE = "fedora-iot-rawhide"

    _cur_user = None

    @classmethod
    def setUpTestData(cls):
        for macaddr in (cls.DEVICE_1, cls.DEVICE_2, cls.DEVICE_3):
            models.Device(
                mac_address=macaddr, architecture="x86_64", last_ip_address="127.0.0.1"
            ).save()

        models.Device(
            mac_address=cls.REMOTE_DEVICE_1,
            architecture="x86_64",
            last_ip_address="10.10.10.10",
        ).save()

        User.objects.create_superuser(cls.ADMIN_1, password="testpass")

        for username in (cls.USER_1, cls.USER_2):
            User.objects.create_user(username, password="testpass")

    @contextmanager
    def loggedin_as(self, username: str = USER_1):
        self.assertIsNone(self._cur_user)
        self.assertTrue(self.client.login(username=username, password="testpass"))
        self._cur_user = self.get_user(username)
        try:
            yield self._cur_user
        finally:
            self.client.logout()
            self._cur_user = None

    def get_user(self, username: str):
        user = User.objects.get(username=username)
        self.assertIsNotNone(user)
        return user

    def get_device(self, device: str) -> models.Device:
        device = models.Device.objects.get(mac_address=device)
        self.assertIsNotNone(device)
        return device

    def claim_device(self, device: str, username: str):
        user = self.get_user(username)
        dev = models.Device.objects.get(mac_address=device)
        self.assertIsNone(dev.owner)
        dev.owner = user
        dev.full_clean()
        dev.save()
        return dev

    def unclaim_device(self, device: str):
        dev = models.Device.objects.get(mac_address=device)
        self.assertIsNotNone(dev.owner)
        dev.owner = None
        dev.full_clean()
        dev.save()

    @contextmanager
    def claimed_device(self, device: str):
        self.assertIsNotNone(self._cur_user)
        self.assertFalse(self._cur_user.is_anonymous)

        dev = models.Device.objects.get(mac_address=device)
        self.assertIsNone(dev.owner)
        dev.owner = self._cur_user
        dev.full_clean()
        dev.save()
        try:
            yield dev
        finally:
            dev.owner = None
            dev.full_clean()
            dev.save()

    @contextmanager
    def device_with_runreq(self, device: models.Device, runreq_autoid: str):
        rreq = models.RunRequest.objects.get(auto_generated_id=runreq_autoid)
        self.assertIsNotNone(rreq)
        device.run_request = rreq
        device.full_clean()
        device.save()
        try:
            yield rreq
        finally:
            device.run_request = None
            device.full_clean()
            device.save()

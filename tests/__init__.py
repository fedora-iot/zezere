from contextlib import contextmanager

from django.test import TestCase as djangoTestCase
from django.contrib.auth.models import User


class TestCase(djangoTestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_user('testuser1', password='testpass')
        User.objects.create_user('testuser2', password='testpass')

    @contextmanager
    def loggedin_as(self, username: str = "testuser1"):
        resp = self.client.post(
            "/accounts/login/",
            {"username": username, "password": "testpass"},
            follow=True,
        )
        # Check that we're logged in
        self.assertInHTML("Log out", resp.content.decode())
        try:
            yield None
        finally:
            resp = self.client.get(
                "/accounts/logout/",
                follow=True,
            )
            # Check that we're back at the login page
            self.assertEqual(resp.template_name, ["registration/login.html"])

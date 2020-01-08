from django.test import TestCase

from django.contrib.auth.models import User


class LoginTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_user('testuser', password='testpass')

    def test_login_required(self):
        for path in ('/',):
            resp = self.client.get(path, follow=True)
            self.assertEqual(resp.template_name, ["registration/login.html"])

    def test_invalid_login(self):
        resp = self.client.post(
            "/accounts/login/",
            {"username": "foo", "password": "bar"},
            follow=True,
        )
        # Check that we're back at the login page
        self.assertEqual(resp.template_name, ["registration/login.html"])

    def test_valid_login(self):
        resp = self.client.post(
            "/accounts/login/",
            {"username": "testuser", "password": "testpass"},
            follow=True,
        )
        # Check that we're logged in
        self.assertInHTML("Log out", resp.content.decode())

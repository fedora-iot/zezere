from . import TestCase


class MainTest(TestCase):
    def test_logout(self):
        with self.loggedin_as():
            resp = self.client.get("/accounts/logout/", follow=True)
            self.assertTemplateUsed(resp, "registration/login.html")

    def test_profile(self):
        with self.loggedin_as():
            resp = self.client.get("/accounts/profile/", follow=True)
            self.assertTemplateUsed(resp, "portal/index.html")

    def test_index(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "/portal/")

    def test_ping(self):
        resp = self.client.get("/ping/")
        self.assertEqual(resp.status_code, 200)

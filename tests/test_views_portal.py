from . import TestCase


class PortalTest(TestCase):
    def test_home(self):
        with self.loggedin_as():
            resp = self.client.get("/portal/", follow=True)
            self.assertTemplateUsed(resp, "portal/index.html")

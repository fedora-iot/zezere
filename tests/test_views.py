from . import TestCase


class MainTest(TestCase):
    def test_index(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "/portal/")

    def test_ping(self):
        resp = self.client.get("/ping/")
        self.assertEqual(resp.status_code, 200)

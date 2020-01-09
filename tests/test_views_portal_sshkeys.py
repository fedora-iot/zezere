from django.http import HttpResponseNotFound

from . import TestCase


class PortalSSHKeyTest(TestCase):
    def test_key_list(self):
        with self.loggedin_as():
            resp = self.client.get(
                "/portal/sshkeys/",
                follow=True,
            )
            self.assertEqual(len(resp.context['sshkeys']), 0)

    def test_add_empty_key(self):
        with self.loggedin_as():
            resp = self.client.post(
                "/portal/sshkeys/add/",
                {"sshkey": ""},
                follow=True,
            )
            self.assertEqual(len(resp.context['sshkeys']), 0)

    def test_add_key(self):
        with self.loggedin_as():
            resp = self.client.post(
                "/portal/sshkeys/add/",
                {"sshkey": "somekeyvalue<script>"},
                follow=True,
            )
            self.assertEqual(len(resp.context['sshkeys']), 1)
            # Check that we don't print the key back
            self.assertNotContains(resp, "<script>")

            self.assertEqual(
                resp.context['sshkeys'][0].key, "somekeyvalue<script>")

    def test_remove_key(self):
        with self.loggedin_as():
            resp = self.client.post(
                "/portal/sshkeys/add/",
                {"sshkey": "somekeyvalue<script>"},
                follow=True,
            )
            self.assertEqual(len(resp.context['sshkeys']), 1)
            key = resp.context['sshkeys'][0]

            resp = self.client.post(
                "/portal/sshkeys/delete/",
                {"sshkey_id": key.id+5},
                follow=True,
            )
            self.assertIsInstance(resp, HttpResponseNotFound)

            resp = self.client.post(
                "/portal/sshkeys/delete/",
                {"sshkey_id": key.id},
                follow=True,
            )
            self.assertNotIsInstance(resp, HttpResponseNotFound)
            self.assertEqual(len(resp.context['sshkeys']), 0)

    def test_other_person_key(self):
        with self.loggedin_as(self.USER_1):
            resp = self.client.post(
                "/portal/sshkeys/add/",
                {"sshkey": "somekeyvalue<script>"},
                follow=True,
            )
            self.assertEqual(len(resp.context['sshkeys']), 1)
            user1key = resp.context['sshkeys'][0]

        with self.loggedin_as(self.USER_2):
            resp = self.client.post(
                "/portal/sshkeys/add/",
                {"sshkey": "someotherkey"},
                follow=True,
            )
            self.assertEqual(len(resp.context['sshkeys']), 1)
            user2key = resp.context['sshkeys'][0]

            self.assertNotEqual(user1key, user2key)

            resp = self.client.post(
                "/portal/sshkeys/delete/",
                {"sshkey_id": user1key.id},
                follow=True,
            )
            self.assertIsInstance(resp, HttpResponseNotFound)

        with self.loggedin_as(self.USER_1):
            resp = self.client.get(
                "/portal/sshkeys/",
                follow=True,
            )
            self.assertEqual(len(resp.context['sshkeys']), 1)
            self.assertEqual(resp.context['sshkeys'][0], user1key)

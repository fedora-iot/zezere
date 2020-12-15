from . import TestCase


# Coming from Fedora Infrastructure Application Security Policy on 2020-12-15
ALLOWED_ORIGINS = ["https://apps.fedoraproject.org"]


class SecurityTest(TestCase):
    def test_headers(self):
        resp = self.client.get("/portal/")
        self.assertEqual(resp["X-Frame-Options"], "DENY")
        self.assertEqual(resp["X-Xss-Protection"], "1; mode=block")
        self.assertEqual(resp["X-Content-Type-Options"], "nosniff")
        self.assertEqual(resp["Referrer-Policy"], "no-referrer")

    def test_cookies(self):
        resp = self.client.get("/accounts/login/")
        for cookie in resp.cookies:
            val = resp.cookies[cookie]
            self.assertEqual(val["secure"], True)
            self.assertEqual(val["httponly"], True)
            self.assertEqual(val["domain"], "")

    def test_csp(self):
        resp = self.client.get("/portal/")
        csp = resp["Content-Security-Policy"]
        self.assertIn("default-src", csp)

        failed = False

        for part in csp.split(";"):
            part = part.strip().split(" ", 1)
            if len(part) == 1:
                # This means this scope is not allowed. Great!
                continue
            scope, allowed = part
            scope = scope.strip()
            allowed = allowed.strip().split(" ")

            for allowed in allowed:
                if allowed not in ["'none'", "'self'"]:
                    if allowed.startswith("'nonce-"):
                        continue
                    is_allowed_origin = False
                    for allowed_origin in ALLOWED_ORIGINS:
                        if allowed.startswith(allowed_origin):
                            is_allowed_origin = True
                            break
                    if is_allowed_origin:
                        continue
                    print("FAILED CSP: %s allows %s" % (scope, allowed))
                    failed = True

        if failed:
            raise Exception("At least one CSP check failed")

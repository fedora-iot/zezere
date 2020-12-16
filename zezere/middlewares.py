class MySecurityMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Content-Security-Policy"] = (
            "default-src; "
            + "style-src https://apps.fedoraproject.org/;"
            + "script-src https://apps.fedoraproject.org/;"
            + "font-src https://apps.fedoraproject.org/;"
        )
        return response

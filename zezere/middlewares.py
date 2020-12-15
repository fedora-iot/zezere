class MySecurityMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Content-Security-Policy"] = (
            "default-src; "
            + "style-src 'self' https://cdnjs.cloudflare.com/;"
            + "script-src 'self' https://cdnjs.cloudflare.com/;"
        )
        return response

from typing import Dict, Any, List, Optional

import os

from django.shortcuts import redirect
from django.urls import path, include


def urls_oidc():
    return [
        path("oidc/", include("mozilla_django_oidc.urls"), name="oidc"),
        path(
            "accounts/login/",
            lambda request: redirect("oidc_authentication_init"),
            name="login",
        ),
    ]


AUTH_METHODS: Dict[str, Any] = {
    "oidc": {
        "backends": ("mozilla_django_oidc.auth.OIDCAuthenticationBackend",),
        "installed_apps": ["mozilla_django_oidc"],
        "drf_auth_classes": ["mozilla_django_oidc.contrib.drf.OIDCAuthentication"],
        "urlfunc": urls_oidc,
    },
    "local": {
        "backends": (),
        "installed_apps": [],
        "drf_auth_classes": [
            "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly"
        ],
        "urlfunc": lambda: [path("accounts/", include("django.contrib.auth.urls"))],
    },
}

REST_FRAMEWORK: Dict[str, List[str]] = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "mozilla_django_oidc.contrib.drf.OIDCAuthentication"
    ]
}

auth_method: Optional[str] = None

# Try to auto-detect the used auth method
for envvar in os.environ.keys():
    if envvar.startswith("OIDC_"):  # pragma: no cover
        auth_method = "oidc"
    if envvar == "LOCAL_AUTH":
        auth_method = "local"

if auth_method is None:  # pragma: no cover
    print("No authentication method configured")
    raise Exception(
        "Please configure authentication or set the LOCAL_AUTH environment "
        "variable to use local auth"
    )

# The settings used in other settings
AUTH_INFO = AUTH_METHODS[auth_method]

# OpenID Connect configuration
OIDC_RP_CLIENT_ID = os.environ.get("OIDC_RP_CLIENT_ID")
OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET")
OIDC_OP_AUTHORIZATION_ENDPOINT = os.environ.get("OIDC_OP_AUTHORIZATION_ENDPOINT")
OIDC_OP_TOKEN_ENDPOINT = os.environ.get("OIDC_OP_TOKEN_ENDPOINT")
OIDC_OP_USER_ENDPOINT = os.environ.get("OIDC_OP_USER_ENDPOINT")
OIDC_OP_JWKS_ENDPOINT = os.environ.get("OIDC_OP_JWKS_ENDPOINT")
OIDC_RP_SIGN_ALGO = os.environ.get("OIDC_RP_SIGN_ALGO")

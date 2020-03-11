from typing import Dict, Any, List, Optional

import os

from django.shortcuts import redirect
from django.urls import path, include

from .settings_external import get


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

auth_method = get("global", "auth_method", "AUTH_METHOD")

if auth_method not in AUTH_METHODS:
    raise Exception(
        "Auth method '%s' is not known. Valid: %s" % (auth_method, AUTH_METHODS.keys())
    )

# The settings used in other settings
AUTH_INFO = AUTH_METHODS[auth_method]

# OpenID Connect configuration
# RP Settings
OIDC_RP_CLIENT_ID = get("oidc.rp", "client_id", "OIDC_RP_CLIENT_ID")
OIDC_RP_CLIENT_SECRET = get("oidc.rp", "client_secret", "OIDC_RP_CLIENT_SECRET")
OIDC_RP_SIGN_ALGO = get("oidc.rp", "sign_algo", "OIDC_RP_SIGN_ALGO")
# OP Info
OIDC_OP_AUTHORIZATION_ENDPOINT = get(
    "oidc.op", "authorization_endpoint", "OIDC_OP_AUTHORIZATION_ENDPOINT"
)
OIDC_OP_TOKEN_ENDPOINT = get("oidc.op", "token_endpoint", "OIDC_OP_TOKEN_ENDPOINT")
OIDC_OP_USER_ENDPOINT = get("oidc.op", "userinfo_endpoint", "OIDC_OP_USER_ENDPOINT")
OIDC_OP_JWKS_ENDPOINT = get("oidc.op", "jwks_endpoint", "OIDC_OP_JWKS_ENDPOINT")

import os

from django.shortcuts import redirect
from django.urls import path, include


def urls_oidc():
    return [
        path(
            'oidc/',
            include('mozilla_django_oidc.urls'),
            name='oidc',
        ),

        path(
            'accounts/login/',
            lambda request: redirect('oidc_authentication_init'),
            name='login',
        ),
    ]


AUTH_METHODS = {
    'oidc': {
        'backends': ('mozilla_django_oidc.auth.OIDCAuthenticationBackend',),
        'installed_apps': ['mozilla_django_oidc'],
        'drf_auth_classes': [
            'mozilla_django_oidc.contrib.drf.OIDCAuthentication',
        ],
        'urlfunc': urls_oidc,
    },
    'local': {
        'backends': (),
        'installed_apps': [],
        'drf_auth_classes': [
            'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
        ],
        'urlfunc': lambda: [
            path('accounts/', include('django.contrib.auth.urls')),
        ],
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'mozilla_django_oidc.contrib.drf.OIDCAuthentication',
    ],
}

auth_method = None

# Try to auto-detect the used auth method
for envvar in os.environ.keys():
    if envvar.startswith('OIDC_'):
        auth_method = 'oidc'

if auth_method is None:
    auth_method = 'local'
    print("No auth configuration variables set, enabling local authentication")

# The settings used in other settings
AUTH_INFO = AUTH_METHODS[auth_method]

# OpenID Connect configuration
OIDC_RP_CLIENT_ID = os.environ.get('OIDC_RP_CLIENT_ID')
OIDC_RP_CLIENT_SECRET = os.environ.get('OIDC_RP_CLIENT_SECRET')
OIDC_OP_AUTHORIZATION_ENDPOINT = os.environ.get('OIDC_RP_ENDPOINT_AUTHORIZATION')
OIDC_OP_TOKEN_ENDPOINT = os.environ.get('OIDC_RP_ENDPOINT_TOKEN')
OIDC_OP_USER_ENDPOINT = os.environ.get('OIDC_RP_ENDPOINT_USER')
OIDC_OP_JWKS_ENDPOINT = os.environ.get('OIDC_RP_ENDPOINT_JWKS')
OIDC_RP_SIGN_ALGO = os.environ.get('OIDC_RP_SIGN_ALGO')

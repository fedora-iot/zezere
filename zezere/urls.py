from django.contrib import admin
from django.urls import path, include

from rest_framework import routers

from zezere import views
from zezere import views_netboot
from zezere import views_portal

router = routers.DefaultRouter()
router.register(r'devices/unowned', views.UnownedDevicesViewSet)

urlpatterns = [
    path(
        '',
        views.index,
    ),
    path(
        'ping/',
        views.ping,
    ),
    path(
        'admin/',
        admin.site.urls,
    ),
    path(
        'accounts/',
        include('django.contrib.auth.urls'),
    ),

    # Portal
    path(
        'accounts/signup/',
        views.SignUp.as_view(),
        name='signup',
    ),
    path(
        'portal/',
        views_portal.index,
    ),
    path(
        'portal/claim/',
        views_portal.claim,
    ),

    # API
    path(
        'api/',
        include(router.urls),
    ),
    path(
        'api-auth/',
        include(
            'rest_framework.urls',
            namespace='rest_framework',
        ),
    ),

    # Netboot
    path(
        'netboot/x64',
        views_netboot.efi_static_server("shimx64.efi"),
    ),
    path(
        'netboot/grubx64.efi',
        views_netboot.efi_static_server('grubx64.efi'),
    ),
    path(
        'netboot//grubx64.efi',
        views_netboot.efi_static_server('grubx64.efi'),
    ),
    path(
        'netboot/grub.cfg',
        views_netboot.static_grub_cfg,
    ),
    path(
        'netboot/grubcfg/<str:mac_addr>',
        views_netboot.dynamic_grub_cfg,
    ),
    path(
        'netboot/kickstart/<str:mac_addr>',
        views_netboot.kickstart,
    ),
    path(
        'netboot/ignition/<str:mac_addr>',
        views_netboot.ignition_cfg,
    ),
    path(
        'netboot/proxydl/<str:mac_addr>/<str:filetype>',
        views_netboot.static_proxy,
    ),
]

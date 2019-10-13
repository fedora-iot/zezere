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
        name='index',
    ),
    path(
        'ping/',
        views.ping,
        name='ping',
    ),
    path(
        'admin/',
        admin.site.urls,
        name='admin',
    ),
    path(
        'accounts/',
        include('django.contrib.auth.urls'),
        name='accounts',
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
        name='portal_index',
    ),
    path(
        'portal/claim/',
        views_portal.claim,
        name='portal_claim',
    ),

    # API
    path(
        'api/',
        include(router.urls),
        name='apis',
    ),
    path(
        'api-auth/',
        include(
            'rest_framework.urls',
            namespace='rest_framework',
        ),
        name='authed_apis',
    ),

    # Netboot
    path(
        'netboot/x64',
        views_netboot.efi_static_server("shimx64.efi"),
        name='netboot_shim',
    ),
    path(
        'netboot/grubx64.efi',
        views_netboot.efi_static_server('grubx64.efi'),
        name='netboot_grub',
    ),
    path(
        'netboot//grubx64.efi',
        views_netboot.efi_static_server('grubx64.efi'),
        name='netboot_grub_double_slash',
    ),
    path(
        'netboot/grub.cfg',
        views_netboot.static_grub_cfg,
        name='netboot_grubcfg_static',
    ),
    path(
        'netboot/grubcfg/<str:mac_addr>',
        views_netboot.dynamic_grub_cfg,
        name='netboot_grubcfg_dynamic',
    ),
    path(
        'netboot/kickstart/<str:mac_addr>',
        views_netboot.kickstart,
        name='netboot_kickstart',
    ),
    path(
        'netboot/ignition/<str:mac_addr>',
        views_netboot.ignition_cfg,
        name='netboot_ignition_cfg',
    ),
    path(
        'netboot/proxydl/<str:mac_addr>/<str:filetype>',
        views_netboot.static_proxy,
        name='netboot_proxydl',
    ),
]

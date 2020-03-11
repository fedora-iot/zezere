from django.contrib import admin
from django.urls import path, include

from rest_framework import routers

from zezere import views
from zezere import views_netboot
from zezere import views_portal
from zezere.settings_auth import AUTH_INFO

router = routers.DefaultRouter()
router.register(r"devices/unowned", views.UnownedDevicesViewSet)

urlpatterns = [
    path("", views.index, name="index"),
    path("ping/", views.ping, name="ping"),
    path("admin/", admin.site.urls, name="admin"),
    # Login/logout stuff
    path("accounts/logout/", views.logout, name="logout"),
    path("accounts/profile/", views.profile, name="profile"),
    path("accounts/signup/", views.SignUp.as_view(), name="signup"),
    # Portal
    path("portal/", views_portal.index, name="portal_index"),
    path("portal/claim/", views_portal.claim, name="portal_claim"),
    path("portal/devices/", views_portal.devices, name="portal_devices"),
    path(
        "portal/devices/runreq/<str:mac_addr>/",
        views_portal.new_runreq,
        name="portal_newrunreq",
    ),
    path(
        "portal/devices/runreq/<str:mac_addr>/clean/",
        views_portal.clean_runreq,
        name="portal_cleanrunreq",
    ),
    path("portal/sshkeys/", views_portal.sshkeys, name="portal_sshkeys"),
    path("portal/sshkeys/add/", views_portal.add_ssh_key, name="portal_sshkeys_add"),
    path(
        "portal/sshkeys/delete/",
        views_portal.remove_ssh_key,
        name="portal_sshkeys_remove",
    ),
    # API
    path("api/", include(router.urls), name="apis"),
    path(
        "api-auth/",
        include("rest_framework.urls", namespace="rest_framework"),
        name="authed_apis",
    ),
    # Netboot
    path("netboot", views_netboot.index, name="netboot_index"),
    path(
        "netboot/<str:arch>/grub.cfg",
        views_netboot.static_grub_cfg,
        name="netboot_grubcfg_static",
    ),
    path(
        "netboot/<str:arch>/grubcfg/<str:mac_addr>",
        views_netboot.dynamic_grub_cfg,
        name="netboot_grubcfg_dynamic",
    ),
    path(
        "netboot/<str:arch>/proxydl/<str:mac_addr>/<str:filetype>",
        views_netboot.static_proxy,
        name="netboot_proxydl",
    ),
    path(
        "netboot/<str:arch>/ignition/<str:mac_addr>",
        views_netboot.ignition_cfg,
        name="netboot_ignition_cfg",
    ),
    path(
        "netboot/kickstart/<str:mac_addr>",
        views_netboot.kickstart,
        name="netboot_kickstart",
    ),
    path(
        "netboot/postboot/<str:mac_addr>",
        views_netboot.postboot,
        name="netboot_postboot",
    ),
    path(
        "netboot/<str:arch>/<str:filetype>",
        views_netboot.arch_file,
        name="netboot_arch_file",
    ),
    path(
        "netboot/<str:arch>//<str:filetype>",
        views_netboot.arch_file,
        name="netboot_arch_file_double_slash",
    ),
] + AUTH_INFO["urlfunc"]()

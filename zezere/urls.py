from django.contrib import admin
from django.urls import path, include

from rest_framework import routers

from zezere import views
from zezere import views_netboot

router = routers.DefaultRouter()
router.register(r'devices/unowned', views.UnownedDevicesViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    path('netboot/x64', views_netboot.efi_static_server("shimx64.efi")),
    path('netboot/grubx64.efi', views_netboot.efi_static_server('grubx64.efi')),
    path('netboot//grubx64.efi', views_netboot.efi_static_server('grubx64.efi')),
    path('netboot/grub.cfg', views_netboot.static_grub_cfg),
    path('netboot/grubcfg/<str:mac_addr>/', views_netboot.dynamic_grub_cfg),
    path('netboot/kickstart/<str:mac_addr>/', views_netboot.kickstart),
    path('netboot/ignition/<str:mac_addr>/', views_netboot.ignition_cfg),
    path('netboot/proxydl/<str:mac_addr>/<str:filetype>', views_netboot.static_proxy),
]
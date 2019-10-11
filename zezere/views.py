from django.contrib.auth.models import User, Group
from django.http import FileResponse, HttpResponse
from rest_framework import viewsets

from zezere.models import Device, UnownedDeviceSerializer


def index(request):
    return HttpResponse(
        "Please visit the portal",
    )


class UnownedDevicesViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows unowned devices to be seen.
    """
    queryset = Device.objects.filter(owner__isnull=True)
    serializer_class = UnownedDeviceSerializer

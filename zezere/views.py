from django.contrib.auth import logout
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import redirect
from rest_framework import viewsets

from zezere.models import Device, UnownedDeviceSerializer


def index(request):
    return redirect("/portal/")


def ping(request):
    return HttpResponse("Pong")


def login(request):
    return redirect('oidc_authentication_init')


def logout(request):
    logout(request)
    return redirect('index')


class UnownedDevicesViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows unowned devices to be seen.
    """
    queryset = Device.objects.filter(owner__isnull=True)
    serializer_class = UnownedDeviceSerializer

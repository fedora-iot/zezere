from django.contrib.auth import logout as django_logout
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
    django_logout(request)
    return redirect('index')


def profile(request):
    return redirect('/')


class UnownedDevicesViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows unowned devices to be seen.
    """
    queryset = Device.objects.filter(owner__isnull=True)
    serializer_class = UnownedDeviceSerializer

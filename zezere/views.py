from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.http import FileResponse, HttpResponse
from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import redirect
from rest_framework import viewsets

from zezere.models import Device, UnownedDeviceSerializer


def index(request):
    return redirect("/portal/")


def ping(request):
    return HttpResponse("Pong")


class SignUp(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'


class UnownedDevicesViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows unowned devices to be seen.
    """
    queryset = Device.objects.filter(owner__isnull=True)
    serializer_class = UnownedDeviceSerializer

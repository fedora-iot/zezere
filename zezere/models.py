from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User, Group

from rest_framework import serializers

class RunRequest(models.Model):
    pass

class Device(models.Model):
    def clean_mac_address(self):
        return self.cleaned_data['mac_address'].upper()

    mac_address = models.CharField(
        "Device MAC Address",
        max_length=20,
        validators=[RegexValidator("^([0-9A-F]{2}[:]){5}([0-9A-F]{2})$")],
    )
    hostname = models.CharField(
        "Device hostname",
        max_length=200,
        default=None,
        blank=True,
        null=True,
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        default=None,
        blank=True,
        null=True,
    )
    last_ip_address = models.CharField(
        "Last check-in IP address",
        max_length=50,
    )
    run_request = models.ForeignKey(
        RunRequest,
        on_delete=models.SET_NULL,
        default=None,
        blank=True,
        null=True,
    )

class UnownedDeviceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Device
        fields = ['mac_address']
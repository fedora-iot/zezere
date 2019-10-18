from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import RegexValidator, URLValidator
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rules.contrib.models import RulesModel
from rest_framework import serializers

from . import rules
from .runreqs import (
    validate_runreq_autoid,
    generate_auto_runreq,
)


class RunRequest(RulesModel):
    auto_generated_id = models.CharField(
        "Auto generated ID",
        null=True,
        blank=True,
        unique=True,
        max_length=80,
        validators=[validate_runreq_autoid],
    )
    kernel_url = models.CharField(
        "Kernel URL",
        null=True,
        blank=True,
        max_length=255,
        validators=[URLValidator],
    )
    kernel_cmd = models.CharField(
        "Kernel Command Line",
        null=True,
        blank=True,
        max_length=255,
    )
    initrd_url = models.CharField(
        "InitRD URL",
        null=True,
        blank=True,
        max_length=255,
        validators=[URLValidator],
    )

    @property
    def is_auto_generated(self):
        return self.auto_generated_id is not None

    def __str__(self):
        if self.is_auto_generated:
            return "Auto: %s" % self.auto_generated_id
        return "Unnamed runrequest"

    def clean(self):
        if self.is_auto_generated:
            self.kernel_url = None
            self.kernel_cmd = None
            self.initrd_url = None
        else:
            if not self.kernel_url:
                raise ValidationError(_(
                    "For non-auto runreqs, kernel URL is required"))


models.signals.post_init.connect(generate_auto_runreq, sender=RunRequest)


class Device(RulesModel):
    class Meta:
        rules_permissions = {
            "add": rules.rules.is_staff,
            "view": rules.owns_device | rules.can_claim,
            "change": rules.owns_device,
            "delete": rules.owns_device,

            "provision": rules.owns_device,
            "claim": rules.can_claim,
        }

    def clean_mac_address(self):
        return self.cleaned_data['mac_address'].upper()

    mac_address = models.CharField(
        "Device MAC Address",
        max_length=20,
        validators=[RegexValidator("^([0-9A-F]{2}[:]){5}([0-9A-F]{2})$")],
    )
    architecture = models.CharField(
        "Architecture",
        max_length=50,
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


def device_getter(request, mac_addr):
    return get_object_or_404(Device, mac_address=mac_addr.upper())


class UnownedDeviceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Device
        fields = ['mac_address']

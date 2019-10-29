import json

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


class AttrDict(dict):
    def __getattr__(self, name):
        ret = self[name]
        if isinstance(ret, dict):
            ret = AttrDict(ret)
        return ret


class RunRequest(RulesModel):
    TYPE_ONLINE_KERNEL = 'ok'
    TYPE_EFI = 'ef'

    TYPE_CHOICES = [
        (TYPE_ONLINE_KERNEL, "Online kernel"),
        (TYPE_EFI, "EFI application"),
    ]

    auto_generated_id = models.CharField(
        "Auto generated ID",
        null=True,
        blank=True,
        unique=True,
        max_length=80,
        validators=[validate_runreq_autoid],
    )
    type = models.CharField(
        "RunRequest type",
        max_length=2,
        choices=TYPE_CHOICES,
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

    efi_application = models.CharField(
        "EFI Application path",
        null=True,
        blank=True,
        max_length=255,
    )

    raw_settings = models.TextField(
        "JSON-encoded settings",
        null=True,
        blank=True,
    )

    _auto_generated_settings = None
    _settings = None

    @property
    def settings(self):
        if self._settings is None:
            self._settings = json.loads(self.raw_settings)
        return AttrDict(self._settings)

    @property
    def is_auto_generated(self):
        return self.auto_generated_id is not None

    @property
    def typestr(self):
        if self.type == RunRequest.TYPE_ONLINE_KERNEL:
            return "Online kernel"
        elif self.type == RunRequest.TYPE_EFI:
            return "EFI"

    def __str__(self):
        if self.is_auto_generated:
            return "Auto: %s: %s" % (self.typestr, self.auto_generated_id)
        return "Unnamed runrequest"

    def clean(self):
        if self.is_auto_generated:
            raise ValidationError(_(
                "Automatic generated runreq can't be saved"))
        else:
            if self.type == RunRequest.TYPE_ONLINE_KERNEL:
                if not self.kernel_url:
                    raise ValidationError(_(
                        "For online kernel runreqs, kernel URL is required"))
                if not self.initrd_url:
                    raise ValidationError(_(
                        "For online kernel runreqs, initrd URL is required"))
            elif self.type == RunRequest.TYPE_EFI:
                if not self.efi_application:
                    raise ValidationError(_(
                        "For EFI runreqs, EFI app is required"))
            else:
                raise ValidationError(_(
                    "Invalid runreq type"))


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

    def __str__(self):
        return "Device %s" % self.mac_address

    def clean_mac_address(self):
        return self.cleaned_data['mac_address'].upper()

    mac_address = models.CharField(
        "Device MAC Address",
        max_length=20,
        unique=True,
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

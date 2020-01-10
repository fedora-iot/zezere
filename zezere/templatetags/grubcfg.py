from django import template
from django.utils.safestring import mark_safe

from ..runreqs import generate_runreq_grubcfg

register = template.Library()


@register.simple_tag(takes_context=True)
def render_runreq_grubcfg(context, device):
    return mark_safe(
        generate_runreq_grubcfg(context["request"], device, device.run_request)
    )

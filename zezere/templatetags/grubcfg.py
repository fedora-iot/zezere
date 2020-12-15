from django import template
from django.utils.safestring import mark_safe

from ..runreqs import generate_runreq_grubcfg

register = template.Library()


@register.simple_tag(takes_context=True)
def render_runreq_grubcfg(context, device):
    # nosec justification: This is a very minimal template.
    # For those parts where data is injected, it is data injected by the owner of the
    #  device.
    return mark_safe(  # nosec
        generate_runreq_grubcfg(context["request"], device, device.run_request)
    )

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .number_sequence import NumberSequenceAdmin

admin.site.site_header = _("Argus administration")
admin.site.site_title = _("Argus admin")
admin.site.index_title = _("IT asset management")

__all__ = ["NumberSequenceAdmin"]

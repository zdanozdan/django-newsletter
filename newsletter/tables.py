import django_tables2 as tables
from django_tables2.utils import A  # alias for Accessor
from django.utils.translation import ugettext_lazy as _

class MessagesTable(tables.Table):
    title = tables.LinkColumn('newsletter_detail', args=[A('slug')], verbose_name=_("Newsletter"))
    date_create = tables.Column(verbose_name=_('Date'))


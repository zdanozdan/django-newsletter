from django import template
import html2text

register = template.Library()

@register.filter(name='convert2text')
def convert(html):
    h = html2text.HTML2Text()
    h.unicode_snob = True
    h.body_width = 234
    h.links_each_paragraph=True
    h.ignore_links=True
    return h.handle(html)


"""``{% static_v %}``: a static URL stamped with the file's mtime.

The dev server sends no cache validators for static files, so browsers keep
serving a stale style.css after every pull until someone hard-refreshes. The
stamp changes whenever the file does, which is exactly when the cache should
be dropped.
"""
import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def static_v(path):
    url = static(path)
    absolute = finders.find(path)
    if not absolute:
        return url
    stamp = int(os.path.getmtime(absolute))
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}v={stamp}"

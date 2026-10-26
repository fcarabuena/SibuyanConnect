from functools import reduce
from operator import or_

from django.conf import settings
from django.db.models import Q


def multilingual_q(fields, words):
    """OR of `<field>_<lang>__icontains=word` over every language, field and word.

    modeltranslation rewrites `name__icontains` to the active language only,
    which misses residents who search in English while browsing in Filipino.
    """
    if isinstance(words, str):
        words = [words]
    terms = [
        Q(**{f"{field}_{code}__icontains": word})
        for word in words
        for field in fields
        for code, _ in settings.LANGUAGES
    ]
    return reduce(or_, terms) if terms else Q()

from django.conf import settings
from django.utils import translation

LANG_SESSION_KEY = "lang"
LANG_COOKIE = "sc_lang"


class SiteLanguageMiddleware:
    """Activate the visitor's chosen language (English, Filipino or Romblomanon).

    Django's LocaleMiddleware only accepts languages that ship a compiled
    catalog, and Romblomanon does not, so we activate the choice directly.
    Untranslated strings fall back to English.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.codes = {code for code, _ in settings.LANGUAGES}

    def __call__(self, request):
        lang = request.session.get(LANG_SESSION_KEY) or request.COOKIES.get(LANG_COOKIE)
        if lang not in self.codes:
            lang = settings.LANGUAGE_CODE
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        response.headers.setdefault("Content-Language", lang)
        translation.deactivate()
        return response

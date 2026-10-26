from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Core: towns, offices, alerts"

    def ready(self):
        # Django has no built-in metadata for Filipino or Romblomanon; register it
        # so {% get_language_info %} and the language switcher work.
        from django.conf.locale import LANG_INFO

        LANG_INFO.setdefault("fil", {"bidi": False, "code": "fil", "name": "Filipino", "name_local": "Filipino"})
        LANG_INFO.setdefault("rol", {"bidi": False, "code": "rol", "name": "Romblomanon", "name_local": "Romblomanon"})

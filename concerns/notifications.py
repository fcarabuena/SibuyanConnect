from django.conf import settings

from core.notify import send_email, send_sms


def _link(concern, request=None):
    path = concern.get_absolute_url()
    return request.build_absolute_uri(path) if request else path


def notify_received(concern, request=None):
    link = _link(concern, request)
    office = concern.office or "the Mayor's Office"
    send_email(
        concern.email,
        f"[SibuyanConnect] Concern received: {concern.ticket_number}",
        f"Hello {concern.name},\n\n"
        f"We received your concern \"{concern.subject}\". Your ticket number is "
        f"{concern.ticket_number}. It has been routed to: {office}.\n\n"
        f"Track it and message the office here (keep this link private):\n{link}\n\n"
        f"- SibuyanConnect",
    )
    send_sms(concern.phone, f"SibuyanConnect: concern {concern.ticket_number} received.")
    if concern.office and concern.office.email:
        send_email(
            concern.office.email,
            f"[SibuyanConnect] New concern {concern.ticket_number}: {concern.subject}",
            f"A new {concern.category} concern was filed in {concern.barangay}.\n"
            f"Open it in the CMS: /admin/concerns/concern/{concern.pk}/change/",
        )


def notify_status(concern, request=None):
    send_email(
        concern.email,
        f"[SibuyanConnect] {concern.ticket_number} is now {concern.get_status_display()}",
        f"Hello {concern.name},\n\nYour concern \"{concern.subject}\" is now: "
        f"{concern.get_status_display()}.\n\nDetails: {_link(concern, request)}\n\n- SibuyanConnect",
    )
    send_sms(concern.phone, f"SibuyanConnect: {concern.ticket_number} is now {concern.get_status_display()}.")


def notify_reply(concern, message, request=None):
    send_email(
        concern.email,
        f"[SibuyanConnect] New reply on {concern.ticket_number}",
        f"Hello {concern.name},\n\nThe {concern.office} replied:\n\n{message.body}\n\n"
        f"Reply here: {_link(concern, request)}\n\n- SibuyanConnect",
    )

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext as _

from core.models import Barangay
from core.town import get_current_town

from .forms import ConcernForm, MessageForm, TrackForm
from .models import Concern, ConcernCategory, ConcernMessage
from .notifications import notify_received


def new_concern(request):
    initial = {"municipality": get_current_town(request)}
    if request.user.is_authenticated:
        initial.update(name=request.user.get_full_name() or request.user.username, email=request.user.email)
    if request.GET.get("category"):
        initial["category"] = ConcernCategory.objects.filter(slug=request.GET["category"]).first()
    if request.GET.get("description"):
        initial["description"] = request.GET["description"][:2000]
    form = ConcernForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        concern = form.save(commit=False)
        concern.consent_given_at = timezone.now()
        concern.source = request.POST.get("source", "web")[:12]
        if request.user.is_authenticated:
            concern.citizen = request.user
        concern.save()
        concern.messages.create(
            sender=ConcernMessage.Sender.SYSTEM,
            body=_("Concern received and routed to %(office)s.") % {"office": concern.office or _("the Mayor's Office")},
        )
        notify_received(concern, request)
        messages.success(request, _("Thank you. Your ticket number is %(n)s.") % {"n": concern.ticket_number})
        return redirect(concern)
    return render(request, "concerns/new.html", {
        "form": form,
        "categories": ConcernCategory.objects.all(),
        "barangay_towns": {str(pk): town for pk, town in Barangay.objects.values_list("pk", "municipality_id")},
    })


def ticket(request, ticket_number, token):
    concern = get_object_or_404(
        Concern.objects.select_related("office", "barangay", "category", "municipality"),
        ticket_number=ticket_number,
    )
    if not constant_time_compare(concern.access_token, token):
        raise Http404
    form = MessageForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        concern.messages.create(sender=ConcernMessage.Sender.CITIZEN, body=form.cleaned_data["body"])
        messages.success(request, _("Message sent to the office."))
        return redirect(concern)
    return render(request, "concerns/ticket.html", {
        "concern": concern,
        "thread": concern.messages.filter(is_internal=False),
        "form": form,
    })


def track(request):
    form = TrackForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        number = form.cleaned_data["ticket_number"].strip().upper()
        contact = form.cleaned_data["contact"].strip()
        concern = Concern.objects.filter(ticket_number=number).filter(
            Q(email__iexact=contact) | Q(phone=contact.replace(" ", ""))
            | Q(phone=contact)
        ).first()
        if concern:
            return redirect(concern)
        form.add_error(None, _("No concern matches that ticket number and contact detail."))
    return render(request, "concerns/track.html", {"form": form})


@login_required
def my_concerns(request):
    return render(request, "concerns/mine.html", {
        "concerns": request.user.concerns.select_related("office", "category"),
    })

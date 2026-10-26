from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.town import get_current_town

from .forms import EligibilityForm
from .models import Program, ProgramSchedule


def program_list(request):
    town = get_current_town(request)
    programs = Program.objects.filter(is_published=True).for_town(town)
    kind = request.GET.get("kind")
    if kind:
        programs = programs.filter(kind=kind)
    schedules = (
        ProgramSchedule.objects.for_town(town)
        .filter(Q(closes_on__gte=timezone.localdate()) | Q(closes_on__isnull=True))
        .select_related("program")[:6]
    )
    return render(request, "programs/list.html", {
        "programs": programs,
        "kinds": Program.Kind.choices,
        "active_kind": kind,
        "schedules": schedules,
    })


def program_detail(request, pk, slug):
    program = get_object_or_404(Program, pk=pk, is_published=True)
    if program.slug != slug:
        return redirect(program, permanent=True)
    Program.objects.filter(pk=pk).update(view_count=F("view_count") + 1)
    return render(request, "programs/detail.html", {
        "program": program,
        "schedules": program.schedules.all(),
    })


def eligibility(request):
    form = EligibilityForm(request.GET or None, initial={"town": get_current_town(request)})
    results = None
    if request.GET and form.is_valid():
        profile = form.profile()
        programs = Program.objects.filter(is_published=True).for_town(profile.get("town"))
        results = []
        for program in programs:
            ok, reasons = program.evaluate(profile)
            if ok:
                results.append({"program": program, "reasons": reasons})
    template = "programs/_results.html" if request.headers.get("HX-Request") else "programs/eligibility.html"
    return render(request, template, {"form": form, "results": results})

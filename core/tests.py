"""End-to-end tests for the prototype, run against the SAMPLE fixture.

    python manage.py test
"""
from io import BytesIO, StringIO

from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image

from concerns.models import Concern, ConcernCategory, StatusChange
from core.models import Barangay, Municipality, Office, StaffProfile
from news.models import Post
from programs.models import Program
from services.models import Service

TEMP_MEDIA = override_settings(MEDIA_ROOT="test-media-tmp")


class SampleDataTestCase(TestCase):
    fixtures = ["sample_data"]

    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", stdout=StringIO())
        cls.mag = Municipality.objects.get(code="MAG")
        cls.sfe = Municipality.objects.get(code="SFE")


class PublicPagesTests(SampleDataTestCase):
    def test_pages_render(self):
        service = Service.objects.first()
        program = Program.objects.first()
        post = Post.objects.first()
        urls = [
            "/", "/services/", service.get_absolute_url(), f"/services/{service.pk}/checklist/",
            "/programs/", program.get_absolute_url(), "/programs/eligibility/?age=30",
            "/concerns/new/", "/concerns/track/", "/news/", post.get_absolute_url(), "/news/feed/",
            "/transport/", "/emergency/", "/assistant/", "/privacy/", "/offline/",
            "/manifest.webmanifest", "/sw.js", "/accounts/login/", "/accounts/signup/",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_service_worker_precaches_services(self):
        body = self.client.get("/sw.js").content.decode()
        self.assertIn(Service.objects.first().get_absolute_url(), body)
        self.assertIn("/emergency/", body)

    def test_language_switch_shows_filipino_content(self):
        service = Service.objects.filter(name_fil__startswith="Pagpaparehistro").first()
        self.client.post("/language/", {"language": "fil", "next": "/"})
        response = self.client.get(service.get_absolute_url())
        self.assertContains(response, service.name_fil)
        self.assertEqual(response["Content-Language"], "fil")

    def test_romblomanon_falls_back_to_english(self):
        service = Service.objects.filter(name_rol="").first()
        self.client.post("/language/", {"language": "rol"})
        self.assertContains(self.client.get(service.get_absolute_url()), service.name_en)

    def test_town_switch_filters_services(self):
        self.client.get("/town/", {"town": "magdiwang"})
        services = self.client.get("/services/").context["services"]
        self.assertTrue(services)
        self.assertTrue(all(s.municipality_id in (self.mag.pk, None) for s in services))

    def test_service_search_matches_any_language(self):
        response = self.client.get("/services/", {"q": "cedula"})
        self.assertTrue(response.context["services"])
        self.client.post("/language/", {"language": "fil"})
        self.assertTrue(self.client.get("/services/", {"q": "senior"}).context["services"])

    def test_service_view_is_counted(self):
        service = Service.objects.first()
        before = service.view_count
        self.client.get(service.get_absolute_url())
        service.refresh_from_db()
        self.assertEqual(service.view_count, before + 1)


class ChecklistTests(SampleDataTestCase):
    def test_conditional_requirements(self):
        service = Service.objects.get(municipality=self.mag, slug="birth-registration-on-time-and-late")
        questions = service.requirement_questions()
        late = questions.index("Is it more than 30 days after the birth (late registration)?")

        on_time = self.client.get(f"/services/{service.pk}/checklist/").context["items"]
        self.assertFalse(any("PSA" in r.text for r in on_time))

        late_items = self.client.get(f"/services/{service.pk}/checklist/", {f"q{late}": "yes"}).context["items"]
        self.assertTrue(any("Negative certification" in r.text for r in late_items))
        self.assertGreater(len(late_items), len(on_time))

    def test_htmx_returns_partial(self):
        service = Service.objects.first()
        response = self.client.get(f"/services/{service.pk}/checklist/", HTTP_HX_REQUEST="true")
        self.assertNotContains(response, "<html")


class EligibilityTests(SampleDataTestCase):
    def names(self, **params):
        response = self.client.get("/programs/eligibility/", params)
        return {r["program"].name for r in response.context["results"]}

    def test_senior(self):
        names = self.names(age=67)
        self.assertIn("Social Pension for Indigent Senior Citizens", names)
        self.assertNotIn("Pantawid Pamilyang Pilipino Program (4Ps)", names)

    def test_low_income_student_in_town(self):
        names = self.names(town=self.mag.pk, age=19, income="10000", student="on")
        self.assertIn("Magdiwang municipal scholarship (sample)", names)
        self.assertNotIn("San Fernando municipal scholarship (sample)", names)

    def test_income_limit(self):
        self.assertNotIn("Magdiwang municipal scholarship (sample)",
                         self.names(town=self.mag.pk, age=19, income="40000", student="on"))

    def test_flags(self):
        names = self.names(age=40, fisherfolk="on", listahanan_poor="on")
        self.assertIn("BFAR fisherfolk support", names)
        self.assertIn("Pantawid Pamilyang Pilipino Program (4Ps)", names)
        self.assertNotIn("DA farm inputs and cash assistance", names)


@TEMP_MEDIA
class ConcernFlowTests(SampleDataTestCase):
    def payload(self, **extra):
        data = {
            "municipality": self.mag.pk,
            "barangay": Barangay.objects.get(municipality=self.mag, name="Poblacion").pk,
            "category": ConcernCategory.objects.get(slug="road").pk,
            "subject": "Broken road",
            "description": "There is a big hole.",
            "name": "Juan Tester",
            "email": "juan@example.com",
            "phone": "",
            "consent": "on",
        }
        data.update(extra)
        return data

    def tearDown(self):
        import shutil
        shutil.rmtree("test-media-tmp", ignore_errors=True)

    def test_submit_routes_and_notifies(self):
        response = self.client.post("/concerns/new/", self.payload())
        concern = Concern.objects.latest("pk")
        self.assertRedirects(response, concern.get_absolute_url())
        self.assertTrue(concern.ticket_number.startswith("SC-MAG-"))
        self.assertEqual(concern.office, Office.objects.get(municipality=self.mag, kind=Office.Kind.ENGINEERING))
        self.assertIsNotNone(concern.consent_given_at)
        self.assertEqual(len(mail.outbox), 2)  # citizen + office
        self.assertIn(concern.ticket_number, mail.outbox[0].subject)

    def test_consent_required(self):
        data = self.payload()
        del data["consent"]
        self.client.post("/concerns/new/", data)
        self.assertFalse(Concern.objects.filter(subject="Broken road").exists())

    def test_contact_required(self):
        response = self.client.post("/concerns/new/", self.payload(email=""))
        self.assertFalse(Concern.objects.filter(subject="Broken road").exists())
        self.assertContains(response, "email or a mobile number")

    def test_barangay_must_match_town(self):
        other = Barangay.objects.get(municipality=self.sfe, name="Taclobo")
        self.client.post("/concerns/new/", self.payload(barangay=other.pk))
        self.assertFalse(Concern.objects.filter(subject="Broken road").exists())

    def test_photo_is_compressed(self):
        buf = BytesIO()
        Image.new("RGB", (3000, 2000), "green").save(buf, "PNG")
        photo = SimpleUploadedFile("road.png", buf.getvalue(), content_type="image/png")
        self.client.post("/concerns/new/", self.payload(photo=photo))
        concern = Concern.objects.latest("pk")
        with Image.open(concern.photo.path) as img:
            self.assertEqual(img.format, "JPEG")
            self.assertLessEqual(max(img.size), 1280)

    def test_ticket_requires_token_and_accepts_messages(self):
        self.client.post("/concerns/new/", self.payload())
        concern = Concern.objects.latest("pk")
        bad = f"/concerns/t/{concern.ticket_number}/wrongtoken/"
        self.assertEqual(self.client.get(bad).status_code, 404)
        self.client.post(concern.get_absolute_url(), {"body": "Any update?"})
        self.assertTrue(concern.messages.filter(sender="citizen", body="Any update?").exists())

    def test_track_lookup(self):
        self.client.post("/concerns/new/", self.payload())
        concern = Concern.objects.latest("pk")
        response = self.client.post("/concerns/track/", {"ticket_number": concern.ticket_number.lower(),
                                                         "contact": "JUAN@example.com"})
        self.assertRedirects(response, concern.get_absolute_url())
        response = self.client.post("/concerns/track/", {"ticket_number": concern.ticket_number,
                                                         "contact": "someone@else.com"})
        self.assertEqual(response.status_code, 200)

    def test_signed_in_citizen_sees_own_concerns(self):
        user = User.objects.create_user("citizen", password="x-pass-12345")
        self.client.force_login(user)
        self.client.post("/concerns/new/", self.payload())
        self.assertContains(self.client.get("/concerns/mine/"), "Broken road")


class AdminTests(SampleDataTestCase):
    def setUp(self):
        call_command("create_demo_staff", force=True, stdout=StringIO())

    def test_department_staff_only_see_their_office(self):
        self.client.force_login(User.objects.get(username="mag_engineering"))
        response = self.client.get("/admin/concerns/concern/")
        self.assertEqual(response.status_code, 200)
        office = StaffProfile.objects.get(user__username="mag_engineering").office
        shown = response.context["cl"].queryset
        self.assertTrue(all(c.office_id == office.pk for c in shown))

    def test_municipal_admin_scoped_to_town(self):
        self.client.force_login(User.objects.get(username="mag_admin"))
        shown = self.client.get("/admin/services/service/").context["cl"].queryset
        self.assertTrue(shown.exists())
        self.assertTrue(all(s.municipality_id == self.mag.pk for s in shown))

    def test_staff_reply_and_status_change(self):
        concern = Concern.objects.filter(municipality=self.mag, status="received").first() or \
            Concern.objects.filter(municipality=self.mag).first()
        self.client.force_login(User.objects.get(username="superadmin"))
        url = f"/admin/concerns/concern/{concern.pk}/change/"
        form = self.client.get(url).context["adminform"].form
        data = {k: v for k, v in form.initial.items() if v is not None and k in form.fields}
        data.update({
            "status": "in_progress", "priority": "normal",
            "municipality": concern.municipality_id, "barangay": concern.barangay_id,
            "category": concern.category_id, "office": concern.office_id or "", "assigned_to": "",
            "messages-TOTAL_FORMS": "1", "messages-INITIAL_FORMS": "0",
            "messages-MIN_NUM_FORMS": "0", "messages-MAX_NUM_FORMS": "1000",
            "messages-0-body": "We will fix it this week.", "messages-0-concern": concern.pk,
            "status_changes-TOTAL_FORMS": "0", "status_changes-INITIAL_FORMS": "0",
            "status_changes-MIN_NUM_FORMS": "0", "status_changes-MAX_NUM_FORMS": "1000",
        })
        data.pop("photo", None)
        mail.outbox.clear()
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302, getattr(response, "context", None) and
                         response.context["adminform"].form.errors)
        concern.refresh_from_db()
        self.assertEqual(concern.status, "in_progress")
        self.assertTrue(StatusChange.objects.filter(concern=concern, to_status="in_progress").exists())
        self.assertTrue(concern.messages.filter(sender="staff", body="We will fix it this week.").exists())
        self.assertEqual(len(mail.outbox), 2)  # status update + reply

    def test_analytics(self):
        self.client.force_login(User.objects.get(username="superadmin"))
        response = self.client.get("/admin/analytics/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["by_office"])
        self.assertTrue(any(r["avg_hours"] for r in response.context["by_office"]))


class AssistantTests(SampleDataTestCase):
    def ask(self, q, lang="en"):
        self.client.post("/language/", {"language": lang})
        return self.client.post("/assistant/", {"q": q}).context["result"]

    def test_faq_answers_in_each_language(self):
        self.assertEqual(self.ask("How do I get a cedula?")["layer"], "faq")
        result = self.ask("Paano kumuha ng cedula?", "fil")
        self.assertEqual(result["layer"], "faq")
        self.assertIn("Pumunta", result["answer"])
        self.assertEqual(self.ask("Pauno ako makakuha it cedula?", "rol")["layer"], "faq")

    def test_handoff_when_unknown(self):
        result = self.ask("zxqv blorf")
        self.assertTrue(result["handoff"])
        self.assertEqual(result["layer"], "none")

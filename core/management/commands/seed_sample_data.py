"""Build the SAMPLE data set for the prototype and (optionally) dump it as a fixture.

    python manage.py seed_sample_data --flush --dump fixtures/sample_data.json

Everything created here is SAMPLE DATA. Barangay names and national laws/programs
are real; office contacts, phone numbers, fees, schedules, names of people and
businesses are placeholders that each LGU must replace before launch.
Romblomanon text is a draft that needs review by a native speaker.
"""
from datetime import time, timedelta
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from assistant.models import FAQEntry
from civic.models import EnvironmentUpdate, Official, PublicDocument
from concerns.models import Concern, ConcernCategory, ConcernMessage, StatusChange
from core.models import Alert, Barangay, Municipality, Office
from emergency.models import EvacuationCenter, Hotline, PreparednessGuide
from marketplace.models import JobPosting, Listing
from news.models import Event, Post
from programs.models import Program, ProgramSchedule
from services.models import Service, ServiceCategory, ServiceRequirement, ServiceStep
from tourism.models import Attraction, Business, ClimbAdvisory, TravelRule
from transport.models import JeepneySchedule, Route, TricycleFare, Trip

SAMPLE_APPS = ["core", "services", "programs", "concerns", "news", "tourism", "transport",
               "emergency", "marketplace", "civic", "assistant"]


def tr(field, en, fil="", rol=""):
    """kwargs for a translated field in English, Filipino and (draft) Romblomanon."""
    return {f"{field}_en": en, f"{field}_fil": fil, f"{field}_rol": rol}


TOWNS = [
    {
        "name": "Magdiwang", "code": "MAG", "lat": "12.4833", "lon": "122.5167", "order": 1,
        "tagline": tr("tagline", "Gateway to Mt. Guiting-Guiting",
                      "Pintuan patungong Bundok Guiting-Guiting",
                      "Puertahan pakadto sa Bukid Guiting-Guiting"),
        "barangays": ["Agsao", "Agutay", "Ambulong", "Dulangan", "Ipil", "Jao-Asan",
                      "Poblacion", "Silum", "Tampayan"],
    },
    {
        "name": "San Fernando", "code": "SFE", "lat": "12.3000", "lon": "122.6000", "order": 2,
        "tagline": tr("tagline", "Home of Cresta de Gallo and Cantingas River",
                      "Tahanan ng Cresta de Gallo at Ilog Cantingas",
                      "Puloy-an it Cresta de Gallo kag Suba it Cantingas"),
        "barangays": ["Agtiwa", "Azagra", "Campalingo", "Canjalon", "España", "Mabini", "Mabulo",
                      "Otod", "Panangcalan", "Pili", "Poblacion", "Taclobo"],
    },
    {
        "name": "Cajidiocan", "code": "CAJ", "lat": "12.3667", "lon": "122.6833", "order": 3,
        "tagline": tr("tagline", "The eastern shore of Sibuyan",
                      "Ang silangang baybayin ng Sibuyan",
                      "Ang sidlangan nga baybay it Sibuyan"),
        "barangays": ["Alibagon", "Cambajao", "Cambalo", "Cambijang", "Cantagda", "Danao", "Gutivan",
                      "Lico", "Lumbang Este", "Lumbang Weste", "Marigondon", "Poblacion", "Sugod",
                      "Taguilos"],
    },
]

OFFICES = [
    (Office.Kind.MAYOR, "Office of the Municipal Mayor", "Municipal Hall, 2nd floor"),
    (Office.Kind.MDRRMO, "Municipal Disaster Risk Reduction and Management Office", "MDRRMO Operations Center"),
    (Office.Kind.MSWDO, "Municipal Social Welfare and Development Office", "Municipal Hall, ground floor"),
    (Office.Kind.MENRO, "Municipal Environment and Natural Resources Office", "Municipal Hall annex"),
    (Office.Kind.ENGINEERING, "Municipal Engineering Office", "Municipal Hall annex"),
    (Office.Kind.HEALTH, "Municipal Health Office / Rural Health Unit", "Rural Health Unit building"),
    (Office.Kind.AGRICULTURE, "Municipal Agriculture Office", "Municipal Hall annex"),
    (Office.Kind.CIVIL_REGISTRY, "Office of the Municipal Civil Registrar", "Municipal Hall, ground floor"),
    (Office.Kind.TREASURY, "Office of the Municipal Treasurer", "Municipal Hall, ground floor"),
    (Office.Kind.BPLO, "Business Permits and Licensing Office", "Municipal Hall, ground floor"),
    (Office.Kind.TOURISM, "Municipal Tourism Office", "Municipal Hall, 2nd floor"),
    (Office.Kind.OSCA, "Office of Senior Citizens Affairs", "Municipal Hall, ground floor"),
    (Office.Kind.PDAO, "Persons with Disability Affairs Office", "Municipal Hall, ground floor"),
]


class Command(BaseCommand):
    help = "Create SAMPLE data for all three towns (and optionally dump it to a fixture)."

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="Delete existing content first")
        parser.add_argument("--dump", metavar="PATH", help="Write a fixture of the sample data to PATH")

    def handle(self, *args, **opts):
        with transaction.atomic():
            if opts["flush"]:
                for model in [ConcernMessage, StatusChange, Concern, Trip, Route, JeepneySchedule, TricycleFare,
                              ProgramSchedule, Program, ServiceStep, ServiceRequirement, Service, ServiceCategory,
                              ConcernCategory, Post, Event, Alert, Hotline, EvacuationCenter, PreparednessGuide,
                              ClimbAdvisory, Attraction, Business, TravelRule, Listing, JobPosting,
                              PublicDocument, Official, EnvironmentUpdate, FAQEntry, Office, Barangay, Municipality]:
                    model.objects.all().delete()
            self.today = timezone.localdate()
            self.now = timezone.now()
            self.towns = self.make_towns()
            self.make_services()
            self.make_programs()
            self.make_concerns()
            self.make_news_and_alerts()
            self.make_transport()
            self.make_emergency()
            self.make_tourism()
            self.make_market_and_civic()
            self.make_faq()
        self.stdout.write(self.style.SUCCESS("Sample data created."))
        if opts["dump"]:
            with open(opts["dump"], "w", encoding="utf-8") as fh:
                call_command("dumpdata", *SAMPLE_APPS, exclude=["assistant.assistantquery", "core.staffprofile",
                                                               "core.alertsubscription"],
                             indent=1, stdout=fh, natural_foreign=False)
            self.stdout.write(self.style.SUCCESS(f"Fixture written to {opts['dump']}"))

    # ------------------------------------------------------------------ towns
    def make_towns(self):
        towns = {}
        for i, t in enumerate(TOWNS, start=1):
            town = Municipality.objects.create(
                name=t["name"], slug=slugify(t["name"]), code=t["code"], order=t["order"],
                latitude=Decimal(t["lat"]), longitude=Decimal(t["lon"]), **t["tagline"],
                **tr("description", f"Municipality of {t['name']}, Sibuyan Island, Province of Romblon.",
                     f"Bayan ng {t['name']}, Isla ng Sibuyan, Lalawigan ng Romblon."),
            )
            for b in t["barangays"]:
                Barangay.objects.create(municipality=town, name=b)
            for n, (kind, name, location) in enumerate(OFFICES, start=1):
                Office.objects.create(
                    municipality=town, kind=kind, name=name, location=f"{location}, {t['name']}",
                    head="(Sample) Office Head",
                    email=f"{kind.lower()}@{slugify(t['name'])}.example",
                    phone=f"0900 000 {i}{n:03d}",
                    latitude=Decimal(t["lat"]) + Decimal("0.0005") * n,
                    longitude=Decimal(t["lon"]) + Decimal("0.0004") * n,
                )
            towns[t["code"]] = town
        return towns

    def office(self, town, kind):
        return Office.objects.get(municipality=town, kind=kind)

    # --------------------------------------------------------------- services
    def make_services(self):
        cats = {}
        for order, (slug, icon, en, fil, rol) in enumerate([
            ("civil-registry", "🧾", "Civil Registry", "Rehistro Sibil", "Rehistro Sibil"),
            ("permits", "🏪", "Permits & Clearances", "Mga Permit at Clearance", "Mga Permit kag Clearance"),
            ("social-welfare", "🤝", "Social Welfare", "Kapakanang Panlipunan", "Kaayuhan it Kumunidad"),
            ("health", "🩺", "Health", "Kalusugan", "Kalusugan"),
            ("agriculture", "🌾", "Agriculture & Fisheries", "Agrikultura at Pangisdaan", "Agrikultura kag Pangisda"),
        ]):
            cats[slug] = ServiceCategory.objects.create(slug=slug, icon=icon, order=order, **tr("name", en, fil, rol))

        K = Office.Kind
        catalogue = [
            {
                "cat": "civil-registry", "office": K.CIVIL_REGISTRY, "fee": "50.00",
                "name": tr("name", "Certified copy of a birth, marriage or death certificate",
                           "Certified true copy ng birth, marriage o death certificate"),
                "summary": tr("summary",
                              "Get a certified copy of a civil registry record kept by the Municipal Civil Registrar. "
                              "For PSA-security-paper copies, the MCR can also forward your request to PSA.",
                              "Kumuha ng certified copy ng rekord sa Municipal Civil Registrar. Maaari ring ipadala "
                              "ng MCR ang iyong request sa PSA para sa kopyang nasa security paper."),
                "fees": tr("fees", "Sample: PHP 50 per certified copy (local copy). PSA copy: PSA rates apply.",
                           "Halimbawa: PHP 50 bawat kopya (lokal). Kopya ng PSA: presyo ng PSA."),
                "time": tr("processing_time", "15-30 minutes (local copy)", "15-30 minuto (lokal na kopya)"),
                "who": tr("who_may_apply", "The owner of the record, a parent, spouse, or an authorised representative.",
                          "Ang may-ari ng rekord, magulang, asawa, o awtorisadong kinatawan."),
                "legal": "Act No. 3753 (Civil Registry Law)",
                "reqs": [
                    ("Valid government-issued ID of the requester", "", "", False),
                    ("Accomplished request form", "MCR window", "", False),
                    ("Authorization letter signed by the owner of the record, with a copy of the owner's ID", "",
                     "Are you requesting for another person?", False),
                ],
                "steps": [("Fill out the request form and present your ID.", "Client", "5 min"),
                          ("Pay the fee at the Municipal Treasurer's Office and get an official receipt.", "Treasury", "5 min"),
                          ("Present the receipt and receive the certified copy.", "MCR staff", "10-20 min")],
            },
            {
                "cat": "civil-registry", "office": K.CIVIL_REGISTRY, "fee": "0",
                "name": tr("name", "Birth registration (on-time and late)", "Pagpaparehistro ng kapanganakan (on-time at late)",
                           "Pagparehistro it pagkatawo"),
                "summary": tr("summary",
                              "Register a birth with the Municipal Civil Registrar. On-time registration (within 30 days) "
                              "is free; late registration needs extra documents and a 10-day posting period.",
                              "Iparehistro ang kapanganakan sa Municipal Civil Registrar. Libre kung on-time (sa loob ng 30 araw); "
                              "ang late registration ay may dagdag na dokumento at 10 araw na pagpapaskil."),
                "fees": tr("fees", "On-time: free. Late registration: sample PHP 200 (see local tax ordinance).",
                           "On-time: libre. Late registration: halimbawa PHP 200 (ayon sa lokal na ordinansa)."),
                "time": tr("processing_time", "Same day (on-time); about 11 working days (late, includes posting)",
                           "Sa parehong araw (on-time); mga 11 araw ng trabaho (late, kasama ang posting)"),
                "who": tr("who_may_apply", "Parents, the attending physician or midwife, or the person (if of age) for late registration."),
                "legal": "Act No. 3753; PSA Administrative Order No. 1, s. 1993",
                "reqs": [
                    ("Certificate of Live Birth (Municipal Form 102), 4 copies, signed", "Hospital, RHU or midwife", "", False),
                    ("Valid ID of the informant (parent)", "", "", False),
                    ("Affidavit of Acknowledgment/Admission of Paternity", "Notary / MCR",
                     "Are the parents not married to each other, and the father will acknowledge the child?", False),
                    ("Negative certification of birth record from PSA", "PSA",
                     "Is it more than 30 days after the birth (late registration)?", False),
                    ("Two of: baptismal certificate, school record, barangay certificate, medical record", "",
                     "Is it more than 30 days after the birth (late registration)?", False),
                    ("Affidavit of two disinterested persons who know the facts of birth", "Notary",
                     "Is it more than 30 days after the birth (late registration)?", False),
                ],
                "steps": [("Submit the signed Certificate of Live Birth and requirements to the MCR.", "Client", "10 min"),
                          ("MCR reviews the documents. Late registrations are posted for 10 days.", "MCR", "1-10 days"),
                          ("Registration is recorded; get your registered copy.", "MCR", "15 min")],
            },
            {
                "cat": "civil-registry", "office": K.CIVIL_REGISTRY, "fee": "300.00",
                "name": tr("name", "Marriage license application", "Aplikasyon para sa marriage license",
                           "Aplikasyon para sa lisensya sa kasal"),
                "summary": tr("summary",
                              "Apply for a marriage license at the MCR of the town where either party lives. The "
                              "application is posted for 10 consecutive days before the license is issued.",
                              "Mag-apply ng marriage license sa MCR ng bayan kung saan nakatira ang isa sa magkasintahan. "
                              "Ipapaskil ito nang 10 magkakasunod na araw bago ibigay ang lisensya."),
                "fees": tr("fees", "Sample: PHP 300 license fee + PHP 100 marriage counselling certificate (verify)",
                           "Halimbawa: PHP 300 + PHP 100 para sa counselling certificate (beripikahin)"),
                "time": tr("processing_time", "About 11 working days (includes 10-day posting)", "Mga 11 araw ng trabaho"),
                "legal": "Family Code of the Philippines (E.O. 209), Arts. 9-21",
                "reqs": [
                    ("PSA birth certificate of both parties", "PSA", "", False),
                    ("PSA Certificate of No Marriage (CENOMAR) of both parties", "PSA", "", False),
                    ("Pre-marriage counselling / orientation certificate", "MSWDO / MHO", "", False),
                    ("Community tax certificate (cedula) and valid IDs", "Treasury", "", False),
                    ("Written parental consent", "", "Is either party 18 to 21 years old?", False),
                    ("Parental advice (written)", "", "Is either party 22 to 25 years old?", False),
                    ("Death certificate of the late spouse, or the annulment/nullity decree", "PSA / Court",
                     "Was either party married before?", False),
                ],
                "steps": [("Submit the application and requirements to the MCR (both parties present).", "Couple", "20 min"),
                          ("Attend the pre-marriage orientation and counselling.", "MSWDO / MHO", "half day"),
                          ("Application is posted for 10 consecutive days.", "MCR", "10 days"),
                          ("Pay the fees and claim the marriage license (valid 120 days anywhere in the Philippines).", "MCR / Treasury", "15 min")],
            },
            {
                "cat": "civil-registry", "office": K.CIVIL_REGISTRY, "fee": "0",
                "name": tr("name", "Death registration and burial permit", "Pagpaparehistro ng pagkamatay at burial permit"),
                "summary": tr("summary", "Register a death within 30 days and get the burial permit needed for interment.",
                              "Iparehistro ang pagkamatay sa loob ng 30 araw at kumuha ng burial permit."),
                "fees": tr("fees", "Registration: free. Sample burial permit fee: PHP 50.", "Rehistro: libre. Burial permit: halimbawa PHP 50."),
                "time": tr("processing_time", "30 minutes", "30 minuto"),
                "legal": "Act No. 3753; P.D. 856 (Sanitation Code)",
                "reqs": [
                    ("Certificate of Death (Municipal Form 103), 4 copies, signed by the attending physician or the Municipal Health Officer", "Hospital / MHO", "", False),
                    ("Valid ID of the informant", "", "", False),
                    ("Affidavit of delayed registration and negative certification from PSA", "Notary / PSA",
                     "Is it more than 30 days after the death?", False),
                ],
                "steps": [("Have the Certificate of Death signed by the physician or MHO.", "Family / MHO", "varies"),
                          ("Submit it to the MCR for registration.", "Family", "15 min"),
                          ("Pay the burial permit fee and receive the permit.", "Treasury / MCR", "15 min")],
            },
            {
                "cat": "permits", "office": K.BPLO, "fee": None,
                "name": tr("name", "Business permit (new or renewal)", "Business permit (bago o renewal)", "Permit sa negosyo"),
                "summary": tr("summary",
                              "Mayor's permit to operate a business. Renewals are due in January; business taxes are "
                              "payable within the first 20 days of January to avoid surcharges.",
                              "Mayor's permit para magpatakbo ng negosyo. Ang renewal ay tuwing Enero; bayaran ang buwis "
                              "sa unang 20 araw ng Enero para walang multa."),
                "fees": tr("fees", "Varies: business tax, mayor's permit fee, sanitary and garbage fees per the municipal revenue code.",
                           "Iba-iba: business tax, mayor's permit fee, sanitary at garbage fees ayon sa revenue code."),
                "time": tr("processing_time", "1-3 working days (Business One-Stop Shop in January: same day)",
                           "1-3 araw ng trabaho (BOSS tuwing Enero: sa parehong araw)"),
                "legal": "RA 7160 (Local Government Code), Sec. 165; RA 11032 (Ease of Doing Business)",
                "reqs": [
                    ("DTI business name registration (sole proprietor) or SEC/CDA registration", "DTI / SEC / CDA", "", False),
                    ("Barangay business clearance", "Barangay Hall", "", False),
                    ("Proof of business location: lease contract, land title or tax declaration", "", "", False),
                    ("Community tax certificate (cedula)", "Treasury", "", False),
                    ("Fire Safety Inspection Certificate", "BFP", "", False),
                    ("Sanitary permit and health certificates of food handlers", "RHU", "Do you sell food or drinks?", False),
                    ("Previous year's mayor's permit and sworn declaration of gross sales", "", "Is this a renewal?", False),
                ],
                "steps": [("Get the unified application form at the BPLO and submit it with the requirements.", "Client", "15 min"),
                          ("BPLO assesses taxes and fees.", "BPLO", "30 min"),
                          ("Pay at the Municipal Treasurer's Office.", "Treasury", "15 min"),
                          ("Claim the Mayor's Permit and business plate.", "BPLO", "same day to 3 days")],
            },
            {
                "cat": "permits", "office": K.ENGINEERING, "fee": None,
                "name": tr("name", "Building permit", "Building permit", "Permit sa pagpatindog it balay"),
                "summary": tr("summary",
                              "Required before building, renovating or demolishing a structure. Filed with the Office of "
                              "the Building Official (Municipal Engineering Office).",
                              "Kailangan bago magtayo, mag-renovate o gumiba ng gusali. Inihahain sa Office of the Building "
                              "Official (Municipal Engineering Office)."),
                "fees": tr("fees", "Computed from the National Building Code schedule of fees, based on floor area and use.",
                           "Kinukuwenta ayon sa National Building Code batay sa laki at gamit."),
                "time": tr("processing_time", "Up to 15 working days (sample)", "Hanggang 15 araw ng trabaho (halimbawa)"),
                "legal": "P.D. 1096 (National Building Code)",
                "reqs": [
                    ("Unified application form for building permit, notarised", "Engineering Office", "", False),
                    ("Certified true copy of land title or tax declaration; or lease/consent of the lot owner", "Assessor / RD", "", False),
                    ("5 sets of plans and specifications signed and sealed by licensed professionals", "Your engineer/architect", "", False),
                    ("Bill of materials and cost estimate", "", "", False),
                    ("Barangay clearance for construction", "Barangay Hall", "", False),
                    ("Locational/zoning clearance", "MPDO", "", False),
                    ("Fire Safety Evaluation Clearance", "BFP", "", False),
                    ("Environmental Compliance Certificate or Certificate of Non-Coverage", "DENR-EMB",
                     "Is the project large, commercial, or near a protected area or the coast?", False),
                ],
                "steps": [("Submit the complete application to the Office of the Building Official.", "Applicant", "30 min"),
                          ("Technical evaluation of plans (line and grade, structural, electrical, sanitary).", "OBO", "5-10 days"),
                          ("Pay the assessed fees.", "Treasury", "15 min"),
                          ("Release of the building permit.", "OBO", "1 day")],
            },
            {
                "cat": "permits", "office": K.TREASURY, "fee": "5.00",
                "name": tr("name", "Community Tax Certificate (cedula)", "Community Tax Certificate (cedula)", "Cedula"),
                "summary": tr("summary",
                              "The cedula is required for many transactions (permits, notarisation, employment). Get it at "
                              "the Municipal Treasurer's Office.",
                              "Kailangan ang cedula sa maraming transaksyon (permit, notaryo, trabaho). Makukuha sa "
                              "Municipal Treasurer's Office.",
                              "Kinahangean ang cedula sa madamong transaksyon. Makuha sa Municipal Treasurer's Office."),
                "fees": tr("fees", "Individuals: PHP 5 basic tax, plus PHP 1 for every PHP 1,000 of gross income (max PHP 5,000 additional). Interest applies after February.",
                           "Indibidwal: PHP 5 basic, dagdag PHP 1 bawat PHP 1,000 na kita (hanggang PHP 5,000). May interes pagkatapos ng Pebrero."),
                "time": tr("processing_time", "5 minutes", "5 minuto", "5 minutos"),
                "who": tr("who_may_apply", "Residents 18 years old and above; businesses and corporations."),
                "legal": "RA 7160 (Local Government Code), Secs. 156-158",
                "reqs": [
                    ("Valid ID or any document showing your name and address", "", "", False),
                    ("Statement of gross income (payslip or ITR)", "", "Do you have a salary or business income?", True),
                ],
                "steps": [("Fill out the cedula information slip.", "Client", "2 min"),
                          ("Pay at the Treasury window and receive the cedula.", "Treasury", "3 min")],
            },
            {
                "cat": "permits", "office": None, "fee": "50.00",
                "name": tr("name", "Barangay clearance", "Barangay clearance", "Barangay clearance"),
                "summary": tr("summary",
                              "Issued by your Barangay Hall (not the Municipal Hall). Often needed for employment, permits and IDs.",
                              "Ibinibigay ng inyong Barangay Hall (hindi ng Munisipyo). Kadalasang kailangan sa trabaho, permit at ID."),
                "fees": tr("fees", "Sample: PHP 50 (set by each barangay ordinance)", "Halimbawa: PHP 50 (ayon sa ordinansa ng barangay)"),
                "time": tr("processing_time", "15 minutes", "15 minuto"),
                "office_hours": "Barangay Hall hours, usually Mon-Fri 8:00 AM - 5:00 PM",
                "legal": "RA 7160, Sec. 152(c)",
                "reqs": [
                    ("Community tax certificate (cedula)", "Municipal Treasurer", "", False),
                    ("Valid ID showing your barangay address", "", "", False),
                    ("Statement of purpose (e.g. employment, business)", "", "", False),
                ],
                "steps": [("Go to your Barangay Hall and state the purpose.", "Client", "5 min"),
                          ("Pay the fee and have the clearance signed by the Punong Barangay.", "Barangay Secretary", "10 min")],
            },
            {
                "cat": "social-welfare", "office": K.OSCA, "fee": "0",
                "name": tr("name", "Senior citizen ID", "Senior citizen ID", "ID para sa senior citizen"),
                "summary": tr("summary",
                              "Free ID for residents 60 and older. Use it for the 20% discount and VAT exemption on medicines, "
                              "fares, food and other goods and services.",
                              "Libreng ID para sa edad 60 pataas. Gamitin para sa 20% diskwento at VAT exemption sa gamot, "
                              "pamasahe, pagkain at iba pa."),
                "fees": tr("fees", "Free", "Libre", "Libre"),
                "time": tr("processing_time", "Same day to 1 week", "Sa parehong araw hanggang 1 linggo"),
                "who": tr("who_may_apply", "Filipino residents of the municipality who are 60 years old or older."),
                "legal": "RA 9994 (Expanded Senior Citizens Act of 2010)",
                "reqs": [
                    ("Proof of age: PSA birth certificate, or any government ID showing birth date", "", "", False),
                    ("Two 1x1 ID photos", "", "", False),
                    ("Barangay certificate of residency", "Barangay Hall", "", False),
                ],
                "steps": [("Submit the requirements to OSCA.", "Applicant or relative", "10 min"),
                          ("Verification and encoding.", "OSCA", "1 day"),
                          ("Claim the ID and purchase booklet.", "OSCA", "5 min")],
            },
            {
                "cat": "social-welfare", "office": K.PDAO, "fee": "0",
                "name": tr("name", "PWD ID", "PWD ID", "ID para sa PWD"),
                "summary": tr("summary",
                              "Free ID for persons with disability, giving the 20% discount, VAT exemption and other benefits.",
                              "Libreng ID para sa may kapansanan para sa 20% diskwento, VAT exemption at iba pang benepisyo."),
                "fees": tr("fees", "Free", "Libre", "Libre"),
                "time": tr("processing_time", "Same day to 2 weeks", "Sa parehong araw hanggang 2 linggo"),
                "legal": "RA 7277 as amended by RA 10754",
                "reqs": [
                    ("Certificate of disability signed by a licensed physician (or school head for apparent disabilities)", "RHU / hospital", "", False),
                    ("Accomplished PRPWD application form", "PDAO / MSWDO", "", False),
                    ("Two 1x1 ID photos", "", "", False),
                    ("Barangay certificate of residency", "Barangay Hall", "", False),
                ],
                "steps": [("Submit the requirements to the PDAO or MSWDO.", "Applicant or relative", "15 min"),
                          ("Encoding in the DOH PWD registry.", "PDAO", "1-5 days"),
                          ("Claim the ID and purchase booklet.", "PDAO", "5 min")],
            },
            {
                "cat": "social-welfare", "office": K.MSWDO, "fee": "0",
                "name": tr("name", "MSWDO financial assistance (medical, burial, crisis)",
                           "Tulong pinansyal ng MSWDO (medikal, pampalibing, krisis)",
                           "Bulig pinansyal it MSWDO"),
                "summary": tr("summary",
                              "Help for families in crisis: hospital bills, medicines, burial, or after a fire or disaster. "
                              "A social worker will interview you.",
                              "Tulong para sa pamilyang nasa krisis: bayarin sa ospital, gamot, pagpapalibing, o matapos ang "
                              "sunog o kalamidad. Iinterbyuhin ka ng social worker."),
                "fees": tr("fees", "Free", "Libre", "Libre"),
                "time": tr("processing_time", "1-3 working days (depends on available funds)",
                           "1-3 araw ng trabaho (depende sa pondo)"),
                "legal": "DSWD AICS guidelines; municipal social welfare ordinance",
                "reqs": [
                    ("Barangay certificate of indigency", "Barangay Hall", "", False),
                    ("Valid ID of the client", "", "", False),
                    ("Medical certificate/abstract, prescription or hospital bill", "Doctor / hospital",
                     "Is the help for medical needs?", False),
                    ("Death certificate and funeral contract", "MCR / funeral parlor", "Is the help for a burial?", False),
                    ("Barangay or BFP certification of the incident", "Barangay / BFP",
                     "Is the help because of a fire, flood or other disaster?", False),
                ],
                "steps": [("Go to the MSWDO with your requirements.", "Client", "10 min"),
                          ("Interview and assessment by a social worker.", "MSWDO", "30 min"),
                          ("Approval and release of assistance.", "MSWDO / Treasury", "1-3 days")],
            },
            {
                "cat": "health", "office": K.HEALTH, "fee": "0",
                "name": tr("name", "Rural Health Unit services", "Mga serbisyo ng Rural Health Unit", "Serbisyo it RHU"),
                "summary": tr("summary",
                              "Free consultations, immunisation, prenatal care, family planning, TB-DOTS, dental and "
                              "laboratory services at the Rural Health Unit and Barangay Health Stations.",
                              "Libreng konsulta, bakuna, prenatal care, family planning, TB-DOTS, dental at laboratoryo sa "
                              "RHU at Barangay Health Stations."),
                "fees": tr("fees", "Free for most services; some laboratory tests may have minimal fees.", "Libre ang karamihan."),
                "time": tr("processing_time", "Walk-in, first come first served", "Walk-in, unahan"),
                "office_hours": "Mon-Fri, 8:00 AM - 5:00 PM; immunisation day every Wednesday (sample)",
                "legal": "RA 11223 (Universal Health Care Act)",
                "reqs": [
                    ("PhilHealth ID or member data record, if any", "PhilHealth", "", True),
                    ("Child's immunisation booklet", "", "Is this for a child's vaccination?", False),
                    ("Mother and child book / previous prenatal records", "", "Is this a prenatal check-up?", False),
                ],
                "steps": [("Register at the RHU front desk.", "Patient", "5 min"),
                          ("Vital signs and triage.", "Nurse / midwife", "10 min"),
                          ("Consultation or service.", "Doctor / nurse", "varies")],
            },
            {
                "cat": "agriculture", "office": K.AGRICULTURE, "fee": "0",
                "name": tr("name", "RSBSA registration (farmers and fisherfolk)", "Pagpaparehistro sa RSBSA",
                           "Pagparehistro sa RSBSA"),
                "summary": tr("summary",
                              "Register in the Registry System for Basic Sectors in Agriculture to access DA seeds, "
                              "fertiliser, cash aid, crop insurance and training.",
                              "Magparehistro sa RSBSA para makakuha ng binhi, abono, ayuda, crop insurance at training mula sa DA."),
                "fees": tr("fees", "Free", "Libre", "Libre"),
                "time": tr("processing_time", "15 minutes (encoding may take 1-2 weeks)", "15 minuto"),
                "legal": "DA Memorandum Order on RSBSA",
                "reqs": [
                    ("Accomplished RSBSA enrolment form", "Municipal Agriculture Office", "", False),
                    ("Valid ID and one 2x2 photo", "", "", False),
                    ("Proof of farm: tax declaration, CLOA, or barangay/MAO certification of tenancy", "Assessor / Barangay",
                     "Do you farm land?", False),
                    ("FishR registration or barangay certification as fisherfolk", "MAO / BFAR",
                     "Are you a fisherfolk?", False),
                ],
                "steps": [("Fill out the RSBSA form at the MAO or during barangay registration drives.", "Farmer", "10 min"),
                          ("Validation by the Agricultural Technician.", "MAO", "1-2 weeks"),
                          ("Encoding in the national RSBSA database.", "MAO", "")],
            },
        ]

        fee_factor = {"MAG": Decimal("1.0"), "SFE": Decimal("1.0"), "CAJ": Decimal("1.0")}
        for code, town in self.towns.items():
            for i, item in enumerate(catalogue):
                fee = item["fee"]
                svc = Service.objects.create(
                    municipality=town, category=cats[item["cat"]],
                    office=self.office(town, item["office"]) if item["office"] else None,
                    slug=slugify(item["name"]["name_en"])[:150],
                    fee_amount=(Decimal(fee) * fee_factor[code]) if fee is not None else None,
                    office_hours=item.get("office_hours", ""), legal_basis=item.get("legal", ""),
                    **item["name"], **item["summary"], **item["fees"], **item["time"], **item.get("who", {}),
                )
                for n, (text, where, cond, optional) in enumerate(item["reqs"], start=1):
                    ServiceRequirement.objects.create(service=svc, order=n, text=text, where_to_get=where,
                                                      condition=cond, is_optional=optional)
                for n, (desc, who, dur) in enumerate(item["steps"], start=1):
                    ServiceStep.objects.create(service=svc, order=n, description=desc, responsible=who, duration=dur)
                # Different view counts make the "most-used services" list believable.
                Service.objects.filter(pk=svc.pk).update(view_count=(len(catalogue) - i) * 17 + len(code) * i)

    # --------------------------------------------------------------- programs
    def make_programs(self):
        K, L = Program.Kind, Program.Level
        progs = [
            dict(kind=K.CASH, level=L.NATIONAL, agency="DSWD", requires_listahanan_poor=True,
                 official_url="https://pantawid.dswd.gov.ph/",
                 **tr("name", "Pantawid Pamilyang Pilipino Program (4Ps)", "Pantawid Pamilyang Pilipino Program (4Ps)", "4Ps"),
                 **tr("summary", "Conditional cash grants for poor households with children 0-18 or a pregnant member, "
                                 "tied to school attendance and health check-ups.",
                      "Kondisyonal na cash grant para sa mahihirap na pamilyang may anak na 0-18 o buntis, kapalit ng "
                      "pagpasok sa paaralan at pagpapa-check-up."),
                 **tr("benefits", "Monthly health and education grants and rice subsidy (amounts set by DSWD)."),
                 **tr("how_to_apply", "Households are selected from the DSWD Listahanan. Ask your MSWDO or the 4Ps "
                                      "Municipal Link if your household was assessed."),
                 **tr("eligibility_notes", "Household must be assessed as poor by Listahanan and have children 0-18 or a pregnant member.")),
            dict(kind=K.LIVELIHOOD, level=L.NATIONAL, agency="DOLE", min_age=18, requires_informal_worker=True,
                 **tr("name", "TUPAD emergency employment", "TUPAD (Tulong Panghanapbuhay sa Ating Disadvantaged/Displaced Workers)"),
                 **tr("summary", "Short-term community work (10-30 days) for displaced, underemployed and informal workers, "
                                 "paid at the regional minimum wage.",
                      "Panandaliang trabaho (10-30 araw) para sa nawalan ng hanapbuhay at impormal na manggagawa, "
                      "bayad sa minimum wage ng rehiyon."),
                 **tr("how_to_apply", "Register through your barangay or the PESO/Mayor's Office when a TUPAD batch is announced."),
                 **tr("eligibility_notes", "At least 18 years old; one beneficiary per family per year.")),
            dict(kind=K.CASH, level=L.NATIONAL, agency="DSWD", requires_in_crisis=True,
                 **tr("name", "Assistance to Individuals in Crisis Situation (AICS)", "AICS (Tulong sa mga nasa krisis)"),
                 **tr("summary", "Medical, burial, transportation, educational and food assistance for individuals and "
                                 "families in crisis.",
                      "Tulong medikal, pampalibing, pamasahe, pang-edukasyon at pagkain para sa nasa krisis."),
                 **tr("how_to_apply", "Go to your MSWDO with the requirements for the type of help. See the MSWDO "
                                      "financial assistance service for the checklist.")),
            dict(kind=K.SENIOR_PWD, level=L.NATIONAL, agency="DSWD", min_age=60,
                 **tr("name", "Social Pension for Indigent Senior Citizens", "Social Pension para sa mahihirap na Senior Citizen"),
                 **tr("summary", "Monthly stipend of PHP 1,000 for indigent senior citizens (RA 11916).",
                      "Buwanang PHP 1,000 para sa mahihirap na senior citizen (RA 11916)."),
                 **tr("how_to_apply", "Apply through OSCA or MSWDO; you will be assessed for the waitlist."),
                 **tr("eligibility_notes", "Frail, sickly or with disability; no regular pension or income; no regular family support.")),
            dict(kind=K.SENIOR_PWD, level=L.NATIONAL, agency="LGU / OSCA", min_age=60,
                 **tr("name", "Senior citizen privileges", "Mga pribilehiyo ng senior citizen"),
                 **tr("summary", "20% discount and VAT exemption on medicines, fares, food and more, plus priority lanes.",
                      "20% diskwento at VAT exemption sa gamot, pamasahe, pagkain at iba pa, at priority lane."),
                 **tr("how_to_apply", "Get your senior citizen ID from OSCA.")),
            dict(kind=K.SENIOR_PWD, level=L.NATIONAL, agency="LGU / PDAO", requires_pwd=True,
                 **tr("name", "PWD privileges", "Mga pribilehiyo ng PWD"),
                 **tr("summary", "20% discount and VAT exemption on medicines, fares and more, plus educational assistance.",
                      "20% diskwento at VAT exemption at tulong pang-edukasyon."),
                 **tr("how_to_apply", "Get your PWD ID from PDAO/MSWDO.")),
            dict(kind=K.CASH, level=L.NATIONAL, agency="DSWD / LGU", requires_solo_parent=True,
                 **tr("name", "Solo parent benefits", "Benepisyo para sa solo parent"),
                 **tr("summary", "Solo Parent ID, flexible work, parental leave, and a PHP 1,000 monthly subsidy for "
                                 "solo parents earning minimum wage or less, subject to available funds (RA 11861).",
                      "Solo Parent ID, flexible na trabaho, leave, at PHP 1,000 kada buwan para sa kumikita ng minimum "
                      "wage pababa, depende sa pondo (RA 11861)."),
                 **tr("how_to_apply", "Apply for a Solo Parent ID at the MSWDO.")),
            dict(kind=K.SCHOLARSHIP, level=L.NATIONAL, agency="CHED", requires_student=True, min_age=16,
                 official_url="https://unifast.gov.ph/",
                 **tr("name", "CHED Tertiary Education Subsidy / Tulong Dunong", "CHED TES / Tulong Dunong"),
                 **tr("summary", "Grants for college students in public and private higher education institutions, with "
                                 "priority for students from poor households.",
                      "Grant para sa mga estudyante sa kolehiyo, uunahin ang galing sa mahihirap na pamilya."),
                 **tr("how_to_apply", "Apply through your school's scholarship office during the CHED application period.")),
            dict(kind=K.SCHOLARSHIP, level=L.PROVINCIAL, agency="Provincial Government of Romblon", requires_student=True,
                 max_monthly_income=25000,
                 **tr("name", "Provincial scholarship program (sample)", "Iskolarsip ng Probinsya (halimbawa)"),
                 **tr("summary", "Sample entry: financial assistance for deserving Romblomanon college students.",
                      "Halimbawa: tulong pinansyal para sa karapat-dapat na estudyanteng Romblomanon."),
                 **tr("eligibility_notes", "Sample rules: resident of Romblon, household income PHP 25,000/month or less, passing grades.")),
            dict(kind=K.LIVELIHOOD, level=L.NATIONAL, agency="TESDA", min_age=18,
                 **tr("name", "TESDA Training for Work Scholarship (TWSP)", "TESDA TWSP"),
                 **tr("summary", "Free skills training and assessment (e.g. agricultural crops, cookery, electrical, "
                                 "housekeeping, tour guiding), sometimes with a training allowance.",
                      "Libreng skills training at assessment, minsan may allowance."),
                 **tr("how_to_apply", "Ask the TESDA provincial office or your LGU PESO about open slots.")),
            dict(kind=K.AGRI, level=L.NATIONAL, agency="DA", requires_farmer=True,
                 **tr("name", "DA farm inputs and cash assistance", "Binhi, abono at ayuda mula sa DA"),
                 **tr("summary", "Seeds, fertiliser, and cash aid for RSBSA-registered farmers, plus free crop insurance from PCIC.",
                      "Binhi, abono at ayuda para sa mga magsasakang rehistrado sa RSBSA, at libreng crop insurance."),
                 **tr("how_to_apply", "Register in RSBSA at the Municipal Agriculture Office, then watch for distribution schedules.")),
            dict(kind=K.AGRI, level=L.NATIONAL, agency="BFAR", requires_fisherfolk=True,
                 **tr("name", "BFAR fisherfolk support", "Suporta ng BFAR sa mangingisda"),
                 **tr("summary", "Boats, fishing gear, livelihood kits and training for FishR-registered fisherfolk.",
                      "Bangka, gamit pangisda, livelihood kit at training para sa rehistradong mangingisda."),
                 **tr("how_to_apply", "Register in FishR through the Municipal Agriculture Office.")),
            dict(kind=K.HEALTH, level=L.NATIONAL, agency="PhilHealth",
                 **tr("name", "PhilHealth primary care (Konsulta) package", "PhilHealth Konsulta package"),
                 **tr("summary", "All Filipinos are PhilHealth members under the Universal Health Care Act. Register with an "
                                 "accredited primary care provider such as your RHU for free consultations and basic tests.",
                      "Lahat ng Pilipino ay miyembro ng PhilHealth. Magparehistro sa RHU para sa libreng konsulta at basic tests."),
                 **tr("how_to_apply", "Bring your PhilHealth ID or member data record to the RHU.")),
            dict(kind=K.SCHOLARSHIP, level=L.NATIONAL, agency="NCIP", requires_indigenous=True, requires_student=True,
                 **tr("name", "NCIP Educational Assistance Program", "NCIP Educational Assistance Program"),
                 **tr("summary", "Educational grants for indigenous peoples' students, including members of the Sibuyan Mangyan Tagabukid.",
                      "Tulong pang-edukasyon para sa estudyanteng katutubo, kabilang ang Sibuyan Mangyan Tagabukid."),
                 **tr("how_to_apply", "Apply through the NCIP provincial office with a certificate of tribal membership.")),
        ]
        for p in progs:
            p["slug"] = slugify(p["name_en"])[:150]
            Program.objects.create(**p)

        for code, town in self.towns.items():
            prog = Program.objects.create(
                municipality=town, kind=Program.Kind.SCHOLARSHIP, level=Program.Level.MUNICIPAL,
                agency=f"LGU {town.name}", requires_student=True, max_monthly_income=15000,
                contact_office=self.office(town, Office.Kind.MSWDO),
                slug=f"{town.slug}-municipal-scholarship",
                **tr("name", f"{town.name} municipal scholarship (sample)", f"Iskolarsip ng {town.name} (halimbawa)"),
                **tr("summary", f"Sample: educational assistance for {town.name} students in senior high school and college.",
                     f"Halimbawa: tulong pang-edukasyon para sa mga estudyante ng {town.name}."),
                **tr("how_to_apply", "Submit the application form, latest grades, barangay certificate of residency and "
                                     "certificate of indigency or income to the MSWDO."),
                **tr("eligibility_notes", "Sample rules: resident for at least 2 years, household income up to PHP 15,000/month."),
            )
            ProgramSchedule.objects.create(
                program=prog, municipality=town, opens_on=self.today - timedelta(days=5),
                closes_on=self.today + timedelta(days=20), venue=f"MSWDO, Municipal Hall, {town.name}",
                **tr("title", "Application period, 2nd semester (sample)", "Panahon ng aplikasyon, ika-2 semestre (halimbawa)"),
            )
        tupad = Program.objects.get(agency="DOLE")
        ProgramSchedule.objects.create(
            program=tupad, municipality=self.towns["CAJ"], opens_on=self.today + timedelta(days=7),
            closes_on=self.today + timedelta(days=9), venue="Cajidiocan Municipal Gym",
            **tr("title", "TUPAD orientation and contract signing (sample)", "TUPAD orientation (halimbawa)"),
        )

    # --------------------------------------------------------------- concerns
    def make_concerns(self):
        K = Office.Kind
        cats = {}
        for order, (slug, icon, kind, en, fil, desc) in enumerate([
            ("road", "🚧", K.ENGINEERING, "Road or bridge damage", "Sirang kalsada o tulay", "Potholes, landslides on roads, broken bridges"),
            ("garbage", "🗑️", K.MENRO, "Garbage and sanitation", "Basura at kalinisan", "Uncollected garbage, illegal dumping"),
            ("water", "🚰", K.ENGINEERING, "Water supply", "Suplay ng tubig", "No water, leaks, dirty water"),
            ("peace", "👮", K.MAYOR, "Peace and order", "Kapayapaan at kaayusan", "Noise, disputes, safety concerns (not emergencies)"),
            ("hazard", "⚠️", K.MDRRMO, "Disaster risk or hazard", "Panganib o sakuna", "Fallen trees, cracks on slopes, flooding"),
            ("health", "🩺", K.HEALTH, "Health and sanitation", "Kalusugan", "Stray animals, dengue breeding sites, food safety"),
            ("welfare", "🤝", K.MSWDO, "Social welfare", "Kapakanang panlipunan", "Families or persons needing help"),
            ("farm", "🌾", K.AGRICULTURE, "Farm and fisheries", "Sakahan at pangisdaan", "Pests, crop damage, fishing concerns"),
            ("environment", "🌳", K.MENRO, "Environment", "Kalikasan", "Illegal cutting, quarrying, coastal concerns"),
            ("request", "✉️", K.MAYOR, "Request or question for the LGU", "Kahilingan o tanong sa LGU", "Anything else for your LGU"),
        ]):
            cats[slug] = ConcernCategory.objects.create(
                slug=slug, icon=icon, office_kind=kind, order=order,
                **tr("name", en, fil), **tr("description", desc),
            )

        samples = [
            ("MAG", "Poblacion", "road", "Pothole near the public market", "Large pothole in front of the market entrance, dangerous for tricycles at night.", "resolved", 30, 52),
            ("MAG", "Tampayan", "water", "No water since Monday", "Our purok has had no water supply for three days.", "in_progress", 4, None),
            ("MAG", "Agsao", "garbage", "Garbage not collected", "Garbage along the national road has not been collected for two weeks.", "assigned", 2, None),
            ("SFE", "Taclobo", "hazard", "Leaning tree over the road", "A big tree is leaning over the road after the rains, near the school.", "resolved", 12, 6),
            ("SFE", "España", "health", "Stray dogs near the school", "Several stray dogs are chasing children near the elementary school.", "received", 1, None),
            ("SFE", "Poblacion", "request", "Schedule of the senior citizen payout", "When is the next social pension payout in San Fernando?", "resolved", 8, 20),
            ("CAJ", "Cambajao", "farm", "Rats damaging rice fields", "Rats are damaging our rice fields before harvest. Can the MAO help?", "in_progress", 6, None),
            ("CAJ", "Poblacion", "peace", "Loud karaoke past midnight", "Karaoke near the plaza continues past midnight on weekdays.", "resolved", 20, 30),
            ("CAJ", "Lico", "road", "Damaged culvert", "The culvert on the barangay road collapsed, vehicles cannot pass.", "received", 0, None),
        ]
        for code, brgy, cat, subject, desc, status, days_ago, hours_to_resolve in samples:
            town = self.towns[code]
            concern = Concern.objects.create(
                municipality=town, barangay=Barangay.objects.get(municipality=town, name=brgy),
                category=cats[cat], subject=f"{subject} (sample)", description=desc,
                name="Sample Citizen", email="citizen@example.com", phone="0900 000 0000",
                consent_given_at=self.now, status=Concern.Status.RECEIVED,
            )
            created = self.now - timedelta(days=days_ago, hours=3)
            concern.messages.create(sender=ConcernMessage.Sender.SYSTEM,
                                    body=f"Concern received and routed to {concern.office}.")
            path = Concern.TRACKER_STEPS[1:Concern.TRACKER_STEPS.index(status) + 1]
            prev = Concern.Status.RECEIVED
            for step in path:
                StatusChange.objects.create(concern=concern, from_status=prev, to_status=step, note="sample")
                prev = step
            if status != Concern.Status.RECEIVED:
                concern.messages.create(sender=ConcernMessage.Sender.STAFF,
                                        body="Thank you. Our team has been informed and will inspect the area. (sample reply)")
            resolved_at = created + timedelta(hours=hours_to_resolve) if hours_to_resolve else None
            Concern.objects.filter(pk=concern.pk).update(status=status, created_at=created, resolved_at=resolved_at)

    # ------------------------------------------------------ news and alerts
    def make_news_and_alerts(self):
        C = Post.Category
        posts = [
            (None, C.ADVISORY, True, 0, "Sea travel advisory: check before you go (sample)",
             "Pagkansela ng biyahe sa dagat: alamin muna bago umalis (halimbawa)",
             "Sailings may be cancelled when PAGASA raises a gale warning or a wind signal. Check the Ferry Board.",
             "The Philippine Coast Guard suspends sea travel for small vessels when a gale warning or Tropical Cyclone "
             "Wind Signal is raised. Check the Ferry Board on this site, which port staff update, and confirm with your "
             "shipping line before going to the port. This is a sample advisory."),
            ("MAG", C.LGU, False, 1, "Business One-Stop Shop schedule for permit renewals (sample)", "",
             "Renew your business permit at the Municipal Hall lobby in January.",
             "The LGU will open a Business One-Stop Shop (BOSS) in the Municipal Hall lobby from January 3 to 20. "
             "Bring your previous permit and sworn declaration of gross sales. This is a sample announcement."),
            ("SFE", C.HEALTH, False, 2, "Free anti-rabies vaccination for pets (sample)", "Libreng bakuna kontra rabies para sa alaga (halimbawa)",
             "The Municipal Health Office and MAO will vaccinate dogs and cats in all barangays this month.",
             "Bring your pets to your barangay hall on the scheduled day. Vaccination is free. Sample announcement."),
            ("CAJ", C.AGRICULTURE, False, 3, "RSBSA registration drive in all barangays (sample)", "",
             "Farmers and fisherfolk who are not yet registered in RSBSA can register at their barangay hall.",
             "The Municipal Agriculture Office will hold RSBSA registration in all 14 barangays. Bring a valid ID and "
             "proof of farm. Sample announcement."),
            (None, C.EDUCATION, False, 4, "Scholarship applications open in all three towns (sample)", "",
             "Students may now apply for municipal scholarships. Use the eligibility checker to see if you qualify.",
             "Applications are accepted at each town's MSWDO. Sample announcement."),
            ("MAG", C.EVENT, False, 6, "Mt. Guiting-Guiting clean-up climb (sample)", "",
             "Volunteers joined DENR and the LGU in collecting trash along the trail.",
             "A sample event post describing a clean-up climb with accredited guides."),
        ]
        for code, cat, pinned, days, title, title_fil, summary, body in posts:
            Post.objects.create(
                municipality=self.towns.get(code), category=cat, is_pinned=pinned, slug=slugify(title)[:190],
                published_at=self.now - timedelta(days=days, hours=2),
                **tr("title", title, title_fil), **tr("summary", summary), **tr("body", body),
            )

        Alert.objects.create(
            kind=Alert.Kind.TYPHOON, level=Alert.Level.INFO, starts_at=self.now - timedelta(hours=6),
            ends_at=self.now + timedelta(days=2), source_url="https://bagong.pagasa.dost.gov.ph/",
            **tr("title", "SAMPLE: Gale warning over the eastern seaboard", "HALIMBAWA: Gale warning sa silangang baybayin"),
            **tr("body", "Small sea craft are advised not to venture out. Check the Ferry Board for sailing status."),
        )
        Alert.objects.create(
            municipality=self.towns["SFE"], kind=Alert.Kind.POWER, level=Alert.Level.WARNING,
            starts_at=self.now - timedelta(hours=1), ends_at=self.now + timedelta(days=1),
            **tr("title", "SAMPLE: Scheduled power interruption, 8 AM - 5 PM", "HALIMBAWA: Brownout, 8 AM - 5 PM"),
            **tr("body", "Line maintenance affecting Poblacion, Mabini and España (sample)."),
        )
        Alert.objects.create(
            municipality=self.towns["CAJ"], kind=Alert.Kind.WATER, level=Alert.Level.WARNING,
            starts_at=self.now - timedelta(hours=1), ends_at=self.now + timedelta(hours=20),
            **tr("title", "SAMPLE: Water interruption in Poblacion", "HALIMBAWA: Walang tubig sa Poblacion"),
            **tr("body", "Pipe repair. Please store water (sample)."),
        )
        for code, kind, title, delta, length in [
            ("MAG", Event.Kind.FIESTA, "Magdiwang town fiesta (sample date)", 30, 2),
            ("SFE", Event.Kind.FESTIVAL, "San Fernando founding anniversary (sample date)", 45, 3),
            ("CAJ", Event.Kind.FIESTA, "Cajidiocan town fiesta (sample date)", 60, 2),
            (None, Event.Kind.LGU, "Island-wide coastal clean-up day (sample)", 12, 0),
        ]:
            Event.objects.create(
                municipality=self.towns.get(code), kind=kind, slug=slugify(title),
                starts_on=self.today + timedelta(days=delta), ends_on=self.today + timedelta(days=delta + length),
                **tr("title", title), **tr("description", "Sample event for the calendar prototype."),
                **tr("venue", "Town plaza"),
            )

    # -------------------------------------------------------------- transport
    def make_transport(self):
        routes = [
            ("MAG", "Magdiwang (Ambulong) Port", "Magdiwang", "Batangas City", "Sample Shipping Lines", "MV Sample Star",
             "Tue, Thu, Sat - depart 7:00 PM", "about 12 hours", "Sample: PHP 1,100 economy", time(19, 0)),
            ("MAG", "Magdiwang (Ambulong) Port", "Magdiwang", "Lucena City", "Sample Shipping Lines", "MV Sample Dawn",
             "Mon, Wed, Fri - depart 6:00 PM", "about 13 hours", "Sample: PHP 1,050 economy", time(18, 0)),
            ("SFE", "San Fernando Port", "San Fernando", "Romblon (town)", "Sample Fast Craft Co.", "FC Sample Wave",
             "Daily - depart 8:00 AM", "about 2 hours", "Sample: PHP 450", time(8, 0)),
            ("SFE", "San Fernando Port", "San Fernando", "San Agustin (Tablas)", "Sample Fast Craft Co.", "FC Sample Wave",
             "Mon, Wed, Fri - depart 1:00 PM", "about 3 hours", "Sample: PHP 500", time(13, 0)),
            ("CAJ", "Cajidiocan Port", "Cajidiocan", "Roxas City (Capiz)", "Sample Island Ferries", "MV Sample Breeze",
             "Tue, Fri, Sun - depart 9:00 PM", "about 6 hours", "Sample: PHP 700 economy", time(21, 0)),
        ]
        statuses = [Trip.Status.ON_TIME, Trip.Status.DELAYED, Trip.Status.ON_TIME, Trip.Status.CANCELLED, Trip.Status.ON_TIME]
        notes = {Trip.Status.DELAYED: "Delayed 2 hours: late arrival of vessel (sample)",
                 Trip.Status.CANCELLED: "No sailing: gale warning (sample)"}
        for i, (code, port, origin, dest, op, vessel, sched, dur, fare, dep) in enumerate(routes):
            route = Route.objects.create(
                municipality=self.towns[code], port=port, origin=origin, destination=dest, operator=op,
                vessel=vessel, duration=dur, fare_info=fare, **tr("schedule_text", sched),
                **tr("notes", "Sample schedule. Confirm with the shipping line."),
            )
            for day in range(0, 4):
                st = statuses[(i + day) % len(statuses)] if day < 2 else Trip.Status.ON_TIME
                Trip.objects.create(route=route, departure_date=self.today + timedelta(days=day), departure_time=dep,
                                    status=st, **tr("status_note", notes.get(st, "")))
        M, S, C = self.towns["MAG"], self.towns["SFE"], self.towns["CAJ"]
        for o, d, terminal, t, fare in [
            (M, S, "Magdiwang public market", time(5, 30), "60"), (S, M, "San Fernando terminal", time(13, 0), "60"),
            (C, S, "Cajidiocan public market", time(6, 0), "50"), (S, C, "San Fernando terminal", time(14, 0), "50"),
            (M, C, "Magdiwang public market", time(6, 30), "90"), (C, M, "Cajidiocan public market", time(12, 30), "90"),
        ]:
            JeepneySchedule.objects.create(origin=o, destination=d, terminal=terminal, departure_time=t,
                                           fare=Decimal(fare), days="Daily (sample)")
        for town in self.towns.values():
            for frm, to, reg, disc, special in [
                ("Poblacion", "Port", "15", "12", "60"),
                ("Poblacion", "Rural Health Unit", "15", "12", "50"),
                ("Poblacion", "Neighbouring barangay", "25", "20", "100"),
            ]:
                TricycleFare.objects.create(municipality=town, from_point=f"{frm}, {town.name}", to_point=to,
                                            regular_fare=Decimal(reg), discounted_fare=Decimal(disc),
                                            special_trip_fare=Decimal(special), ordinance="Sample fare ordinance")

    # -------------------------------------------------------------- emergency
    def make_emergency(self):
        A = Hotline.Agency
        Hotline.objects.create(agency=A.NATIONAL, number="911", is_verified=True, order=0,
                               **tr("name", "National Emergency Hotline", "Pambansang Emergency Hotline", "Emergency Hotline"))
        Hotline.objects.create(agency=A.COAST_GUARD, number="0900 000 9001", order=5,
                               **tr("name", "Coast Guard Sub-Station Sibuyan (sample)"))
        Hotline.objects.create(agency=A.HOSPITAL, number="0900 000 9002", order=6,
                               **tr("name", "District hospital, Sibuyan (sample)"))
        Hotline.objects.create(agency=A.POWER, number="0900 000 9003", order=8, is_24h=False,
                               **tr("name", "Electric cooperative (sample)"))
        for i, town in enumerate(self.towns.values(), start=1):
            for n, (agency, label) in enumerate([(A.MDRRMO, "MDRRMO"), (A.PNP, "Police station"),
                                                 (A.BFP, "Fire station"), (A.RHU, "Rural Health Unit")], start=1):
                Hotline.objects.create(municipality=town, agency=agency, number=f"0900 000 {i}{n}00", order=n,
                                       **tr("name", f"{label} {town.name} (sample)"))
            for brgy in town.barangays.filter(name__in=["Poblacion", "Tampayan", "Taclobo", "España", "Cambajao", "Lico", "Agsao"]):
                EvacuationCenter.objects.create(barangay=brgy, name=f"{brgy.name} Elementary School (sample)",
                                                capacity=250, facilities="Classrooms, comfort rooms, water tank")
                EvacuationCenter.objects.create(barangay=brgy, name=f"{brgy.name} covered court (sample)", capacity=150,
                                                facilities="Open hall, generator")
        H = PreparednessGuide.Hazard
        PreparednessGuide.objects.create(hazard=H.TYPHOON, order=1, **tr(
            "title", "Before and during a typhoon", "Bago at habang may bagyo", "Antes kag samtang may bagyo"), **tr(
            "body",
            "Monitor PAGASA bulletins and LGU alerts.\nPrepare a go-bag: water, food for 3 days, medicines, flashlight, "
            "radio, power bank, copies of IDs.\nSecure your roof and bring in loose objects.\nKnow your barangay's "
            "evacuation center and route.\nEvacuate early when told by the MDRRMO or barangay officials.",
            "Subaybayan ang PAGASA at mga abiso ng LGU.\nMaghanda ng go-bag: tubig, pagkain para sa 3 araw, gamot, flashlight, "
            "radyo, power bank, kopya ng ID.\nItali ang bubong at ipasok ang mga bagay na maaaring liparin.\nAlamin ang "
            "evacuation center ng barangay.\nLumikas nang maaga kapag sinabihan ng MDRRMO o barangay."))
        PreparednessGuide.objects.create(hazard=H.FLOOD, order=2, **tr(
            "title", "Flash floods and landslides", "Biglang baha at pagguho ng lupa"), **tr(
            "body",
            "Sibuyan's rivers rise fast after heavy rain in the mountains. Stay away from riverbanks.\nDo not cross "
            "flooded rivers or spillways.\nWatch for cracks, tilting trees and muddy water on slopes - report them.\n"
            "Move to higher ground at once if you hear rumbling."))
        PreparednessGuide.objects.create(hazard=H.EARTHQUAKE, order=3, **tr(
            "title", "Earthquake", "Lindol"), **tr(
            "body", "Drop, cover and hold on.\nAfter shaking stops, go to an open area.\nIf you are near the coast and "
                    "the shaking is strong or long, move inland and uphill: a tsunami may follow."))

    # ---------------------------------------------------------------- tourism
    def make_tourism(self):
        K = Attraction.Kind
        mggnp = Attraction.objects.create(
            municipality=self.towns["MAG"], kind=K.MOUNTAIN, name="Mt. Guiting-Guiting", slug="mt-guiting-guiting",
            is_protected_area=True, environmental_fee=Decimal("500"), latitude=Decimal("12.4136"), longitude=Decimal("122.5644"),
            **tr("summary", "The jagged 2,058 m peak at the heart of Mt. Guiting-Guiting Natural Park, one of the "
                            "toughest climbs in the Philippines.",
                 "Ang matulis na 2,058 m na tuktok sa gitna ng Mt. Guiting-Guiting Natural Park."),
            **tr("tips", "Train well: the trail has knife-edge ridges and boulders.\nClimb only in the dry months and "
                         "after checking the trail status.\nBring at least 3 litres of water per day.\nCarry out all your trash."),
            **tr("guide_requirement", "DENR climbing permit, accredited guide and porter required (sample)"),
            **tr("fee_notes", "Sample: environmental fee per climber; guide fees separate"),
            **tr("best_time", "Dry months, usually March to May. The trail closes in the rainy season; confirm "
                              "with the Protected Area Office (sample)."),
            **tr("getting_there", "Ferry to Magdiwang, then a tricycle to the Protected Area Office to register and "
                                  "attend the climbers' orientation (sample)."),
        )
        ClimbAdvisory.objects.create(
            attraction=mggnp, trail="Main trail (sample)", status=ClimbAdvisory.Status.CLOSED,
            valid_from=self.today - timedelta(days=20), valid_until=self.today + timedelta(days=60),
            **tr("season_note", "Sample: closed during the rainy season for safety and trail recovery."),
            **tr("permit_requirements", "Sample: register at the Protected Area Office, attend the orientation, sign the "
                                        "waiver, present a medical certificate, hire an accredited guide."),
        )
        # Pins are approximate (sample): the Tourism Offices should confirm exact coordinates.
        for code, kind, name, slug, summary, fee, guide, lat, lon, best, getting in [
            ("SFE", K.BEACH, "Cresta de Gallo", "cresta-de-gallo", "A small white-sand islet off San Fernando, reached by boat.",
             "100", "Boat hire through accredited operators (sample)", "12.2167", "122.6917",
             "Calm-sea months, usually March to May. Boats do not sail in rough weather.",
             "Hire an accredited boat from San Fernando (sample: about 45 minutes each way)."),
            ("SFE", K.RIVER, "Cantingas River", "cantingas-river", "A clear, cold river with a popular jump-off spot and swimming holes.",
             "50", "", "12.3150", "122.6150",
             "Clear days all year. Stay out of the water after heavy rain, when the river rises fast.",
             "About 10 to 15 minutes by tricycle from San Fernando town proper (Barangay Taclobo)."),
            ("MAG", K.FALLS, "Lambingan Falls", "lambingan-falls", "A forest waterfall with a natural pool near the foot of the mountains.",
             "30", "", "12.4630", "122.5280",
             "Dry season. The forest path is slippery after rain (sample).",
             "A short ride from Magdiwang town, then a forest walk; ask the Tourism Office for a guide (sample)."),
            ("SFE", K.FALLS, "Cawa-Cawa Falls", "cawa-cawa-falls", "Tiered falls with cauldron-like pools (location to be confirmed by the Tourism Office).",
             "30", "Local guide recommended", "12.2950", "122.5800",
             "Dry season (sample).", "Ask the San Fernando Tourism Office for directions and a local guide (sample)."),
        ]:
            Attraction.objects.create(municipality=self.towns[code], kind=kind, name=name, slug=slug,
                                      environmental_fee=Decimal(fee), latitude=Decimal(lat), longitude=Decimal(lon),
                                      **tr("summary", summary), **tr("guide_requirement", guide),
                                      **tr("fee_notes", "Sample fee"), **tr("best_time", best),
                                      **tr("getting_there", getting))
        B = Business.Kind
        for town in self.towns.values():
            for kind, name in [(B.ACCOMMODATION, "Sample Lodge"), (B.RESTAURANT, "Sample Carinderia"),
                               (B.GUIDE, "Sample Guides Association"), (B.TRANSPORT, "Sample Habal-Habal Operators")]:
                Business.objects.create(municipality=town, kind=kind, name=f"{name} {town.name}", is_accredited=True,
                                        accredited_by="LGU Tourism Office (sample)", phone="0900 000 0000",
                                        **tr("description", "Sample listing."))
        S = TravelRule.Scope
        for scope, title, body in [
            (S.PROTECTED_AREA, "Do not collect plants or animals",
             "Sibuyan's forests are home to endemic species such as Nepenthes sibuyanensis. Collecting, buying or "
             "selling wildlife is illegal under RA 9147 and RA 7586 (NIPAS Act, as amended by RA 11038)."),
            (S.PROTECTED_AREA, "Leave no trace", "Stay on trails, carry out all trash, and do not use soap in rivers."),
            (S.ANCESTRAL_DOMAIN, "Respect the Sibuyan Mangyan Tagabukid",
             "Parts of the island are within the ancestral domain of the Sibuyan Mangyan Tagabukid. Ask permission "
             "before entering communities, follow their guides' instructions, and ask before taking photos."),
            (S.GENERAL, "Register with the Tourism Office", "Tell the Municipal Tourism Office your itinerary, "
                                                            "especially for climbs and remote falls."),
        ]:
            TravelRule.objects.create(scope=scope, **tr("title", title), **tr("body", body))

    # ------------------------------------------------- market, jobs, civic
    def make_market_and_civic(self):
        L = Listing.Kind
        for code, kind, title, price, unit in [
            ("MAG", L.HONEY, "Wild Sibuyan honey (sample)", "450", "per 750 ml bottle"),
            ("SFE", L.BALITSAW, "Balitsaw (sample)", "120", "per pack"),
            ("CAJ", L.WOVEN, "Handwoven bags and mats (sample)", "350", "per piece"),
            ("CAJ", L.FISH, "Dried fish (sample)", "300", "per kilo"),
            ("MAG", L.FARM, "Organic vegetables (sample)", "60", "per bundle"),
        ]:
            Listing.objects.create(municipality=self.towns[code], kind=kind, title=title, price=Decimal(price), unit=unit,
                                   seller_name="Sample Seller", contact_phone="0900 000 0000", is_approved=True,
                                   description="Sample marketplace listing.")
        JobPosting.objects.create(municipality=self.towns["SFE"], kind=JobPosting.Kind.LGU, employer="LGU San Fernando",
                                  title="Administrative Aide I (sample)", description="Sample job posting.",
                                  pay="Salary Grade 1 (sample)", how_to_apply="Submit your PDS to the HR Office.",
                                  deadline=self.today + timedelta(days=14), is_approved=True)
        JobPosting.objects.create(kind=JobPosting.Kind.LIVELIHOOD, employer="TESDA (sample)",
                                  title="Free training: tour guiding (sample)", description="Sample livelihood posting.",
                                  how_to_apply="Register at your Municipal Tourism Office.",
                                  deadline=self.today + timedelta(days=21), is_approved=True)
        D = PublicDocument.Kind
        for town in self.towns.values():
            PublicDocument.objects.create(municipality=town, kind=D.CHARTER, title=f"Citizen's Charter of {town.name} (sample)",
                                          date_issued=self.today - timedelta(days=90), **tr("summary", "Sample document."))
            PublicDocument.objects.create(municipality=town, kind=D.ORDINANCE, number="Ord. No. 2026-01 (sample)",
                                          title="Sample ordinance on solid waste segregation",
                                          date_issued=self.today - timedelta(days=60))
            docs = [
                (D.PROCUREMENT, "ITB 2026-014", "Invitation to bid: rehabilitation of a farm-to-market road", 12),
                (D.PROCUREMENT, "RFQ 2026-031", "Request for quotation: office and school supplies", 20),
                (D.PROCUREMENT, "NOA 2026-009", "Notice of award: rural health unit equipment", 41),
                (D.PROCUREMENT, "", "Pre-bid conference notice: municipal water system expansion", 55),
                (D.BUDGET, "", "Statement of receipts and expenditures, 3rd quarter", 25),
                (D.BUDGET, "", "Annual budget summary, fiscal year 2026", 200),
                (D.BUDGET, "", "Full Disclosure Policy report: trust fund utilization, 2nd quarter", 110),
                (D.BUDGET, "", "20% development fund utilization, 2nd quarter", 115),
                (D.EXECUTIVE_ORDER, "EO No. 12, s. 2026", "Creating the SibuyanConnect technical working group", 30),
                (D.EXECUTIVE_ORDER, "EO No. 9, s. 2026", "Suspension of classes and work during typhoons: protocol", 95),
            ]
            for kind, number, title, days in docs:
                PublicDocument.objects.create(
                    municipality=town, kind=kind, number=f"{number} (sample)" if number else "",
                    date_issued=self.today - timedelta(days=days),
                    **tr("title", f"{title} (sample)"), **tr("summary", "Sample document for the prototype."),
                )
            mayor_names = {"MAG": "Hon. Juan dela Cruz", "SFE": "Hon. Maria Santos", "CAJ": "Hon. Jose Reyes"}
            for n, (position, name) in enumerate([("Municipal Mayor", mayor_names[town.code]),
                                                  ("Municipal Vice Mayor", "Hon. Ana Bautista")], start=1):
                Official.objects.create(municipality=town, name=f"{name} (sample)", position=position, order=n,
                                        term="2025-2028", office=self.office(town, Office.Kind.MAYOR) if n == 1 else None)
        EnvironmentUpdate.objects.create(
            kind=EnvironmentUpdate.Kind.CLEANUP, source="MENRO (sample)",
            **tr("title", "Coastal clean-up results (sample)"),
            **tr("body", "Sample report: volunteers collected sacks of mostly plastic waste along the shoreline. "
                         "Figures to be supplied by MENRO."))
        EnvironmentUpdate.objects.create(
            kind=EnvironmentUpdate.Kind.PROTECTED_AREA, source="DENR-PAMO (sample)", municipality=self.towns["MAG"],
            **tr("title", "Protected Area Management Board meeting held (sample)"),
            **tr("body", "Sample update summarising agenda items of the PAMB meeting, as reported by DENR."))

    # -------------------------------------------------------------------- FAQ
    def make_faq(self):
        T = FAQEntry.Topic
        faqs = [
            (T.SERVICES, "/services/",
             ("How do I get a cedula?", "Paano kumuha ng cedula?", "Pauno ako makakuha it cedula?"),
             ("Go to the Municipal Treasurer's Office with a valid ID. The basic tax is PHP 5, plus PHP 1 for every "
              "PHP 1,000 of income. It takes about 5 minutes.",
              "Pumunta sa Municipal Treasurer's Office dala ang valid ID. PHP 5 ang basic, dagdag PHP 1 bawat PHP 1,000 "
              "na kita. Mga 5 minuto lang.",
              "Mag-adto sa Municipal Treasurer's Office dara ang imong ID. PHP 5 ang basic, dugang PHP 1 kada PHP 1,000 "
              "nga kita. Mga 5 minutos lang. (Draft translation)"),
             ("cedula, community tax, ctc", "cedula, sedula, buwis", "cedula, sedula")),
            (T.SERVICES, "/services/",
             ("How do I get a copy of my birth certificate?", "Paano kumuha ng kopya ng birth certificate?",
              "Pauno mag-kuha it kopya it birth certificate?"),
             ("Ask the Municipal Civil Registrar in the town where the birth was registered. Bring a valid ID. For a "
              "PSA copy, request it through the MCR or a PSA outlet.",
              "Magtanong sa Municipal Civil Registrar ng bayan kung saan nakarehistro ang kapanganakan. Magdala ng ID. "
              "Para sa kopya ng PSA, mag-request sa MCR o sa PSA.",
              "Pamangkot sa Municipal Civil Registrar it banwa kung diin narehistro. Mag-dara it ID. (Draft translation)"),
             ("birth certificate, psa, nso, civil registry", "birth certificate, kapanganakan, psa", "birth certificate, pagkatawo")),
            (T.TRANSPORT, "/transport/",
             ("Is the ferry cancelled today?", "May biyahe ba ang barko ngayon?", "May biyahe bala ang barko subong?"),
             ("Check the Ferry Board, which port and LGU staff update. Sailings are suspended when PAGASA raises a gale "
              "warning or wind signal. Always confirm with the shipping line.",
              "Tingnan ang Ferry Board na ina-update ng port at LGU. Walang biyahe kapag may gale warning o signal ng "
              "bagyo. Kumpirmahin sa shipping line.",
              "Tan-awa ang Ferry Board. Wara it biyahe kung may gale warning o signal it bagyo. (Draft translation)"),
             ("ferry, boat, ship, schedule, cancelled, sailing", "barko, biyahe, bangka, kansela", "barko, biyahe, sakayan")),
            (T.EMERGENCY, "/emergency/",
             ("What is the emergency hotline?", "Ano ang emergency hotline?", "Ano ang emergency hotline?"),
             ("Dial 911 for any emergency. Town MDRRMO, police, fire and health numbers are on the Emergency page, "
              "which also works offline.",
              "Tumawag sa 911 para sa anumang emergency. Nasa Emergency page ang numero ng MDRRMO, pulis, bumbero at "
              "RHU ng bawat bayan, at gumagana ito kahit offline.",
              "Tawag sa 911 kung may emergency. Ang mga numero it MDRRMO, pulis kag bumbero yara sa Emergency page. (Draft translation)"),
             ("emergency, hotline, police, fire, ambulance, mdrrmo, 911", "emergency, pulis, bumbero, ambulansya", "emergency, pulis, bumbero")),
            (T.SERVICES, "/services/",
             ("How do I get a senior citizen ID?", "Paano kumuha ng senior citizen ID?", "Pauno mag-kuha it senior citizen ID?"),
             ("Go to the Office of Senior Citizens Affairs (OSCA) with proof of age, two 1x1 photos and a barangay "
              "certificate of residency. It is free.",
              "Pumunta sa OSCA dala ang patunay ng edad, dalawang 1x1 na litrato at barangay certificate of residency. Libre ito.",
              "Mag-adto sa OSCA dara ang patunay it edad, duha ka 1x1 nga litrato kag barangay certificate. Libre ra. (Draft translation)"),
             ("senior, osca, elderly, 60", "senior, matanda, lolo, lola", "senior, maeam")),
            (T.SERVICES, "/services/",
             ("When must I renew my business permit?", "Kailan dapat i-renew ang business permit?", ""),
             ("Every January. Pay business taxes within the first 20 days of January to avoid surcharges. Bring your "
              "previous permit and sworn declaration of gross sales to the BPLO.",
              "Tuwing Enero. Bayaran ang buwis sa unang 20 araw ng Enero para walang multa. Dalhin ang lumang permit at "
              "sworn declaration of gross sales sa BPLO.", ""),
             ("business permit, renewal, mayor's permit, bplo", "negosyo, permit, renew", "")),
            (T.TOURISM, "/",
             ("Can I climb Mt. Guiting-Guiting?", "Puwede bang umakyat sa Mt. Guiting-Guiting?", "Pwede bala mag-saka sa Guiting-Guiting?"),
             ("Only with a permit from the Protected Area Office (DENR) and an accredited guide, and only when the trail "
              "is open. It is usually closed during the rainy season. Register with the Magdiwang Tourism Office first.",
              "Kailangan ng permit mula sa Protected Area Office (DENR) at accredited guide, at kapag bukas lang ang trail. "
              "Karaniwang sarado tuwing tag-ulan.",
              "Kinahangean it permit halin sa DENR kag accredited guide. Sarado kung tag-uean. (Draft translation)"),
             ("climb, mountain, guiting, trail, permit, denr, hike", "akyat, bundok, trail", "bukid, saka")),
            (T.GENERAL, "/concerns/track/",
             ("How do I follow up my concern?", "Paano i-follow up ang aking concern?", "Pauno ko i-follow up ang akon concern?"),
             ("Open the link we emailed you, or go to Track a concern and enter your ticket number and the email or "
              "mobile number you used. You can message the office there.",
              "Buksan ang link na in-email sa iyo, o pumunta sa Track a concern at ilagay ang ticket number at email o "
              "mobile number na ginamit mo.",
              "Bukasa ang link nga gin-email sa imo, o mag-adto sa Track a concern. (Draft translation)"),
             ("ticket, follow up, status, track, concern, complaint", "reklamo, follow up, ticket", "reklamo, ticket")),
            (T.PROGRAMS, "/programs/",
             ("How can my family join 4Ps?", "Paano makasali sa 4Ps?", "Pauno kami maka-apil sa 4Ps?"),
             ("4Ps households are chosen from the DSWD Listahanan assessment of poor households. Ask your MSWDO or the "
              "4Ps Municipal Link whether your household has been assessed.",
              "Pinipili ang mga pamilya sa 4Ps mula sa Listahanan ng DSWD. Magtanong sa MSWDO o sa 4Ps Municipal Link.",
              "Ang mga pamilya sa 4Ps ginapili halin sa Listahanan it DSWD. Pamangkot sa MSWDO. (Draft translation)"),
             ("4ps, pantawid, listahanan, dswd", "4ps, pantawid, ayuda", "4ps, ayuda")),
            (T.PROGRAMS, "/programs/eligibility/",
             ("What assistance can I get?", "Anong tulong ang makukuha ko?", "Ano nga bulig ang makuha ko?"),
             ("Use the eligibility checker on the Programs page. Answer a few questions and it lists programs you may "
              "qualify for. Nothing you enter is saved.",
              "Gamitin ang eligibility checker sa Programs page. Sagutin ang ilang tanong para makita ang mga programang "
              "puwede sa iyo. Walang nai-save.",
              "Gamita ang eligibility checker sa Programs page. (Draft translation)"),
             ("assistance, help, aid, program, scholarship, eligible", "tulong, ayuda, iskolarsip", "bulig, ayuda")),
        ]
        for topic, link, (q_en, q_fil, q_rol), (a_en, a_fil, a_rol), (k_en, k_fil, k_rol) in faqs:
            FAQEntry.objects.create(topic=topic, link_url=link, **tr("question", q_en, q_fil, q_rol),
                                    **tr("answer", a_en, a_fil, a_rol), **tr("keywords", k_en, k_fil, k_rol))

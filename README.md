# SibuyanConnect

A mobile-first community portal for **Sibuyan Island, Romblon**: Magdiwang, San Fernando and Cajidiocan.
Residents can look up LGU services, check which assistance programs they may qualify for, and report
concerns that are routed to the right municipal office. Tourism information comes second.

Built with Python 3 and Django using free and open-source tools only. You don't need a paid service
or an API key with billing to run it.

> **Prototype with SAMPLE DATA.** Barangay names and national laws and programs are real. Office
> contacts, phone numbers, fees, schedules, people and businesses are placeholders. Each LGU must
> replace them before launch. The Romblomanon text is a **draft** that a native speaker needs to review.

## What's in the prototype

| Area | Status | URL |
|---|---|---|
| Home dashboard: town switcher, live alerts, quick links, weather, today's sailings | Working | `/` |
| Municipal Services Directory with the "What do I need?" checklist generator | Working | `/services/` |
| Programs & Assistance with the eligibility checker and application schedules | Working | `/programs/`, `/programs/eligibility/` |
| Report a Concern: ticket number, routing, status tracker, two-way messages | Working | `/concerns/new/`, `/concerns/track/` |
| News & Updates with pinned advisories, sharing and RSS | Working | `/news/`, `/news/feed/` |
| Ferry & Transport Board | Working | `/transport/` |
| Emergency & Disaster Hub (works offline) | Working | `/emergency/` |
| Help Assistant (FAQ search, optional LLM, hand-off to staff) | Working | `/assistant/` |
| CMS: customised Django admin with roles and analytics | Working | `/admin/`, `/admin/analytics/` |
| Tourism: attractions, climb advisories, responsible-travel rules, accredited businesses | Working | `/tourism/` |
| Transparency: documents by type, officials, offices directory | Working | `/transparency/` |
| Events calendar, Marketplace & Jobs, Environment Watch | Models, admin and sample data built; public pages are phase 2 | see [docs/SITEMAP.md](docs/SITEMAP.md) |

Other docs: [photo and font credits](CREDITS.md) · [site map](docs/SITEMAP.md) · [database schema](docs/SCHEMA.md) · [rollout plan](docs/ROLLOUT.md)

## Quick start (Windows, macOS or Linux)

Requires Python 3.10 or newer.

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py loaddata sample_data      # SAMPLE data for all three towns
python manage.py shift_sample_dates        # move sample sailings/alerts so they start today
python manage.py setup_roles               # create the 4 staff roles (Django groups)
python manage.py compile_translations      # Filipino and Romblomanon UI strings
python manage.py create_demo_staff         # optional: demo CMS logins (DEBUG only)
python manage.py runserver
```

Then open http://127.0.0.1:8000/ for the public site and http://127.0.0.1:8000/admin/ for the CMS.

Demo CMS accounts from `create_demo_staff` all use the password `sibuyan-demo-2026`:

| Username | Role | Sees |
|---|---|---|
| `superadmin` | Super Admin | Everything, all towns |
| `mag_admin` | Municipal Admin | Magdiwang content and tickets |
| `mag_engineering` | Department Staff | Only tickets routed to Magdiwang Engineering |
| `mag_mswdo` | Department Staff | Only tickets routed to Magdiwang MSWDO |
| `editor` | Content Editor | News, services, programs, schedules; no tickets |

Emails (ticket confirmations, status updates, replies) print to the terminal by default.

### Run the tests

```bash
python manage.py test
```

The 27 tests load the sample fixture. They cover every public page, language and town switching,
the checklist generator, eligibility rules, the full concern flow (routing, consent, photo
compression, private ticket links, tracking, email), admin role scoping, staff replies, analytics
and the assistant.

## Trying the main flows

1. **Services**: open *Services*, pick *Birth registration*, answer "Yes" to the late-registration
   question under **What do I need?**, and the checklist adds the late-registration documents.
2. **Eligibility**: open *Programs → Which programs can I get?*, enter age 67, and Social Pension and
   senior privileges appear. Tick "fisherfolk" to see BFAR support.
3. **Report a Concern**: file a road concern in Magdiwang. You get a ticket number like
   `SC-MAG-2026-00010` and a private tracking link, and it is routed to Magdiwang Engineering.
   Sign in to `/admin/` as `mag_engineering`, open the ticket, set the status to *In progress* and
   add a reply. The citizen's page and email update.
4. **Assistant**: ask "Paano kumuha ng cedula?" in Filipino. Ask something it doesn't know and it
   offers to open a ticket for staff.

## How it's built

- **Django 5.2** with server-rendered templates. Interactivity uses **HTMX** (vendored in
  `static/vendor/` so it works offline) plus about 80 lines of plain JavaScript. Every form also
  works without JavaScript.
- **Database**: SQLite for development, PostgreSQL in production via `DATABASE_URL`. On PostgreSQL
  the assistant uses full-text search (`SearchVector`/`SearchRank`). On SQLite it falls back to
  keyword scoring.
- **Languages**: Django i18n for UI strings (`locale/`) and **django-modeltranslation** for content
  (each translated field has `_en`, `_fil` and `_rol` columns, edited side by side in the admin).
  Romblomanon has no two-letter ISO code, so it uses ISO 639-3 `rol`. `core.middleware` activates it
  directly. Missing translations fall back to English.
- **Design**: minimalist green, white and blue. Colours are CSS variables at the top of
  `static/css/site.css`, and every text and background pair passes WCAG AA (secondary grey darkens
  slightly on mint and sky backgrounds to stay above 4.5:1). Headings use Fraunces and body text uses
  Inter, both self-hosted so they work offline. The line icons are one cached SVG sprite
  (`static/img/icons.svg`), used with `{% icon "name" %}` from `core/templatetags/ui.py`.
- **Photos**: free-licence photos of Sibuyan from Wikimedia Commons; `CREDITS.md` lists each one
  and how it was confirmed to be from Sibuyan, plus the places that still need photos.
  `tools/build_photos.py` crops and compresses them to WebP at the sizes the layout uses, and
  `core/photos.py` holds alt text and credits. The desktop hero crossfades between 3 photos; it stays
  on one photo for reduced motion, Data Saver, 2G connections and phones.
- **Low bandwidth** (homepage, measured): about 20 KB of compressed HTML, CSS, JS, icons and pattern;
  about 81 KB with fonts. With photos it is about 150 KB on a standard-density phone screen, about
  192 KB on a high-density one, and about 248 KB on desktop. The two crossfade photos add about
  80 KB on desktop after the page has loaded. Everything below the hero is lazy-loaded behind mint
  placeholders. Leaflet and its map tiles load only when the tourism map scrolls into view; HTMX
  loads only on the pages that use it. Uploaded photos are resized to 1280 px JPEG, and Pillow strips
  their GPS EXIF data.
- **PWA**: `/manifest.webmanifest` and `/sw.js`. The service worker pre-caches the home page,
  hotlines, ferry board, programs and **every service page**. Its cache version comes from the
  database, so phones refresh it when staff edit a service or a sailing. Private pages (tickets,
  admin, accounts) are never cached.
- **Maps**: Leaflet 1.9.4 with OpenStreetMap tiles, loaded only on pages that have a map.
- **Weather**: the browser calls the Open-Meteo API (free, no key), with links to PAGASA bulletins.
- **Notifications**: Django email (`core/notify.py`). SMS is a pluggable hook and is off by
  default. Set `SMS_BACKEND` to a dotted path such as `core.notify.console_sms_backend` to test it.
- **Assistant** (`assistant/engine.py`): layer 1 searches FAQ entries in all three languages, plus
  service and program names. Layer 2 is optional (`ASSISTANT_LLM_BACKEND=gemini` with a free
  Google AI Studio key, or `ollama` for a self-hosted model) and only answers from site content.
  With no answer, it hands off to a concern ticket. Questions are logged anonymously so staff can
  find gaps in the FAQ.
- **Privacy (RA 10173)**: consent checkbox with a timestamp and privacy-notice version on every
  concern, a privacy notice at `/privacy/`, contact details visible only to the staff handling the
  ticket, ticket links protected by a random token, and the eligibility checker saves nothing.
- **Security**: Django auth for staff, CSRF on all forms, and HTTPS/HSTS/secure cookies when
  `DJANGO_DEBUG=false`.

### Roles and permissions

`python manage.py setup_roles` creates the four groups. A staff member's scope comes from their
**Staff profile** (*Admin → Core → Staff profiles*):

- **Super Admin**: all permissions; leave the profile's municipality empty.
- **Municipal Admin**: all content and tickets for the municipality set on their profile.
- **Department Staff**: tickets routed to the office set on their profile; can reply and change status.
- **Content Editor**: add and edit news, services, programs, schedules, ferry status and directory
  content.

To add a real staff member: create the user in *Admin → Users* and tick *Staff status*. Add them to
one group, then create their Staff profile.

### Updating the sample data

`python manage.py seed_sample_data --flush --dump fixtures/sample_data.json` rebuilds the sample
set from `core/management/commands/seed_sample_data.py` and rewrites the fixture.

## Free hosting for the pilot

**PythonAnywhere (free "Beginner" account): recommended for the pilot.** The disk is persistent, so
uploaded concern photos survive. The free plan has no PostgreSQL (SQLite works) and only allows
outbound internet to an allow-list, so keep `ASSISTANT_LLM_BACKEND=none` there.

1. Upload the code (`git clone` in a Bash console), then
   `mkvirtualenv --python=python3.10 sc && pip install -r requirements.txt`.
2. In *Web*, add a manual-config app and point the WSGI file at `sibuyanconnect.wsgi`.
3. Set the environment variables from `.env.example`. With manual config, set them at the top of
   the WSGI file.
4. Run `python manage.py migrate`, `compile_translations`, `collectstatic`, `setup_roles` and
   `createsuperuser`.
5. Map `/static/` to `staticfiles/` and `/media/` to `media/` in the *Web* tab.

**Render (free tier)**: `render.yaml` and `build.sh` are included (*New → Blueprint*). You get free
PostgreSQL with full-text search. Free web services sleep when idle, free databases expire after a
set period, and the disk is wiped on each deploy, so uploaded photos don't survive. Use it for
demos, or add free object storage later.

Free tiers change. Check the current limits on each provider's pricing page before committing.

## Project layout

```
sibuyanconnect/   settings, URLs
core/             towns, barangays, offices, staff profiles, alerts, PWA, i18n middleware,
                  image compression, notifications, management commands, tests
services/         Services Directory + checklist generator
programs/         Programs + eligibility checker
concerns/         tickets, messages, status history, routing, CMS analytics
news/             posts (RSS), events + photo galleries
transport/        ferry routes, dated sailings with status, jeepney trips, tricycle fares
emergency/        hotlines, evacuation centers, preparedness guides
tourism/          attractions, climb advisories, accredited businesses, travel rules
marketplace/      product listings, job and livelihood postings
civic/            Transparency Corner documents, officials, Environment Watch
assistant/        FAQ (3 languages), search engine, optional LLM, query log
templates/ static/ locale/ fixtures/ docs/ tools/
```

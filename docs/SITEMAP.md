# SibuyanConnect: site map and page list

Legend: ✅ built in the prototype · 🟡 models, CMS and sample data built; public page is phase 2

Every public page respects the **town switcher** (All / Magdiwang / San Fernando / Cajidiocan) and the
**language switcher** (English / Filipino / Romblomanon). Mobile users get a fixed bottom bar with
Home · Services · Report · Ferry · Hotlines.

```
/                                   ✅ Home dashboard
├── /news/                          ✅ News & Updates (category chips, pinned first, pagination)
│   ├── /news/<id>/<slug>/          ✅ Article (Share, Facebook, SMS)
│   └── /news/feed/                 ✅ RSS feed
├── /services/                      ✅ Services Directory (search in any language, category chips)
│   ├── /services/<id>/<slug>/      ✅ Service detail: requirements, steps, office, fees, time, hours, forms, map
│   └── /services/<id>/checklist/   ✅ "What do I need?" printable checklist (HTMX partial or full page)
├── /programs/                      ✅ Programs & Assistance + application schedules
│   ├── /programs/eligibility/      ✅ Eligibility checker
│   └── /programs/<id>/<slug>/      ✅ Program detail
├── /concerns/
│   ├── /concerns/new/              ✅ Report a Concern / Ask Your LGU
│   ├── /concerns/track/            ✅ Find a ticket by ticket number + email/mobile
│   ├── /concerns/t/<no>/<token>/   ✅ Private ticket page: status tracker + two-way messages
│   └── /concerns/mine/             ✅ Signed-in citizen's tickets
├── /assistant/                     ✅ Help Assistant chat
├── /transport/                     ✅ Ferry board (3-day status), routes, jeepney trips, tricycle fares
├── /emergency/                     ✅ Hotlines (tap to call), weather + PAGASA/PHIVOLCS, evacuation centers, guides
├── /tourism/                       ✅ Attractions, trail status, travel rules, accredited businesses
│   ├── /tourism/<slug>/            🟡 Attraction: map, tips, guide requirement, environmental fee
│   ├── /tourism/guiting-guiting/   🟡 Climb info: DENR permits, trail status, seasonal closures
│   ├── /tourism/stay-eat-go/       🟡 Accredited accommodations, restaurants, guides, transport
│   └── /tourism/responsible-travel/🟡 Protected-area and ancestral-domain rules
├── /events/                        🟡 Festivals & events calendar (month view + list)
│   └── /events/<slug>/             🟡 Event with photo gallery
├── /market/                        🟡 Local products (honey, balitsaw, woven goods, farm and fish)
├── /jobs/                          🟡 Job and livelihood postings
├── /transparency/                  ✅ Ordinances, EOs, budget, procurement, Citizen's Charter (filter by type)
│   └── /transparency/#offices      ✅ Officials and offices directory
├── /environment/                   🟡 Environment Watch updates
├── /privacy/                       ✅ Privacy Notice (RA 10173)
├── /offline/                       ✅ Offline fallback page
├── /accounts/login/ · signup/      ✅ Optional citizen account
├── /manifest.webmanifest · /sw.js  ✅ PWA
└── /admin/                         ✅ CMS (customised Django admin)
    └── /admin/analytics/           ✅ Most-viewed services and programs, tickets and resolution time per office
```

## Page details

| Page | Main content | Primary users |
|---|---|---|
| Home | Split hero (heading, service search, Report a Concern and Ferry Schedule buttons, photo), town pills, dismissible alert strip, 6 service tiles with counts, municipal mayors, "Today on Sibuyan" (weather, ferry status, hotlines), programs, transparency panels, latest news, Discover Sibuyan banner, 4-column footer | Residents, tourists |
| Services list | Search, category chips, cards showing processing time and fee | Residents |
| Service detail | Facts box (office, fees, time, hours, who may apply, location), requirements with "only if" conditions, numbered steps, checklist generator, downloadable forms, office map, legal basis, share | Residents |
| Programs | Eligibility checker banner, open and upcoming schedules, type chips, program cards | Residents |
| Eligibility checker | Town, age and income bracket, 9 yes/no situations; results with reasons and a disclaimer; nothing is stored | Residents |
| Report a Concern | Category tiles, subject, details, photo, town and barangay (filtered list), landmark, name, email or mobile, privacy box and consent | Residents |
| Ticket page | Ticket number, 4-step tracker (Received → Assigned → In Progress → Resolved), routed office, details, photo, message thread, reply box | Residents |
| Ferry board | 3-day sailing table with status badges and notes, routes, jeepney table, tricycle fares | Residents, tourists |
| Emergency hub | Tap-to-call hotlines (911 first), weather and official bulletin links, evacuation centers by barangay, preparedness guides | Everyone |
| Help Assistant | Chat in 3 languages; FAQ answers with "learn more" links, related pages, optional AI answer, hand-off button | Everyone |
| CMS | Per-module admin with filters, list-editable ferry status, ticket inline replies and history, translation tabs, analytics | LGU staff |

## Offline availability

The service worker pre-caches: Home, Services list, **every service detail page**, Programs list,
Emergency hub, Ferry board and the Offline page. Pages a user opens later are cached on first visit.
Ticket pages, accounts and the admin are never cached.

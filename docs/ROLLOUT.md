# SibuyanConnect: rollout plan

**Approach:** pilot in one municipality, train its staff, fix what the pilot shows, then expand to
the other two towns. Running costs stay at ₱0 (free hosting, free and open-source software). The
real investment is staff time.

## Choosing the pilot town

Pick the municipality that best meets these conditions:

- A Mayor's Office willing to sponsor it, plus one ICT or admin focal person with about 4 hours a week
- An up-to-date Citizen's Charter (RA 11032) to load into the Services Directory
- Offices that already reply to walk-in or Facebook concerns (MDRRMO, Engineering, MSWDO first)
- An appointed Data Protection Officer, or one who can be named during preparation

## Timeline (about 7 months)

| Phase | Weeks | What happens | Done when |
|---|---|---|---|
| **0. Preparation** | 1–4 | Agreement with the pilot LGU, naming the focal person, DPO and one "ticket champion" per office. Replace all SAMPLE data: services from the Citizen's Charter, real office contacts, **called-and-verified hotlines**, ferry routes from the port, programs and schedules from MSWDO/MAO. Native speakers review the Filipino and Romblomanon text. DPO adopts the Privacy Notice. Deploy to PythonAnywhere free tier. | Every sample badge is gone for the pilot town, and the DPO has signed off |
| **1. Staff training** | 5–6 | Three short sessions (below). Each office handles 10 practice tickets end to end. | Every office has resolved a practice ticket |
| **2. Soft launch** | 7–8 | Open to barangay officials, BHWs and SK first. They file real concerns and give feedback. | 30 real tickets handled |
| **3. Public pilot** | 9–18 | Announce on the LGU Facebook page, radio, barangay assemblies, a QR poster at the Municipal Hall and port. Monthly review of analytics and assistant gaps. | Targets below met, or causes known |
| **4. Evaluation** | 19–20 | Survey residents and staff, review analytics, fix issues, update the training kit. Decide whether to expand. | Expansion approved by the participating Mayors |
| **5. Expansion** | 21–30 | Repeat phases 0–2 for the second and third towns, with pilot-town staff as peer trainers. Turn on island-wide content (ferries, hotlines, tourism). | All three towns live |
| **6. Island-wide features** | 30+ | Publish the phase-2 public pages (tourism, events calendar, marketplace, transparency, environment). Consider PostgreSQL hosting, a `.gov.ph` domain, and SMS if a free or sponsored gateway turns up. | |

## Training plan

| Session | Who | Length | Content |
|---|---|---|---|
| CMS basics | Content editors, focal person | 2 hrs | Logging in, news and pinned advisories, alerts, editing services in 3 languages, ferry status from a phone, uploading forms |
| Handling tickets | Department staff, office heads | 2 hrs | Reading a ticket, assigning, replying, internal notes, status changes, re-routing, privacy rules (who may see contact details) |
| Administration | Municipal admin, DPO | 1.5 hrs | Creating staff accounts, groups and staff profiles, analytics, assistant query log, data-privacy duties, backups |

Hand out a one-page printed quick guide per role. Record short screen videos in Filipino for
refreshers.

## Working agreements for the pilot

- **Response targets:** acknowledge (Assigned) within 1 working day, and update the status at least
  weekly until Resolved.
- **Ferry status:** port or MDRRMO staff update the day's sailings by 6:00 AM and whenever there is a
  PAGASA or Coast Guard advisory.
- **Content owners:** each office keeps its own services current. The focal person checks monthly.
- **Backups:** download the database weekly (PythonAnywhere Files tab), and keep it on an
  LGU-owned drive.

## Success measures (end of pilot)

| Measure | Target |
|---|---|
| Concerns filed through the portal | 150+ |
| Tickets acknowledged within 1 working day | 80% |
| Median time to resolve (per office, from `/admin/analytics/`) | Baseline set, then improving month on month |
| Unanswered assistant questions (`layer = none`) | Falling each month as FAQ entries are added |
| Residents who found what they needed (survey) | 70% |
| Staff who can handle a ticket without help | 100% of trained staff |

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Weak mobile data | PWA offline caching, ~4 KB pages, and an SMS-share link on news. Walk-in and phone channels stay open |
| Tickets go unanswered | Ticket champion per office, a weekly review in the Mayor's staff meeting, and the analytics page |
| Wrong or outdated information (fees, hotlines) | Verified flag on hotlines, an "updated" date on services, and a monthly check by the focal person |
| Privacy breach | Least-privilege roles, ticket links behind a token, DPO oversight, staff training, HTTPS |
| Free-tier limits or changes | Code runs on any Django host. Keep weekly backups, and move to an LGU or DICT host if needed |
| Low adoption | Barangay officials as first users, QR posters, radio, and the LGU Facebook page linking to the portal |

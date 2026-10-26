# Credits

## Photos

All photos are free-licence images from Wikimedia Commons. Before using each one I checked that it
was taken on Sibuyan, from its Commons description and the place it shows, plus GPS data where the
file has it. Each photo was cropped, resized and converted to WebP (`tools/build_photos.py`), which
counts as a modification under CC BY and CC BY-SA. Every photo is credited on the page where it
appears, and `core/photos.py` holds the same details.

| Used as | Original on Commons | Author | Licence | How it was checked |
|---|---|---|---|---|
| Homepage hero (mountain) | [Mt. Guiting - Guiting.jpg](https://commons.wikimedia.org/wiki/File:Mt._Guiting_-_Guiting.jpg) | Dosias | CC BY-SA 4.0 | Description: "Highest mountain in the province of Romblon"; the range matches the other Guiting-Guiting photos |
| Hero crossfade (sea) | [Sibuyan Island (Romblon; 12-05-2023).jpg](https://commons.wikimedia.org/wiki/File:Sibuyan_Island_(Romblon;_12-05-2023).jpg) | Patrickroque01 | CC BY-SA 4.0 | Title and description name Sibuyan Island |
| Hero crossfade (river); Cantingas River header on the tourism page | [Cantingas River.jpg](https://commons.wikimedia.org/wiki/File:Cantingas_River.jpg) | Carlojoseph14 | CC BY-SA 4.0 | Description: "Cantingas River in Barangay Taclobo" (San Fernando) |
| "Discover" gallery: Mt. Guiting-Guiting; tourism gallery | [Guiting-guiting 3.jpg](https://commons.wikimedia.org/wiki/File:Guiting-guiting_3.jpg) | Androkoy | CC BY-SA 4.0 | GPS 12.4163, 122.5691 (summit area) |
| "Discover" gallery: Cantingas River; tourism gallery | [CantingasRiver.jpg](https://commons.wikimedia.org/wiki/File:CantingasRiver.jpg) | Christian Jules Llave | CC BY-SA 4.0 | Description: Cantingas River, Sibuyan Island. It names the town as Cajidiocan, but the river is in Brgy. Taclobo, San Fernando, which is what the site uses |
| "Discover" gallery: the coastline | [Sibuyan Island.JPG](https://commons.wikimedia.org/wiki/File:Sibuyan_Island.JPG) | P199 | CC BY-SA 3.0 | Aerial view; the island's outline matches Sibuyan |
| Mt. Guiting-Guiting header on the tourism page | [Mount Guiting-Guiting DSC06614.jpg](https://commons.wikimedia.org/wiki/File:Mount_Guiting-Guiting_DSC06614.jpg) | rjabalosIII (via Flickr) | CC BY 2.0 | GPS 12.4176, 122.5677 (summit ridge) |
| Tourism gallery: sea of clouds | [Mount Guiting Guiting 5.jpg](https://commons.wikimedia.org/wiki/File:Mount_Guiting_Guiting_5.jpg) | Ray Santa Maria | CC BY-SA 4.0 | Description: view from the summit of Mount Guiting Guiting |
| Tourism gallery: forest | [Guiting-guiting 5.jpg](https://commons.wikimedia.org/wiki/File:Guiting-guiting_5.jpg) | Androkoy | CC BY-SA 4.0 | GPS 12.4163, 122.5691 |
| Tourism gallery: pitcher plant | [Nepenthes sibuyanensis ASR 062007 guiting2 sibuyan.jpg](https://commons.wikimedia.org/wiki/File:Nepenthes_sibuyanensis_ASR_062007_guiting2_sibuyan.jpg) | Alastair Robinson (Attenboroughii) | CC BY 3.0 | Description: photographed on the Knife Edge ridge of Mt. Guiting-Guiting, June 2007 |

Photos I looked at but didn't use:
- "Cresta de Gallo MPA view.jpg" shows a different Cresta de Gallo, in Anini-y, Antique.
- "LV IMG 1588426936316.jpg" has no location information.
- "CuteLilFella.jpg" has an unknown location.

## Needs photo

No free-licence photo of these places was found on Wikimedia Commons (October 2026). They show a
labelled "Photo needed" placeholder until you add your own.

| Place | Where it appears | Suggested shot |
|---|---|---|
| Cawa-Cawa Falls (San Fernando) | Homepage gallery, tourism page | The tiered falls and pools, landscape (4:3 or wider) |
| Lambingan Falls (Magdiwang) | Homepage gallery, tourism page | The falls and natural pool, landscape |
| Cresta de Gallo (San Fernando) | Homepage gallery, tourism page | The white-sand islet from the boat or the air, landscape |
| Mangroves / coastline close-up | Optional: could replace the aerial coastline tile | Mangroves or a beach at eye level |
| A waterfall for the hero crossfade | Hero (desktop) | Any Sibuyan waterfall, wide 16:9; it would replace the river slide |

**To add a photo:**
1. Put the original in a folder and add an entry to `PHOTOS` in `tools/build_photos.py`.
2. Run `python tools/build_photos.py <folder>`.
3. Register the photo with its author and licence in `core/photos.py`.
4. Point the place at it in `tourism/showcase.py`.
5. Add a row to the table above.

Only use photos you took yourself or that carry a CC0, CC BY or CC BY-SA licence.

## Facts on the homepage ("Did you know?")

Each fact links to its source on the page. They were checked in October 2026:
- Nepenthes sibuyanensis is endemic to Sibuyan: [Wikipedia](https://en.wikipedia.org/wiki/Nepenthes_sibuyanensis), citing Nerz (1998), *Carnivorous Plant Newsletter*.
- 1,551 trees in one hectare, the densest forest recorded in the Philippines, with 54 endemic tree species: [Wikipedia: Sibuyan](https://en.wikipedia.org/wiki/Sibuyan) and [Mount Guiting-Guiting](https://en.wikipedia.org/wiki/Mount_Guiting-Guiting). The article calls these "preliminary reports". The site does not claim "one of the world's densest", because the sources don't support it.
- Mt. Guiting-Guiting Natural Park: [Proclamation No. 746, s. 1996](https://lawphil.net/executive/proc/proc1996/proc_746_1996.html). Elevation 2,058 m per Wikipedia.
- Cantingas River called the cleanest inland body of water by the government (since 2007): [Philippine Daily Inquirer](https://newsinfo.inquirer.net/639773/campaign-on-to-save-cleanest-river-in-ph). This is a news report, not the primary government record.
- "The Galápagos of Asia" nickname: [Wikipedia: Sibuyan](https://en.wikipedia.org/wiki/Sibuyan).

## Fonts (self-hosted, SIL Open Font License 1.1)

- **Inter** by Rasmus Andersson, weights 400 and 600, Latin subset (via Fontsource)
- **Fraunces** by Undercase Type, weight 500, Latin subset (via Fontsource)

## Icons, logo, pattern and dividers

The line icons (`static/img/icons.svg`), the leaf-and-wave logo mark (`templates/_logo.html`), the
leaf pattern (`static/img/pattern-leaf.svg`, under 0.5 KB), the ridge and wave dividers
(`templates/_divider.html`) and the PWA icons (`tools/make_icons.py`) were all made for
SibuyanConnect.

## Libraries and data

Django, django-modeltranslation, Pillow, WhiteNoise, HTMX and Leaflet. Map tiles are
© OpenStreetMap contributors. Weather data comes from Open-Meteo (CC BY 4.0). Attraction map pins
are approximate sample coordinates.

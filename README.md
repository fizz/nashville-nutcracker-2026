# Nashville Ballet Nutcracker Youth Schedule Helper

A small parent-built static web app that turns the youth-cast master schedule into a
dancer-specific schedule. No build step, package manager, framework, server, or backend.

## What it does

Pick a **role** and a **cast color** and it shows only that dancer's calls:

- rehearsals, fittings, spacing, tech and dress calls, performances
- call times and locations
- production notes
- the next call pinned at the top
- a `.ics` file for the whole schedule, or for any single call

## Cast rules encoded

- Party Boys: double cast — Red / Green
- All other youth roles: triple cast — Blue / Purple / Yellow

## On a phone

- **Add it to your home screen** and it opens like an app, full screen:
  Safari → Share → *Add to Home Screen*; Chrome → menu → *Install app* / *Add to Home screen*.
- **Works without signal.** A service worker caches the page, so it still opens in a
  basement dressing room or a dead-zone parking garage. It fetches fresh content whenever
  there is a connection, so schedule updates still land.
- **Remembers your dancer.** Your role/cast/view are saved on the device and written into
  the URL, so the page reopens where you left it.
- **Shareable links.** The Share button copies a link like
  `...#role=Baby%20Mice&cast=Purple` that opens straight to that dancer's schedule —
  handy for the other parent or a carpool thread.
- **Add to calendar** hands the `.ics` to the phone's share sheet, so it can go straight
  into Apple Calendar or Google Calendar. On desktop it downloads instead.
- Tap a venue name for directions.
- Follows the phone's light/dark setting.

## A note on times

Listed start times include the arrival/call time where the original notice gave one, so a
listed start can be earlier than the rehearsal time quoted in the note underneath it
(e.g. listed 4:00 PM, note says "Rehearsal 4:30–6:00 p.m."). The `.ics` export uses the
listed times.

## Important

This is an unofficial parent-built helper. Nashville Ballet's official notices and schedule
updates always take priority.

Schedule last updated: November 1, 2026.

## Publishing with GitHub Pages

Files are already laid out to be served from the repository root.

1. In GitHub, open **Settings → Pages**.
2. Under **Build and deployment** choose:
   - Source: **Deploy from a branch**
   - Branch: **main**
   - Folder: **/(root)**
3. Save. The public URL appears after the first deployment (a minute or two).

For this repository that URL is:

`https://fizz.github.io/nashville-nutcracker-2026/`

## Updating the schedule

All the schedule data is the `const DATA = {...}` object near the top of the `<script>` in
`index.html` — roles with their cast system and scene groups, then one entry per event:

```json
{ "date": "2026-12-12", "start": "17:30", "end": "21:00",
  "title": "Act I", "target": ["act:1"],
  "location": "Tennessee Performing Arts Center (TPAC), 505 Deaderick St, Nashville, TN 37243",
  "double": ["Red"], "triple": ["Blue"],
  "note": "Call 5:30 p.m.", "all_day": false }
```

`target` entries are matched against the role (`role:Clara`), its scenes (`scene:party`,
`scene:battle`) and acts (`act:1`, `act:2`). `double` / `triple` list the cast colors
called for that event.

Bump `CACHE` in `sw.js` (e.g. `nutcracker-v2`) after a schedule change if you want phones
that already have it installed to drop their old cached copy immediately.

## Local preview

Open `index.html` in a browser. For the service worker and install prompt you need a real
origin rather than `file://`:

```sh
python3 -m http.server 8000   # then visit http://localhost:8000/
```

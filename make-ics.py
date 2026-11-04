#!/usr/bin/env python
"""Generate a dancer-specific .ics from the live schedule data.

    python -I make-ics.py index.html "Baby Mice" Purple Kamala > kamala.ics

Stable UIDs are derived from (role, cast, date, start), so republishing after a
schedule change updates existing entries on subscribers' devices instead of
duplicating them. That is the whole point of regenerating rather than hand-editing.

Follows the conventions already in Kamala's published calendar: a "<name> — "
summary prefix, the rehearsal window and the call-time-is-arrival reminder in the
description, and America/Chicago with a real VTIMEZONE so the November 1 DST
change resolves instead of being guessed at.
"""
import hashlib
import json
import pathlib
import re
import sys

SOURCE = "https://fizz.github.io/nashville-nutcracker-2026/"

src_arg, role, cast, who = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
if src_arg in ("-", "live"):
    src_arg = SOURCE
if src_arg.startswith(("http://", "https://")):
    import urllib.request
    page = urllib.request.urlopen(src_arg, timeout=30).read().decode("utf-8")
    print(f"read schedule from {src_arg}", file=sys.stderr)
else:
    page = pathlib.Path(src_arg).read_text()

# Optional 5th arg: an .ics already living in the target calendar. Its UIDs are
# reused for events that match on (date, start), so importing UPDATES those
# entries in place instead of creating a second copy of each. Matters on a shared
# calendar, where duplicates and deletions both notify every participant.
KEEP = {}
if len(sys.argv) > 5:
    prev = re.sub(r"\r?\n[ \t]", "", pathlib.Path(sys.argv[5]).read_text())
    for blk in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", prev, re.S):
        u = re.search(r"^UID:(.*)$", blk, re.M)
        s = re.search(r"^DTSTART[^:]*:(\d{8})T(\d{4})", blk, re.M)
        if u and s:
            KEEP[(s.group(1), s.group(2))] = u.group(1).strip()
    print(f"reusing {len(KEEP)} existing UIDs", file=sys.stderr)
DATA = json.loads(re.search(r"const DATA=(\{.*?\});\s*\n",
                            page, re.S).group(1))

# The family notice supplied the omitted Act I and Act II runs for November
# 13 and 16–20.  Keep this normalization here as well as in index.html: the
# browser runs that JavaScript, while this exporter reads the literal DATA
# object directly.  Clara is deliberately separate because every Clara is
# called on every one of these dates, irrespective of the day's cast color.
ACT_RUN_WEEK = {
    "2026-11-13", "2026-11-16", "2026-11-17",
    "2026-11-18", "2026-11-19", "2026-11-20",
}
ACT1_WEEK_ROLES = [
    "role:Party Girls", "role:Party Boys", "role:Fritz",
    "role:Baby Mice", "role:Medium Mice", "role:Frontier Soldiers",
    "role:Infantry", "role:Teddy Bear Cavalry", "role:Commodore Cavalry",
]
ACT2_WEEK_ROLES = [
    "role:Garden Fairies", "role:Bon Bons", "role:Russians", "role:Lambs",
]
for act1 in [event for event in DATA["events"]
             if event["date"] in ACT_RUN_WEEK and event["title"] == "Act I"]:
    act1["target"] = ACT1_WEEK_ROLES
    act2_note = act1["note"].replace("4:00–5:00", "5:00–6:00")
    common = dict(act1)
    DATA["events"].extend([
        {**common, "target": ["role:Clara"], "double": [],
         "triple": ["Blue", "Purple", "Yellow"], "title": "Act I — Clara",
         "note": "All casts of Clara. " + act1["note"]},
        {**common, "start": "16:45", "end": "18:00",
         "target": ACT2_WEEK_ROLES, "title": "Act II", "note": act2_note},
        {**common, "start": "16:45", "end": "18:00", "target": ["role:Clara"],
         "double": [], "triple": ["Blue", "Purple", "Yellow"],
         "title": "Act II — Clara", "note": "All casts of Clara. " + act2_note},
    ])

roles = DATA["roles"]
if role not in roles:
    sys.exit(f"unknown role {role!r}; known: {sorted(roles)}")

meta = roles[role]
castfield = "double" if meta["castSystem"] == "double" else "triple"


def targets(r):
    g = roles[r]["groups"]
    s = {"role:" + r}
    if "party" in g:
        s |= {"scene:party", "act:1"}
    if "battle" in g:
        s |= {"scene:battle", "act:1"}
    if "act2" in g:
        s |= {"act:2"}
    return s


want = targets(role)
calls = [e for e in DATA["events"]
         if (set(e.get("target", [])) & want) and cast in (e.get(castfield) or [])]
calls.sort(key=lambda e: (e["date"], e.get("start") or ""))


def esc(s):
    return (s.replace("\\", "\\\\").replace(";", r"\;")
             .replace(",", r"\,").replace("\n", r"\n"))


def fold(line):
    """RFC 5545 folding, counted in UTF-8 octets — em dashes push past 75 bytes."""
    b = line.encode("utf-8")
    if len(b) <= 75:
        return line
    out, cur = [], b""
    for ch in line:
        e = ch.encode("utf-8")
        if len(cur) + len(e) > (75 if not out else 74):
            out.append(cur.decode("utf-8"))
            cur = b""
        cur += e
    out.append(cur.decode("utf-8"))
    return out[0] + "".join("\r\n " + x for x in out[1:])


L = ["BEGIN:VCALENDAR", "VERSION:2.0",
     "PRODID:-//fizz//nutcracker-youth-schedule//EN",
     "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
     f"X-WR-CALNAME:{esc(who)} — Nutcracker 2026",
     "X-WR-TIMEZONE:America/Chicago",
     "BEGIN:VTIMEZONE", "TZID:America/Chicago",
     "BEGIN:DAYLIGHT", "TZOFFSETFROM:-0600", "TZOFFSETTO:-0500", "TZNAME:CDT",
     "DTSTART:19700308T020000", "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU", "END:DAYLIGHT",
     "BEGIN:STANDARD", "TZOFFSETFROM:-0500", "TZOFFSETTO:-0600", "TZNAME:CST",
     "DTSTART:19701101T020000", "RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU", "END:STANDARD",
     "END:VTIMEZONE"]

STAMP = "20261103T000000Z"
for e in calls:
    if not e.get("start"):
        continue
    d = e["date"].replace("-", "")
    hhmm = e["start"].replace(":", "")
    seed = f"{role}|{cast}|{e['date']}|{e['start']}".encode()
    uid = KEEP.get((d, hhmm)) or f"{hashlib.sha1(seed).hexdigest()[:32]}@nutcracker.fizz"
    desc = f"{role} / {cast}."
    if e.get("note"):
        desc += " " + e["note"]
    desc += " Call time is ARRIVAL time."
    L += ["BEGIN:VEVENT",
          f"UID:{uid}",
          f"DTSTAMP:{STAMP}",
          f"DTSTART;TZID=America/Chicago:{d}T{e['start'].replace(':','')}00",
          f"DTEND;TZID=America/Chicago:{d}T{(e.get('end') or e['start']).replace(':','')}00",
          fold(f"SUMMARY:{esc(who)} — {esc(e.get('title',''))}"),
          fold(f"LOCATION:{esc(e.get('location',''))}"),
          fold(f"DESCRIPTION:{esc(desc)}"),
          "END:VEVENT"]
L.append("END:VCALENDAR")

sys.stdout.write("\r\n".join(L) + "\r\n")
print(f"{len(calls)} events for {role} / {cast}", file=sys.stderr)

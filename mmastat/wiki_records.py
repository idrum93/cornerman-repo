"""Full professional records from Wikipedia, for PREREGISTRATION addendum 18.

The corpus holds UFC bouts only, so a debutant who went 14-0 on the regional
scene looks identical to one who went 7-5, and a third of all bouts since 2020
cannot be priced at all. Wikipedia's fighter articles carry the complete
"Mixed martial arts record" table. This collects it through the MediaWiki API
the card refresh already uses — free, keyless, and bot-friendly.

Design choices that matter:

  IDENTITY IS CHECKED, NOT ASSUMED. A page is accepted for a corpus fighter
  only if its record table contains his known UFC bouts (dates within two
  days). Names collide — the corpus already has seven ambiguous ones — and a
  wrong-person record would be worse than none.

  RESUMABLE, WITH A TIME BUDGET. The first run is a backfill of ~3,000
  fighters. It works in batches, saves after each, and stops cleanly when its
  budget runs out; the next run carries on. Nothing is lost to a timeout.

  INCREMENTAL AFTERWARDS. A record only changes when the fighter fights, so
  later runs refresh: fighters on the upcoming card, fighters with a new UFC
  bout since they were last checked, and — slowly — pages that were missing
  last time, in case they have since been written.

  AMATEUR, EXHIBITION AND OTHER-SPORT TABLES ARE EXCLUDED by their section
  heading. Articles often carry an amateur MMA record, a TUF exhibition record
  or a kickboxing record in tables with the same columns.

Storage: rows are stored as compact [date, result, method, ufc_named] arrays,
about 25 bytes each — roughly 2 MB for the whole corpus.
"""
import json
import re
import time
from pathlib import Path

import pandas as pd

API = "https://en.wikipedia.org/w/api.php"
UA = ("CornermanBot/1.0 (https://github.com/idrum93/cornerman-repo; "
      "UFC research, weekly, low volume)")
OUT = "data/wiki/records.json"
BATCH = 20                 # pages per content request; keeps responses small
PAUSE = 1.0                # seconds between requests: polite, well under limits

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], 1)}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})
EXCLUDE_HEADING = re.compile(r"amateur|exhibition|kickbox|boxing|grappl|muay|"
                             r"karate|bare.?knuckle|wrestling", re.I)


# ---------------------------------------------------------------- parsing
def _split_top(s, sep="|"):
    """Split on `sep` only outside [[...]] and {{...}}."""
    out, cur, sq, cu, i = [], [], 0, 0, 0
    while i < len(s):
        two = s[i:i + 2]
        if two == "[[":
            sq += 1; cur.append(two); i += 2; continue
        if two == "]]" and sq:
            sq -= 1; cur.append(two); i += 2; continue
        if two == "{{":
            cu += 1; cur.append(two); i += 2; continue
        if two == "}}" and cu:
            cu -= 1; cur.append(two); i += 2; continue
        if not sq and not cu and s.startswith(sep, i):
            out.append("".join(cur)); cur = []; i += len(sep); continue
        cur.append(s[i]); i += 1
    out.append("".join(cur))
    return out


def clean_cell(c):
    """Drop cell attributes, refs, links and formatting; keep the text."""
    parts = _split_top(c, "|")
    if len(parts) > 1 and re.search(r"(style|align|class|rowspan|colspan|data-sort-value)\s*=",
                                    parts[0], re.I):
        c = "|".join(parts[1:])
    c = re.sub(r"<ref[^>]*/>", "", c)
    c = re.sub(r"<ref[^>]*>.*?</ref>", "", c, flags=re.S)
    c = re.sub(r"<[^>]+>", "", c)
    c = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", c)
    c = re.sub(r"'''?", "", c)
    return c.strip()


def parse_date(cell):
    """{{dts|2024|4|13}}, {{dts|April 13, 2024}}, {{Start date|2024|4|13}},
    or plain "April 13, 2024" / "13 April 2024". Returns ISO or None."""
    m = re.search(r"\{\{\s*(?:dts|start date|date)\s*\|([^}]*)\}\}", cell, re.I)
    text = cell
    if m:
        args = [a.strip() for a in m.group(1).split("|") if "=" not in a and a.strip()]
        if len(args) >= 3 and re.fullmatch(r"\d{4}", args[0]):
            y, mo, d = args[0], args[1], args[2]
            mo = MONTHS.get(mo.lower()[:3]) if not mo.isdigit() else int(mo)
            if mo and d.isdigit():
                try:
                    return pd.Timestamp(int(y), int(mo), int(d)).date().isoformat()
                except ValueError:
                    return None
        text = " ".join(args)
    text = clean_cell(re.sub(r"\{\{[^}]*\}\}", "", text) if not m else text)
    y = re.search(r"\b(19|20)\d{2}\b", text)
    mn = re.search(r"\b(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\.?\b", text, re.I)
    d = re.search(r"\b([0-3]?\d)\b(?!\d)", re.sub(r"\b(19|20)\d{2}\b", "", text))
    if y and mn and d:
        try:
            return pd.Timestamp(int(y.group(0)), MONTHS[mn.group(1).lower()[:3]],
                                int(d.group(1))).date().isoformat()
        except (ValueError, KeyError):
            return None
    return None


def _result(c):
    c = c.lower()
    if c.startswith("win"):
        return "W"
    if c.startswith("loss"):
        return "L"
    if c.startswith("draw"):
        return "D"
    if c.startswith("nc") or "no contest" in c:
        return "NC"
    return None


def _method(c):
    c = c.lower()
    if "submission" in c or re.search(r"\bsub\b", c):
        return "SUB"
    if "ko" in c:                      # KO and TKO
        return "KO"
    if "decision" in c:
        return "DEC"
    if "disqualif" in c or re.search(r"\bdq\b", c):
        return "DQ"
    return "OTHER"


def _sections(wikitext):
    """(heading, body) pairs; the lead has heading ''."""
    parts = re.split(r"^(={2,6})\s*(.*?)\s*\1\s*$", wikitext, flags=re.M)
    out = [("", parts[0])]
    for i in range(1, len(parts) - 2, 3):
        out.append((parts[i + 1], parts[i + 2]))
    return out


def _tables(body):
    return re.findall(r"^\{\|.*?^\|\}", body, flags=re.M | re.S)


def _parse_table(t):
    lines = t.split("\n")
    header = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("!"):
            header += [clean_cell(x) for x in _split_top(s[1:].replace("!!", "\x00"), "\x00")]
    hl = [h.lower().rstrip(".") for h in header]
    if not hl or not (("res" in hl or "result" in hl) and "record" in hl):
        return None
    ix = lambda *names: next((i for i, h in enumerate(hl) if h in names), None)
    i_res, i_met, i_evt, i_dat = ix("res", "result"), ix("method"), ix("event"), ix("date")
    if i_res is None or i_dat is None:
        return None
    rows, cells = [], []

    def flush():
        if cells and len(cells) > max(i_res, i_dat):
            res = _result(clean_cell(cells[i_res]))
            dt = parse_date(cells[i_dat])
            if res and dt:
                met = _method(clean_cell(cells[i_met])) if i_met is not None and i_met < len(cells) else "OTHER"
                evt = clean_cell(cells[i_evt]) if i_evt is not None and i_evt < len(cells) else ""
                rows.append([dt, res, met, int("ufc" in evt.lower())])

    for ln in lines[1:]:
        s = ln.strip()
        if s.startswith("|-") or s.startswith("|}"):
            flush(); cells = []
            continue
        if s.startswith("|+") or s.startswith("!"):
            continue
        if s.startswith("|"):
            cells += _split_top(s[1:].replace("||", "\x00"), "\x00")
        elif cells:
            cells[-1] += " " + s          # a cell continued on the next line
    flush()
    return rows


def parse_record(wikitext):
    """The professional MMA record table, or None. Prefers a section headed
    "Mixed martial arts record"; never takes amateur, exhibition or
    other-sport tables."""
    best = None
    for heading, body in _sections(wikitext):
        if EXCLUDE_HEADING.search(heading or ""):
            continue
        for t in _tables(body):
            rows = _parse_table(t)
            if rows:
                pref = "mixed martial arts record" in (heading or "").lower()
                if best is None or (pref and not best[0]) or (pref == best[0] and len(rows) > len(best[1])):
                    best = (pref, rows)
    if not best:
        return None
    return sorted(best[1], key=lambda r: r[0])


# ---------------------------------------------------------------- the API
def _get(params, tries=4):
    import requests
    p = dict(params, format="json", formatversion=2, maxlag=5)
    for k in range(tries):
        r = requests.get(API, params=p, timeout=60, headers={"User-Agent": UA})
        if r.status_code in (429, 503) or (r.ok and r.json().get("error", {}).get("code") == "maxlag"):
            time.sleep(min(60, 5 * (k + 1)))
            continue
        r.raise_for_status()
        time.sleep(PAUSE)
        return r.json()
    raise RuntimeError("Wikipedia API kept asking us to wait; will retry next run")


def fetch_pages(titles):
    """{requested title: (final title, wikitext or None)} for up to BATCH
    titles in one request, following redirects."""
    j = _get({"action": "query", "prop": "revisions", "rvprop": "content",
              "rvslots": "main", "redirects": 1, "titles": "|".join(titles)})
    q = j.get("query", {})
    hop = {}
    for key in ("normalized", "redirects"):
        for x in q.get(key, []):
            hop[x["from"]] = x["to"]
    content = {}
    for pg in q.get("pages", []):
        if pg.get("missing") or not pg.get("revisions"):
            content[pg["title"]] = None
        else:
            content[pg["title"]] = pg["revisions"][0]["slots"]["main"]["content"]
    out = {}
    for t in titles:
        f = t
        for _ in range(3):
            f = hop.get(f, f)
        out[t] = (f, content.get(f))
    return out


def search_title(name):
    j = _get({"action": "query", "list": "search", "srlimit": 3,
              "srsearch": f'"{name}" mixed martial artist'})
    last = name.split()[-1].lower()
    for hit in j.get("query", {}).get("search", []):
        if last in hit["title"].lower():
            return hit["title"]
    return None


# ---------------------------------------------------------------- matching
def validate(rows, ufc_dates, tol_days=2):
    """True if the table contains this fighter's known UFC bouts. Needs
    min(2, n) matches so one coincidental date cannot pass a wrong page."""
    if not ufc_dates:
        return None                   # a debutant: nothing to check against
    have = [pd.Timestamp(r[0]) for r in rows]
    hits = sum(any(abs((d - h).days) <= tol_days for h in have) for d in ufc_dates)
    return hits >= min(2, len(ufc_dates))


def _load(path=OUT):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "fighters": {}}


def _save(store, path=OUT):
    store["updated_utc"] = pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(store, sort_keys=True, separators=(",", ":")),
                          encoding="utf-8")


def _candidates(fights, fighters, store, card_names=()):
    """Who to check this run, in priority order."""
    fs = store["fighters"]
    now = pd.Timestamp.now(tz="UTC").tz_localize(None)
    recent = fights[fights.date >= pd.Timestamp("2012-01-01")]
    last_bout = pd.concat([recent[["r_id", "date"]].rename(columns={"r_id": "id"}),
                           recent[["b_id", "date"]].rename(columns={"b_id": "id"})]
                          ).groupby("id").date.max()
    name_of = dict(zip(fighters.fighter_id, fighters.name))
    card, changed, fresh, retry = [], [], [], []
    for n in card_names:
        card.append(("name:" + n.lower(), n))
    for fid, lb in last_bout.sort_values(ascending=False).items():
        rec = fs.get(fid)
        nm = name_of.get(fid)
        if not nm:
            continue
        if rec is None:
            fresh.append((fid, nm))
        elif pd.Timestamp(rec["checked"]) < lb:
            changed.append((fid, nm))
        elif rec["status"] in ("missing", "no_table", "mismatch") and \
                (now - pd.Timestamp(rec["checked"])).days > 30:
            retry.append((fid, nm))
    return card + changed + fresh + retry[:200]


def collect(fights, fighters, card_names=(), budget_min=40, path=OUT, verbose=True):
    t0 = time.time()
    store = _load(path)
    fs = store["fighters"]
    ufc_dates = {}
    for r in fights.itertuples():
        ufc_dates.setdefault(r.r_id, []).append(pd.Timestamp(r.date))
        ufc_dates.setdefault(r.b_id, []).append(pd.Timestamp(r.date))
    todo = _candidates(fights, fighters, store, card_names)
    done = 0
    while todo and (time.time() - t0) < budget_min * 60:
        batch, todo = todo[:BATCH], todo[BATCH:]
        # try "Name", then "Name (fighter)", then search, stopping at the first
        # page whose record table validates
        pending = {key: nm for key, nm in batch}
        clash = set()                     # found a record table, but not his
        for suffix in ("", " (fighter)", " (mixed martial artist)"):
            if not pending:
                break
            titles = {key: nm + suffix for key, nm in pending.items()}
            try:
                got = fetch_pages(list(titles.values()))
            except Exception as e:
                if verbose:
                    print(f"  pausing: {e}")
                todo = list(pending.items()) + todo
                pending = {}
                break
            for key, t in list(titles.items()):
                final, text = got.get(t, (t, None))
                rows = parse_record(text) if text else None
                if rows:
                    ok = validate(rows, ufc_dates.get(key, []))
                    if ok is False:
                        clash.add(key)    # a table, but not this fighter's
                        continue
                    fs[key] = {"name": pending[key], "title": final,
                               "status": "ok" if ok else "unvalidated",
                               "checked": pd.Timestamp.now(tz="UTC").date().isoformat(),
                               "rows": rows}
                    pending.pop(key)
        for key, nm in list(pending.items()):
            if (time.time() - t0) > budget_min * 60:
                todo = [(key, nm)] + todo
                continue
            status = "mismatch" if key in clash else "missing"
            try:
                t = search_title(nm)
                if t:
                    final, text = fetch_pages([t])[t]
                    rows = parse_record(text) if text else None
                    if rows:
                        ok = validate(rows, ufc_dates.get(key, []))
                        if ok is not False:
                            fs[key] = {"name": nm, "title": final,
                                       "status": "ok" if ok else "unvalidated",
                                       "checked": pd.Timestamp.now(tz="UTC").date().isoformat(),
                                       "rows": rows}
                            continue
                        status = "mismatch"
                    else:
                        status = "no_table"
            except Exception:
                todo = [(key, nm)] + todo
                continue
            fs[key] = {"name": nm, "status": status,
                       "checked": pd.Timestamp.now(tz="UTC").date().isoformat()}
        done += len(batch)
        _save(store, path)
    if verbose:
        report(store, fights, remaining=len(todo), elapsed=time.time() - t0)
    return store


def report(store, fights, remaining=0, elapsed=0):
    """Progress, and the addendum 18 stop-rule number: coverage of debutants
    since 2020. Printed every run so the decision is visible as it forms."""
    fs = store["fighters"]
    from collections import Counter
    c = Counter(v["status"] for v in fs.values())
    size = len(json.dumps(store, separators=(",", ":")).encode())
    print(f"wiki records: {len(fs)} fighters checked in {elapsed/60:.1f} min, "
          f"{remaining} still queued, file {size/1e6:.2f} MB")
    print("  " + "  ".join(f"{k} {v}" for k, v in sorted(c.items())))
    rec = fights[fights.date >= pd.Timestamp("2020-01-01")].sort_values("date")
    first = {}
    for r in fights.sort_values("date").itertuples():
        first.setdefault(r.r_id, r.date)
        first.setdefault(r.b_id, r.date)
    debut = [fid for fid, d in first.items() if d >= pd.Timestamp("2020-01-01")]
    checked = [f for f in debut if f in fs]
    ok = [f for f in checked if fs[f]["status"] == "ok"]
    if checked:
        print(f"  STOP-RULE coverage: {len(ok)} of {len(checked)} debutants since 2020 "
              f"checked so far have a validated record ({100*len(ok)/len(checked):.0f}%; "
              f"the test proceeds only at 50% or more), {len(debut)-len(checked)} not yet checked")


if __name__ == "__main__":
    import sys
    from .loaders import load
    budget = 40
    if "--budget-min" in sys.argv:
        budget = float(sys.argv[sys.argv.index("--budget-min") + 1])
    f, p, _ = load(verbose=False)
    names = []
    try:
        from .upcoming import parse_card, resolve
        _, bouts = parse_card("data/upcoming.txt")
        allnames = sorted({n for b in bouts for n in b[:2]})
        ids, _ = resolve(allnames, p)
        names = [n for n in allnames if n not in ids]   # debutants not in the corpus
    except Exception:
        pass
    collect(f, p, card_names=names, budget_min=budget)

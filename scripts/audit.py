#!/usr/bin/env python3
"""Closet audit for the fashion-coach skill (Mode D): counts, never judges.

Reads the client's closet CSV, outfit history (CSV, or the older markdown table), shopping file
and gap log, and prints a compact markdown report the coach interprets:
  coverage grid, orphans, over-reliance, unworn, gap-log tally, stale gaps.
Read-only: never writes anything. Python 3 standard library only.

Usage: audit.py [--project DIR] [--season spring|summer|fall|winter] [--date YYYY-MM-DD] [--json]

Data location, first match wins (same order as load-context.sh):
  1. <project>/.fashion-coach   config file (PROFILE= CLOSET= HISTORY= SHOPPING= GAPLOG= ...),
                                paths relative to the config file's folder, or absolute or ~/
  2. <project>/wardrobe/        profile.md, closet.csv, outfit-history.md, shopping.md
  3. ~/.fashion-coach           global config file, same keys
  4. ~/fashion-coach/           same layout as 2
<project> is --project, else $CLAUDE_PROJECT_DIR, else the current directory.
GAPLOG defaults to gap-log.csv beside the shopping file.
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

TOPS = {"tshirt", "polo", "shirt", "sweater", "sweatshirt", "hoodie", "tank"}
BOTTOMS = {"jeans", "pants", "shorts"}
LAYERS = {"outerwear"}
SHOES = {"shoes"}
ACCESSORIES = {"belt", "watch", "sunglasses", "jewelry", "bag", "hat"}
SEASONS = ["spring", "summer", "fall", "winter"]
SUPPRESSED = {"low-wear-parked", "too-tight", "skinny-fit", "end-of-life", "gym-register"}
LANES = ["neutral", "earth"]
SLOT_COLS = ["layer", "top", "under", "bottom", "shoes", "belt"]
# Gap nouns -> how to recognise an owned piece of that kind (closet type, words in name/description).
GAP_NOUNS = {
    "blazer": ("outerwear", r"blazer|suit jacket"), "jacket": ("outerwear", r"jacket"),
    "overshirt": ("outerwear", r"overshirt|shacket"), "coat": ("outerwear", r"coat"),
    "harrington": ("outerwear", r"harrington"), "bomber": ("outerwear", r"bomber"),
    "chore": ("outerwear", r"chore"), "jeans": ("jeans", r""), "denim": ("jeans", r""),
    "chinos": ("pants", r"chino"), "trousers": ("pants", r"trouser"), "trouser": ("pants", r"trouser"),
    "shorts": ("shorts", r""), "tee": ("tshirt", r""), "tees": ("tshirt", r""), "t-shirt": ("tshirt", r""),
    "polo": ("polo", r""), "shirt": ("shirt", r""), "knit": ("sweater|polo", r""),
    "sweater": ("sweater", r""), "merino": ("sweater|polo", r"merino"), "cardigan": ("sweater", r"cardigan"),
    "hoodie": ("hoodie", r""), "loafers": ("shoes", r"loafer"), "loafer": ("shoes", r"loafer"),
    "sneakers": ("shoes", r"sneaker|trainer"), "boots": ("shoes", r"boot"), "chelsea": ("shoes", r"chelsea"),
    "derbies": ("shoes", r"derb"), "derby": ("shoes", r"derb"), "belt": ("belt", r""), "watch": ("watch", r""),
    "sunglasses": ("sunglasses", r""),
}
BASE_COLOURS = {"navy", "charcoal", "black", "white", "gray", "grey", "indigo", "olive", "emerald", "cobalt",
                "stone", "cream", "ivory", "camel", "brown", "espresso", "taupe", "beige", "blue", "green",
                "burgundy", "rust", "tan", "khaki", "sage", "teal", "red", "pink", "yellow", "orange", "purple"}


# ---------------------------------------------------------------- paths (mirrors load-context.sh)
def read_conf(path):
    cfg = {}
    for ln in path.read_text().splitlines():
        m = re.match(r"\s*([A-Z_]+)\s*=\s*(.*?)\s*$", ln)
        if m and not ln.lstrip().startswith("#"):
            cfg[m.group(1)] = m.group(2).strip('"')
    return cfg


def resolve(project):
    project, home = Path(project).expanduser().resolve(), Path.home()
    conf = None
    if (project / ".fashion-coach").is_file():
        conf = project / ".fashion-coach"
    elif not (project / "wardrobe/profile.md").is_file() and (home / ".fashion-coach").is_file():
        conf = home / ".fashion-coach"
    p = {}
    if conf:
        cfg = read_conf(conf)

        def ab(v):
            if not v:
                return None
            if v.startswith("~/"):
                return home / v[2:]
            return Path(v) if v.startswith("/") else conf.parent / v
        for k in ("PROFILE", "CLOSET", "HISTORY", "SHOPPING", "GAPLOG"):
            p[k.lower()] = ab(cfg.get(k))
        p["source"] = f"config {conf}"
    else:
        base = project / "wardrobe" if (project / "wardrobe/profile.md").is_file() else home / "fashion-coach"
        p.update(profile=base / "profile.md", closet=base / "closet.csv", history=base / "outfit-history.md",
                 shopping=base / "shopping.md", gaplog=None, source=f"folder {base}")
    if not p.get("gaplog"):
        anchor = p.get("shopping") or p.get("closet")
        p["gaplog"] = anchor.parent / "gap-log.csv" if anchor else None
    return p


def ok(path):
    return bool(path) and Path(path).is_file()


# ---------------------------------------------------------------- loading
def split_colorways(color):
    """'white, cobalt (loud + hero)' -> ['white', 'cobalt']; slashes stay one colourway."""
    color = re.sub(r"\([^)]*\)", "", color or "")
    return [c.strip().lower() for c in color.split(",") if c.strip()]


def load_closet(path):
    items = []
    if not ok(path):
        return items
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            if not (r.get("id") or "").strip().isdigit():
                continue
            t = (r.get("type") or "").strip().lower()
            try:
                form = int(float(r.get("formality") or 0))
            except ValueError:
                form = 0
            seasons = {s for s in SEASONS if (r.get(s) or "").strip().lower() == "true"} or set(SEASONS)
            flags = set((r.get("flag") or "").lower().split())
            cat = ("top" if t in TOPS else "bottom" if t in BOTTOMS else "layer" if t in LAYERS
                   else "shoes" if t in SHOES else "acc")
            name = (r.get("name") or "").strip() or f"{r.get('color', '').strip()} {t}".strip()
            items.append({"id": r["id"].strip(), "type": t, "cat": cat, "name": name,
                          "color": (r.get("color") or "").strip(), "colours": split_colorways(r.get("color")),
                          "desc": (r.get("description") or "").strip(), "formality": form,
                          "register": (r.get("register") or "").strip().lower(),
                          "volume": (r.get("volume") or "").strip().lower(),
                          "loud": (r.get("loud") or "").strip().lower() == "yes", "flags": flags,
                          "suppressed": bool(flags & SUPPRESSED), "seasons": seasons})
    return items


def load_history(path, ids):
    """List of outfits, each a set of closet ids. Returns (outfits, kind, dates)."""
    if not ok(path):
        return [], "missing", []
    outfits, dates = [], []
    if str(path).endswith(".csv"):
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                cells = [r.get(k) or "" for k in SLOT_COLS] + (r.get("acc") or "").split(";")
                got = {c.strip().partition(":")[0].strip() for c in cells if c.strip() and not c.strip().startswith("?")}
                got &= ids
                if got:
                    outfits.append(got)
                    if (r.get("date") or "").strip():
                        dates.append(r["date"].strip())
        return outfits, "csv", dates
    for ln in Path(path).read_text().splitlines():  # older markdown table: "(36)" or "(36/40)" refs
        if re.match(r"#+ .*anti", ln, re.I):
            break
        if not ln.startswith("|"):
            continue
        first = ln.strip().strip("|").split("|")[0].strip()
        if not first.isdigit():
            continue
        got = {i for m in re.finditer(r"\((\d+(?:/\d+)*)", ln) for i in m.group(1).split("/")} & ids
        if got:
            outfits.append(got)
            m = re.search(r"\d{4}-\d{2}(?:-\d{2})?", ln)
            if m:
                dates.append(m.group(0))
    return outfits, "markdown", dates


def formality_range(profile):
    """(lo, hi) from the profile's 'Formality life' section, e.g. 'He lives at **2-4**'; else None."""
    if not ok(profile):
        return None
    txt = Path(profile).read_text()
    m = re.search(r"^#+\s*Formality life\s*$(.*?)(?=^#+\s|\Z)", txt, re.M | re.S | re.I)
    if not m:
        return None
    r = re.search(r"\b([1-5])\s*(?:-|to)\s*([1-5])\b", m.group(1))
    return (int(r.group(1)), int(r.group(2))) if r else None


def section(txt, title_re):
    m = re.search(rf"^#+\s*{title_re}.*?$(.*?)(?=^#+\s|\Z)", txt, re.M | re.S | re.I)
    return m.group(1) if m else ""


# ---------------------------------------------------------------- rules
def reg_ok(a, b):
    ra, rb = a["register"], b["register"]
    return (not ra or not rb or ra == rb or "both" in (ra, rb) or {ra, rb} == {"street", "neutral"})


def pair_fail(a, b):
    """First mechanical hard rule a pair breaks, or None."""
    if abs(a["formality"] - b["formality"]) > 1:
        return "formality"
    if not reg_ok(a, b):
        return "register"
    if not (a["seasons"] & b["seasons"]):
        return "season"
    if a["loud"] and b["loud"]:
        return "two loud"
    for s, o in ((a, b), (b, a)):
        if s["cat"] == "shoes" and s["volume"] == "chunky" and o["cat"] == "bottom" and o["volume"] not in ("relaxed", "oversized"):
            return "chunky shoe"
        if s["cat"] in ("top", "layer") and s["volume"] == "oversized" and o["cat"] == "bottom" and o["volume"] == "fitted":
            return "silhouette"
    return None


def completions(item, pool):
    """Valid top+bottom+shoe outfits containing item (layers: over a valid base). Returns (count, partners, top reason)."""
    reasons, partners = Counter(), set()
    cats = ["top", "bottom", "shoes"]
    need = [c for c in cats if c != item["cat"]] if item["cat"] in cats else cats

    def fits(x):
        r = pair_fail(item, x)
        if r:
            reasons[r] += 1
        return r is None
    cand = {c: [x for x in pool[c] if x is not item and fits(x)] for c in need}
    count = 0
    if len(need) == 2:
        c1, c2 = need
        for x in cand[c1]:
            for y in cand[c2]:
                if pair_fail(x, y) is None and item["seasons"] & x["seasons"] & y["seasons"]:
                    count += 1
                    partners.update((x["id"], y["id"]))
    else:
        for t in cand["top"]:
            for b in cand["bottom"]:
                if pair_fail(t, b):
                    continue
                for s in cand["shoes"]:
                    if pair_fail(t, s) is None and pair_fail(b, s) is None and \
                            item["seasons"] & t["seasons"] & b["seasons"] & s["seasons"]:
                        count += 1
                        partners.update((t["id"], b["id"], s["id"]))
    return count, len(partners), (reasons.most_common(1)[0][0] if reasons else "")


# ---------------------------------------------------------------- lenses
def season_for(date, override):
    if override:
        return override
    return {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring",
            6: "summer", 7: "summer", 8: "summer"}.get(date.month, "fall")


def coverage(items, season, frange):
    """Per formality level F: usable tops/bottoms/shoes within 1 point of F (what an outfit at F can draw on),
    in the neutral lane (neutral + `both` + street, which pairs with neutral) and the earth lane (earth + `both`)."""
    usable = [i for i in items if not i["suppressed"] and i["cat"] in ("top", "bottom", "shoes")]
    lanes = {"neutral": ("neutral", "both", "street"), "earth": ("earth", "both")}
    out = {}
    for scope in (season, "all"):
        rows = {}
        for f in range(1, 6):
            row = {}
            for lane, regs in lanes.items():
                pick = [i for i in usable if abs(i["formality"] - f) <= 1 and i["register"] in regs
                        and (scope == "all" or scope in i["seasons"])]
                c = Counter(i["cat"] for i in pick)
                cell = {"tops": c["top"], "bottoms": c["bottom"], "shoes": c["shoes"]}
                inside = frange is None or frange[0] <= f <= frange[1]
                cell["thin"] = inside and min(cell.values()) <= 1
                row[lane] = cell
            rows[f] = row
        out[scope] = rows
    return out


def gap_tally(path):
    if not ok(path):
        return [], 0
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            if (r.get("gap") or "").strip():
                rows.append(r)
    stop = {"a", "an", "the", "in", "of", "for", "with", "or", "and", "to", "piece", "one", "his", "that"}

    def toks(s):
        return {w for w in re.findall(r"[a-z]+", s.lower()) if w not in stop and len(w) > 2}
    clusters = []  # [slot, token set, rows]
    for r in rows:
        slot, t = (r.get("slot") or "").strip().lower(), toks(r["gap"])
        for c in clusters:
            if c[0] == slot and t and len(t & c[1]) / len(t | c[1]) >= 0.5:
                c[2].append(r)
                c[1] |= t
                break
        else:
            clusters.append([slot, t, [r]])
    out = []
    for slot, _, rs in clusters:
        dates = sorted({(r.get("date") or "").strip() for r in rs if (r.get("date") or "").strip()})
        label = Counter(r["gap"].strip() for r in rs).most_common(1)[0][0]
        out.append({"gap": label, "slot": slot, "count": len(rs), "dates": len(dates),
                    "last": dates[-1] if dates else "", "promote": len(dates) >= 3})
    out.sort(key=lambda g: (-g["dates"], -g["count"]))
    return out, len(rows)


def stale_gaps(shopping, items):
    if not ok(shopping):
        return []
    body = section(Path(shopping).read_text(), r"Known gaps")
    vocab = set(BASE_COLOURS)
    for i in items:
        vocab |= {w for c in i["colours"] for w in re.findall(r"[a-z]+", c) if len(w) > 2}
    vocab -= {"light", "dark", "deep", "pale", "mid", "medium", "near", "not", "favorite", "loud", "hero", "colour"}
    out = []
    for ln in body.splitlines():
        if not re.match(r"\s*[-*]\s", ln) or "~~" in ln or re.search(r"\bCLOSED\b", ln):
            continue
        title = re.search(r"\*\*(.+?)\*\*", ln)
        head = (title.group(1) if title else ln.split(":")[0]).lower()
        nouns = [n for n in GAP_NOUNS if re.search(rf"\b{re.escape(n)}\b", head)]
        colours = {w for w in re.findall(r"[a-z]+", head) if w in vocab}
        hits = []
        for i in items:
            text = f"{i['name']} {i['desc']}".lower()
            for n in nouns:
                types, rx = GAP_NOUNS[n]
                if re.fullmatch(types, i["type"]) and (not rx or re.search(rx, text)):
                    if not colours or colours & {w for c in i["colours"] for w in re.findall(r"[a-z]+", c)}:
                        hits.append(i)
                        break
        if hits:
            out.append({"gap": head.strip(" *:"), "owned": [f"{i['name']} ({i['color']})" for i in hits[:4]]})
    return out


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Closet audit (counts only; the coach judges).")
    ap.add_argument("--project", default=os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    ap.add_argument("--season", choices=SEASONS, help="override the season (default: from the date, northern hemisphere)")
    ap.add_argument("--date", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.date) if a.date else dt.date.today()
    season = season_for(today, a.season)
    p = resolve(a.project)
    items = load_closet(p.get("closet"))
    by_id = {i["id"]: i for i in items}
    outfits, hkind, hdates = load_history(p.get("history"), set(by_id))
    frange = formality_range(p.get("profile"))

    pool = {c: [i for i in items if i["cat"] == c and not i["suppressed"]] for c in ("top", "bottom", "shoes")}
    orphans = []
    for i in items:
        if i["cat"] == "acc" or i["suppressed"]:
            continue
        n, partners, why = completions(i, pool)
        if n < 10:
            orphans.append({"id": i["id"], "name": i["name"], "color": i["color"], "cat": i["cat"],
                            "outfits": n, "partners": partners, "main_block": why})
    orphans.sort(key=lambda o: (o["outfits"], o["name"]))

    worn = Counter(iid for o in outfits for iid in o)
    total = len(outfits)
    over = [{"id": k, "name": by_id[k]["name"], "cat": by_id[k]["cat"], "outfits": v, "share": round(v / total, 2)}
            for k, v in worn.most_common() if total and v / total > 0.25]
    unworn = [{"id": i["id"], "name": i["name"], "cat": i["cat"], "suppressed": i["suppressed"]}
              for i in items if i["id"] not in worn and season in i["seasons"]]
    gaps, gap_rows = gap_tally(p.get("gaplog"))
    data = {
        "date": today.isoformat(), "season": season, "source": p["source"],
        "files": {k: (str(v) if v else None, ok(v)) for k, v in p.items() if k != "source"},
        "items": len(items), "suppressed": sum(i["suppressed"] for i in items),
        "formality_range": frange, "history": {"kind": hkind, "outfits": total,
                                               "first": min(hdates) if hdates else "", "last": max(hdates) if hdates else ""},
        "never_logged_any_season": sum(1 for i in items if i["id"] not in worn),
        "coverage": coverage(items, season, frange), "orphans": [o for o in orphans if o["outfits"] < 3],
        "near_orphans": [o for o in orphans if o["outfits"] >= 3],
        "over_reliance": over, "unworn": unworn, "gap_log": {"rows": gap_rows, "clusters": gaps},
        "stale_gaps": stale_gaps(p.get("shopping"), items),
    }
    if a.json:
        json.dump(data, sys.stdout, indent=1, default=list)
        print()
        return
    print_md(data)


def print_md(d):
    out = []
    w = out.append
    w(f"# Closet audit, {d['date']} (season: {d['season']})")
    w("")
    h = d["history"]
    fr = d["formality_range"]
    missing = [k for k, (path, there) in d["files"].items() if k in ("closet", "history", "shopping", "gaplog", "profile") and not there]
    w(f"- Source: {d['source']}. Closet: {d['items']} items ({d['suppressed']} suppressed by flag).")
    w(f"- History: {h['outfits']} logged outfits ({h['kind']}{', ' + h['first'] + ' to ' + h['last'] if h['first'] else ''}). "
      f"It covers only outfits he logged, not everything he wore.")
    w(f"- Formality life: {f'{fr[0]}-{fr[1]} (from the profile)' if fr else 'not machine-readable: thin cells flagged at every level, judge them'}.")
    if missing:
        w(f"- Not found: {', '.join(missing)} (those lenses are empty; a missing gaplog just means none logged yet).")
    if not d["items"]:
        w("")
        w("Closet is empty: run closet intake before an audit.")
        print("\n".join(out))
        return
    w("")
    w("## Coverage grid")
    w("Cells: tops/bottoms/shoes within 1 point of formality F (what an outfit at F can draw on), suppressed items excluded. "
      "Lanes: neutral = neutral + `both` + street (street pairs with neutral); earth = earth + `both`. "
      "`!` = thin (a slot at 0-1) inside his formality range.")
    for scope, rows in d["coverage"].items():
        w("")
        w(f"**{'Now (' + scope + ')' if scope != 'all' else 'All year'}**")
        w("")
        w("| F | " + " | ".join(LANES) + " |")
        w("|---|" + "---|" * len(LANES))
        for f, row in rows.items():
            cells = [f"{c['tops']}/{c['bottoms']}/{c['shoes']}{' !' if c['thin'] else ''}" for c in (row[l] for l in LANES)]
            w(f"| {f} | " + " | ".join(cells) + " |")
    w("")
    w("## Orphans (<3 valid top+bottom+shoe outfits under the mechanical rules)")
    w("Rules checked: formality within 1, register, season overlap, one loud piece, chunky shoe, oversized top on fitted bottom. "
      "Colourway parentheticals and personal constraints are not modelled: the coach confirms.")
    near = d["near_orphans"]
    if not d["orphans"]:
        w("- none")
    for o in d["orphans"][:20]:
        w(f"- {o['name']} ({o['color']}, {o['cat']}): {o['outfits']} outfits, {o['partners']} partners"
          f"{', mostly blocked by ' + o['main_block'] if o['main_block'] else ''}")
    if len(d["orphans"]) > 20:
        w(f"- ...and {len(d['orphans']) - 20} more (use --json)")
    if near:
        w("- Near-orphans (3-9 outfits): " + "; ".join(f"{o['name']} {o['outfits']}" for o in near[:12]))
    w("")
    w("## Over-reliance (in >25% of logged outfits)")
    if h["outfits"] < 8:
        w(f"- Only {h['outfits']} logged outfits: too few to call reliance.")
    enough = h["outfits"] >= 8
    garments = [o for o in d["over_reliance"] if o["cat"] != "acc" and enough]
    accs = [o for o in d["over_reliance"] if o["cat"] == "acc" and enough]
    for o in garments:
        w(f"- **{o['name']}** ({o['cat']}): {o['outfits']}/{h['outfits']} outfits ({round(o['share'] * 100)}%)")
    if not garments and enough:
        w("- none (garments)")
    if accs:
        w("- Accessories (signature pieces are normal): " + ", ".join(f"{o['name']} {round(o['share'] * 100)}%" for o in accs))
    w("")
    gar_unworn = [u for u in d["unworn"] if u["cat"] != "acc"]
    w(f"## Unworn in {d['season']} ({len(gar_unworn)} garments never in a logged outfit; "
      f"{d['never_logged_any_season']} of {d['items']} items unlogged across all seasons)")
    if not h["outfits"]:
        w("- No history yet: every item is unlogged, so this lens says nothing.")
    else:
        by = defaultdict(list)
        for u in gar_unworn:
            by[u["cat"]].append(u["name"] + (" [suppressed]" if u["suppressed"] else ""))
        for cat in ("top", "layer", "bottom", "shoes"):
            if by[cat]:
                w(f"- {cat}: " + "; ".join(by[cat]))
        acc_unworn = [u["name"] for u in d["unworn"] if u["cat"] == "acc"]
        if acc_unworn:
            w(f"- accessories: {len(acc_unworn)} unlogged (often just not logged)")
    w("")
    g = d["gap_log"]
    w(f"## Gap log tally ({g['rows']} rows)")
    if not g["rows"]:
        w("- empty or missing (Mode A appends stylist Gap: lines over time)")
    for c in g["clusters"][:15]:
        w(f"- {c['gap']}{' [' + c['slot'] + ']' if c['slot'] else ''}: {c['count']}x on {c['dates']} date{'s' if c['dates'] != 1 else ''}, last {c['last'] or '?'}"
          f"{'  **PROMOTE**' if c['promote'] else ''}")
    w("")
    w("## Stale gaps (open in Known gaps, but something owned matches: verify)")
    w("Heuristic match on garment noun + colour words; false positives are likely, the coach decides.")
    if not d["stale_gaps"]:
        w("- none found")
    for s in d["stale_gaps"]:
        w(f"- \"{s['gap']}\": possibly already owned: " + "; ".join(s["owned"]))
    print("\n".join(out))


if __name__ == "__main__":
    main()

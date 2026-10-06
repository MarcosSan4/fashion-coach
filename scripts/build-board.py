#!/usr/bin/env python3
"""Build the fashion-coach Outfit Board: a self-contained local HTML page that renders
outfits on an SVG mannequin, with a remix drawer of the whole closet and live rule checks.

Usage:
  build-board.py --slug drinks < outfits.json   # JSON on stdin: adds this board to the page
  build-board.py path/to/outfits.json            # same, from a file (the file is not kept)
  build-board.py --closet                        # rebuilds the page and prints its URL opened on the closet sandbox
  build-board.py --rebuild                       # rebuilds the page (e.g. after closet edits)
  build-board.py --history-text                  # prints the CSV history as lines for the coach prompt
  build-board.py --where                         # print the resolved closet and page path
  add -v to any build to list every guessed colour
  add --open to any build: starts the local board server (if needed) and opens the board in a browser;
    with a CSV history the page then saves worn outfits and remixes straight into the CSVs

There is ONE file per user, <BOARD_DIR>/outfit-board.html. It stores its own history (the last 10 boards,
newest first, history menu + the closet sandbox) inside itself; nothing else is written.

Paths resolve like load-context.sh (first match wins):
  1. <project>/.fashion-coach   config file: CLOSET= PROFILE= HISTORY=, optional REMIXES= LESSONS=
                                BOARD_DIR= COLORS= BROWSER= (relative paths resolve against the config
                                file's folder; absolute and ~/ paths as given)
  2. <project>/wardrobe/        closet.csv, profile.md, outfit-history.csv (with remixes.csv and lessons.md
                                beside it) else outfit-history.md, optional board-colors.json, boards in boards/
  3. ~/.fashion-coach           global config file, same keys as 1 (used only without <project>/wardrobe/)
  4. ~/fashion-coach/           same layout as 2
<project> is $CLAUDE_PROJECT_DIR, else the current directory. Default BOARD_DIR with a config file is
<project>/outputs/outfits when <project>/outputs exists, else <closet folder>/boards.
COLORS=path/to/board-colors.json: optional per-closet tuning, JSON {"colors": {"name": "#hex"},
  "items": {"<id>": ["#main", "#trim", "#accent", "#sole"]}, "shapes": {"<id>": "<shape>"}}.
BROWSER=<macOS app name> (optional, e.g. Firefox): opens the board in that app; default the system browser.
Mannequin colouring comes from the profile frontmatter, e.g. `figure: skin fair, hair dark brown, eyes blue,
texture curly` (texture: curly | wavy | short | buzz | bald). A "figure" object in the outfits JSON overrides it.

Shapes (for shape overrides and Mode B ghosts):
  layer   overshirt leather-jacket shell-jacket puffer blazer coat trench bomber denim-jacket gilet
  top     tee tank henley polo knit-polo ls-polo shirt camp-shirt crew-knit turtleneck vneck cardigan
          quarter-zip sweatshirt hoodie zip-hoodie
  bottom  trouser jeans cargo jogger shorts
  shoes   low-sneaker chunky-sneaker high-top runner loafer derby chunky-derby oxford chelsea desert-boot
          lug-boot hiking-boot espadrille boat-shoe sandal
  acc     belt rect rounded-square aviator round (sunglasses) watch chain pendant ring bracelet cap beanie
          bucket-hat tote crossbody backpack

Prints the HTML path. Colours not in the table are guessed from their words: a base colour ("terracotta",
"sage", "navy") shifted by modifiers ("soft", "dusty", "dark", "warm", "heather"...), noted on an INFO line.
A colour with no known base word is drawn mid gray and named on a WARNING line (the build still succeeds):
add it under "colors" in the COLORS file. Exit code 1 only for real data errors (unknown type, bad ids).
"""
import colorsys
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

import os

INFO = []
info = INFO.append
NOTES = []  # non-fatal WARNINGs: printed, but the page is still built and the exit code stays 0


def soft_warn(msg):
    if msg not in NOTES:  # resolve() runs more than once per build
        NOTES.append(msg)
SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets/outfit-board.template.html"
PROJECT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
DEFAULT_FIGURE = {"skin": "#e9c9b1", "hair": "#4a3426", "eyes": "#6f6253", "texture": "short"}


# Named colouring for the mannequin, so onboarding writes words, not hex codes.
FIGURE_NAMES = {
    "skin": {"very fair": "#f3dccd", "fair": "#efd3c0", "light": "#e6c4a8", "light-medium": "#d9ae8a", "medium": "#c4916a",
             "olive": "#b58a60", "tan": "#9c6c47", "deep": "#6e4631", "very deep": "#4b2e21"},
    "hair": {"black": "#1b1716", "dark brown": "#3a281e", "brown": "#5a3c28", "medium brown": "#5a3c28", "light brown": "#8a6240",
             "dark blond": "#a7834f", "blond": "#d0b07a", "platinum": "#e6dcc4", "red": "#8a3b1f", "auburn": "#6e2f1c",
             "gray": "#9a9a9a", "grey": "#9a9a9a", "white": "#dedede"},
    "eyes": {"dark brown": "#3f2a1d", "brown": "#6b4a2f", "hazel": "#7d6b3c", "amber": "#a7712e", "green": "#5f7d4f",
             "gray": "#8a949c", "grey": "#8a949c", "blue": "#5d8fc2", "light blue": "#7db3e2", "dark blue": "#3d5f8f"},
}
TEXTURES = {"straight": "short", "short": "short", "wavy": "wavy", "curly": "curly", "coily": "curly", "buzz": "buzz", "bald": "bald", "shaved": "bald"}


def profile_figure(path):
    """Read `figure: skin fair, hair dark brown, eyes light blue, texture curly` from the profile frontmatter."""
    try:
        txt = Path(path).read_text()
    except OSError:
        return {}
    fm = re.match(r"---\s*\n(.*?)\n---", txt, re.S)
    line = re.search(r"^figure:\s*(.+)$", fm.group(1), re.M) if fm else None
    if not line:
        return {}
    out = {}
    for part in line.group(1).split(","):
        m = re.match(r"\s*(skin|hair|eyes|texture)\s+(.+?)\s*$", part.strip().lower())
        if not m:
            continue
        key, val = m.groups()
        if key == "texture":
            out[key] = TEXTURES.get(val, "short")
        elif val.startswith("#"):
            out[key] = val
        elif val in FIGURE_NAMES[key]:
            out[key] = FIGURE_NAMES[key][val]
        else:
            INFO.append(f"profile figure: unknown {key} '{val}', using the default")
    return out


PATHS = {}


def resolve():
    """(closet_csv, board_dir, figure) using the same lookup order as load-context.sh."""
    cfg, conf = {}, None
    if (PROJECT / ".fashion-coach").is_file():
        conf = PROJECT / ".fashion-coach"
    elif not (PROJECT / "wardrobe/profile.md").is_file() and (Path.home() / ".fashion-coach").is_file():
        conf = Path.home() / ".fashion-coach"
    if conf:
        for ln in conf.read_text().splitlines():
            m = re.match(r"\s*([A-Z_]+)\s*=\s*(.*?)\s*$", ln)
            if m and not ln.lstrip().startswith("#"):
                cfg.setdefault(m.group(1), m.group(2).strip('"'))  # first one wins, like load-context.sh
        # relative paths resolve against the config file's folder (absolute and ~/ as given), like load-context.sh
        ab = lambda v: Path(os.path.expanduser(v)) if v.startswith(("/", "~")) else conf.parent / v
        closet = ab(cfg.get("CLOSET", "wardrobe/closet.csv"))
        profile = ab(cfg.get("PROFILE", "wardrobe/profile.md"))
        PATHS["history"] = ab(cfg.get("HISTORY", "wardrobe/outfit-history.md"))
        PATHS["remixes"] = ab(cfg["REMIXES"]) if cfg.get("REMIXES") else None
        PATHS["lessons"] = ab(cfg["LESSONS"]) if cfg.get("LESSONS") else None
        PATHS["browser"] = cfg.get("BROWSER")
        board = ab(cfg["BOARD_DIR"]) if cfg.get("BOARD_DIR") else None
        tune = ab(cfg["COLORS"]) if cfg.get("COLORS") else None
    else:
        base = PROJECT / "wardrobe" if (PROJECT / "wardrobe/profile.md").is_file() else Path.home() / "fashion-coach"
        closet, board, profile = base / "closet.csv", base / "boards", base / "profile.md"
        # same files load-context.sh reads in this layout: a CSV history (with lessons.md and remixes.csv
        # beside it) when there is one or no history exists yet (new setups), else the older markdown history
        if (base / "outfit-history.csv").is_file() or not (base / "outfit-history.md").is_file():
            PATHS["history"], PATHS["remixes"] = base / "outfit-history.csv", base / "remixes.csv"
            PATHS["lessons"] = base / "lessons.md" if (base / "lessons.md").is_file() else None
        else:
            PATHS["history"] = base / "outfit-history.md"
            PATHS["remixes"] = PATHS["lessons"] = None
        PATHS["browser"] = None
        tune = base / "board-colors.json"
        tune = tune if tune.is_file() else None  # optional in this layout: no note when absent
    if board is None:
        board = PROJECT / "outputs/outfits" if (PROJECT / "outputs").is_dir() else closet.parent / "boards"
    fig = dict(DEFAULT_FIGURE)
    for k, v in re.findall(r"(\w+):(\S+)", cfg.get("FIGURE", "")):  # legacy config key
        fig[k] = v
    fig.update(profile_figure(profile))  # the profile's own `figure:` line wins
    if tune:
        if tune.is_file():
            try:
                t = json.loads(tune.read_text())
            except ValueError as e:
                t = {}
                soft_warn(f"COLORS file {tune} is not valid JSON ({e}), using the built-in colour table")
            COLOR_HEX.update({k.lower(): v for k, v in t.get("colors", {}).items()})
            HEX_OVERRIDE.update({int(k): v for k, v in t.get("items", {}).items()})
            SHAPE_OVERRIDE.update({int(k): v for k, v in t.get("shapes", {}).items()})
        else:
            INFO.append(f"COLORS file {tune} not found, using the built-in colour table")
    return closet, board, fig

# Colour words as they appear in the catalog -> hex, tuned to how the real pieces read.
COLOR_HEX = {
    "black": "#161616", "white": "#f7f6f2", "pearl white": "#f1eee6", "cream": "#ece3cf",
    "navy": "#1f2a46", "dark navy": "#19213a", "midnight navy": "#151c32",
    "near-black navy": "#181c29", "dark blue": "#22305c",
    "charcoal": "#3b3e43", "charcoal gray": "#46494e", "dark gray": "#4b4e53",
    "near-black gray": "#27282b", "gray": "#8e9196", "light gray": "#c8cacc",
    "heather gray": "#9d9fa3", "ice gray": "#d6d3ca", "clear light gray": "#dde1e4",
    "silver": "#c3c7cb",
    "baby blue": "#b8d2ec", "light blue": "#a8c0d8", "light sky blue": "#a6cdee",
    "porcelain blue": "#8db5de", "dusty blue": "#8fa3b7", "slate blue": "#6e8096",
    "air force blue": "#5d86a6", "pale blue-green": "#cfe1dc",
    "taupe brown": "#8b7560", "taupe greige": "#aa9d8b", "taupe gray": "#8c827a",
    "stone taupe": "#a89d8a", "taupe olive": "#7b7457",
    "beige": "#cdbb9a", "light beige": "#ddd1b9",
    "espresso brown": "#3a2a22", "dark chocolate brown": "#3e2b21", "dark brown": "#4a3527",
    "brown": "#6b4b36", "medium brown": "#8b5a35", "tortoiseshell": "#8a5b2c",
    "olive green": "#6a6c43", "dark green": "#2d3a31",
    "unconfirmed": "#8a8f99",
}

# Fallback for colour words not in the table: the last base word wins ("olive green" -> olive),
# then every modifier word shifts it, in order. Words it knows neither way are listed in the INFO line.
BASE_HEX = {
    # neutrals
    "black": "#161616", "nearblack": "#1e1f21", "white": "#f7f6f2", "offwhite": "#efeadf", "chalk": "#eeebe3", "ivory": "#f3eedf",
    "cream": "#ece3cf", "bone": "#e3dccb", "ecru": "#e6dcc6", "natural": "#e3d8c1", "oatmeal": "#d8ccb4",
    "oat": "#d8ccb4", "putty": "#c2b59b", "gray": "#8e9196", "grey": "#8e9196", "ash": "#b2b0aa",
    "smoke": "#a3a5a7", "pewter": "#8f9194", "slate": "#6e7a86", "steel": "#6f7f8f", "graphite": "#44474c",
    "charcoal": "#3b3e43", "silver": "#c3c7cb", "gold": "#c9a54a", "brass": "#b5994f", "bronze": "#8c6a3a",
    "copper": "#b06a3b", "champagne": "#e6d6b4",
    # beiges and browns
    "beige": "#cdbb9a", "sand": "#d3c19f", "stone": "#a89d8a", "taupe": "#8b7f71", "greige": "#aa9d8b",
    "mushroom": "#9e8f80", "wheat": "#dcc59a", "biscuit": "#d4b98f", "fawn": "#c8a888", "khaki": "#a99d72",
    "camel": "#b48a57", "tan": "#b89470", "caramel": "#a8703d", "tobacco": "#7a5530", "cognac": "#8b4a24",
    "chestnut": "#7b4a2e", "walnut": "#5c4033", "mocha": "#6f5443", "coffee": "#5a4130", "brown": "#6b4b36",
    "chocolate": "#3e2b21", "espresso": "#3a2a22", "umber": "#5c4430", "mahogany": "#6a2e22",
    # warm colours
    "rust": "#9c4a25", "terracotta": "#b5603f", "brick": "#9a4434", "clay": "#b07a5c", "sienna": "#a0522d",
    "ochre": "#c08a2e", "mustard": "#c49a2c", "amber": "#c38a2a", "saffron": "#e0a83a", "pumpkin": "#c86a2a",
    "orange": "#d9772f", "apricot": "#eeb48a", "peach": "#f0b896", "coral": "#e47c64", "salmon": "#e08f7a",
    "yellow": "#e3c44a", "butter": "#f0dc96", "lemon": "#ecd85a",
    "red": "#b3262c", "tomato": "#c8442f", "scarlet": "#c0242a", "crimson": "#a51c30", "cherry": "#8e1b2c",
    "cranberry": "#8a1f35", "burgundy": "#6b1f2a", "oxblood": "#5a1a20", "maroon": "#5e1d24", "wine": "#5f1f2d",
    "berry": "#7a2a4a", "pink": "#e6a3b5", "blush": "#e8c0bc", "rose": "#c9808f", "mauve": "#a5838f",
    "fuchsia": "#c2307a", "magenta": "#b02a78",
    # purples
    "lilac": "#b8a5d0", "lavender": "#b5a8d6", "periwinkle": "#8c94d6", "violet": "#6a4a9a", "purple": "#5b3b80",
    "plum": "#5b2e4c", "aubergine": "#3e2236", "eggplant": "#3e2236",
    # blues
    "navy": "#1f2a46", "ink": "#22283a", "indigo": "#2b3561", "denim": "#4a6587", "blue": "#3e64a8",
    "cobalt": "#1f4fb4", "royal": "#2a4fb0", "cornflower": "#6f8fd8", "sky": "#9cc8ec", "powder": "#b0cbe6",
    "azure": "#4f8fd0", "petrol": "#1f4f5c", "teal": "#1f6d6e", "turquoise": "#3fb1b0", "aqua": "#6fc8c8",
    # greens
    "seafoam": "#9ccdb8", "mint": "#bfe3d2", "eucalyptus": "#8faa9a", "sage": "#9caf94", "pistachio": "#b5c99a",
    "lime": "#a8c64a", "chartreuse": "#b8c43a", "green": "#3f6b4a", "kelly": "#2f8a4a", "emerald": "#0f6b4f",
    "moss": "#6b7445", "fern": "#5a7a4a", "olive": "#6a6c43", "army": "#5a5d3c", "forest": "#24412f",
    "hunter": "#2e4a36", "bottle": "#1f4a33", "pine": "#2c4a3a",
    # patterns that read as one colour from across a room
    "camo": "#5f6448", "tortoiseshell": "#8a5b2c", "tortoise": "#8a5b2c",
}
FAMILY = {"blue", "green", "gray", "grey", "brown", "red", "pink", "purple", "yellow", "orange", "white", "black"}
GRAY_MID = "#8e9196"  # what an undrawable colour falls back to
# word -> (kind, amount). mix: toward that hex; sat: scale saturation (and pull lightness toward the
# middle a little); hue: warm/cool nudge (neutrals get a tint instead); a list is several steps.
# Several words stack, in order.
MODS = {
    "nearblack": ("#000000", .7), "verydark": ("#000000", .5), "dark": ("#000000", .35), "deep": ("#000000", .3),
    "midnight": ("#000000", .45), "rich": ("#000000", .12),
    "light": ("#ffffff", .45), "pale": ("#ffffff", .55), "baby": ("#ffffff", .5), "ice": ("#ffffff", .6),
    "icy": ("#ffffff", .6), "pastel": ("#ffffff", .5), "bleached": ("#ffffff", .35),
    "soft": ("sat", .5), "muted": ("sat", .5), "dusty": ("sat", .45), "dusky": ("sat", .5), "washed": [("sat", .6), ("#ffffff", .2)],
    "faded": [("sat", .55), ("#ffffff", .2)], "smoky": ("sat", .5), "vintage": ("sat", .65), "burnt": ("#4a2410", .2), "greyed": ("sat", .4), "grayed": ("sat", .4),
    "brushed": ("sat", .8), "bright": ("sat", 1.3), "vivid": ("sat", 1.35), "electric": ("sat", 1.4),
    "heather": ("#9a9a9a", .2), "heathered": ("#9a9a9a", .2), "melange": ("#9a9a9a", .2), "marl": ("#9a9a9a", .2),
    "mottled": ("#9a9a9a", .15),
    "warm": ("hue", 30), "cool": ("hue", 215),
}
NEUTRAL_WORDS = {"mid", "medium", "true", "classic", "tonal", "solid", "plain", "wash", "rinse", "raw", "mix", "and", "with", "tone", "toned"}
PHRASES = [("near-black", "nearblack"), ("near black", "nearblack"), ("very dark", "verydark"),
           ("off-white", "offwhite"), ("off white", "offwhite")]


def mix(h, to, a):
    x, y = int(h[1:], 16), int(to[1:], 16)
    ch = lambda sh: round(((x >> sh) & 255) * (1 - a) + ((y >> sh) & 255) * a)
    return "#%02x%02x%02x" % (ch(16), ch(8), ch(0))


def shift(h, kind, amt):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    hh, l, s = colorsys.rgb_to_hls(r, g, b)
    if kind == "sat":
        s = min(1.0, s * amt)
        if amt < 1:  # soft/dusty colours also sit nearer the middle of the light range
            l += (0.55 - l) * (1 - amt) * 0.4
    else:  # warm/cool: rotate up to 12 degrees toward amber or blue; neutrals have no hue, so tint them
        if s < 0.12:
            return mix(h, "#a4875f" if amt == 30 else "#7f93ad", .18)
        d = ((amt / 360 - hh + 0.5) % 1) - 0.5
        hh = (hh + max(-12 / 360, min(12 / 360, d))) % 1
    return "#%02x%02x%02x" % tuple(round(c * 255) for c in colorsys.hls_to_rgb(hh, l, s))


def guess_hex(name):
    """(hex, base word or None, ignored words). With no base word the hex is a mid gray."""
    name = name.lower()
    for a, b in PHRASES:
        name = name.replace(a, b)
    words, found, tints, ignored = re.findall(r"[a-z]+", name), [], [], []
    for w in words:
        stem = next((s for s in (w[:-3], w[:-4], w[:-3] + "e") if s in BASE_HEX), None) if w.endswith("ish") else None
        if stem:  # "bluish gray": a tint of blue on gray
            tints.append(stem)
        elif w in BASE_HEX:
            found.append(w)
        elif w not in MODS and w not in NEUTRAL_WORDS:
            ignored.append(w)
    if not found and tints:
        found = [tints.pop()]
    specific = [w for w in found if w not in FAMILY]
    pick = (specific or found or [None])[-1]
    base = BASE_HEX.get(pick, GRAY_MID)
    for w in tints:
        base = mix(base, BASE_HEX[w], .25)
    for w in words:
        steps = MODS.get(w, []) if w != pick else []
        for to, a in steps if isinstance(steps, list) else [steps]:
            base = shift(base, to, a) if to in ("sat", "hue") else mix(base, to, a)
    return base, pick, ignored


# Per-closet tuning lives with the client's data, not in the skill: the optional COLORS=
# file named in .fashion-coach (JSON): {"colors": {"name": "#hex"}, "items": {"<id>": ["#main",
# "#trim", "#accent"]}, "shapes": {"<id>": "<shape>"}}. Items get multi-tone fills (sneaker
# accents, logo prints, two-tone drawcords); shapes fix pieces the keyword rules misread.
HEX_OVERRIDE, SHAPE_OVERRIDE = {}, {}

SLOT_BY_TYPE = {
    "outerwear": "layer", "hoodie": "top", "sweatshirt": "top", "sweater": "top",
    "polo": "top", "tshirt": "top", "shirt": "top", "jeans": "bottom", "pants": "bottom",
    "shorts": "bottom", "shoes": "shoes", "belt": "belt", "sunglasses": "acc",
    "watch": "acc", "jewelry": "acc", "cap": "acc", "tank": "top", "hat": "acc", "bag": "acc",
}

NOUN = {
    "puffer": "puffer", "leather-jacket": "jacket", "shell-jacket": "shell jacket",
    "overshirt": "overshirt", "zip-hoodie": "zip hoodie", "hoodie": "hoodie",
    "sweatshirt": "crewneck sweatshirt", "quarter-zip": "quarter-zip", "turtleneck": "turtleneck",
    "crew-knit": "crewneck knit", "ls-polo": "long-sleeve knit polo", "knit-polo": "Johnny-collar polo",
    "polo": "polo", "tank": "ribbed tank", "henley": "henley", "tee": "tee",
    "camp-shirt": "short-sleeve shirt", "shirt": "shirt", "jeans": "jeans", "cargo": "cargo pants",
    "trouser": "trousers", "shorts": "shorts", "chelsea": "Chelsea boots", "lug-boot": "lug boots",
    "hiking-boot": "hiking boots", "loafer": "loafers", "chunky-derby": "chunky Derbies",
    "derby": "Derbies", "espadrille": "espadrilles", "boat-shoe": "boat shoes", "runner": "runners",
    "chunky-sneaker": "chunky sneakers", "low-sneaker": "sneakers", "belt": "belt",
    "round": "round sunglasses", "aviator": "aviators", "rounded-square": "sunglasses",
    "rect": "sunglasses", "watch": "watch", "pendant": "pendant necklace", "chain": "chain necklace",
    "cap": "cap", "blazer": "blazer", "coat": "coat", "trench": "trench coat", "bomber": "bomber",
    "denim-jacket": "denim jacket", "gilet": "gilet", "cardigan": "cardigan", "vneck": "V-neck knit",
    "jogger": "joggers", "oxford": "oxfords", "desert-boot": "desert boots", "sandal": "sandals",
    "high-top": "high-tops", "beanie": "beanie", "bucket-hat": "bucket hat", "tote": "tote",
    "crossbody": "crossbody bag", "backpack": "backpack", "ring": "ring", "bracelet": "bracelet",
}
MATERIALS = ["linen", "leather", "suede", "merino", "corduroy", "flannel", "canvas", "denim", "knit"]
PATTERN_WORD = {"stripe": "striped", "hstripe": "striped", "check": "check", "graphic": "graphic"}


def infer_shape(t, d, vol):
    if t == "outerwear":
        if "trench" in d: return "trench"
        if "puffer" in d or "nuptse" in d or "down jacket" in d: return "puffer"
        if "gilet" in d or "vest" in d or "sleeveless" in d: return "gilet"
        if "blazer" in d or "sport coat" in d or "suit jacket" in d: return "blazer"
        first = d.split(",")[0]
        if re.search(r"\b(overcoat|topcoat|peacoat|parka|coat)\b", first) and not re.search(r"overshirt|shacket", first): return "coat"
        if "bomber" in d or "harrington" in d: return "bomber"
        if "leather" not in first and ("denim" in first or "trucker" in first): return "denim-jacket"
        if "leather" in d: return "leather-jacket"
        if "shell" in d: return "shell-jacket"
        return "overshirt"
    if t == "hoodie":
        return "zip-hoodie" if "zip-up" in d else "hoodie"
    if t == "sweatshirt":
        return "quarter-zip" if "quarter-zip" in d else "sweatshirt"
    if t == "sweater":
        if "cardigan" in d: return "cardigan"
        if "turtleneck" in d or "roll neck" in d or "rollneck" in d: return "turtleneck"
        if "v-neck" in d or "v neck" in d: return "vneck"
        if "quarter-zip" in d or "half-zip" in d: return "quarter-zip"
        return "crew-knit"
    if t == "polo":
        if "long-sleeve" in d or "polo sweater" in d: return "ls-polo"
        if "johnny" in d: return "knit-polo"
        return "polo"
    if t == "tank": return "tank"
    if t == "tshirt":
        if "tank" in d: return "tank"
        if "henley" in d: return "henley"
        return "tee"
    if t == "shirt":
        return "camp-shirt" if "short-sleeve" in d else "shirt"
    if t == "jeans": return "jeans"
    if t == "pants":
        if "cargo" in d: return "cargo"
        if "jeans" in d or "denim" in d: return "jeans"
        if ("jogger" in d or "sweatpant" in d) and ("cuff" in d and "no elastic cuff" not in d and "open hem" not in d): return "jogger"
        return "trouser"
    if t == "shorts": return "shorts"
    if t == "shoes":
        if "sandal" in d or "slide" in d: return "sandal"
        if "desert" in d or "chukka" in d: return "desert-boot"
        if "chelsea" in d: return "chelsea"
        if "hiking" in d: return "hiking-boot"
        if "timberland" in d: return "lug-boot"
        if "loafer" in d or "moccasin" in d: return "loafer"
        if "derb" in d: return "chunky-derby" if vol == "chunky" else "derby"
        if "oxford" in d or "brogue" in d or "monk" in d or "dress shoe" in d: return "oxford"
        if "boot" in d: return "lug-boot" if vol == "chunky" else "desert-boot"
        if "espadrille" in d: return "espadrille"
        if "boat" in d: return "boat-shoe"
        if "running" in d or "trainer" in d: return "runner"
        if "high-top" in d or "high top" in d or "hi-top" in d: return "high-top"
        return "chunky-sneaker" if vol == "chunky" else "low-sneaker"
    if t == "belt": return "belt"
    if t == "sunglasses":
        if "round sunglasses" in d or "round-frame" in d or re.search(r"\bround\b", d) and "rounded" not in d:
            return "round"
        if "aviator" in d: return "aviator"
        if "rounded-square" in d: return "rounded-square"
        return "rect"
    if t == "watch": return "watch"
    if t == "jewelry":
        if "ring" in d.split(",")[0]: return "ring"
        if "bracelet" in d or "bangle" in d or "cuff" in d: return "bracelet"
        return "pendant" if "pendant" in d else "chain"
    if t in ("cap", "hat"):
        if "beanie" in d or "knit hat" in d: return "beanie"
        if "bucket" in d: return "bucket-hat"
        return "cap"
    if t == "bag":
        if "backpack" in d: return "backpack"
        if "crossbody" in d or "sling" in d or "messenger" in d: return "crossbody"
        return "tote"
    return None


def infer_texture(t, d):
    """Read the first sentence only: later sentences are styling notes, not fabric."""
    if t in ("sunglasses", "watch", "jewelry"): return None
    d = re.split(r"[;.] ", d)[0]
    if "stripe" in d or "breton" in d:
        if "tonal" in d: return "rib"
        return "hstripe" if re.search(r"horizontal|breton|marini", d) else "stripe"
    if re.search(r"\bcheck|plaid|gingham|tartan|buffalo", d): return "check"
    if "graphic" in d or ("print" in d and t == "tshirt" and "small" not in d): return "graphic"
    if "corduroy" in d or " cord " in d: return "cord"
    if "tessellation" in d or "geometric" in d: return "geo"
    if "houndstooth" in d: return "houndstooth"
    if "quilt" in d or "puffer" in d: return "quilt"
    if "canale" in d or "ribbed" in d or "pointelle" in d: return "rib"
    if "cable" in d or "braided" in d: return "cable"
    if "waffle" in d or "pique" in d: return "waffle"
    if "suede" in d: return "suede"
    if "leather" in d and t in ("outerwear", "shoes", "belt"): return "leather"
    if "linen" in d: return "linen"
    if t == "jeans" or "denim" in d: return "denim"
    if "melange" in d or "heather" in d or "slub" in d or "flannel" in d: return "melange"
    if "canvas" in d: return "canvas"
    return None


def split_colorways(color):
    """'white, porcelain blue (loud + hero-colour, not favorite)' -> [(name, note)]"""
    parts, depth, cur = [], 0, ""
    for ch in color:
        if ch == "(": depth += 1
        if ch == ")": depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur); cur = ""
        else:
            cur += ch
    parts.append(cur)
    out = []
    for p in parts:
        m = re.match(r"\s*([^()]*?)\s*(?:\((.*)\))?\s*$", p)
        out.append((m.group(1).strip(), (m.group(2) or "").strip()))
    return out


def colorway_spec(name, note, base, warn, iid):
    hexes = []
    for piece in name.split("/"):
        piece = piece.strip().lower()
        if piece.startswith("multi"):  # multicolor / multi-colour: the default multi-tone fill below
            continue
        if piece in COLOR_HEX:
            hexes.append(COLOR_HEX[piece])
            continue
        hx, pick, ignored = guess_hex(piece)
        hexes.append(hx)
        skipped = f"; ignored {', '.join(repr(w) for w in ignored)}" if ignored else ""
        if pick:
            info(f"id {iid}: guessed '{piece}' as {hx}{skipped} (tune it under colors in the COLORS file)")
        else:  # never fatal: draw it mid gray (modifiers still apply) and say so
            soft_warn(f"id {iid}: unknown colour '{piece or '(blank)'}', drawn as {hx}; add it under colors in the COLORS file")
    cw = {"name": name, "hex": hexes}
    n = note.lower()
    if note:
        cw["note"] = note
        if "loud" in n: cw["loud"] = "yes"
        if "hero-colour" in n: cw["flag"] = (base["flag"] + " hero-colour").strip()
        if "earth register" in n: cw["register"] = "earth"
        if "not winter" in n: cw["winter"] = False
        if "not favorite" in n: cw["favorite"] = "no"
    return cw


def label_for(shape, desc, color_name, texture=None):
    d = desc.lower()
    mat = next((m for m in MATERIALS if m in d.split(",")[0] or m in d[:60]), "")
    if shape in ("jeans",) or (mat == "denim"): mat = ""
    if shape in ("leather-jacket",): mat = "leather"
    noun = NOUN.get(shape, shape)
    if "jogger" in d[:80]: noun = "joggers"
    if color_name == "unconfirmed": color_name, noun = "", noun + " (colour unconfirmed)"
    if "multi" in color_name.lower():  # a colour word says nothing here: use the piece's own name
        head = re.split(r",|;|\(", desc)[0].strip()
        head = re.sub(r"(?i)\b(multicolou?r|multi-colou?r)\b", "", head).strip(" -")
        if head: return head
    if mat and mat in noun: mat = ""
    if mat == "knit" and ("knit" in noun or "polo" in noun or "sweater" in noun): mat = ""
    pat = PATTERN_WORD.get(texture, "")
    if pat and mat == "flannel": mat = ""
    return " ".join(x for x in [color_name, pat, mat, noun] if x)


def load_items(csv_path, warn):
    items = []
    with open(csv_path, newline="") as f:
        for r in csv.DictReader(f):
            iid = int(r["id"])
            t = r["type"].strip()
            d = r["description"].lower()
            slot = SLOT_BY_TYPE.get(t)
            if not slot:
                warn(f"id {iid}: unknown type '{t}'")
                continue
            # the main clause names the garment; brackets and post-";" notes often mention OTHER pieces
            d_main = re.sub(r"\([^)]*\)", "", d).split(";")[0]
            shape = SHAPE_OVERRIDE.get(iid) or infer_shape(t, d_main, r["volume"]) or infer_shape(t, d, r["volume"])
            if not shape:
                warn(f"id {iid}: could not infer a shape (add to SHAPE_OVERRIDE)")
                shape = "tee"
            base = {k: r[k] for k in ("formality", "register", "volume", "loud", "flag", "favorite")}
            base["formality"] = int(base["formality"]) if base["formality"].isdigit() else 3
            seasons = {s: r[s].strip().lower() == "true" for s in ("spring", "summer", "fall", "winter")}
            cws = []
            for name, note in split_colorways(r["color"]):
                cw = colorway_spec(name, note, base, warn, iid)
                if iid in HEX_OVERRIDE and len(cws) == 0:
                    cw["hex"] = HEX_OVERRIDE[iid]
                if not cw["hex"] and "multi" in name.lower():
                    cw["hex"] = ["#c9bfae", "#3e64a8", "#d9772f"]
                    info(f"id {iid}: '{name}' drawn with a default multi-tone fill (tune it under items in the COLORS file)")
                elif not cw["hex"]:
                    soft_warn(f"id {iid}: colour '{name}' has no hex, drawn as {GRAY_MID}")
                    cw["hex"] = [GRAY_MID]
                nm = (r.get("name") or "").strip()
                if nm:  # his own name for the piece; colourway shown after it on multi-colour rows
                    m = re.match(r"^(.*?)\s*(\([^()]*\))?$", nm)  # "Slub tee (Benetton)": brand rides at the end
                    main, brand = m.group(1), m.group(2) or ""
                    if len(split_colorways(r["color"])) > 1: main = f"{main}, {name}"
                    cw["label"] = f"{main} {brand}".strip()
                else:
                    cw["label"] = label_for(shape, r["description"], name, infer_texture(t, d))
                cws.append(cw)
            items.append({
                "id": iid, "type": t, "slot": slot, "shape": shape,
                "texture": infer_texture(t, d), "colorways": cws, "seasons": seasons,
                "desc": r["description"], **base,
            })
    return items


DESCRIPTOR = re.compile(r"-|^(plain|slub|thin|slim|regular|oversized|chunky|fine|basic|ribbed|textured|heavy|light|soft|classic|minimal|minimalist|square|round)$", re.I)


def disambiguate(items):
    """Two pieces with the same label get the first distinctive word of their description."""
    by = {}
    for it in items:
        for cw in it["colorways"]:
            by.setdefault(cw["label"].lower(), []).append((it, cw))
    for group in (g for g in by.values() if len(g) > 1):
        for it, cw in group:
            have = set(re.findall(r"[a-z]+", cw["label"].lower())) | set(re.findall(r"[a-z]+", cw["name"].lower()))
            for w in re.findall(r"[A-Za-z][A-Za-z'-]*", it["desc"]):
                if w.lower() in have or w.lower() in COLOR_HEX or w.lower() in BASE_HEX or len(w) < 3:
                    continue
                cw["label"] += ", " + (w.lower() if DESCRIPTOR.search(w) else w)
                break


HISTORY_MAX = 10


def parse_history(items):
    """His graded outfits from the outfit-history file, for the board's Saved outfits gallery.
    Reads every markdown table whose header has an Outfit column and a grade column, up to the
    anti-examples section; pieces are found by closet id in brackets, "(36)", else by name."""
    path = PATHS.get("history")
    try:
        txt = Path(path).read_text()
    except (OSError, TypeError):
        return []
    by_id = {str(i["id"]): i for i in items if not i.get("ghost")}
    names = sorted(((cw["label"].split(" (")[0].split(",")[0].lower(), i, j) for i in by_id.values()
                    for j, cw in enumerate(i["colorways"])), key=lambda t: -len(t[0]))
    added = {m.group(1): m.group(2) for m in re.finditer(r"#(\d+)\D{0,40}?added (\d{4}-\d{2}-\d{2})", txt)}
    out, cols = [], None
    for ln in txt.splitlines():
        if re.match(r"#+ .*anti", ln, re.I):
            break
        if not ln.startswith("|"):
            cols = None if not ln.strip() else cols
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        low = [c.lower() for c in cells]
        if "outfit" in low and any("grade" in c for c in low):
            gi = next((i for i, c in enumerate(low) if "his grade" in c), None)
            gi = gi if gi is not None else next(i for i, c in enumerate(low) if "grade" in c)
            cols = {"n": low.index("#") if "#" in low else None, "outfit": low.index("outfit"), "grade": gi,
                    "date": low.index("date") if "date" in low else None,
                    "est": next((i for i, c in enumerate(low) if "coach est" in c), None)}
            continue
        if not cols or set(ln.replace("|", "").strip()) <= set("-: "):
            continue
        get = lambda k: cells[cols[k]] if cols.get(k) is not None and cols[k] < len(cells) else ""
        n = re.sub(r"\D", "", get("n")) or str(len(out) + 1)
        nums = [float(x) for x in re.findall(r"\d\.\d", get("grade"))]
        if not nums:
            continue
        o = {"layer": None, "top": None, "under": None, "bottom": None, "shoes": None, "belt": None, "acc": []}
        pieces, partial = [], False
        for seg in re.split(r"\s\+\s", get("outfit")):
            if re.search(r"not owned|uncatalogued", seg, re.I):
                partial = True
                continue
            m = re.search(r"\((\d+(?:/\d+)*)(?:,\s*([^)]*))?\)", seg)
            refs = []
            if m:
                cwm = re.search(r"([a-z][a-z -]*?) colou?rway", m.group(2) or "", re.I)
                for iid in m.group(1).split("/"):
                    it = by_id.get(iid)
                    if not it:
                        continue
                    cw = 0
                    if cwm:
                        want = cwm.group(1).strip().lower()
                        cw = next((j for j, c in enumerate(it["colorways"]) if c["name"].lower() == want), 0)
                    refs.append((it, cw))
            else:
                hit = next(((it, j) for nm, it, j in names if nm and nm in seg.lower()), None)
                if hit:
                    refs.append(hit)
            for it, cw in refs:
                ref = {"id": str(it["id"]), "cw": cw}
                slot = it["slot"]
                if slot == "acc":
                    o["acc"].append(ref)
                elif slot == "top" and o["top"]:
                    o["under"] = ref; o["open"] = True
                elif not o[slot]:
                    o[slot] = ref
                    if slot == "top" and re.search(r"\btucked\b", seg, re.I):
                        o["tuck"] = True
                pieces.append(it["colorways"][cw]["label"].split(" (")[0])
        if not (o["top"] or o["bottom"]):
            continue
        est = "coach est" in get("grade").lower()
        out.append({"id": f"hist-{n}", "n": n, "name": f"#{n} " + " + ".join(pieces[:2]), "outfit": o,
                    "grade": round(sum(nums) / len(nums), 2), "gradeText": "-".join(f"{x:.1f}" for x in nums),
                    "est": est, "date": get("date") or added.get(n, ""), "source": "history", "partial": partial})
    return out

# ---------- outfit history as CSV (the page, the coach and he all read and write the same rows) ----------
HIST_COLS = ["n", "date", "layer", "top", "under", "bottom", "shoes", "belt", "acc", "tuck", "open",
             "grade", "coach_grade", "occasion", "details", "note", "sid", "name"]
REMIX_COLS = ["n", "date", "layer", "top", "under", "bottom", "shoes", "belt", "acc", "tuck", "open", "name", "sid", "details", "note", "grade"]
SLOTS = ["layer", "top", "under", "bottom", "shoes", "belt"]


def is_csv(path):
    return bool(path) and str(path).endswith(".csv")


def read_rows(path):
    try:
        with open(path, newline="") as f:
            return list(csv.DictReader(f))
    except (OSError, TypeError):
        return []


def write_rows(path, cols, rows):
    tmp = str(path) + ".tmp"  # write then swap, so a reader never sees a half-written CSV
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    os.replace(tmp, path)


def cell_ref(cell, by_id, warn=None, ctx=""):
    """'102:dark gray' -> {"id": "102", "cw": 1}; '?name' or unknown ids -> None (and a note)."""
    cell = (cell or "").strip()
    if not cell or cell.startswith("?"):
        if cell and warn:
            warn(f"{ctx}: '{cell[1:]}' is not in the closet, so it is not drawn")
        return None
    iid, _, cwname = cell.partition(":")
    it = by_id.get(iid.strip())
    if not it:
        if warn:
            warn(f"{ctx}: id {iid} is not in the closet")
        return None
    cw = 0
    if cwname.strip():
        want = cwname.strip().lower()
        cw = next((j for j, c in enumerate(it["colorways"]) if c["name"].lower() == want), 0)
    return {"id": str(it["id"]), "cw": cw}


def row_outfit(r, by_id, warn=None, ctx=""):
    o = {k: cell_ref(r.get(k), by_id, warn, ctx) for k in SLOTS}
    o["acc"] = [x for x in (cell_ref(c, by_id, warn, ctx) for c in (r.get("acc") or "").split(";")) if x]
    if str(r.get("tuck", "")).lower() in ("true", "false"):  # blank = the page's default (tucked when a belt is worn)
        o["tuck"] = str(r["tuck"]).lower() == "true"
    if str(r.get("open", "")).lower() == "true":
        o["open"] = True
    return o


def outfit_name(o, by_id, n):
    names = []
    for k in ("layer", "top", "under", "bottom", "shoes"):
        ref = o.get(k)
        it = by_id.get(ref["id"]) if ref else None
        if it:
            names.append(it["colorways"][ref["cw"]]["label"].split(" (")[0])
    return f"#{n} " + " + ".join(names[:2])


def history_from_csv(items, warn=None):
    by_id = {str(i["id"]): i for i in items if not i.get("ghost")}
    out = []
    for r in read_rows(PATHS.get("history")):
        n = r["n"].strip()
        nums = [float(x) for x in re.findall(r"\d\.\d", r.get("grade", ""))]
        est = False
        if not nums:  # no grade of his yet: show the coach's estimate
            nums = [float(x) for x in re.findall(r"\d\.\d", r.get("coach_grade", ""))]
            est = True
        if not nums:
            continue
        o = row_outfit(r, by_id, warn, f"history #{n}")
        if not (o["top"] or o["bottom"]):
            continue
        text = "-".join(f"{x:.1f}" for x in nums)
        out.append({"id": f"hist-{n}", "n": n, "name": (r.get("name") or "").strip() or outfit_name(o, by_id, n), "outfit": o,
                    "grade": round(sum(nums) / len(nums), 2), "gradeText": text, "est": est,
                    "date": r.get("date", ""), "source": "history", "sid": r.get("sid", ""), "note": r.get("note", "")})
    return out


def remixes_from_csv(items, warn=None):
    by_id = {str(i["id"]): i for i in items if not i.get("ghost")}
    out = []
    for r in read_rows(PATHS.get("remixes")):
        o = row_outfit(r, by_id, warn, f"remix {r.get('name') or r.get('n')}")
        g = re.findall(r"\d\.\d", r.get("grade", ""))
        if o["top"] or o["bottom"]:
            out.append({"id": f"remix-{r.get('sid') or r['n']}", "name": r.get("name") or f"Remix {r['n']}", "outfit": o,
                        "date": r.get("date", ""), "source": "remix", "sid": r.get("sid", ""), "n": r.get("n", ""), "note": r.get("note", ""),
                        "grade": float(g[0]) if g else None, "gradeText": g[0] if g else ""})
    return out


def load_history(items, warn=None):
    return history_from_csv(items, warn) if is_csv(PATHS.get("history")) else parse_history(items)


def ref_cell(ref, by_id):
    if not ref:
        return ""
    it = by_id.get(str(ref["id"]))
    cw = ref.get("cw", 0) or 0
    return f"{ref['id']}:{it['colorways'][cw]['name']}" if it and cw and cw < len(it["colorways"]) else str(ref["id"])


def outfit_cells(o, by_id):
    return {"tuck": "" if o.get("tuck") is None else str(bool(o["tuck"])).lower(), "open": "true" if o.get("open") else "",
            "acc": ";".join(ref_cell(a, by_id) for a in o.get("acc") or []), **{k: ref_cell(o.get(k), by_id) for k in SLOTS}}


def find_row(rows, kind, e):
    """The CSV row an edit or delete targets: history by its number n, remixes by sid (else n)."""
    if kind == "history":
        return next((r for r in rows if str(r.get("n", "")).strip() == str(e.get("n", "")).strip()), None)
    sid = e.get("sid") or ""
    return next((r for r in rows if (r.get("sid") == sid if sid else str(r.get("n", "")).strip() == str(e.get("n", "")).strip())), None)


def update_entry(items, e):
    """Edit a saved row in place: pieces for both kinds, plus his grade and note (history) or the name (remix)."""
    kind = e.get("kind")
    path, cols = (PATHS.get("history"), HIST_COLS) if kind == "history" else (PATHS.get("remixes"), REMIX_COLS)
    if kind not in ("history", "remix") or not is_csv(path):
        return 0
    rows = read_rows(path)
    row = find_row(rows, kind, e)
    o = e.get("outfit") or {}
    if row is None or not (o.get("top") or o.get("bottom")):
        return 0
    by_id = {str(i["id"]): i for i in items if not i.get("ghost")}
    row.update(outfit_cells(o, by_id))
    if e.get("grade") not in (None, ""):
        row["grade"] = f"{max(1.0, min(5.0, float(e['grade']))):.1f}"
    if "note" in e:
        row["note"] = e["note"]
    if "name" in e and (kind == "history" or e["name"]):
        row["name"] = e["name"]  # history: blank goes back to the generated "#n pieces" name
    write_rows(path, cols, rows)
    return 1


def import_entries(items, entries):
    """File entries from the page: worn outfits -> history CSV, saved remixes -> remixes CSV (deduped by sid)."""
    hist, remx = PATHS.get("history"), PATHS.get("remixes")
    if not is_csv(hist):
        return 0
    by_id = {str(i["id"]): i for i in items if not i.get("ghost")}
    hrows, rrows = read_rows(hist), (read_rows(remx) if remx else [])
    seen = {r.get("sid") for r in hrows + rrows if r.get("sid")}
    added = 0
    for e in entries if isinstance(entries, list) else []:
        sid, o = e.get("id"), e.get("outfit") or {}
        if not sid or sid in seen or not (o.get("top") or o.get("bottom")):
            continue
        seen.add(sid)
        row = {"date": e.get("date", ""), "sid": sid, **outfit_cells(o, by_id)}
        if e.get("worn"):
            row.update(n=str(max([int(r["n"]) for r in hrows if str(r["n"]).isdigit()] + [0]) + 1),
                       grade=str(e.get("grade", "")), occasion=e.get("boardTitle", ""), note=e.get("note", ""))
            hrows.append(row)
        elif remx:
            row.update(n=str(max([int(r["n"]) for r in rrows if str(r["n"]).isdigit()] + [0]) + 1), name=e.get("name", ""))
            rrows.append(row)
        else:
            continue
        added += 1
    if added:
        write_rows(hist, HIST_COLS, hrows)
        if remx:
            write_rows(remx, REMIX_COLS, rrows)
    return added


def delete_entry(e):
    """Remove a saved row: a remix, or a history row (kind "history", by n). Old callers send just {sid}."""
    kind = e.get("kind") or "remix"
    path = PATHS.get("history") if kind == "history" else PATHS.get("remixes")
    cols = HIST_COLS if kind == "history" else REMIX_COLS
    rows = read_rows(path) if is_csv(path) else []
    row = find_row(rows, kind, e) if e.get("sid") or e.get("n") else None
    if row is None:
        return 0
    write_rows(path, cols, [r for r in rows if r is not row])
    return 1


# ---------- local server: the page saves straight into the CSVs ----------
import threading, time, subprocess, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT, IDLE_HOURS = 8765, 4


def ping(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=1) as r:
            return json.loads(r.read()).get("app") == "outfit-board"
    except Exception:
        return False


def serve(port):
    closet, board_dir, _ = resolve()
    lock, last = threading.Lock(), [time.time()]

    def lists():
        its = load_items(closet, lambda m: None); disambiguate(its)
        return {"history": history_from_csv(its), "remixes": remixes_from_csv(its)}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass

        def send(self, code, body, ctype="application/json"):
            data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
            self.send_response(code); self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data))); self.send_header("Cache-Control", "no-store")
            self.end_headers(); self.wfile.write(data)

        def do_GET(self):
            last[0] = time.time()
            if self.path.startswith("/api/ping"):
                return self.send(200, {"app": "outfit-board"})
            if self.path.startswith("/api/lists"):  # the page polls this so CSV edits (the coach's or his) show without a reload
                with lock:
                    return self.send(200, lists())
            try:
                with lock:  # a CSV or closet edited since the page was built: rebuild before serving
                    page = board_dir / PAGE
                    srcs = [closet] + [Path(PATHS[k]) for k in ("history", "remixes") if PATHS.get(k)]
                    if page.exists() and any(p.exists() and p.stat().st_mtime > page.stat().st_mtime for p in srcs):
                        build(board_dir, lambda m: None)
                
                self.send(200, (board_dir / PAGE).read_bytes(), "text/html")
            except OSError:
                self.send(404, {"error": "page not built yet"})

        def do_POST(self):
            last[0] = time.time()
            origin = self.headers.get("Origin", "")  # only this page may write (blocks other sites posting to localhost)
            if origin not in (f"http://127.0.0.1:{port}", f"http://localhost:{port}") or "json" not in self.headers.get("Content-Type", ""):
                return self.send(403, {"error": "forbidden"})
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"[]")
                with lock:
                    its = load_items(closet, lambda m: None); disambiguate(its)
                    changed = {"/api/log": lambda: import_entries(its, body), "/api/update": lambda: update_entry(its, body),
                               "/api/delete": lambda: delete_entry(body or {})}.get(self.path, lambda: 0)()
                    if changed:
                        build(board_dir, lambda m: None)
                    self.send(200, {"changed": changed, **lists()})
            except Exception as e:
                self.send(500, {"error": str(e)})

    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    def idle():
        while True:
            time.sleep(300)
            if time.time() - last[0] > IDLE_HOURS * 3600:
                srv.shutdown(); return
    threading.Thread(target=idle, daemon=True).start()
    srv.serve_forever()


def open_board(frag=""):
    """Start the local server if it is not running, then open the board (BROWSER app on macOS, else the default browser)."""
    port = next((p for p in range(PORT, PORT + 10) if ping(p)), None)
    if port is None:
        port = next(p for p in range(PORT, PORT + 10) if not ping(p))
        subprocess.Popen([sys.executable, __file__, "--serve", str(port)], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=os.getcwd())
        for _ in range(30):
            if ping(port):
                break
            time.sleep(0.2)
    url = f"http://127.0.0.1:{port}/{frag}"
    browser = PATHS.get("browser")
    try:
        if browser and sys.platform == "darwin":
            subprocess.run(["open", "-a", browser, url], check=True)
        else:
            import webbrowser; webbrowser.open(url)
    except Exception:
        pass
    return url


def history_text(items):
    """The history as prose lines for the coach prompt (ids resolved to names), generated from the CSV."""
    by_id = {str(i["id"]): i for i in items if not i.get("ghost")}
    def nm(ref):
        it = by_id.get(str(ref["id"])) if ref else None
        return f"{it['colorways'][ref['cw']]['label'].split(' (')[0]} ({it['id']}{', ' + it['colorways'][ref['cw']]['name'] + ' colorway' if ref['cw'] else ''})" if it else None
    lines = ["| # | Date | Outfit | His grade | Coach est. | Notes |", "|---|---|---|---|---|---|"]
    for r in read_rows(PATHS.get("history")):
        o = row_outfit(r, by_id)
        parts = []
        for k in ("layer", "top", "under", "bottom", "shoes", "belt"):
            t = nm(o.get(k))
            if t:
                tag = " tucked" if (k == "top" and o.get("tuck")) else " untucked" if (k == "top" and o.get("tuck") is False) else (", worn open" if (k == "top" and o.get("open")) else "")
                parts.append(t + tag)
        parts += [t for t in (nm(a) for a in o["acc"]) if t]
        notes = "; ".join(x for x in (r.get("occasion"), r.get("details"), r.get("note")) if x)
        lines.append(f"| {r['n']} | {r.get('date', '')} | {' + '.join(parts)} | {r.get('grade') or ''} | {r.get('coach_grade') or ''} | {notes} |")
    return "\n".join(lines)

PAGE = "outfit-board.html"


def ghost_item(ghost, bid, warn):
    gd = (ghost.get("desc") or ghost.get("label") or "").lower()
    gt = ghost.get("type", "tshirt")
    ghost.setdefault("shape", infer_shape(gt, gd, ghost.get("volume", "regular")) or "tee")
    ghost.setdefault("texture", infer_texture(gt, gd))
    if not ghost.get("hex"):
        cname = ghost.get("color", "").lower()
        hx, pick, _ = (COLOR_HEX[cname], cname, []) if cname in COLOR_HEX else guess_hex(cname)
        if not pick:
            soft_warn(f"ghost {bid}: unknown colour '{cname or '(blank)'}', drawn as {hx}")
        ghost["hex"] = [hx]
    ghost.setdefault("label", label_for(ghost["shape"], ghost.get("desc", ""), ghost.get("color", ""), ghost["texture"]))
    if ghost["shape"] not in NOUN:
        warn(f"ghost: unknown shape '{ghost['shape']}'")
    return {"id": f"ghost:{bid}", "board": bid, "type": gt, "ghost": True,
            "slot": ghost.get("slot") or SLOT_BY_TYPE.get(gt, "top"),
            "shape": ghost["shape"], "texture": ghost.get("texture"),
            "colorways": [{"name": ghost.get("color", ""), "hex": ghost["hex"], "label": ghost["label"]}],
            "seasons": ghost.get("seasons", {"spring": True, "summer": True, "fall": True, "winter": True}),
            "desc": ghost.get("desc", ghost.get("label", "")), "formality": ghost.get("formality", 3),
            "register": ghost.get("register", "neutral"), "volume": ghost.get("volume", "regular"),
            "loud": ghost.get("loud", "no"), "flag": ghost.get("flag", ""), "favorite": "no"}


def page_history(page):
    """Boards stored inside the page itself (newest first); the page is the only file."""
    try:
        m = re.search(r"const DATA = (.*?);\n", page.read_text())
        return json.loads(m.group(1)).get("boards", []) if m else []
    except (OSError, ValueError):
        return []


def build(board_dir, warn, new_board=None):
    """Rewrite the one page: its stored history (+ an optional new board on top), capped at HISTORY_MAX."""
    closet, _, fig = resolve()
    items = load_items(closet, warn)
    disambiguate(items)
    ids = {i["id"] for i in items}
    page = board_dir / PAGE
    boards = page_history(page)
    for legacy in sorted(board_dir.glob("*.json")):  # boards saved as files by older versions: fold them in once
        b = json.loads(legacy.read_text())
        b.setdefault("id", legacy.stem)
        if all(x.get("id") != b["id"] for x in boards):
            boards.append(b)
        legacy.unlink()
    if new_board:
        boards = [b for b in boards if b.get("id") != new_board["id"]]
        boards.insert(0, new_board)
    boards.sort(key=lambda b: b.get("date", ""), reverse=True)
    if new_board:  # the new board leads even if another shares its date
        boards.remove(new_board); boards.insert(0, new_board)
    boards = boards[:HISTORY_MAX]
    for b in boards:
        bid = b["id"]
        if b.get("ghost"):
            items.append(ghost_item(b["ghost"], bid, warn))
            ids.add(f"ghost:{bid}")
        for opt in b.get("options", []):
            for slot, v in opt.get("slots", {}).items():
                for ref in (v if isinstance(v, list) else [v]):
                    if ref and ref.get("id") == "ghost":
                        ref["id"] = f"ghost:{bid}"
                    if ref and ref.get("id") not in ids:
                        (warn if b is new_board else info)(f"board {bid}, option {opt.get('label')}: {slot} id {ref.get('id')} not in the catalog")
    data = {"items": items, "boards": boards, "history": load_history(items, info), "remixes": remixes_from_csv(items, info), "built": date.today().isoformat(), "figure": fig}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text().replace("/*__DATA__*/", "const DATA = " + payload + ";")
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(html)
    return page


def main():
    warnings = []
    warn = warnings.append
    args = [a for a in sys.argv[1:] if a not in ("-v", "--open")]
    want_open = "--open" in sys.argv
    if not args or args[0] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    closet, board_dir, _ = resolve()
    if args[0] == "--where":
        print(f"closet: {closet}{'' if closet.is_file() else ' (MISSING)'}\npage: {board_dir / PAGE}"); sys.exit(0)
    if not closet.is_file():
        print(f"ERROR: closet not found at {closet}"); sys.exit(2)
    if args[0] == "--history-text":
        its = load_items(closet, warn); disambiguate(its)
        print(history_text(its)); sys.exit(0)
    if args[0] == "--serve":
        serve(int(args[1]) if len(args) > 1 else PORT); sys.exit(0)
    new_board, suffix = None, ""
    if args[0] in ("--closet", "--rebuild"):
        suffix = "#closet" if args[0] == "--closet" else ""
    else:
        if args[0] == "--slug":
            slug = re.sub(r"[^a-z0-9]+", "-", (args[1] if len(args) > 1 else "board").lower()).strip("-")
            new_board = json.loads(sys.stdin.read())
        else:
            src = Path(args[0])
            slug, new_board = src.stem, json.loads(src.read_text())
        new_board["id"] = f"{new_board.get('date') or date.today().isoformat()}_{slug}"
    out = build(board_dir, warn, new_board)
    if INFO and "-v" in sys.argv:
        for m in INFO: print("INFO:", m)
    elif INFO:
        print(f"INFO: {len(INFO)} note(s): guessed colours or old boards citing removed pieces (fine; -v lists them)")
    for w in NOTES + warnings:
        print("WARNING:", w)
    if want_open:
        print(open_board(suffix))
    else:
        print(f"file://{out}{suffix}" if suffix else out)
    sys.exit(1 if warnings else 0)

if __name__ == "__main__":
    main()

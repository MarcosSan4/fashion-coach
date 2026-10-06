# fashion-coach

A personal stylist for men, as a Claude Code skill. It dresses you from the clothes you actually own, learns your taste from the grades you give its outfits, and explains the why behind every call so you get better at it yourself. Your style profile (colour season, frame, aesthetic, hard no's), your full closet and your graded outfit history are injected into the prompt on every run, so answers are about your wardrobe, not generic menswear advice.

## What it does

| Mode | What happens | Try |
|---|---|---|
| **Build outfits** | Four stylist sub-agents run in parallel and draft about 12 candidates across different lanes (register x value story, plus a wildcard). The coach anonymizes and shuffles them, re-checks every one against the hard rules, grades them blind on a /5 rubric and shows the best 4, each with a "what caps it" line, a verdict and a short teaching block. | `/fashion-coach what should I wear to a dinner on Friday` |
| **Buy or skip** | Runs a candidate purchase through six gates: fills a documented gap, duplicate check, combinability (must unlock ~3 outfits with what you own), palette and fit, the rare statement-piece exception, invest-vs-save and queue position. Verdict is BUY, SKIP or BUY-IF. | `/fashion-coach should I buy a soft navy unstructured blazer for 220 EUR` |
| **Grade my outfit** | Grades an outfit you put together on the full scale, names what carries it and the weakest element, proposes the minimal swap from your own closet and re-grades it. | `/fashion-coach grade this: Fair Isle sweater, straight jeans, suede chukkas` |
| **Onboarding** | About 10 minutes: daylight selfies and a full-body photo plus short numbered question blocks (colouring, build, aesthetic and dislikes, your week and city). Writes a rules-based profile, then hands over to closet intake and a "rate these 5" calibration round. | `/fashion-coach set me up` |
| **Closet intake** | Turns garment photos (or a typed list) into catalog rows, merges colourways, asks all fit questions in one batch, and closes any shopping gaps the new pieces fill. | `/fashion-coach add these` (with photos dragged in) |
| **Closet audit** | `scripts/audit.py` counts six lenses (formality x register coverage, orphans, over-relied pieces, unworn items, recurring gaps from the stylists' gap log, stale gaps already closed); the coach interprets them, asks one batched question and rewrites your gap list and priority queue. | `/fashion-coach audit my closet` |

## What it doesn't do

- **It can't see fit in person.** Fit calls are only as good as your answers about how things fit you.
- **Colour analysis is a stylist heuristic,** not validated science. The coach says so once when it matters and marks low-confidence palettes as provisional.
- **It never checks out or buys.** You complete every purchase. Live product search only if you have a web tool set up.
- **No hair, beard or skin.** Those are out of scope (your profile can route them to another coach).
- **Outfits use owned items only.** A missing piece becomes a gap note, never a pretend garment.

## Privacy

Your profile, closet and history live in plain local files on your disk. The Outfit Board server binds to `127.0.0.1` only and accepts writes only from its own page. Photos and closet data are still sent to the model like any other prompt content.

## Quick start

**1. Install.** Clone or copy this repo to one of:

```bash
git clone https://github.com/MarcosSan4/fashion-coach.git ~/.claude/skills/fashion-coach              # all your projects
git clone https://github.com/MarcosSan4/fashion-coach.git <project>/.claude/skills/fashion-coach      # one project
```

**2. Try the demo** (Alex, a fictional Soft Autumn client with a 26-item closet, 6 graded outfits and a parked issue). The coach writes to its files, so work on a copy:

```bash
cp -R ~/.claude/skills/fashion-coach/examples/demo ~/alex-demo
cd ~/alex-demo && claude
```

Then ask `/fashion-coach what should I wear to a dinner on Friday`. More prompts in [`examples/demo/README.md`](examples/demo/README.md).

**3. Set yourself up.** From a folder with no `wardrobe/` folder (and no `~/fashion-coach/` or `~/.fashion-coach` yet), run `/fashion-coach set me up`. The coach notices there is no profile and starts onboarding, writing your files to `~/fashion-coach/` unless you name another folder.

## Where your data lives

`scripts/load-context.sh` finds your files in this order, first match wins (`<project>` is `$CLAUDE_PROJECT_DIR`):

1. `<project>/.fashion-coach`: a config file with the keys below
2. `<project>/wardrobe/`: the plain folder layout (`profile.md`, `closet.csv`, `outfit-history.csv` + `lessons.md`, `shopping.md`, `gap-log.csv`, `issues/`; an older single-file `outfit-history.md` also works, but the board can only log worn outfits into the CSV)
3. `~/.fashion-coach`: a global config file, same keys (onboarding writes it if you choose a custom folder)
4. `~/fashion-coach/`: same layout as 2, the default for a global install

Config files are plain `KEY=value` lines (never executed). Paths can be absolute, `~/`, or relative to the config file's folder.

| Key | What it points to |
|---|---|
| `PROFILE` | Your style profile (markdown). Injected as binding rules on every run |
| `CLOSET` | The closet catalog CSV, one row per garment (`id,type,name,color,description,formality,register,volume,loud,flag,favorite,spring,summer,fall,winter`) |
| `HISTORY` | Your graded outfits: a markdown table, or a CSV (`.csv` extension switches mode) |
| `LESSONS` | With a CSV history: the markdown file holding lessons and anti-examples |
| `SHOPPING` | Known gaps, purchase priority queue, sourcing |
| `ISSUES_DIR` | Folder of issue files (`status:` frontmatter); open ones are injected so the coach avoids parked or flagged items |
| `GAPLOG` | The stylists' gap log CSV (default `gap-log.csv` beside the shopping file), tallied by the audit |
| `BOARD_DIR` | Where the Outfit Board page goes (default `<project>/outputs/outfits` if `<project>/outputs` exists, else `boards/` beside the closet) |
| `BROWSER` | App name the board opens in on macOS (e.g. `Firefox`) |
| `COLORS` | Optional JSON that tunes how the board draws your colours and shapes |
| `REMIXES` | Optional CSV where the board saves remixed outfits |

Blank templates for every file are in `templates/`.

## The Outfit Board

After building, judging or grading outfits, the coach renders them with `scripts/build-board.py`: one self-contained local HTML page per user (`outfit-board.html`) that draws each outfit on an SVG mannequin coloured from the `figure:` line in your profile, keeps the last 10 boards in a history menu, and includes a closet sandbox for remixing with live rule checks.

```bash
python3 scripts/build-board.py --closet          # rebuild, print the closet sandbox URL
python3 scripts/build-board.py --rebuild         # rebuild after closet or history edits
python3 scripts/build-board.py --closet --open   # also start the local server and open it
python3 scripts/build-board.py --where           # print the resolved closet and page path
```

With `--open` it starts a small server on `127.0.0.1` (port 8765 or the next free one, stops after 4 idle hours). Served this way, the page saves outfits you mark as worn straight into your history (when `HISTORY` is a CSV) and remixes into `REMIXES`, and lets you edit or delete saved rows. Opened as a plain file (e.g. on your phone), its wear button gives you a message to paste to the coach instead.

If a colour is drawn wrong, point `COLORS=` at a small JSON tuning file; `build-board.py --help` documents the format.

The board finds your files the same way the loader does (the four-step order above).

## How it learns

- **Graded history.** Every outfit you grade, wear or reject is logged with your grade, the coach's estimate and your words. Every future grade is calibrated against it.
- **Lessons.** Where your grade and the coach's differ by 0.3 or more, a one-line lesson is added. When two or more outfits sharing a trait miss in the same direction, the coach proposes a *personal method note* for your profile (with your OK).
- **Anti-examples.** Outfits you reject or grade below 4.0 anchor the bottom of your scale.
- **Calibration anchors.** Until you have 10 graded outfits and at least one anti-example of your own, a fixed set of graded reference outfits (`references/anchor-examples.md`, a fictional client) is injected to show what each band of the scale looks like. They retire automatically.
- **Durable facts.** New facts about a garment go into its closet row; new facts about you are proposed as one-line profile edits.

## Requirements

- **Claude Code** with skills support. The skill relies on `${CLAUDE_SKILL_DIR}`, dynamic context injection (`` !`command` `` in `SKILL.md`) and the Agent tool for the parallel stylists.
- **python3**, standard library only (board and audit).
- **bash** (context loader).
- `--open` uses macOS `open -a <BROWSER>` when `BROWSER` is set on a Mac; otherwise it uses Python's `webbrowser` module (your default browser). The URL is always printed, so you can open it manually on any platform.

## Repo layout

```
fashion-coach/
├── SKILL.md                    the coach: router, rules, rubric, modes
├── references/                 loaded on demand per mode
│   ├── onboarding.md           Mode O: profile interview, season and frame tables
│   ├── closet-intake.md        Mode I: photos to catalog rows, column guide
│   ├── closet-audit.md         Mode D: how to read the audit lenses
│   ├── capsule-blueprint.md    generic core wardrobe, seeds the shopping queue
│   ├── worked-examples.md      gold-standard answers for Modes A, B, C
│   └── anchor-examples.md      calibration anchors (fictional client)
├── scripts/
│   ├── load-context.sh         injects profile, closet, history into the prompt (read-only)
│   ├── build-board.py          the Outfit Board and its local server
│   └── audit.py                closet audit counts (read-only)
├── assets/outfit-board.template.html
├── templates/                  blank profile, closet, history, shopping, gap log
└── examples/demo/              Alex, a ready-made demo client
```

## License

MIT. See [LICENSE](LICENSE).

# Demo client: Alex

Try the coach in 30 seconds, without onboarding.

> **SAMPLE DATA: everything in this folder is fictional.** The closet (`closet.csv`, 26 made-up garments), the 6 graded outfits and their quotes, the shopping gaps and the parked issue all belong to "Alex", who does not exist. Nothing here is advice for you. Delete the folder (or work on a copy, as below) when you start your own wardrobe.

**Alex**, 27, 176cm, slim/rectangle frame, product designer at a small studio in Lyon. **Soft Autumn** colouring (muted, warm, low contrast): his neutrals are soft navy, warm charcoal and ivory, his earth tones olive, camel and chocolate, his heroes sage and dusty teal; no black or optic white near the face. Scandi-minimal taste with workwear texture. He lives at formality 2-4, and his closet is thin at 4-5 (no blazer, and his only dressy trouser is parked).

## What is in `wardrobe/`

| File | What it shows |
|---|---|
| `profile.md` | A filled-in client file: colouring, registers, frame rules, hard constraints, a personal flag (`weekend-only`) |
| `closet.csv` | 26 items across every type, multi-colourway rows, one parenthetical colourway (`ivory, sage (hero-colour)`), flags (`low-wear-parked`, `hero-colour`, `logo`, `off-palette-near-face`), one loud piece (the Fair Isle sweater) |
| `outfit-history.md` | 6 graded outfits with his words, two lessons, two anti-examples |
| `shopping.md` | Gaps and a priority queue seeded from the capsule blueprint |
| `issues/` | One `status: parked` issue (the pleated trousers) |
| `gap-log.csv` | Empty log of gaps the coach notices while building outfits |

This is the plain folder layout: the coach finds a `wardrobe/` folder in the project it runs from, so no config is needed.

## Run it

1. Install the skill (e.g. copy or symlink the `fashion-coach` folder into `~/.claude/skills/`).
2. The coach writes to these files (it logs outfits and updates the shopping queue), so work on a copy:
   ```bash
   cp -R examples/demo ~/alex-demo && cd ~/alex-demo && claude
   ```
3. Ask, for example, `/fashion-coach what should I wear to a dinner on Friday`.

Optional, the Outfit Board with Alex's closet and history on a mannequin (writes `wardrobe/boards/outfit-board.html`):
```bash
python3 ~/.claude/skills/fashion-coach/scripts/build-board.py --closet
```

## Prompts to try

**Build outfits (Mode A)**
- `/fashion-coach what should I wear to a dinner on Friday`
- `/fashion-coach client presentation tomorrow, about 14C and dry`
- `/fashion-coach Saturday at a friend's flat, I want to wear the chore jacket`

**Buy or skip (Mode B)**
- `/fashion-coach should I buy a soft navy unstructured blazer for 220 EUR`
- `/fashion-coach thinking about a black leather biker jacket, it was on sale`
- `/fashion-coach is a cobalt merino crew a good second hero knit`

**Grade my outfit (Mode C)**
- `/fashion-coach grade this: Fair Isle sweater, straight jeans, suede chukkas`
- `/fashion-coach knit polo in sage, soft navy chinos, penny loafers for the office, does it work`
- `/fashion-coach how bad is the logo sweatshirt with the corduroy trousers and trail runners for a Sunday walk`

To start your own profile instead, run the coach from a folder without a `wardrobe/` folder (and with no `~/fashion-coach/` or `~/.fashion-coach` set up yet) and it begins onboarding.

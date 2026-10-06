---
last_updated: 2026-10-01
figure: skin light, hair light brown, eyes hazel, texture wavy
---

# Style profile: Alex (demo client)

> Injected into the fashion coach as binding instruction on every run. Write rules, not adjectives. Edit it any time; the coach proposes edits when it learns something durable.
>
> **SAMPLE DATA:** Alex is a fictional client shipped with the skill so you can try it without onboarding. His profile, closet (`closet.csv`), outfit history, shopping file and issue are all made up. Delete this `wardrobe/` folder (or run the coach from another folder) to start your own profile.

## Snapshot
Alex, 27, 176cm, slim/rectangle frame. Lyon, France (hot summers, grey cold winters, wet shoulder seasons). Product designer at a small design studio. Mid budget: buys fewer, better pieces, about 1,200 EUR a year; happy to invest in shoes and outerwear, saves on basics.

## Colouring
**Soft Autumn** (confidence: medium). Light brown hair with a warm cast, hazel eyes, light warm-neutral skin that burns then tans. Defining trait: muted, warm-leaning, everything within a similar depth. **Contrast level: low** (tonal and light-on-light are his default value stories; value sandwich only in a softened form with warm charcoal or chocolate, never black; high-contrast block is ruled out).

### Registers
- **Neutral register:** soft navy, warm charcoal, warm gray, ivory, ecru, washed indigo denim.
- **Earth register:** olive, khaki, camel, tan, warm taupe, chocolate brown, sand, stone.

Keep an outfit mostly inside one register; crossing them needs a named bridge piece. His natural bridges are ivory, ecru, washed denim and tan leather.

### Hero colours
Sage, dusty teal, dusty rose, terracotta. Muted, so they are `loud=no` but still flagged `hero-colour`. One hero near the face per outfit; he likes them and wants one in most workday outfits (his words: "a bit of colour near my face or I look like I haven't slept").

### Avoid near the face
Black, optic white, bright saturated colour (cobalt, true red, kelly green), icy pastels. The test is **temperature plus clarity, not colour family**: a dusty sage knit lights him up, a clear emerald one wears him; a warm ivory tee works, an optic-white one turns his skin grey.

### Metals
Brushed gold and bronze by default, especially near the face. Brushed steel allowed once, away from the face (watch only).

## Body and silhouette
**Slim / rectangle**, narrow shoulders, straight torso, lean.

1. **Signature silhouette: structured top + straight bottom.** A fitted-to-regular top with structure (collar, overshirt, jacket, textured knit) over a straight or relaxed leg. Builds the shoulder line his frame lacks and keeps the leg from looking like a stick.
2. Add structure and texture up top: overshirts, collars, corduroy, waxed cotton, lambswool. A plain tee alone reads underdressed on his frame; layer it when the weather allows.
3. Straight or relaxed legs only, mid rise, no break or a slight break.
4. Avoid oversized everything (swamped) and skinny everything (stick).

**Gate check against `volume`:** no `oversized` top with an `oversized` bottom, and no `fitted` bottom at all (see hard constraints).

## Aesthetic
**Scandi minimal with workwear texture.** Default grammar: clean geometry, few colours, quality basics, solids. The flex comes from texture (waxed cotton, corduroy, suede, lambswool) and one muted hero near the face, never from logos or pattern. Reference points: Arket, Our Legacy, Norse Projects, Drake's knitwear. It collapses when too many colours or textures compete, or when the workwear turns into costume (head-to-toe heritage).

## Formality life
He lives at **2-4**: studio days ~3 (Mon to Thu), Fridays ~2-3, client presentations ~4 (about twice a month), dinners and dates ~3, weddings ~5 (once or twice a year). Thin levels: **4 and 5** (one formality-4 trouser and it is parked; no blazer).

## Climate bands (Lyon)
- **Summer, Jun to Aug (24 to 34C):** linen, open knits, short-sleeve shirts; no layer by day; tonal light earth by default.
- **Shoulder, Apr to May and Sep to Oct (10 to 22C):** layering season: overshirts, chore jacket, lambswool, suede. Expect rain: no suede on wet days.
- **Winter, Nov to Mar (-2 to 10C):** wool overcoat over knit layers, corduroy, boots. Grey light: lean on the warm earth register so he does not look washed out.

## Personal hard constraints
Violating any one caps the outfit at reject, same as the engine's universal constraints.

- **No skinny or slim-tapered bottoms, and no `fitted` bottom** (his words: "skinny jeans make me look like a pencil").
- **No black above the waist.** Black is allowed only on shoes or a belt (his words: "black makes me look ill").
- **No shorts at the studio or with clients**, whatever the temperature.
- **Nothing flagged `weekend-only` on a workday or at a client meeting.**
- **No visible logos at work.**

## Personal flags
- `weekend-only`: fine for errands and hikes, never at the studio, with clients or on a date.

## Personal method notes
Filled in from his graded history over time: patterns in how he grades, what he rates above or below the rules.

- (none yet: two lessons logged in the outfit history, no pattern confirmed)

## Catalog notes
- The knit polo row is `"ivory, sage (hero-colour)"`: pick the sage and it counts as his hero for that outfit.
- The black merino turtleneck is `off-palette-near-face`: kept for a costume party, never proposed near the face.

## Routing and output preferences
- Hair, beard and skin: outside this coach.
- Live shopping searches: WebSearch/WebFetch.
- Keep answers short on weekdays: the outfit first, the teaching in two lines.

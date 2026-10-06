# Mode O: onboarding

Goal: in about 10 minutes of his time, learn who you are dressing well enough to write a profile that is as binding and specific as a stylist's client file. Then get his closet in (Mode I) and calibrate on his own taste (the finale below). **Every rule you write into his profile becomes enforced instruction on every future run, so write rules, not vibes.**

## Ground rules

- **Conversational, one block at a time.** Never dump all the questions at once. Each block is one message from you, short, with the questions numbered so he can answer in a line each (voice-dictated answers are fine).
- **Derive what you can.** Climate from his city, season from today's date, formality needs from his week. Don't ask what you can work out.
- **Photos beat descriptions for build; answers beat photos for colour.** Phone cameras, white balance and indoor light distort skin tone badly. Use the photo for value contrast and hair/eye colour, and let his answers decide undertone and chroma.
- **Be honest about colour analysis.** Seasonal colour systems are a useful stylist heuristic, not validated science. The parts with real consensus are: match your outfit's contrast to your natural contrast, keep the colour nearest your face in harmony with your undertone, and match clarity (clear vs muted) to your colouring. Say this once, in one line, and move on. Give a confidence level, and mark the season `provisional` when the signals disagree.
- **Where files go:** the STATUS block names the folder (default `~/fashion-coach/`). Create it if needed. Templates are in `${CLAUDE_SKILL_DIR}/templates/`: copy `profile.md`, `closet.csv`, `shopping.md`, `gap-log.csv`, `outfit-history.csv` and `lessons.md` (the CSV history is the default: the Outfit Board can then log worn outfits into it by itself; `outfit-history.md` is the older single-file format), then fill in. **If he wants a different folder**, also write `~/.fashion-coach` (absolute `PROFILE=`, `CLOSET=`, `HISTORY=`, `SHOPPING=` lines; optional `HISTORY=...csv` with `LESSONS=` for the CSV history, see the template; optional `GAPLOG=` for the stylists' gap log, default `gap-log.csv` beside the shopping file), otherwise the next run won't find his files.

## Block 1: welcome + photos

One short paragraph on what is about to happen: profile (about 5 min), closet (photos, as much as he wants, 15 items minimum to start), then rating 5 outfits so you learn his taste. Then ask for:
1. **Two selfies in daylight**, facing a window, no filter, no flash, plain background if possible. One with a plain white tee or white paper held under the chin helps.
2. **One full-body photo** in fitted clothes (a fitted tee and his usual trousers), standing straight, camera at chest height.
3. In Claude Code he can drag the image files into the terminal, or paste their paths.

If he would rather skip photos, continue on answers alone: colour confidence then caps at `medium` (see Block 2).

## Block 2: colouring

Ask (numbered, one line each):
1. Natural hair colour (and beard, if different)? Eye colour? Skin: very fair, fair, medium, olive, or deep?
2. In strong sun, does he burn, burn then tan, or tan easily?
3. Wrist veins in daylight: mostly blue/purple, mostly green, or hard to tell?
4. Which looks better next to his face: optic white or cream/ivory? Silver or gold?
5. Which colours get him compliments when he wears them? Which make people ask if he's tired?
6. Does a bright saturated colour (cobalt, emerald, true red) look like *him*, or like it is wearing him?

**Read three axes, then the season.**

- **Value contrast** (from the photo + Q1): the gap in depth between hair, skin and eyes. Dark hair with very fair or fair skin is high; hair, skin and eyes all within a similar depth (blond on fair, dark on deep) is low; one step apart is medium. Without a photo, read it from Q1 alone. This decides which value stories he can use: high contrast opens value sandwich and high-contrast block; low contrast defaults to tonal.
- **Undertone** (up to four votes, majority wins): Q2 burns = cool, tans easily = warm, burns then tans = no vote; Q3 blue/purple = cool, green = warm, hard to tell = no vote; Q4 counts as two votes (optic white = cool, cream = warm; silver = cool, gold = warm). A tie or no majority = neutral-leaning: let Q5's compliment colours pick the side.
- **Chroma / clarity** (Q5-Q6 + photo): if saturated colour looks like him, he is clear/bright; if it wears him and soft dusty colours get compliments, he is muted/soft.

**Map to a season family** with the table below. Undertone picks the family pair; contrast and chroma pick the subtype. Write confidence as `high` (photos plus all three axes clear), `medium` (one axis ambiguous, or no photos with all axes clear) or `low / provisional` (two or more axes ambiguous). Without photos the ceiling is `medium`.

| Season | Defining trait | Neutral register | Earth register | Heroes (near the face) | Avoid near the face | Metals |
|---|---|---|---|---|---|---|
| Bright Winter | high contrast, clear, cool-neutral | navy, black, charcoal, optic white | cool taupe, espresso, cool olive (committed) | cobalt, emerald, true red, icy blue | dusty, muted, warm camel/mustard | silver |
| True Winter | high contrast, cool | black, navy, charcoal, pure white, cool gray | very limited: espresso, cool taupe as near-neutrals | royal blue, emerald, burgundy, icy pink | warm earth, orange, cream | silver, platinum |
| Deep Winter | dark, high contrast, cool-neutral | black, charcoal, navy, white | espresso, dark chocolate, deep olive | burgundy, emerald, sapphire, deep teal | pastels, warm light earth | silver, gunmetal |
| Light Summer | light, low contrast, cool | soft navy, light gray, soft white | stone, light cool taupe | powder blue, soft aqua, lavender, rose | black, heavy dark colour, orange | silver |
| True Summer | cool, soft, medium-low contrast | navy, slate, soft charcoal, cool gray, soft white | stone, oatmeal, cool taupe, mushroom | soft teal, raspberry, periwinkle | black at the face, orange, mustard | silver, pewter |
| Soft Summer | muted, cool-neutral, low contrast | charcoal, slate, gray-navy, soft white | mushroom, taupe, gray-olive | dusty teal, muted plum, soft blue | bright saturated colour, black, orange | pewter, brushed silver |
| Light Spring | light, warm, clear-ish | light navy, warm light gray, ivory | camel-light, sand, light khaki | light aqua, coral, warm light blue | black, heavy dark colour, dusty colour | light gold |
| True Spring | warm, clear | warm navy, ivory, warm gray | camel, khaki, golden tan | warm turquoise, coral, kelly green | black at the face, icy colours, dusty colour | gold |
| Bright Spring | clear, warm-neutral, high contrast | navy, ivory, charcoal | camel, warm taupe | turquoise, bright coral, true green | dusty, muted, very dark colour | gold, polished brass |
| Soft Autumn | muted, warm-neutral, low contrast | warm charcoal, warm gray, ivory, soft navy | camel, olive, khaki, warm taupe | soft teal, sage, terracotta, dusty rose | black, optic white, bright saturated colour | brushed gold, bronze |
| True Autumn | warm, rich | olive, warm brown, warm navy, cream | camel, rust, khaki, chocolate | burnt orange, mustard, deep teal, forest green | icy pastels, black at the face, optic white | gold, bronze |
| Deep Autumn | dark, warm-neutral, high-ish contrast | dark chocolate, warm charcoal, deep navy, cream | olive, espresso, camel | forest green, oxblood, deep teal, burnt orange | pastels, icy colours | gold, bronze, copper |

**The temperature-plus-clarity test** (write it into his profile, phrased for his season): what drains someone is the wrong *temperature* or *clarity* near the face, not a colour family. A cool committed taupe works on a Winter; a warm dusty caramel does not. A warm rich camel works on an Autumn; an icy pastel does not.

**Black and optic white:** the strongest single tell. Winters wear both at the face; Summers soften black to charcoal or navy; Springs and Autumns use cream and ivory instead of optic white, and keep black away from the face.

## Block 3: build

Ask:
1. Height, and roughly weight (optional)?
2. Which is widest: shoulders/chest, midsection, or about even? (The full-body photo usually answers this; confirm.)
3. What never fits him off the rack (shirts tight in the chest, trousers gape at the waist, sleeves short, everything too long)?
4. How does he like things to fit: closer to the body, regular, or relaxed?

**Pick the frame** (combine when two apply: short + athletic, tall + slim; between ~172 and ~188cm height adds no rules). Body shape outranks height when their rules conflict. Write the frame's rules into the profile as numbered rules, plus a **gate check against `volume`** (the explicit forbidden combination) so the pre-output gate can test it mechanically.

Tailored jackets and suits are judged by their description ("fits well through the chest"), not by `volume`: every gate below applies to knits, tees, shirts and casual layers.

| Frame | Read | Signature silhouette | Rules | Gate check (forbidden) | Grade |
|---|---|---|---|---|---|
| **Athletic V** | broad chest and shoulders, narrower waist | fitted top + relaxed bottom | buy to the chest, taper the rest; mid-high rise; tees fitted through the torso, sleeve at mid-bicep; avoid slim cuts (stuffed) and boxy oversize (bulky) | `oversized` top with `fitted` bottom | A |
| **Slim / rectangle** | narrow shoulders, straight torso, lean | fitted-to-regular top with some structure + straight or relaxed bottom | add shoulder structure (overshirts, unstructured blazers, collars), heavier and textured fabrics, layering; straight or relaxed legs; avoid skinny everything (stick) and oversized everything (swamped) | `oversized` top with `oversized` bottom | A/B |
| **Broad / stocky** | wide shoulders and solid torso, little taper, often shorter | regular top + straight bottom with room | vertical lines, darker tonal columns, open layers; mid-heavy fabrics that hang rather than cling; avoid bulky chunky knits, big patterns and cropped boxy tops | `fitted` top with `fitted` bottom (clinging) | B |
| **Heavier midsection** | widest at the waist | regular top that skims + straight bottom, tonal through the middle | structure that skims, never clings; open layers (unbuttoned overshirt or jacket) to create a vertical line; dark or tonal through the midsection; mid-to-high rise at the natural waist; untucked or a structured tuck only; avoid clingy knits, horizontal stripes across the middle, buttons that pull, skinny legs (top-heavy) and very baggy legs (adds mass) | `fitted` top (knit, tee, shirt), or a `fitted` or `oversized` bottom | A/B |
| **Short** (under ~172cm) | proportion is the lever | tonal column, high rise, clean hem | monochrome or tonal columns, mid-high rise, no-break or cropped hems, shorter jackets, smaller-scale details, low contrast at the waist; avoid long coats past the knee, heavy cuffs, oversized everything | `oversized` top with `relaxed`/`oversized` bottom | B |
| **Tall and lean** (over ~188cm) | length to break up | layered, contrast at the waist allowed | layers, texture, contrast breaks at the waist, wider legs and cuffs work; watch sleeve and hem length; avoid ultra-skinny cuts (stretched) and too-short jackets | `fitted` top with skinny bottom | B |

*(Grades: A = broad consensus across menswear authorities and tailors; B = credible frameworks, not universal.)*

**Fit preference (Q4) is taste, not law:** let it shift volume within the frame's rules (a V-frame who likes relaxed fits still wants the top closer than the bottom).

## Block 4: aesthetic + hard dislikes

Ask:
1. Which one or two feel most like him? Offer the menu below in one compact list.
2. Two or three people or brands whose style he'd steal.
3. Optional: drop 2-5 photos of outfits he loves.
4. **What will he never wear, or what look does he hate?** (A specific look, a cut, a colour, a brand vibe, eyewear shapes.) Each answer becomes a **personal hard constraint**, written as a checkable rule.

| Aesthetic | Grammar | Reference points | Collapses when |
|---|---|---|---|
| Old money / quiet luxury | clean lines, restrained colour, quality fabric, no logos | Loro Piana, Ralph Lauren Purple, Massimo Dutti | logos, shine, trend pieces |
| Elevated street | street proportion with refined fabric and restraint | Aime Leon Dore, Fear of God Essentials, COS | street signals stack (oversized hoodie + baggy pants + chunky sneakers at once) |
| Workwear / Americana | rugged fabrics, denim, chore jackets, boots, patina | Carhartt WIP, Levi's Vintage, Red Wing | costume-level heritage head to toe |
| Scandi minimal | monochrome, clean geometry, few pieces, quality basics | Arket, Our Legacy, Norse Projects | too many colours or textures, fussy details |
| Smart-casual prep | oxfords, knit polos, chinos, loafers, polished | J.Crew, Drake's, Todd Snyder | crests, stacked pastels, costume preppy |
| Classic tailoring | structured jackets, trousers, leather shoes | Suitsupply, Drake's, Ring Jacket | sloppy fit; tailoring needs it to be exact |
| Techwear / gorpcore | technical fabrics, utility, performance shells | Arc'teryx, Salomon, and wander | full tactical cosplay |

Write the aesthetic as: default grammar, where any flex comes from, reference points, and what makes it collapse. Blends are fine (that's most men): name which grammar is the default and which supplies the accent.

## Block 5: life

Ask:
1. What does a normal week look like, and where does he dress up? (Office, uni, gym, dates, events, weddings.)
2. City he lives in (for climate)?
3. Rough clothing budget (per month or per year), and stores he likes or can reach?

Derive:
- **Formality life:** each recurring occasion mapped to the 1-5 scale, the range he lives in, and which level is thin (you will confirm thin levels after closet intake).
- **Climate bands:** 3-4 bands for his city with month ranges, temperature ranges and fabric rules (what works in the hottest and the coldest band).
- **Budget stance** in one line (e.g. "student, limited funds: weigh real quality-price ratio, buy-or-skip is genuinely open").

## Write the profile

Fill in `templates/profile.md` at the STATUS path. Rules:
- Every section filled; anything unknown gets `unknown (ask when it matters)`, never invented.
- **Write rules, not adjectives.** "Fitted top + relaxed bottom; no `oversized` top with `fitted` bottom", not "likes a balanced look".
- Quote his own words for every dislike and preference ("his words: ...").
- Leave *Personal method notes* nearly empty: it fills up from his graded history over time.
- Fill the `figure:` frontmatter line from Block 2 (his answers win over the photo), picking the nearest listed word for each: it colours the Outfit Board mannequin so outfits are judged against his own skin, hair and eyes.

Then show him a **6-line summary** (season + confidence, registers, heroes, frame + signature silhouette, aesthetic, hard no's) and ask: "Anything wrong?" Fix it before moving on.

## Then: closet (Mode I)

Hand over to `references/closet-intake.md`. After intake, **seed his shopping file** (it is revisited after the finale): audit the closet against `references/capsule-blueprint.md` (adapted to his palette and frame), write the known gaps and a priority queue into `templates/shopping.md` at the STATUS path, and tell him the top 3 in one line each.

## Finale: rate these 5 (calibration from day one)

The coach learns his taste, not only the rules, by watching him grade.

1. Build **5 outfits from his closet** with the shared build procedure and pre-output gate, for occasions from his real week, **deliberately spread across the scale**: about 4.7, 4.4, 4.1, 3.8 and 3.4 by your estimate. The low ones must pass the pre-output gate yet be visibly weaker, using soft flaws only: a default combo with no elevating element, flat light-on-light without texture separation, a comfort shoe that caps the outfit, regular-on-regular proportion, a belt that doesn't match the shoes. Never a hard-constraint break.
2. Show them in random order **without grades**, items by name, no ids. Ask him to rate each 1-5 (decimals fine) with one sentence of why.
3. For each, append a row to his outfit history: outfit, **his grade**, your hidden estimate, and **his words verbatim** (the `details` column in a CSV history); outfits he grades below 4.0 also get a row in the *Anti-examples* table (the markdown history, or the lessons file when the history is a CSV). Where his grade and your estimate differ by **0.3 or more**, add a one-line lesson (under the table, or in the lessons file for a CSV history) ("he rates X higher than the rules predict: he values comfort / familiarity / ...").
4. **A pattern is clear when 2 or more outfits that share a trait (tonal, a layer, a dressy shoe) all miss your estimate in the same direction by 0.3+.** Then propose the one-line *Personal method note* (e.g. "rates tonal outfits ~0.3 above the rules") and write it into his profile once he agrees, like any durable fact about him. A single outfit is a lesson line, not a method note.
5. **Revisit the shopping queue** with what you just learned (e.g. if anything tailored felt like a costume, the blazer drops down the queue) and tell him in one line if it changed.
6. Close with: what you learned about his taste in 2-3 lines, and the three things he can ask you now (what to wear, buy or skip, grade an outfit).

He now has 5 graded outfits. The calibration anchors stay loaded until he has 10 graded outfits **and** at least one row in his own *Anti-examples* table (log every outfit he rejects or grades below 4.0 there).

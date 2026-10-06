# Mode I: closet intake

Goal: turn photos (or a typed or dictated list) into correct catalog rows with the least effort from him. The catalog is what every outfit is built from, so **a wrong `volume` or `register` is a wrong outfit later.** Speed comes from batching, not from guessing.

## How he hands items over

- **Photos (best):** he drops them in an `intake/` folder next to his closet file (create it and tell him the path), or drags them into the terminal. One garment per photo, laid flat or on a hanger, daylight. A second photo of the label (brand, fabric) is a bonus, never required.
- **Text or voice:** "navy Uniqlo crew neck sweater, fits close; light blue baggy jeans; white leather sneakers". Fine for basics. Ask for a photo only when colour or fit is truly ambiguous.
- **Suggested shot order** (best outfits soonest): bottoms, then shoes, then tops, then layers, then accessories (watch, belts, sunglasses, jewellery). **Minimum viable closet: ~15 items** (e.g. 4 bottoms, 3 shoes, 6 tops, 2 layers). The coach works with a partial closet and says so in one line when a missing category limits an outfit.

## The procedure

1. **Read his profile first** (it is injected): registers, avoid-near-face list, heroes, frame. Columns like `register`, `flag` and `loud` are judged *for his colouring*, not in the abstract.
2. **Draft rows in batches** of up to ~15 items, `name` included. Look at every photo; read labels if shown.
3. **Merge colorways:** the same garment in several colours is ONE row with a comma in `color` (`white, black, navy`). A garment patterned in two colours uses a slash (`charcoal/black`). If one colorway behaves differently (louder, different register, different season), add a parenthetical: `"white, cobalt (loud + hero-colour, not favorite)"`. Before adding a row, check the existing closet for the same garment in another colour.
4. **Ask once, in a batch.** Collect everything the photos can't tell you (mostly fit/volume, sometimes colour under bad light) into ONE numbered question list: "3. Grey crewneck: fits close, regular, or loose on you?" Never ask item by item. Use any fit he already stated ("regular", "pulls at the buttons") without asking. If he can't answer now, tag the likeliest value and write "fit assumed" in the description so it gets checked later.
5. **Append the rows** to his closet CSV (copy `templates/closet.csv` first if it doesn't exist). Ids are sequential integers, never reused, never renumbered, gaps allowed. Quote any field that contains a comma.
6. **Move processed photos** to `photos/<id>.jpg` beside the closet file (keep the extension), so items can be re-checked later.
7. **Report:** items added by category, any merged colorways, anything skipped and why, and the categories still thin.

## Column guide (source of truth)

`id, type, name, color, description, formality, register, volume, loud, flag, favorite, spring, summer, fall, winter`

- **`name`**: the short name he would call it, 2-5 words describing the garment (fit, texture, sleeve length where it tells pieces apart), brand last in brackets if known ("straight jeans (Uniqlo)", "suede Chelsea boots"). When the brand IS the model, lead with the model ("Air Force 1 (Nike)"). No colour on multi-colourway rows (the colourway is shown beside it). Unique across the closet. The coach and the Outfit Board both use it, so it is how he recognises the piece.
- **`type`** (lowercase, one of): `tshirt`, `polo`, `shirt`, `sweater`, `sweatshirt`, `hoodie`, `tank`, `outerwear`, `jeans`, `pants`, `shorts`, `shoes`, `belt`, `watch`, `sunglasses`, `jewelry`, `bag`, `hat`. Overshirts, jackets, coats and blazers are `outerwear` (name which in the description). Joggers, chinos and trousers are `pants`. **A suit is two rows** (jacket as `outerwear`, trousers as `pants`, formality 5), each description naming its partner ("suit jacket, pairs with the navy suit trousers") and saying whether it works as a separate; if not, the coach uses them only together.
- **`color`**: his words when he gives them; otherwise the most specific plain name (navy, charcoal, stone, cream, espresso, olive, light blue). **Fuzzy-match colour words against the existing catalog** before treating something as a new colour: people name colours loosely.
- **`description`**: one dense line (several identical pieces in the same colour: add "(x2)"): brand if known, garment, fabric, cut and fit **on him**, details that matter for styling (collar, texture, rise, leg shape), and any caveats: wear-state, pairing rules, grade caps ("caps any outfit at ~3.5", "reads too baggy, NOT a fitted top"). This is the column the coach reads for everything no other column encodes.
- **`formality`** 1-5: 1 loungewear/gym/street, 2 casual (tees, jeans, sneakers), 3 smart-casual (knit polos, overshirts, chinos, clean leather sneakers), 4 dressed (shirts, fine knits, tailored trousers, loafers, Chelseas), 5 formal (suits, blazers, dress shoes). Darker, smoother, plainer and more structured = higher.
- **`register`**: **his profile's register lists are the authority**; these examples assume a cool season. `neutral` (his neutral register: e.g. navy, charcoal, gray, black, white), `earth` (his earth register: e.g. stone, taupe, espresso, olive, camel), `both` (bridges that sit happily in either: his "white" (optic white for cool seasons, cream/ivory for warm ones), ice gray, near-black leather, denim in many cases), `street` (pieces whose identity is street: graphic hoodies, technical shells, character sneakers).
- **`volume`**: how it fits **on him**, not the brand's label. Garments: `fitted` | `regular` | `relaxed` | `oversized`. Shoes: `low-profile` | `regular` | `chunky`. Accessories: `-`. When unsure, ask (step 4): this column drives the silhouette gate.
- **`loud`**: `yes` for a statement piece: bold pattern, saturated or loud colourway, big logo or graphic, character sneaker. Otherwise `no`. A **saturated** hero colour (clear/bright seasons) is usually `loud=yes`; a **muted** hero (soft seasons: sage, dusty teal) is usually `loud=no` but still flagged `hero-colour`.
- **`flag`** (empty, one value, or several separated by a space, e.g. `too-tight off-palette-near-face`):
  - `off-palette-near-face`: wrong temperature/clarity for his season AND worn near the face (tops, layers, scarves, eyewear). Check against his profile's *Avoid near the face*.
  - `off-palette`: off his palette but worn away from the face (belt, shoes, trousers).
  - `hero-colour`: one of his profile's hero colours.
  - `logo`: visible branding that defines the piece.
  - `skinny-fit`, `too-tight`: fit problems he has told you about.
  - `low-wear-parked`: he owns it but chooses not to wear it.
  - `end-of-life`: worn out (failing soles, pilling, fading); fine for errands, never for occasions.
  - `gym-register`: training wear.
  - `colour-unconfirmed`: the photo can't settle the colour; ask later.
  - Any personal flag his profile declares.
- **`favorite`**: `yes` if he says so, or it obviously gets worn constantly. Default `no`.
- **Season booleans** (`true`/`false`) for his climate bands: linen and open knits summer-only; heavy wool, flannel and boots not summer; most shoes and tees all-true; spring and fall usually match.

## After intake

- **First intake during onboarding:** go back to the onboarding finale (seed the shopping file, then "rate these 5").
- **Every later intake, closing gaps:** check **every** open Known gap and priority-queue line in his shopping file against **each** new row (garment type + colour, read loosely: "navy blazer" matches a dark-navy unstructured jacket). Close each match in place: struck through, `CLOSED <date>`, the owned piece named; then re-rank the queue. Say which gaps closed in the report. A gap left open after its piece is catalogued is the most common way the list goes stale.
- If a new piece duplicates a full slot, say so in one line, no lecture. A big intake (10+ items) is a good moment to offer the closet audit (Mode D).

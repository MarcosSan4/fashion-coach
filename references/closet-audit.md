# Mode D: closet audit (blindspot finder)

Goal: find what the day-to-day modes never see: thin formality and register cells, pieces nothing pairs with, single points of failure, dead weight, gaps that keep recurring, and gaps on the shopping list that are already closed. **The script counts; you judge.** Suggest running it quarterly, after a big intake, or before a shopping trip.

## 1. Run the counts

```
python3 ${CLAUDE_SKILL_DIR}/scripts/audit.py
```

It finds his files the same way the context loader does and prints six lenses: coverage grid, orphans, over-reliance, unworn, gap-log tally, stale gaps. `--season <s>` overrides the season (it assumes the northern hemisphere: pass it for a southern client); `--json` gives the raw numbers. Read-only.

## 2. Interpret (the numbers are evidence, not verdicts)

- **Coverage:** a `!` cell means an outfit at that formality, in that register, has 0-1 options for a slot. It matters only where his formality life and occasions actually live; a thin earth cell for a client who lives in neutrals is a non-issue. Read thin cells against the profile, not in the abstract.
- **Orphans** pass only the mechanical rules (formality, register, season, one loud piece, chunky shoe, oversized-on-fitted). Before calling one, check the description, colourway parentheticals and his personal constraints: some orphans are loud statement pieces doing their job (gate 5), some are gym or lounge pieces that should never pair.
- **Over-reliance:** a garment in more than a quarter of logged outfits is a single point of failure. It is not a problem to fix (he likes it), it is a slot that needs a **backup**: an owned piece that does the same job, or the gap that would.
- **Unworn:** the history covers only outfits he logged, never everything he wore. Seasonal pieces out of season are not dead weight, and accessories are rarely logged. Unworn is a question, not a cull list.
- **Gap log:** the stylists' `Gap:` lines from every Mode A run. A gap requested on **3+ distinct dates** is real demand: promote it into Known gaps (or raise its rank). One-offs stay in the log.
- **Stale gaps:** a heuristic noun + colour match, so false positives happen. Verify each against the closet rows; a real match means the gap is closed.

## 3. Ask ONE batched question

Unworn items, grouped: "These N pieces never appear in a logged outfit. For each: **worn but not logged**, **genuinely unworn**, or **parked on purpose**?" Numbered, one line each, answerable as "1 worn, 2-4 unworn, 5 parked". Skip the question if the history is empty (say so in one line and judge from the other lenses). Use his answers: genuinely unworn plus an orphan or a fit problem is a cull candidate; parked gets `low-wear-parked` (with his OK).

## 4. Output

1. **Blindspots, ranked by leverage** (3-6 lines): each names the lens, the evidence in one clause, and the fix (owned remix, backup, or buy). Leverage = how many outfits the fix unlocks in the formality cells he actually lives in, the same test as the capsule blueprint.
2. **Rewritten Known gaps + priority queue:** auto-close anything he owns (strike through, `CLOSED <date>`, the owned piece named), add promoted gap-log items, drop gaps the coverage grid shows are full, re-rank. Show the diff in a few lines, then write it.
3. **Backup slot** for each over-relied garment: the owned piece that covers it, or "none owned" plus the gap it implies.
4. **Cull / park candidates:** suggestions only, with the reason (orphan + unworn + fit). He decides; never delete closet rows.
5. **Teaching block:** the 1-2 principles the audit exercised (usually combinability and buy-for-the-gap).

## Edits

Lean files rule: the shopping file holds current state only. Rewrite the gaps and queue in place, one line per gap, with no audit narrative, no "was / now" history and no quotes. Flags he agrees to go in the closet CSV. The gap log is append-only; never rewrite or prune it here.

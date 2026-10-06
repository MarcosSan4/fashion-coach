#!/usr/bin/env bash
# Prints the client's style context into the fashion-coach prompt at render time.
# Called by SKILL.md via dynamic context injection. Read-only: never writes anything.
#
# Usage: load-context.sh <project> [section] [part]
#   section: profile (status + profile + shopping + issues) | closet | history (+ anchors) | all (default)
#   part:    1, 2, 3... Each injection is shown inline only up to ~30,000 characters (past that Claude Code
#            swaps it for a file path + preview), so every section is cut into parts under LIMIT characters
#            at line boundaries. SKILL.md injects enough parts to cover a large closet; empty parts print nothing.
#
# Data location, first match wins:
#   1. <project>/.fashion-coach   config file with PROFILE= CLOSET= HISTORY= SHOPPING= ISSUES_DIR= LESSONS=
#                                 (paths relative to the config file's folder, or absolute or ~/)
#                                 Optional GAPLOG= (Mode A's gap log; default gap-log.csv beside SHOPPING, read by audit.py)
#   2. <project>/wardrobe/        profile.md, closet.csv, shopping.md, issues/, and outfit-history.csv + lessons.md
#                                 (preferred: the board can save worn outfits) or the older outfit-history.md
#   3. ~/.fashion-coach           global config file, same keys (for a custom folder)
#   4. ~/fashion-coach/           same layout as 2 (default for a global install)

PROJECT="${1:-${CLAUDE_PROJECT_DIR:-$PWD}}"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANCHOR_MIN=10
SECTION="${2:-all}"
PART="${3:-1}"
LIMIT=27000

PROFILE="" CLOSET="" HISTORY="" LESSONS="" SHOPPING="" ISSUES_DIR="" GAPLOG="" SOURCE=""

conf_get() { # key from the config file, ignoring comments; no code is executed
  sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*//p" "$CONF" | head -1 | sed 's/[[:space:]]*$//; s/^"\(.*\)"$/\1/'
}
abspath() { # relative paths resolve against the config file's folder
  case "$1" in "") ;; /*) echo "$1" ;; "~/"*) echo "$HOME/${1#\~/}" ;; *) echo "$(dirname "$CONF")/$1" ;; esac; }

# A project config wins; otherwise a project wardrobe/ folder; otherwise a global ~/.fashion-coach config
# (written by onboarding when he keeps his files in a custom folder); otherwise ~/fashion-coach/.
CONF=""
if [ -f "$PROJECT/.fashion-coach" ]; then CONF="$PROJECT/.fashion-coach"
elif [ ! -f "$PROJECT/wardrobe/profile.md" ] && [ -f "$HOME/.fashion-coach" ]; then CONF="$HOME/.fashion-coach"; fi

if [ -n "$CONF" ]; then
  SOURCE="config $CONF"
  PROFILE=$(abspath "$(conf_get PROFILE)"); CLOSET=$(abspath "$(conf_get CLOSET)")
  HISTORY=$(abspath "$(conf_get HISTORY)"); SHOPPING=$(abspath "$(conf_get SHOPPING)")
  ISSUES_DIR=$(abspath "$(conf_get ISSUES_DIR)"); LESSONS=$(abspath "$(conf_get LESSONS)")
  GAPLOG=$(abspath "$(conf_get GAPLOG)")
else
  if [ -f "$PROJECT/wardrobe/profile.md" ]; then DIR="$PROJECT/wardrobe"; else DIR="$HOME/fashion-coach"; fi
  SOURCE="folder $DIR"
  PROFILE="$DIR/profile.md"; CLOSET="$DIR/closet.csv"; HISTORY="$DIR/outfit-history.md"
  { [ -f "$DIR/outfit-history.csv" ] || [ ! -f "$DIR/outfit-history.md" ]; } && { HISTORY="$DIR/outfit-history.csv"; LESSONS="$DIR/lessons.md"; }
  SHOPPING="$DIR/shopping.md"; ISSUES_DIR="$DIR/issues"
fi

# Print a markdown file without frontmatter, headings nested two levels under this script's blocks.
strip_fm() {
  awk 'NR==1 && /^---[[:space:]]*$/ {fm=1; next} fm && /^---[[:space:]]*$/ {fm=0; next} fm {next}
       /^```/ {code=!code} !code && /^#+ / {sub(/^#+/, "&##")} {print}' "$1"
}
have() { [ -n "$1" ] && [ -f "$1" ]; }

[ -z "$GAPLOG" ] && GAPLOG="$(dirname "${SHOPPING:-$CLOSET}")/gap-log.csv"

HIST_CSV=no; case "$HISTORY" in *.csv) HIST_CSV=yes ;; esac
items=0; graded=0; has_anti=no
have "$CLOSET" && items=$(awk 'NR>1 && NF' "$CLOSET" | grep -c '^[0-9]')
# Graded = numbered table rows outside any Anti-examples section (or CSV rows); anti = real data rows inside one.
count_md() { awk '
    /^#+ / { anti = (tolower($0) ~ /anti-example/) ; next }
    /^\|/ { cell = $0; sub(/^\|[[:space:]]*/, "", cell); sub(/[[:space:]]*\|.*/, "", cell)
            if (cell == "" || cell == "#" || cell ~ /^[-:]+$/) next
            if (anti) a++; else if (cell ~ /^[0-9]+$/) g++ }
    END { print g + 0, a + 0 }' "$1"; }
if [ "$HIST_CSV" = yes ]; then
  have "$HISTORY" && graded=$(awk 'NR>1 && NF' "$HISTORY" | wc -l | tr -d ' ')
  if have "$LESSONS"; then read -r _ anti_rows < <(count_md "$LESSONS"); [ "$anti_rows" -gt 0 ] && has_anti=yes; fi
elif have "$HISTORY"; then
  read -r graded anti_rows < <(count_md "$HISTORY")
  [ "$anti_rows" -gt 0 ] && has_anti=yes
fi

# Print part $1 of stdin, cut at line boundaries into chunks under LIMIT bytes (bytes >= chars, so safe).
chunk() {
  awk -v want="$1" -v lim="$LIMIT" '{ n = length($0) + 1; if (size + n > lim && size > 0) { part++; size = 0 }
    size += n; if (part + 1 == want) print }' part=0
}

status_block() {
  echo "## STATUS"
  echo "- Today: $(date +%Y-%m-%d)"
  echo "- Data source: $SOURCE"
  echo "- Profile: $PROFILE $(have "$PROFILE" || echo '(MISSING)')"
  echo "- Closet: $CLOSET $(have "$CLOSET" && echo "($items items)" || echo '(MISSING)')"
  echo "- Outfit history: $HISTORY $(have "$HISTORY" && echo "($graded graded outfits, own anti-examples: $has_anti)" || echo '(MISSING)')"
  echo "- Shopping: $SHOPPING $(have "$SHOPPING" || echo '(MISSING)')"
  echo "- Gap log: $GAPLOG $(have "$GAPLOG" || echo '(not created yet)')"
  [ -n "$ISSUES_DIR" ] && [ -d "$ISSUES_DIR" ] && echo "- Issues folder: $ISSUES_DIR"
  echo "- Templates for new files: $SKILL_DIR/templates/"
}

profile_section() {
  echo "=== BEGIN CLIENT CONTEXT ==="
  echo
  status_block
  if ! have "$PROFILE"; then
    echo
    echo "NO PROFILE FOUND -> run Mode O (onboarding)."
    echo "Create the client's files in $HOME/fashion-coach/ unless he names another folder."
    echo "Custom folder: also write $HOME/.fashion-coach with absolute PROFILE= CLOSET= HISTORY= SHOPPING= lines,"
    echo "or the next run will not find them. (A 'wardrobe/' folder inside the current project also works.)"
    return
  fi
  echo
  echo "## PROFILE"
  echo
  strip_fm "$PROFILE"
  echo
  echo "## SHOPPING (gaps, priority queue, sourcing)"
  echo
  if have "$SHOPPING"; then strip_fm "$SHOPPING"; else echo "(none yet: seed it from the capsule blueprint after closet intake)"; fi
  if [ -n "$ISSUES_DIR" ] && [ -d "$ISSUES_DIR" ]; then
    open_issues=""
    for f in "$ISSUES_DIR"/*.md; do
      [ -f "$f" ] || continue
      st=$(sed -n 's/^status:[[:space:]]*//p' "$f" | head -1)
      [ "$st" = "resolved" ] && continue
      title=$(grep -m1 '^# ' "$f" | sed 's/^# //')
      open_issues="${open_issues}- [${st:-open}] ${title} ($f)"$'\n'
    done
    if [ -n "$open_issues" ]; then
      echo
      echo "## OPEN ISSUES (never propose an item these park or flag; Read the file for detail)"
      echo
      printf '%s' "$open_issues"
    fi
  fi
}

closet_section() {
  have "$PROFILE" || return
  echo "## CLOSET (full CSV, every row; the header row is repeated in each part)"
  echo
  if have "$CLOSET" && [ "$items" -gt 0 ]; then
    tail -n +2 "$CLOSET"
  else
    echo "(empty: run Mode I before building outfits)"
  fi
}

history_section() {
  have "$PROFILE" || return
  echo "## OUTFIT HISTORY (his graded outfits: calibrate every grade to these)"
  echo
  if [ "$HIST_CSV" = yes ]; then
    have "$HISTORY" && python3 "$SKILL_DIR/scripts/build-board.py" --history-text 2>/dev/null || echo "(none yet)"
    have "$LESSONS" && { echo; strip_fm "$LESSONS"; }
  elif have "$HISTORY"; then strip_fm "$HISTORY"; else echo "(none yet)"; fi
  if [ "$graded" -lt "$ANCHOR_MIN" ] || [ "$has_anti" = no ]; then
    echo
    echo "## CALIBRATION ANCHORS (loaded because his own history is still thin; retire automatically at $ANCHOR_MIN graded outfits plus his own anti-examples)"
    echo
    strip_fm "$SKILL_DIR/references/anchor-examples.md"
  fi
}

# Wrap a part: label continuations, fence CSV parts, print nothing for an empty part.
emit() { # $1 = section function, $2 = label
  out=$("$1" | chunk "$PART")
  [ -z "$out" ] && { echo "<!-- $2: part $PART empty -->"; return; }
  [ "$PART" -gt 1 ] && echo "## $2 (continued, part $PART)" && echo
  if [ "$1" = closet_section ]; then
    printf '%s\n' "$out" | awk -v hdr="$(head -1 "$CLOSET" 2>/dev/null)" '
      /^## CLOSET/ || (NR <= 2 && /^$/) { print; next }
      !started { print "```csv"; if (hdr != "") print hdr; started = 1 } { print } END { if (started) print "```" }'
  else
    printf '%s\n' "$out"
  fi
}

case "$SECTION" in
  profile) emit profile_section "CLIENT CONTEXT" ;;
  closet)  emit closet_section "CLOSET"
           if [ "$PART" = 4 ] && [ -n "$(closet_section | chunk 5)" ]; then
             echo; echo "WARNING: the closet is larger than the injected parts; rows beyond this point are only in $CLOSET (Grep it by type before building)."
           fi ;;
  history) emit history_section "OUTFIT HISTORY"; [ "$PART" = 3 ] && have "$PROFILE" && { echo; echo "=== END CLIENT CONTEXT ==="; } ;;
  all)     profile_section; echo; closet_section; echo; history_section; echo; echo "=== END CLIENT CONTEXT ===" ;;
  *)       echo "load-context.sh: unknown section '$SECTION' (use profile | closet | history | all)" >&2; exit 2 ;;
esac
exit 0

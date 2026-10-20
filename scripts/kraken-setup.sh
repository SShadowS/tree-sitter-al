#!/usr/bin/env bash
# kraken setup (idempotent): the corpora, pi-mcp and the owner's Claude setup on the work volume.
set -euo pipefail
mkdir -p /work/src
ex="$(git rev-parse --git-common-dir)/info/exclude"
exclude() { grep -qxF "$1" "$ex" 2>/dev/null || echo "$1" >> "$ex"; }

# The public corpora, depth 1 at the commit tools/config_oracle/production-classes.tsv pins
# (`# corpus-head`): a corpus at another HEAD fails the oracle. autocrlf as on the owner's PC, so
# the bytes the parser reads match the evidence.
head_of() { sed -n "s/^# corpus-head $1 \([0-9a-f]*\)$/\1/p" tools/config_oracle/production-classes.tsv; }
corpus() { # <dir> <url> <label>
  local d=/work/src/$1 sha
  sha=$(head_of "$3")
  [ -n "$sha" ] || { echo "kraken-setup: no corpus-head for $3" >&2; return 1; }
  [ "$(git -C "$d" rev-parse HEAD 2>/dev/null)" = "$sha" ] && return 0
  rm -rf "$d.part" && git init -q -b corpus "$d.part"
  git -C "$d.part" config core.autocrlf true
  git -C "$d.part" fetch -q --depth 1 "$2" "$sha"
  git -C "$d.part" -c advice.detachedHead=false checkout -q --detach FETCH_HEAD
  rm -rf "$d" && mv "$d.part" "$d"
}
corpus BC.History https://github.com/StefanMaron/MSDyn365BC.Code.History.git bc-history
corpus BC28.1 https://github.com/StefanMaron/MSDyn365BC.Code.History.git bc28.1
corpus BCApps-29.0 https://github.com/microsoft/BCApps.git bcapps-29.0
# DC (Continia, private) and BC.History's one untracked .al (`# corpus-untracked`) are data,
# copied from the owner's PC
[ -f /work/src/DC/.git/HEAD ] || echo "kraken-setup: /work/src/DC is missing (data copy)" >&2
sed -n 's/^# corpus-untracked bc-history [0-9a-f]* \(.*\)$/\1/p' tools/config_oracle/production-classes.tsv |
  while IFS= read -r f; do
    [ -f "/work/src/BC.History/$f" ] || echo "kraken-setup: BC.History/$f is missing (data copy)" >&2
  done
# Where the tools look: ./BC.History and ./DC, and tools/b7_audit/seeds.py's literal H:/Git/<corpus>
# (a relative path on Linux). Symlinks, which neither .gitignore's `BC.History/` nor `DC/*` matches.
[ -e BC.History ] || ln -s /work/src/BC.History BC.History
[ -e DC ] || ln -s /work/src/DC DC
mkdir -p H: && { [ -e H:/Git ] || ln -s /work/src H:/Git; }
exclude /BC.History; exclude /DC; exclude /H:
# .superpowers/ (handovers, ledgers) and .cache/b7_audit are gitignored data from the PC too
[ -d .superpowers/sdd ] || echo "kraken-setup: .superpowers/ is missing (data copy)" >&2

# pi-mcp: the reviewer models (.mcp.json runs /work/src/pi-mcp/src/pi-server.ts)
if [ ! -d /work/src/pi-mcp/.git ]; then
  git clone -q https://github.com/SShadowS/pi-mcp.git /work/src/pi-mcp
else
  git -C /work/src/pi-mcp pull --quiet --ff-only || true
fi
(cd /work/src/pi-mcp && { [ -d node_modules ] || npm install --silent; } && npm run --silent --if-present build)

# The owner's Claude setup, gitignored on the PC, arrives as one tar through secret_files
# (.claude/kraken-claude.tar): project/ holds this checkout's untracked agents, commands and skills
# (merged in: commands/ and skills/ also hold tracked files), user/ the owner's CLAUDE.md and skills.
# kraken re-runs setup when the tar's bytes change.
if [ -f .claude/kraken-claude.tar ]; then
  t=$(mktemp -d)
  tar -xf .claude/kraken-claude.tar -C "$t"
  cp -r "$t/project/." .claude/
  cfg="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
  mkdir -p "$cfg/skills"
  cp "$t/user/CLAUDE.md" "$cfg/CLAUDE.md"
  for s in "$t"/user/skills/*; do rm -rf "$cfg/skills/$(basename "$s")" && cp -r "$s" "$cfg/skills/"; done
  rm -rf "$t"
fi
# The owner's plugins (on the Claude state volume, so this runs only when one is missing)
if command -v claude >/dev/null; then
  have=$(claude plugin list 2>/dev/null || true)
  for m in anthropics/claude-plugins-official DietrichGebert/ponytail; do
    claude plugin marketplace add "$m" >/dev/null 2>&1 || true
  done
  for p in superpowers@claude-plugins-official ponytail@ponytail; do
    echo "$have" | grep -q "${p%@*}" || claude plugin install "$p" ||
      echo "kraken-setup: plugin $p did not install" >&2
  done
fi

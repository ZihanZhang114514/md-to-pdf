#!/bin/sh
# Install md-to-pdf into the skill directories used by Claude Code, Codex and DSH.
#
#   ./install.sh              symlink into every host directory that exists
#   ./install.sh --copy       copy instead of symlink (survives deleting this folder)
#   ./install.sh --force      replace an existing non-symlink installation
#   ./install.sh --uninstall  remove it again
set -eu

SRC=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MODE=link
FORCE=0
UNINSTALL=0

usage() {
  sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
}

for arg in "$@"; do
  case "$arg" in
    --copy) MODE=copy ;;
    --force) FORCE=1 ;;
    --uninstall|--remove) UNINSTALL=1 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'unknown option: %s\n' "$arg" >&2; usage >&2; exit 2 ;;
  esac
done

install_one() {
  dest=$1
  if [ "$UNINSTALL" = 1 ]; then
    if [ -e "$dest" ] || [ -L "$dest" ]; then
      rm -rf "$dest"
      printf '  removed   %s\n' "$dest"
    fi
    return 0
  fi

  mkdir -p "$(dirname "$dest")"

  if [ -L "$dest" ]; then
    rm -f "$dest"
  elif [ -e "$dest" ] && [ "$FORCE" != 1 ]; then
    printf '  skipped   %s (already exists, use --force to replace)\n' "$dest"
    return 0
  elif [ -e "$dest" ]; then
    rm -rf "$dest"
  fi

  if [ "$MODE" = copy ]; then
    mkdir -p "$dest"
    (cd "$SRC" && tar cf - --exclude=.git .) | (cd "$dest" && tar xf -)
    printf '  copied    %s\n' "$dest"
  else
    ln -s "$SRC" "$dest"
    printf '  linked    %s -> %s\n' "$dest" "$SRC"
  fi
}

printf "%s md-to-pdf\n" "$([ "$UNINSTALL" = 1 ] && echo removing || echo installing)"
install_one "$HOME/.claude/skills/md-to-pdf"
install_one "$HOME/.agents/skills/md-to-pdf"
[ -d "$HOME/.dsh" ] && install_one "$HOME/.dsh/skills/md-to-pdf"

if [ "$UNINSTALL" = 1 ]; then
  printf 'done.\n'
  exit 0
fi

printf '\nnext:\n'
printf '  1. node %s/scripts/md2pdf.js --doctor      # check browser / python / fonts\n' "$SRC"
printf '  2. restart your agent (Claude Code: /md-to-pdf, Codex: $md-to-pdf)\n'
printf '  3. ask it: "turn report.md into an A4 PDF"\n'
if [ "$MODE" = link ]; then
  printf '\nnote: installed as a symlink — keep this folder where it is, or re-run with --copy.\n'
fi

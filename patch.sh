#!/usr/bin/env bash
# Dragon Quest XI (3DS) English patch - Linux / macOS / Steam Deck launcher.
#   ./patch.sh                       open the window (needs python3 with tkinter)
#   ./patch.sh game.cia [out.cia]    patch from the command line
#   ./patch.sh game.3ds out.cia --cia          convert a .3ds to an installable .cia
#   ./patch.sh game.cia --export outdir        make a small LayeredFS update folder
set -e
cd "$(dirname "$0")"
PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "Python 3 is required (install it with your package manager, e.g. 'sudo apt install python3 python3-tk')." >&2
  exit 1
fi
if [ "$#" -eq 0 ]; then
  if "$PY" -c "import tkinter" 2>/dev/null; then
    exec "$PY" DQXIEnglishPatcher.py
  else
    echo "tkinter is not installed, so the window cannot open." >&2
    echo "Either install it ('sudo apt install python3-tk' / 'sudo pacman -S tk')," >&2
    echo "or run from the terminal:  ./patch.sh \"/path/to/Dragon Quest XI.cia\" \"/path/to/output.cia\"" >&2
    exit 1
  fi
else
  exec "$PY" cia_patcher.py "$@"
fi

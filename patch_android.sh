#!/data/data/com.termux/files/usr/bin/bash
# Dragon Quest XI (3DS) English patch - Android (Termux) helper.
#   bash patch_android.sh                  finds your game in Downloads and patches it
#   bash patch_android.sh "/path/game.3ds" patch a specific file
set -e
cd "$(dirname "$0")"

say() { printf '\n== %s\n' "$*"; }

if ! command -v pkg >/dev/null 2>&1; then
  echo "This helper is for the Termux app (F-Droid / GitHub version). On Linux / Steam Deck / macOS use ./patch.sh" >&2
  exit 1
fi

say "1/4 Python"
if ! command -v python >/dev/null 2>&1; then
  if ! pkg install -y python; then
    echo "Package download failed (a mirror out of sync?) - switching to the main Termux mirror and trying again."
    echo "deb https://packages.termux.dev/apt/termux-main stable main" > "$PREFIX/etc/apt/sources.list"
    rm -rf "$PREFIX"/etc/apt/sources.list.d/* 2>/dev/null
    pkg update -y
    pkg install -y python
  fi
fi
python --version

say "2/4 Access to your files"
if [ ! -d "$HOME/storage/downloads" ]; then
  echo "Termux will now ask for permission to read your files - choose Allow."
  termux-setup-storage || true
  for i in 1 2 3 4 5 6 7 8 9 10; do [ -d "$HOME/storage/downloads" ] && break; sleep 2; done
fi
if [ ! -d "$HOME/storage/downloads" ]; then
  echo "No access to your files yet. Run  termux-setup-storage , allow it, then run this script again." >&2
  exit 1
fi

say "3/4 Your game file"
GAME="$1"
if [ -z "$GAME" ]; then
  mapfile -t FOUND < <(find -L "$HOME/storage/downloads" -maxdepth 2 \( -iname '*.3ds' -o -iname '*.cia' \) 2>/dev/null | grep -vi 'english' | sort -u)
  if [ "${#FOUND[@]}" -eq 0 ]; then
    mapfile -t FOUND < <(find -L "$HOME/storage/shared" -maxdepth 3 \( -iname '*.3ds' -o -iname '*.cia' \) 2>/dev/null | grep -vi 'english' | sort -u)
  fi
  if [ "${#FOUND[@]}" -eq 0 ]; then
    echo "No .3ds / .cia found in Downloads. Copy your DECRYPTED Japanese game there, or run:" >&2
    echo "  bash patch_android.sh \"/storage/emulated/0/path/to/game.3ds\"" >&2
    exit 1
  elif [ "${#FOUND[@]}" -eq 1 ]; then
    GAME="${FOUND[0]}"
  else
    echo "Which file is your decrypted Japanese game?"
    select GAME in "${FOUND[@]}"; do [ -n "$GAME" ] && break; done
  fi
fi
echo "Game: $GAME"
SIZE_KB=$(du -k "$GAME" | cut -f1)
FREE_KB=$(df -k "$(dirname "$GAME")" | tail -1 | awk '{print $4}')
NEED_KB=$((SIZE_KB * 2 + 500000))
if [ "$FREE_KB" -lt "$NEED_KB" ]; then
  echo "Not enough free space: about $((NEED_KB / 1048576)) GB needed, $((FREE_KB / 1048576)) GB free. Free some space and run again." >&2
  exit 1
fi

say "4/4 Patching (this takes a while - keep the screen on and Termux open)"
termux-wake-lock 2>/dev/null || true
trap 'termux-wake-unlock 2>/dev/null || true' EXIT
case "${GAME,,}" in
  *.3ds) OUT="${GAME%.*} (English).3ds" ;;
  *)     OUT="${GAME%.*} (English).cia" ;;
esac
python cia_patcher.py "$GAME" "$OUT"
echo
echo "Done. Your patched game: $OUT"
echo "Open it in your emulator (e.g. Azahar). Keep the original Japanese file untouched as a backup."

Dragon Quest XI (3DS, Japanese) - English Patch - Linux / Steam Deck / macOS
===========================================================================

This package runs the same patcher as the Windows .exe, from Python 3.
Nothing to install except Python 3 (and tkinter if you want the window).

1. Extract this folder anywhere.
2. Make the launcher executable (once):      chmod +x patch.sh
3. Window (easiest):                          ./patch.sh
   - Choose your DECRYPTED Japanese .cia or .3ds, choose where to save, press Patch.
   - If it says tkinter is missing:
       Debian/Ubuntu/SteamOS(after "sudo steamos-readonly disable"):  python3-tk
       Arch:   sudo pacman -S tk        Fedora: sudo dnf install python3-tkinter
4. From the terminal (no window needed):
       ./patch.sh "Dragon Quest XI (Japan).cia" "Dragon Quest XI - Echoes of an Elusive Age.cia"
       ./patch.sh "game.3ds"                               (.3ds -> "... (English).3ds", for emulator frontends)
       ./patch.sh "game.3ds" "English.cia" --cia         (.3ds -> installable .cia)

Notes
 * Your game file must be DECRYPTED (see README.txt, GodMode9: "Decrypt file (SD output)").
 * About 6 GB of free disk space is needed while patching.
 * Patch notes for every version are in CHANGELOG.txt and shown in the window.
 * This download contains no game data - only the differences from the original.
 * Made with AI assistance (Anthropic's Claude) and the author's direction and testing.
   File-format tooling is based on dqxi-format-tools by Kenzie-1377 (MIT).

Note: update folders (--export) are turned off for now. The patch changes often, so the best results come from making a NEW full patched .cia / .3ds and installing it each time. Sorry the updates are so frequent - they are needed as the translation keeps improving. Update folders will come back in a future patch once the game is more stable and patches are less frequent.

No window library? The patcher also runs without tkinter: python3 DQXIEnglishPatcher.py "game.3ds" (writes "... (English).3ds"), or ./patch.sh with the game file as shown in step 4.

IMPORTANT: before installing a new full game (.cia/.3ds) on a 3DS, delete any old update (luma) folder from the SD card: SD:/luma/titles/0004000000199200. Leftover files there override the new install (some text stays untranslated, e.g. the battle Plan menu).

Note: always make a new full patched .cia/.3ds from the newest version. Update folders (--export) are turned off for now.

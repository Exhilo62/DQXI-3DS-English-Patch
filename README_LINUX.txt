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
       ./patch.sh "game.cia" --export ~/dqxi_update       (small update folder, see README.txt)

Notes
 * Your game file must be DECRYPTED (see README.txt, GodMode9: "Decrypt file (SD output)").
 * About 6 GB of free disk space is needed while patching.
 * Patch notes for every version are in CHANGELOG.txt and shown in the window.
 * This download contains no game data - only the differences from the original.
 * Made with AI assistance (Anthropic's Claude) and the author's direction and testing.
   File-format tooling is based on dqxi-format-tools by Kenzie-1377 (MIT).

Note: an update folder (--export) cannot include the game-code edits (Link label, equip headers, result wording, 2D object names, full battle labels); a full patched .cia/.3ds has them. Use the full patch if you can.

No window library? The patcher also runs without tkinter: python3 DQXIEnglishPatcher.py "game.3ds" (writes "... (English).3ds"), or ./patch.sh with the game file as shown in step 4.

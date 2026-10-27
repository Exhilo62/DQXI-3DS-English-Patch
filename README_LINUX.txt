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

Android phone / tablet (Termux): see README_ANDROID.txt in this folder (new, not tested on many devices yet).

Notes
 * Your game file must be DECRYPTED (see README.txt, GodMode9: "Decrypt file (SD output)").
 * About 6 GB of free disk space is needed while patching.
 * Patch notes for every version are in CHANGELOG.txt and shown in the window.
 * This download contains no game data - only the differences from the original.
 * Made with AI assistance (Anthropic's Claude) and the author's direction and testing.
   File-format tooling is based on dqxi-format-tools by Kenzie-1377 (MIT).

Luma folder (real 3DS) - optional:  ./patch.sh "game.3ds" --export my_folder
  creates my_folder/luma/... Use it ONLY on a fresh, unmodified Japanese install (not a patched .cia): delete the old
  SD:/luma/titles/0004000000199200 first, copy the new "luma" folder to the SD root, turn on "Enable game patching" in Luma3DS,
  and repeat with EVERY new version. Never combine a Luma folder with a patched .cia/.3ds. 
  !! CAUTION: a Luma folder is NOT a complete translation. It cannot change the game program itself, so the battle
  command menu (Fight / Plan / Swap / Flee, Attack / Spells / Defend / Ability / Items / Equip), the party / bench / bag
  labels, the status abbreviations (KO / Psn / Cur) and the HOME-menu banner stay Japanese (full list: LUMA_FOLDER_LIMITS.txt).
  For the whole game in English use the full patched .cia / .3ds.
  NOTE: Luma folders are an option for people who do not want to reinstall the game for every test version. If they turn out to cause problems again (known crashes or bug reports), they will be switched off again until the project is nearly complete, and the full .cia / .3ds will be the only way.
  Any change to the game program (code) can only be in the full .cia / .3ds, never in a folder.

No window library? The patcher also runs without tkinter: python3 DQXIEnglishPatcher.py "game.3ds" (writes "... (English).3ds"), or ./patch.sh with the game file as shown in step 4.

IMPORTANT: before installing a new full game (.cia/.3ds) on a 3DS, delete any old update (luma) folder from the SD card: SD:/luma/titles/0004000000199200. Leftover files there override the new install (some text stays untranslated, e.g. the battle Plan menu).

Note: always start from the newest version: make a NEW full patched .cia/.3ds, or a new Luma folder on a fresh Japanese install.

SAVE REPAIR (saves from 0.1.17 - 0.1.20): Veronica and Sylvando were stored with names one letter too long (stray symbol after the name, and crashes reported mostly on Old 3DS). New games started with 0.1.21+ are fine. To keep playing an OLD save, download the separate "DQXI_3DS_Save_Repair" zip from the same GitHub page and run  python3 DQXI_SaveRepair.py "folder with your save files"  on a COPY of your save (README inside). Then play with a game patched with 0.1.21 or newer.

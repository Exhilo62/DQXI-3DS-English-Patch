Dragon Quest XI (3DS, Japanese) - English Patch
===============================================

HOW TO USE
 1. Make sure your game file is DECRYPTED (see "If it says your file is encrypted").
 2. Double-click  DQXIEnglishPatcher.exe
 3. Top box:    click Browse and choose your Japanese Dragon Quest XI .cia or .3ds
 4. Bottom box: choose where to save the patched game. It is named automatically:
                "Dragon Quest XI - Echoes of an Elusive Age.cia"  or
                "Dragon Quest XI - Echoes of an Elusive Age (English).3ds"
    If you picked a .3ds you can choose the output format:
                .3ds  (emulators / cartridge dump)   or   .cia  (install on a 3DS with FBI)
 5. Press Patch and wait about a minute. When it says Done, your English game is ready.

 !! BEFORE YOU INSTALL A NEW FULL GAME (.cia / .3ds) ON A 3DS:
    If you ever used an update ("luma") folder, DELETE the old one from your SD card first:
        SD:/luma/titles/0004000000199200
    Files left there (especially a code.ips and old romfs files) override the new install, so
    parts stay untranslated (for example the battle Plan menu shows odd letters instead of
    "Party") even though the new game file is correct. To go back to a clean install, delete
    that folder and install the new .cia.

INSTALLING / PLAYING
 .cia : copy to your 3DS SD card and install with FBI (needs custom firmware, e.g.
        Luma3DS). It keeps the same title ID as the Japanese game, so your saves
        carry over - back them up first to be safe.
 .3ds : use like any other cartridge dump (flashcart, emulators such as Azahar/Citra).

UPDATING AN ALREADY PATCHED GAME
 Update (Luma) folders are turned off for now. The patch changes often, so the best results come from making a NEW full patched .cia / .3ds and installing it each time. Sorry the updates are so frequent - they are needed as the translation keeps improving. Update folders will come back in a future patch once the game is more stable and patches are less frequent.
 To update: patch your Japanese game again with the newest version and install the new full .cia / .3ds
 (delete any old SD:/luma/titles/0004000000199200 folder first, see above).

IF IT SAYS YOUR FILE IS ENCRYPTED (one-time step)
 On your 3DS with GodMode9: select the file ->
   .cia : "CIA image options" -> "Decrypt file (SD output)"
   .3ds : "NCSD image options" -> "Decrypt file (SD output)"
 Copy the decrypted file to your PC and patch that one. Files that already work in
 emulators such as Azahar are usually already decrypted.

AI ASSISTANCE
 This project was made with the help of AI (Anthropic's Claude), working with the
 project's author, who directed, tested and corrected the work. The translation is
 machine-assisted, so some lines may be awkward or wrong - please report them.

NOTES
 * About 6 GB of free disk space is needed while patching.
 * This download contains no game data - only the differences from the original.
   You must provide your own legally obtained copy of the game.
 * Windows may show a SmartScreen/antivirus warning for unsigned small programs.
   The tool is open: the Python source (cia_patcher.py, DQXIEnglishPatcher.py) is
   available alongside this release.
 * The patched game is not signed by Nintendo like every modified game; installing
   a .cia needs signature patches (Luma3DS default).
 * Please report problems with a screenshot and which mode (2D/3D) you were in.

HELP US TEST (v0.1.18)
 These changes pass our text checks but nobody has seen them in the game yet. If you get
 there, please send a screenshot (or "OK") with your model/emulator and 2D/3D mode:
 * Name tags: Placido in Gondolia (was "Yahim") and Valentino in Puerto Valor (was "Seidon").
 * Gallopolis: the knight's vow sign by the palace stairs, and the palace guards/fans at night
   after the Sand National.
 * Battle: Veronica and Serena's pep power "Arboria's Blessing" and its "wore off" messages.
 * Act 1 story cutscenes (rewritten): any line that reads oddly, is cut off or scrolls.
 * Sniflheim bottom-screen map: the "Sn'rfelt" labels (the apostrophe should show).
 * Any leftover old name: Puchalao, Bahatra, Cheron, Lambda, Hinonogi, Shijima, Eckehart,
   Milrean, "... Castle Town".

LINUX / STEAM DECK / MAC
 Use the separate "Linux" download (DQXI_3DS_English_Patch_Linux_v*.zip): extract it,
 chmod +x patch.sh, then run ./patch.sh (window) or ./patch.sh game.cia out.cia (terminal).

CREDITS / LICENSES
 * File-format tooling (PACK/PACA archive handling, BLZ decompression, BXON text
   records) is based on dqxi-format-tools by Kenzie-1377 (MIT License):
   https://github.com/Kenzie-1377/dqxi-3ds-english-patch
   See LICENSE-dqxi-format-tools.txt.
 * Official English names follow the PS4/Switch localisation where available.
 * Dragon Quest is a trademark of Square Enix. Unofficial fan project.

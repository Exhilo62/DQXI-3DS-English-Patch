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
    that folder, install the new .cia, and only then add a newer update folder if you want one.

INSTALLING / PLAYING
 .cia : copy to your 3DS SD card and install with FBI (needs custom firmware, e.g.
        Luma3DS). It keeps the same title ID as the Japanese game, so your saves
        carry over - back them up first to be safe.
 .3ds : use like any other cartridge dump (flashcart, emulators such as Azahar/Citra).

UPDATING AN ALREADY PATCHED GAME (no 2-hour reinstall)
 If you already installed an English .cia and a new version comes out, you do not
 have to rebuild and reinstall the whole game:
 1. Open DQXIEnglishPatcher.exe, choose the SAME decrypted Japanese .cia/.3ds you
    used the first time (step 1), then press "Create update folder".
 2. Pick where to save it. It creates  DQXI_English_Update\luma\titles\
    0004000000199200\  containing only the changed files (about 150 MB).
 3. Real 3DS: copy the "luma" folder to the root of the SD card (merge/replace).
    One-time: hold SELECT while powering on to open the Luma config and turn on
    "Enable game patching". Then just start the game from the HOME menu.
    Updates after that are just copying the new "luma" folder again.
 4. Emulators (Azahar/Citra): copy the contents of
    DQXI_English_Update\luma\titles\0004000000199200\  into the emulator's
    load\mods\0004000000199200\  folder (right-click the game > Open Mods Location).
 Files in this folder override what is installed, so you can also use it with the
 plain Japanese game. To go back, delete the folder.
 LIMITATIONS OF AN UPDATE FOLDER vs A FULL PATCHED .cia / .3ds:
 The update folder only replaces data files; the game's program code cannot be changed
 safely this way (it crashes on real 3DS hardware). So with an update folder only:
   - battle menu labels are the shorter ones (Hit / Spell / Guard / Art / Bag / Eq.)
   - the Plan menu "Party" row is unreadable
   - the "Link" battle command, the equip-window headers (L.H. / Items / Equip), the
     group-battle result wording and the 2D "examined" object names stay Japanese-looking
 A full patched .cia or .3ds has all of these fixed. If you can, use the full patch.

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

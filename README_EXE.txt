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

TWO WAYS TO PLAY ON A REAL 3DS - pick ONE and never mix them
 A) FULL .cia (safest, recommended): press Patch, install the new .cia with FBI. Everything is translated.
    To update: patch your Japanese game again with the newest version and install the new .cia
    (delete any old SD:/luma/titles/0004000000199200 folder first, see above).
 B) LUMA FOLDER (small, quick to update): press "Create Luma folder". Rules:
    1. The game installed on your 3DS must be the original, UNMODIFIED Japanese game - not a patched .cia.
       (If you ever installed a patched .cia, delete it and install a fresh Japanese copy first.)
    2. Delete the old folder SD:/luma/titles/0004000000199200 first, then copy the new "luma" folder to the
       root of the SD card, so you never have old and new files mixed. Do this with EVERY new version.
    3. Luma3DS needs "Enable game patching" turned on (hold SELECT while booting for its menu).
    !! CAUTION: a Luma folder is NOT a complete translation. It cannot change the game program itself, so the
    battle command menu (Fight / Plan / Swap / Flee, Attack / Spells / Defend / Ability / Items / Equip), the
    party / bench / bag labels (Party, Bench, Bag, Soldiers, 's team), the status abbreviations (KO / Psn / Cur)
    and the HOME-menu banner stay Japanese. Full list: LUMA_FOLDER_LIMITS.txt. Everything stored in the game
    files is English. For the whole game in English use the full patched .cia / .3ds.
    NOTE: Luma folders are an option for people who do not want to reinstall the game for every test version. If they turn out to cause problems again (known crashes or bug reports), they will be switched off again until the project is nearly complete, and the full .cia / .3ds will be the only way.
    Any change to the game program (code) can only be in the full .cia / .3ds, never in a folder.
    A patched game (.cia/.3ds) plus a Luma folder at the same time (or a few patched versions installed over
    each other) can crash in battle. If something crashes, go back to one clean setup: either a fresh Japanese
    install + the newest Luma folder, or the newest full .cia with NO luma folder on the SD card.

IF IT SAYS YOUR FILE IS ENCRYPTED (one-time step)
 On your 3DS with GodMode9: select the file ->
   .cia : "CIA image options" -> "Decrypt file (SD output)"
   .3ds : "NCSD image options" -> "Decrypt file (SD output)"
 Copy the decrypted file to your PC and patch that one. Files that already work in
 emulators such as Azahar are usually already decrypted.

SAVE REPAIR (saves from 0.1.17 - 0.1.20)
 Veronica and Sylvando were stored with names one letter too long in saves made with 0.1.17 - 0.1.20:
 a stray symbol after the name in some lists, and battle crashes reported mostly on Old 3DS. New games
 started with 0.1.21 or newer are fine. To keep playing an OLD save, download the separate
 "DQXI_3DS_Save_Repair" zip from the same GitHub page, run DQXI_SaveRepair.exe on a COPY of your save
 (back it up with Checkpoint / JKSM first; instructions in its README), put the repaired save back and
 play with a game patched with 0.1.21 or newer. Your original files are kept in a backup folder.

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

HELP US TEST (v0.1.31)
 The current list of things to check (and where to report them) is on the project page:
 https://github.com/Exhilo62/DQXI-3DS-English-Patch  ("Help us test"). A screenshot or just "OK" with your
 model / emulator and 2D/3D mode helps a lot. Most wanted: menus with shortened labels (camp, shops, Tockle / Labyrinth, battle), Alena and Serenica in dialogue, the Field of Discipline in Angri-La (Gauntlet menus,
 High Lama's name tag, Zoom list), Octagonia on the world map, then Avarith (Phnom Nonh), the Luma folder option and the Android app.

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

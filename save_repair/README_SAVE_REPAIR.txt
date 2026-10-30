DQXI (3DS) English patch - SAVE REPAIR
======================================

WHO NEEDS THIS
 Saves made with English patch versions 0.1.17 - 0.1.20 (a save you started or last saved with one of
 those). In 0.1.17 - 0.1.19 two party names were stored one letter too long ("Veronic" and "Sylvand");
 0.1.20 stored them in a two-letter form that is drawn badly in battle and not recognised by 0.1.21. The game's name field holds only 6 characters, so the 7th letter spills into the next field.
 (0.1.18 and 0.1.19 saves may also hold "Veroni" / "Sylvan" plus a special character that old patches drew as "ca" / "do"; with a
 newer patch that character is drawn as other letters, so Veronica shows as "Veroniro" in the skill panel. The tool converts that form too.)
 What you may notice: a stray symbol after Veronica's or Sylvando's name in some lists, "Veroniro" in the skill panel, and
 "Veronic ,Serena" in the Link requirements. Testers also reported battle crashes (mostly on an Old 3DS)
 with Veronica in the party; one of them crashed even in the unmodified Japanese game with such a save,
 so it is not caused by the translation itself. We do not know that every crash is caused by this,
 but it is the only fault we found in those saves.

 Patch 0.1.21 and newer store the names as 6 characters (two letters share one character), so a NEW
 game started with 0.1.21+ is fine. This tool converts an EXISTING save so you can keep playing it.
 You do not need it if you start a new game, or if your save was started with 0.1.21 or newer.

WHAT IT DOES
 It looks for the 7-letter names in every save slot (Data0 - Data3) and rewrites them in the
 6-character form. Since 0.1.25 it also repairs the NPC name table of the save: the scholar Snorri
 ("Eckehar" with junk after it in old saves) the old forms of Connie, Da and Son, and (0.1.26) Hendrik / the Mysterious Youth / the High Lama, and (0.1.27) the Tockle Ickle (was Kurutch), so the stray character after Hendrik's name in battle goes away. It then fixes the save's checksum (without that the game refuses the file). Nothing
 else in the save is touched. Every file it changes is first copied into a folder
 "DQXI_SaveRepair_backups" next to the program. Running it twice is harmless.

 IMPORTANT: use it only together with the game patched with 0.1.21 or NEWER (make a new patched
 .cia / .3ds with the 0.1.21 patcher first). Older versions cannot draw the new name characters and
 would show odd symbols instead of the names.

HOW TO USE (Windows)
 1. Make a backup of your save. On a real 3DS: open Checkpoint (or JKSM), pick Dragon Quest XI and
    back up the save. Copy the backup folder from the SD card (SD:/3ds/Checkpoint/saves/...) to your PC.
    Emulator (Azahar / Citra): the save folder is under  ...\sdmc\Nintendo 3DS\...\title\00040000\00199200\data\00000001
    (Azahar: File > Open Azahar folder).
 2. Double-click  DQXI_SaveRepair.exe  and pick the folder that holds your save files (Data0, Data1,
    Data2, Data3, mini_0 ...). You can also drag the folder onto the exe. Subfolders are searched too.
 3. It lists each slot and which names it changed (for example "Veronic -> Ve..ca"). "nothing to repair" means that slot is fine.
    The repaired files stay in the folder you chose; the originals are in DQXI_SaveRepair_backups. (A .zip must be unzipped first.)
 4. Copy the repaired files back (on a 3DS: restore the backup with Checkpoint / JKSM; in an emulator:
    close the emulator and replace the files), then start the game patched with 0.1.21 or newer.

 Linux / Steam Deck / Mac:  python3 DQXI_SaveRepair.py "path/to/save folder"

IF SOMETHING GOES WRONG
 The original of every changed file is in DQXI_SaveRepair_backups (same file name, inside a folder
 named after the date and time). Copy it back over the repaired file. The tool refuses files whose
 checksum does not match (not a DQXI save slot) and leaves them alone.
 Please report problems at https://github.com/Exhilo62/DQXI-3DS-English-Patch/issues

This tool contains no game data. Unofficial fan project; made with the help of AI (Anthropic's Claude)
together with the project's author.

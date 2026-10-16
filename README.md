# Dragon Quest XI (3DS) – English Patch

An unofficial fan translation of **Dragon Quest XI: Echoes of an Elusive Age** for the Nintendo 3DS (Japanese
version, *Sugi Sarishi Toki o Motomete*). It translates the whole game – menus, battles, items, monsters, NPCs
and story – using the official PS4/Switch names where they are known.

> **No game data is included.** This repository and download contain only the *differences* from the original
> files. You need your own legally obtained copy of the Japanese game.

> **AI-assisted project.** The translation and the patching tools in this project were created with the help of
> AI (Anthropic's Claude), working with the project's author, who tested the result in emulators and on real
> hardware. As with any machine-assisted translation, some lines may be awkward or wrong – please report them
> in the [issues](../../issues).

## Showcase

[![Watch the showcase video](https://img.youtube.com/vi/JagQnseBXvo/maxresdefault.jpg)](https://youtu.be/JagQnseBXvo)

**Watch the showcase video:** https://youtu.be/JagQnseBXvo

## Community and support

Questions, bug reports, or just want to follow progress? Join the Discord:
**https://discord.gg/w2DSajEUx**

Please report problems with a screenshot, the patch version, where you were in the game, and whether you play on a real 3DS
or an emulator (2D or 3D mode). Bugs can also be filed as [GitHub issues](../../issues).

## Download

Get **`DQXI_3DS_English_Patch_vX.Y.Z.zip`** from the [Releases](../../releases) page, extract it, and run
**`DQXIEnglishPatcher.exe`**.

## How to use

1. Make sure your game file is **decrypted** (one-time step, see below).
2. Open `DQXIEnglishPatcher.exe`.
3. **Top box:** choose your Japanese Dragon Quest XI `.cia` or `.3ds`.
4. **Bottom box:** choose where to save the patched game (the name is filled in for you).
   If you picked a `.3ds` you can output either a `.3ds` or an installable `.cia`.
5. Press **Patch**. When it says *Done*, copy the result to your 3DS / emulator.

| Output | Use |
|---|---|
| `.cia` | Install with FBI on a 3DS with custom firmware (Luma3DS). Same title ID as the Japanese game, saves carry over. |
| `.3ds` | Emulators (Azahar / Citra) and cartridge-dump workflows. |

### Linux / Steam Deck / macOS
Download the separate **Linux** zip (DQXI_3DS_English_Patch_Linux_v*.zip), extract it, then:
```bash
chmod +x patch.sh
./patch.sh                                  # opens the window (needs python3-tk)
./patch.sh game.cia output.cia             # or patch from the terminal
```
The window also shows the patch notes for each version.

### Updating an already patched game (no reinstall)
After a new version, you don't have to rebuild and reinstall the whole game:
1. Open `DQXIEnglishPatcher.exe`, choose the **same decrypted Japanese file** as before (top box), then press
   **Create update folder (already patched game)** and pick where to save it.
2. **Real 3DS:** copy the created `luma` folder to the root of the SD card (replace files). Turn on
   *Enable game patching* once in the Luma config (hold SELECT while powering on).
3. **Azahar / Citra:** copy the contents of `luma/titles/0004000000199200/` into the emulator's
   `load/mods/0004000000199200/` folder.

The update folder is about 150 MB and contains only changed files; it overrides what is installed.

> **Update folder vs full patch:** an update folder (Luma folder / emulator mod) can only replace data files;
> changing the game's program code that way crashes real 3DS hardware, so it is left out. With an update folder only:
> - battle menu labels are the shorter ones (Hit / Spell / Guard / Art / Bag / Eq.)
> - the Plan menu "Party" row is unreadable
> - the "Link" battle command, the equip-window headers (L.H. / Items / Equip), the group-battle result wording
>   and the 2D "examined" object names stay Japanese-looking
>
> A full patched `.cia` / `.3ds` has all of these fixed, so use the full patch if you can.

### Decrypting your file (once)
With **GodMode9** on your 3DS: select the file →
`CIA image options` / `NCSD image options` → **Decrypt file (SD output)**.
Dumps that already run in an emulator are usually decrypted already. The tool tells you if the file is still
encrypted.

## What is translated
- All UI, menus, battle commands, items, spells, monsters (official PS4/Switch names), NPC and story text
- Map labels, town banners, title logo, HOME-menu banner and title text
- Works in both **3D** and **2D** mode (2D text re-fitted to the narrower window)

## Known issues
- A few NPC strings and the "combo available" picture are still Japanese.
- Update folders (LayeredFS) cannot carry the game-code edits listed above; a full patched `.cia` / `.3ds` has them.
- Some very long lines may still be tight in 2D mode – please report them.
- Developed in the Azahar emulator. **Tested on:** a real New Nintendo 3DS (Luma3DS, patched `.cia`) and a
  Retroid Pocket Duo Lite running Citra MMJ (patched `.3ds`).

## Reporting problems
Open an [issue](../../issues) with a **screenshot**, the **mode (2D/3D)**, and where it happened.

## Building from source
The tool is plain Python 3 (standard library only for patching; `tkinter` for the window).
```
python cia_patcher.py "Dragon Quest XI (Japan).cia"  "Dragon Quest XI - Echoes of an Elusive Age.cia"
python DQXIEnglishPatcher.py          # GUI
```
`dqxi_en.dqp` is the patch data (binary deltas against the original game files, no game data).
`cia_templates.bin` (needed only to convert a `.3ds` into a `.cia`) ships in the release download.

## Credits & licenses
- File-format tooling (PACK/PACA archive handling, BLZ decompression and BXON text records) is based on
  **dqxi-format-tools** by **Kenzie-1377** (MIT License):
  [github.com/Kenzie-1377/dqxi-3ds-english-patch](https://github.com/Kenzie-1377/dqxi-3ds-english-patch).
  The copy of `dqxi_blz.py` in this repository comes from that project; see
  `LICENSE-dqxi-format-tools.txt`.
- Official English names follow the PS4/Switch localisation.
- Translation drafting and tool development were done with AI assistance (Anthropic's Claude); the project
  author directed, tested and corrected the work.
- *Dragon Quest* is a trademark of Square Enix. This is an unofficial, non-commercial fan project and is not
  affiliated with or endorsed by Square Enix or Nintendo.

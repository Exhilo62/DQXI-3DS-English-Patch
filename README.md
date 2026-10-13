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

## Known issues

See the pinned "Known issues" entry on the Issues tab for the current list.

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
- Some very long lines may still be tight in 2D mode – please report them.
- Developed in the Azahar emulator; tested on real 3DS hardware (`.cia`) and Citra MMJ (`.3ds`).

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

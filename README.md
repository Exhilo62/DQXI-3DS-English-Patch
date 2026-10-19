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
./patch.sh game.3ds                        # .3ds in, "(English).3ds" out
```
The output type follows the input: a decrypted `.3ds` gives a `.3ds`, a `.cia` gives a `.cia` (an installed `.cia` does not show up in
emulator frontends such as EmuDeck / ES-DE). `--cia` only turns a `.3ds` into an installable `.cia`; a `.cia` cannot become a `.3ds`.
The window needs `python3-tk`; without it, the command-line form above still works.
The window also shows the patch notes for each version.

> **Installing a new full `.cia` / `.3ds` on a 3DS? Delete any old update ("luma") folder from the SD card first**
> (`SD:/luma/titles/0004000000199200`). Files left there, especially a `code.ips`, override the new install, so parts
> stay untranslated (for example the battle Plan menu shows odd letters instead of "Party") even though the new
> game file is correct. Clean install = delete that folder, then install the new `.cia`.

### Updating an already patched game
> **Update (Luma) folders are turned off for now.** The patch changes often, so the best results come from making a NEW full patched .cia / .3ds and installing it each time. Sorry the updates are so frequent - they are needed as the translation keeps improving. Update folders will come back in a future patch once the game is more stable and patches are less frequent.

To update, patch your Japanese game again with the newest version and install the new full `.cia` / `.3ds`
(delete any old `SD:/luma/titles/0004000000199200` folder first, see above).

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
- The "combo available" picture is still Japanese (a full scan of the game text found no Japanese left in dialogue).
- Update (Luma) folders are paused for now; always make a new full `.cia` / `.3ds`.
- Some very long lines may still be tight in 2D mode – please report them.
- Developed in the Azahar emulator. **Tested on:** a real New Nintendo 3DS (Luma3DS, patched `.cia`) and a
  Retroid Pocket Duo Lite running Citra MMJ (patched `.3ds`).

## Help us test (v0.1.18)
These changes pass our automatic text checks but haven't been seen in the game yet. If you get there, please post a
screenshot (or just "OK") with your model or emulator and 2D/3D mode:
- [ ] **Name tags:** Placido's speaker tag in Gondolia (the Doge Rotondo's son; was "Yahim") and Valentino's in Puerto Valor
  (was "Seidon") – check the right name shows and the dialogue isn't garbled.
- [ ] **Gallopolis:** the knight's vow sign by the palm trees left of the palace stairs (three centered lines with periods),
  and the palace guards, fans, wife and child after the Sand National.
- [ ] **Battle:** Veronica and Serena's pep power **Arboria's Blessing** – menu name, "Arboria's Blessing!" and the "...wore off!" messages.
- [ ] **Act 1 story cutscenes** (rewritten into more natural English): any line that reads oddly, is cut off or scrolls.
- [ ] **Sniflheim map:** the "Sn'rfelt" labels on the bottom-screen map (the apostrophe should show).
- [ ] **Leftover old names:** Puchalao, Bahatra, Cheron, Lambda, Hinonogi, Shijima, Eckehart, Milrean or "... Castle Town" anywhere.

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

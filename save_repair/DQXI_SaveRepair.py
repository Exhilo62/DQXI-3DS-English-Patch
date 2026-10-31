"""DQXI (3DS) English patch - save repair.

Saves made with English patch 0.1.17 - 0.1.19 store the party names "Veronica" and "Sylvando" as 7 letters
("Veronic", "Sylvand").  The game's name field holds only 6 characters + an end marker, so the 7th letter runs
into the next field: a stray symbol after the name in some lists, and (found while testing; it also happens in the
unmodified Japanese game) crashes in battle on some setups, mostly Old 3DS.  Patch 0.1.21 and later stores the names as 6
characters (two letters share one character; 0.1.20 used a different, badly drawn form, which this tool also converts).  This tool rewrites the names in an existing save to that form and fixes the
save's checksum, so you do not have to start a new game.

Use it only with the game patched with version 0.1.21 or newer: older versions cannot draw the new characters.

usage:  DQXI_SaveRepair.py [save folder or Data0..Data3 files ...]      (no arguments: a folder window opens)
Every file that is changed is first copied to DQXI_SaveRepair_backups\\<date-time>\\ next to this program."""
import sys, os, re, struct, zlib, time, shutil

# 7 letters -> 6 characters ('Ve'+ro+ni+'ca', 'Sy'+lv+an+'do'; the middle cells are drawn by the patch's font)
FIX = {'Veronic': 'Ve冑冒ca', 'Sylvand': 'Sy冥写do', 'Veroni冑': 'Ve冑冒ca', 'Sylvan冥': 'Sy冥写do', 'Eckehar': 'Snorri', 'Bahatra': 'Da', 'Hendrik': 'He冠rik', 'Mysteri': 'Youth', 'High La': 'Lama', 'Kurucch': 'Ickle', 'Kurutch': 'Ickle'}       # Snorri (JP Eckhart; 0.1.18 and older wrote 'Eckehar'), Phnom Nonh father
# 6-character forms from unreleased test builds
SAME_LEN = {'Vero冒冑': 'Ve冑冒ca', 'Sylv写冥': 'Sy冥写do',
            'Vero冑冒': 'Ve冑冒ca', 'Sylv冥写': 'Sy冥写do'}
SHORT = {'Ruko': 'Connie', 'Cheron': 'Son', 'Kuruch': 'Ickle'}
SLOT = re.compile(r'^Data[0-9]$')
# names as shown in the report: the in-game forms use font cells a Windows console cannot print
SHOWN = {'Ve冑冒ca': 'Veronica', 'Sy冥写do': 'Sylvando', 'He冠rik': 'Hendrik (6 characters)', 'Veroni冑': 'Veronic', 'Sylvan冥': 'Sylvand',
         'Vero冒冑': 'Veroniro', 'Vero冑冒': 'Veroniro', 'Sylv写冥': 'Sylvanlv', 'Sylv冥写': 'Sylvanlv'}


def shown(name):
    return SHOWN.get(name) or name.encode('ascii', 'replace').decode('ascii')


def here():
    return os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))


def repair(path, backup_dir, log=print):
    """Returns the number of names changed (0 = nothing to do), -1 for a file that is not a save slot."""
    d = bytearray(open(path, 'rb').read())
    if len(d) < 16 or zlib.crc32(bytes(d[:-8])) & 0xffffffff != struct.unpack_from('<I', d, len(d) - 4)[0]:
        log('  %s: not a save slot this tool understands (checksum does not match) - left alone' % path)
        return -1
    n = 0
    changed = []                                    # 'old -> new' for the report
    ok = [new for new in ('Ve冑冒ca', 'Sy冥写do') if new.encode('utf-16le') in d]     # party names already in the current form
    for old, new in FIX.items():
        pat = old.encode('utf-16le'); i = d.find(pat)
        while i >= 0:
            if i % 2 == 0 and d[i + 14:i + 16] != b'\0\0':       # 7 letters with no end marker: the bad form
                d[i:i + 14] = (new.encode('utf-16le') + b'\0\0').ljust(14, b'\0')
                n += 1; changed.append('%s -> %s' % (shown(old), shown(new)))
            i = d.find(pat, i + 2)
    # short names stored in the same 6-character fields: bring them in line with the current patch
    for old, new in SHORT.items():
        pat = old.encode('utf-16le'); i = d.find(pat)
        while i >= 0:
            if i % 2 == 0 and d[i + len(pat):i + 14] == bytes(14 - len(pat)):
                d[i:i + 14] = new.encode('utf-16le') + bytes(14 - 2 * len(new)); n += 1; changed.append('%s -> %s' % (shown(old), shown(new)))
            i = d.find(pat, i + 2)
    for old, new in SAME_LEN.items():
        pat = old.encode('utf-16le'); i = d.find(pat)
        while i >= 0:
            if i % 2 == 0:
                d[i:i + 12] = new.encode('utf-16le'); n += 1; changed.append('%s -> %s' % (shown(old), shown(new)))
            i = d.find(pat, i + 2)
    if not n:
        log('  %s: nothing to repair%s' % (path, ' (party names already in the current form)' if ok else ''))
        return 0
    # short backup path (mirroring the full source path overflows Windows' 260-character limit for emulator save folders)
    parent = os.path.basename(os.path.dirname(os.path.abspath(path))) or 'save'
    dst = os.path.join(backup_dir, parent, os.path.basename(path))
    k = 1
    while os.path.exists(dst):
        k += 1
        dst = os.path.join(backup_dir, '%s_%d' % (parent, k), os.path.basename(path))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(path, dst)
    struct.pack_into('<I', d, len(d) - 4, zlib.crc32(bytes(d[:-8])) & 0xffffffff)
    open(path, 'wb').write(bytes(d))
    log('  %s: %d name(s) repaired (%s)\n      original kept in %s' % (path, n, ', '.join(sorted(set(changed))), dst))
    return n


def find_slots(targets):
    files = []
    for t in targets:
        if os.path.isdir(t):
            for dp, dn, fn in os.walk(t):
                files += [os.path.join(dp, f) for f in sorted(fn) if SLOT.match(f)]
        elif os.path.isfile(t):
            files.append(t)
    return files


def ask_folder():
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
        r = tk.Tk(); r.withdraw()
        messagebox.showinfo('DQXI save repair',
                            'Choose the folder that holds your save files (Data0, Data1, Data2, Data3, mini_0 ...).\n\n'
                            'Use a COPY of the save exported from your 3DS (Checkpoint / JKSM) or the save folder of your emulator. '
                            'Your originals are kept in a backup folder next to this program.')
        p = filedialog.askdirectory(title='Folder with the DQXI save files (Data0, Data1 ...)')
        r.destroy()
        return p
    except Exception:
        return input('Folder with the save files (Data0, Data1 ...): ').strip().strip('"')


def default_save_dirs():
    """Save folders of the Japanese Dragon Quest XI in the common 3DS emulators on this computer (only those that exist)."""
    home = os.path.expanduser('~')
    roots = [os.path.join(os.environ.get('APPDATA', ''), n) for n in ('Azahar', 'Lime3DS', 'Citra')] if os.name == 'nt' else []
    for base in ('.local/share', '.var/app/org.azahar_emu.Azahar/data', 'Library/Application Support', '.config'):
        for n in ('azahar-emu', 'lime3ds-emu', 'citra-emu', 'Azahar', 'Lime3DS', 'Citra'):
            roots.append(os.path.join(home, base, n))
    found = []
    for r in roots:
        t = os.path.join(r, 'sdmc', 'Nintendo 3DS')
        if os.path.isdir(t):
            for dp, dn, fn in os.walk(t):
                if dp.replace('\\', '/').endswith('/title/00040000/00199200/data/00000001') and dp not in found:
                    found.append(dp)
                    dn[:] = []
    return found


def run(targets, backup_base=None, log=print):
    """Repair the save slots found in targets (folders or Data files). Returns (code, report text); code 0 = ok, 2 = nothing usable.
    The originals of every changed file go to <backup_base>\\<date-time>\\ (default: next to this program)."""
    out = []

    def say(m=''):
        out.append(m)
        log(m)
    if any(t.lower().endswith(('.zip', '.7z', '.rar')) for t in targets):
        say('That is an archive. Unzip it first, then choose the unzipped folder (the one that holds Data0, Data1 ...).')
        return 2, '\n'.join(out)
    files = find_slots(targets)
    if not files:
        say('No save files named Data0 ... Data9 found in: ' + ', '.join(targets))
        say('Choose the folder that directly holds Data0, Data1, Data2, Data3 (on an emulator it is called 00000001).')
        return 2, '\n'.join(out)
    backup = os.path.join(backup_base or os.path.join(here(), 'DQXI_SaveRepair_backups'), time.strftime('%Y-%m-%d_%H-%M-%S'))
    total = skipped = 0
    say('Found %d save slot file(s):' % len(files))
    for f in files:
        r = repair(f, backup, say)
        if r < 0:
            skipped += 1
        total += max(r, 0)
    say()
    if skipped == len(files):
        say('None of these files is a Dragon Quest XI save slot (the checksum did not match), so nothing was changed.')
        say('Check that you chose the right game folder.')
    elif total:
        say('Done: %d name(s) repaired in the slots listed above.' % total)
        say('The repaired files are in the folder you chose - copy THAT folder back to your 3DS (Checkpoint / JKSM restore) or')
        say('emulator (close it first), then play with the game patched with 0.1.21 or newer.')
        say('The originals are kept in: %s' % backup)
    else:
        say('Nothing needed repairing - this save is already fine. If names still look wrong, update the patch to the latest')
        say('version and make sure the patched game is the one you start.')
    return 0, '\n'.join(out)


def main(argv):
    targets = argv or [p for p in [ask_folder()] if p]
    if not targets:
        return 1
    return run(targets)[0]


if __name__ == '__main__':
    rc = main(sys.argv[1:])
    if getattr(sys, 'frozen', False) or sys.stdin.isatty():
        try:
            input('\nPress Enter to close ...')
        except EOFError:
            pass
    sys.exit(rc)

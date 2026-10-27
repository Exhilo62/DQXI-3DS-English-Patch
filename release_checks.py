"""Release checks that look at the finished release folder (run after build_exe_release.py / cia_patcher.py, before publishing).

  A. reproducible build: make_patch.py run again on the same mod gives byte-identical dqxi_en.dqp / code.ips, and the idempotent
     post-build fixers (cs_key_fix) have nothing left to change.
  B. save repair: the tool is run on COPIES of every test save we have (saves/**, zips included); a second run must find nothing,
     every file must keep a valid checksum, and no 7-letter name form may remain.
  C. release notes and files agree with release/VERSION: GitHub notes, Discord post, CHANGELOG section, README test list / save repair
     zip name, the three zips in dist/, the test .cia, github_repo (VERSION, dqxi_en.dqp, code.ips, save repair files, CHANGELOG).

usage: py release_checks.py [--skip-build]        exit code 1 if anything fails"""
import sys, os, re, struct, zlib, hashlib, shutil, subprocess, tempfile, zipfile, importlib.util
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parent
V = (H / 'VERSION').read_text().strip()
MOD = H / 'mod_build'
problems = 0


def say(*a):
    print(*a, flush=True)


def fail(msg):
    global problems
    problems += 1
    say('   FAIL', msg)


def sha(p):
    return hashlib.sha1(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- A
say(f'== A. reproducible build (version {V})')
if '--skip-build' in sys.argv:
    say('   skipped (--skip-build)')
else:
    before = {n: sha(H / 'dist' / n) for n in ('dqxi_en.dqp', 'code.ips')}
    env = dict(os.environ, DQXI_MOD=str(MOD))
    r = subprocess.run([sys.executable, str(H / 'make_patch.py')], cwd=str(H), env=env, capture_output=True, text=True)
    if r.returncode:
        fail('make_patch.py failed: ' + (r.stderr or r.stdout)[-300:])
    for n, h in before.items():
        if sha(H / 'dist' / n) != h:
            fail(f'{n} differs after rebuilding from the same mod (build is not reproducible)')
        else:
            say(f'   {n}: identical after a rebuild')
fx = subprocess.run([sys.executable, '-I', str(ROOT / 'translation/text-v9/cs_key_fix.py'), str(MOD / 'romfs'), '--dry'],
                    capture_output=True, text=True)
m = re.search(r'total (\d+)', fx.stdout)
if not m or int(m.group(1)):
    fail('cs_key_fix still has fields to restore: ' + fx.stdout[-200:])
else:
    say('   cs_key_fix: nothing left to restore')

# ---------------------------------------------------------------- B
say('== B. save repair on the test saves')
spec = importlib.util.spec_from_file_location('sr', H / 'save_repair/DQXI_SaveRepair.py')
sr = importlib.util.module_from_spec(spec); spec.loader.exec_module(sr)
tmp = Path(tempfile.mkdtemp(prefix='savecheck_'))
saves = ROOT / 'saves'
n_files = 0
if saves.exists():
    for z in saves.rglob('*.zip'):
        try:
            zipfile.ZipFile(z).extractall(tmp / ('zip_' + z.stem))
        except Exception as e:
            fail(f'{z.name}: cannot read ({e})')
    for d in saves.iterdir():
        if d.is_dir():
            shutil.copytree(d, tmp / ('dir_' + d.name), dirs_exist_ok=True)
files = sr.find_slots([str(tmp)])
bk = tmp / '_backups'
for f in files:
    n_files += 1
    r1 = sr.repair(f, str(bk), log=lambda *_: None)
    if r1 < 0:
        fail(f'{f}: not a valid save slot (checksum)'); continue
    r2 = sr.repair(f, str(bk), log=lambda *_: None)
    d = Path(f).read_bytes()
    ok = zlib.crc32(d[:-8]) & 0xffffffff == struct.unpack_from('<I', d, len(d) - 4)[0]
    if r2 != 0:
        fail(f'{f}: second run still repaired {r2} name(s)')
    elif not ok:
        fail(f'{f}: checksum invalid after repair')
    for old in sr.FIX:
        pat = old.encode('utf-16le'); i = d.find(pat)
        while i >= 0:
            if i % 2 == 0 and d[i + 14:i + 16] != b'\0\0':
                fail(f'{f}: 7-letter form "{old}" remains at {hex(i)}'); break
            i = d.find(pat, i + 2)
say(f'   {n_files} save slot(s) repaired twice, checksums valid')
if not n_files:
    say('   (no test saves found under saves/)')
shutil.rmtree(tmp, ignore_errors=True)

# ---------------------------------------------------------------- C
say(f'== C. release notes, version and files agree ({V})')
GH = ROOT / 'github_repo'
for f in (H / f'GITHUB_RELEASE_v{V}.md', H / f'DISCORD_POST_v{V}.md'):
    if not f.exists():
        fail(f'missing {f.name}'); continue
    t = f.read_text(encoding='utf-8')
    if f.name.startswith('GITHUB'):
        for need in (f'v{V}', f'DQXI_3DS_Save_Repair_v{V}.zip', f'DQXI_3DS_English_Patch_v{V}.zip', f'DQXI_3DS_English_Patch_Linux_v{V}.zip',
                     f'DQXI_English_Patcher_Android_v{V}.apk',
                     'AI-assisted project', 'SAVE REPAIR'):
            if need not in t: fail(f'{f.name}: "{need}" missing')
    else:
        for need in (f'v{V}', f'DQXI_3DS_Save_Repair_v{V}.zip', 'save repair'):
            if need.lower() not in t.lower(): fail(f'{f.name}: "{need}" missing')
    for other in re.findall(r'v?0\.1\.(\d+)', t):
        if int(other) > int(V.split('.')[2]): fail(f'{f.name}: mentions a newer version 0.1.{other}')
cl = (H / 'CHANGELOG.txt').read_text(encoding='utf-8')
first = re.search(r'^(0\.1\.\d+)\s*$', cl, re.M)
if not first or first.group(1) != V:
    fail(f'CHANGELOG first section is {first.group(1) if first else "?"}, expected {V}')
sec = cl.split(f'\n{V}\n', 1)[-1].split('\n0.1.', 1)[0] if f'\n{V}\n' in cl else ''
if 'DQXI_3DS_Save_Repair_v' + V not in sec:
    fail('CHANGELOG section does not name the save repair zip of this version')
rd = (GH / 'README.md').read_text(encoding='utf-8')
if f'Help us test (v{V})' not in rd: fail(f'README test list is not "Help us test (v{V})"')
if f'DQXI_3DS_Save_Repair_v{V}.zip' not in rd: fail('README names a different save repair zip')
for n in (f'DQXI_3DS_English_Patch_v{V}.zip', f'DQXI_3DS_English_Patch_Linux_v{V}.zip', f'DQXI_3DS_Save_Repair_v{V}.zip'):
    p = H / 'dist' / n
    if not p.exists() or p.stat().st_size < 1_000_000: fail(f'dist/{n} missing or tiny')
    else:
        z = zipfile.ZipFile(p)
        if z.testzip() is not None: fail(f'dist/{n} is corrupt')
apk = H / 'dist' / f'DQXI_English_Patcher_Android_v{V}.apk'
if not apk.exists() or apk.stat().st_size < 10_000_000:
    fail(f'{apk.name} missing or tiny (build it with android_patcher\build_apk.bat release)')
else:
    z = zipfile.ZipFile(apk)
    if z.testzip() is not None: fail(f'{apk.name} is corrupt')
    if b'APK Sig Block 42' not in apk.read_bytes()[-(8 << 20):] and not any(n.startswith('META-INF/') and n.endswith(('.RSA', '.SF')) for n in z.namelist()): fail(f'{apk.name} is not signed')
    asset_ver = zipfile.ZipFile(apk).read('assets/VERSION').decode().strip() if 'assets/VERSION' in z.namelist() else '?'
    if asset_ver != V: fail(f'{apk.name} carries patch version {asset_ver}, expected {V}')
    # the APK must carry exactly the patch data of this release
    for nm, src in (('assets/dqxi_en.dqp', H / 'dist/dqxi_en.dqp'), ('assets/code.ips', H / 'code.ips')):
        if nm not in z.namelist() or hashlib.sha1(z.read(nm)).hexdigest() != sha(src): fail(f'{apk.name}: {nm} differs from the release build (rebuild the APK)')
if not (GH / 'android_patcher' / 'app' / 'build.gradle').exists(): fail('github_repo/android_patcher is missing (copy the app source)')
cia = H / f'test_english_{V}.cia'
if not cia.exists(): fail(f'{cia.name} missing')
if (GH / 'VERSION').read_text().strip() != V: fail('github_repo/VERSION differs')
for n, src in (('dqxi_en.dqp', H / 'dist/dqxi_en.dqp'), ('code.ips', H / 'code.ips'), ('CHANGELOG.txt', H / 'CHANGELOG.txt'),
               ('save_repair/DQXI_SaveRepair.py', H / 'save_repair/DQXI_SaveRepair.py'),
               ('save_repair/README_SAVE_REPAIR.txt', H / 'save_repair/README_SAVE_REPAIR.txt')):
    g = GH / n
    if not g.exists() or not src.exists() or sha(g) != sha(src): fail(f'github_repo/{n} is not the same as the release build')
# the zips must carry this version's delta / changelog (the Windows exe embeds the delta; its zip carries README + CHANGELOG)
for n in (f'DQXI_3DS_English_Patch_v{V}.zip', f'DQXI_3DS_English_Patch_Linux_v{V}.zip'):
    p = H / 'dist' / n
    if not p.exists(): continue
    z = zipfile.ZipFile(p)
    for member in z.namelist():
        if member.endswith('dqxi_en.dqp') and hashlib.sha1(z.read(member)).hexdigest() != sha(GH / 'dqxi_en.dqp'):
            fail(f'{n}: dqxi_en.dqp differs from github_repo')
        if member.endswith('CHANGELOG.txt') and hashlib.sha1(z.read(member)).hexdigest() != sha(GH / 'CHANGELOG.txt'):
            fail(f'{n}: CHANGELOG.txt differs from github_repo')
        if member.endswith('/VERSION') and z.read(member).decode().strip() != V:
            fail(f'{n}: VERSION inside the zip is not {V}')
say(f'== RESULT: {"FAIL" if problems else "OK"} ({problems} problems)')
sys.exit(1 if problems else 0)

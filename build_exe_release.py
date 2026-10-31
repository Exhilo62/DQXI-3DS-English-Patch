"""Build DQXIEnglishPatcher.exe, the Windows zip (exe + README + changelog + license) and the Linux/Steam Deck zip."""
import subprocess,sys,shutil,zipfile
from pathlib import Path
H=Path(__file__).parent
# pre-release text scan of the build (Japanese left, dialogue over 3 lines / too wide, old names); stops the build on failure.
# Run the full check (text diff + structure check) BEFORE syncing a new mod into mod_build:
#   py translation/text-v9/prerelease_check.py <Azahar mod romfs> --base release/mod_build/romfs
# Set DQXI_SKIP_CHECK=1 to build anyway.
import os
_mod=Path(os.environ.get('DQXI_MOD') or H/'mod_build')
_chk=H.parent/'translation'/'text-v9'/'prerelease_check.py'      # only in the working copy, not in the public repo
if os.environ.get('DQXI_SKIP_CHECK')!='1' and _chk.exists():
    _r=subprocess.run([sys.executable,'-X','utf8',str(_chk),str(_mod/'romfs'),'--scan-only'])
    if _r.returncode:sys.exit('pre-release check failed - fix the problems above or set DQXI_SKIP_CHECK=1')
subprocess.check_call([sys.executable,str(H/'make_patch.py')],cwd=str(H))
for f in ('dqxi_en.dqp','code.ips'):shutil.copy2(H/'dist'/'_build'/f,H/f)
r=str(H)
subprocess.check_call([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--windowed','--name','DQXIEnglishPatcher',
    '--add-data',r+r'\dqxi_en.dqp;.','--add-data',r+r'\code.ips;.','--add-data',r+r'\code_layered.ips;.','--add-data',r+r'\VERSION;.',
    '--add-data',r+r'\CHANGELOG.txt;.','--add-data',r+r'\logo.png;.','--add-data',r+r'\cia_templates.bin;.',
    '--paths',str(H/'save_repair'),'--hidden-import','DQXI_SaveRepair',
    '--distpath',str(H/'exe_dist'),'--workpath',str(H/'exe_build'),'--specpath',str(H/'exe_build'),str(H/'DQXIEnglishPatcher.py')],cwd=r)
v=(H/'VERSION').read_text().strip()
# dist/ holds only this version's uploads: older zips / apks / test files move to dist/archive
(H/'dist'/'archive').mkdir(exist_ok=True)
for _f in list((H/'dist').iterdir()):
    if _f.is_file() and _f.suffix in ('.zip','.apk','.txt') and f'v{v}' not in _f.name and _f.name!='UPLOAD_THESE.txt':
        shutil.move(str(_f),str(H/'dist'/'archive'/_f.name))
z=H/'dist'/f'DQXI_3DS_English_Patch_v{v}.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as zf:
    zf.write(H/'exe_dist'/'DQXIEnglishPatcher.exe','DQXIEnglishPatcher.exe')
    zf.write(H/'README_EXE.txt','README.txt')
    zf.write(H/'CHANGELOG.txt','CHANGELOG.txt')
    zf.write(H/'LUMA_FOLDER_LIMITS.txt','LUMA_FOLDER_LIMITS.txt')
    zf.write(H/'LICENSE-dqxi-format-tools.txt','LICENSE-dqxi-format-tools.txt')
print('wrote',z,round(z.stat().st_size/1e6,1),'MB')
# Linux / Steam Deck / macOS package: python sources + data + launcher (the launcher keeps its executable bit)
lz=H/'dist'/f'DQXI_3DS_English_Patch_Linux_v{v}.zip'
SRC=['cia_patcher.py','DQXIEnglishPatcher.py','dqxi_blz.py','dqxi_en_patcher.py']
DATA=['dqxi_en.dqp','code.ips','code_layered.ips','cia_templates.bin','VERSION','CHANGELOG.txt','logo.png','LICENSE-dqxi-format-tools.txt']
with zipfile.ZipFile(lz,'w',zipfile.ZIP_DEFLATED) as zf:
    for f in SRC+DATA:zf.write(H/f,'DQXI_English_Patch/'+f)
    zf.write(H/'save_repair'/'DQXI_SaveRepair.py','DQXI_English_Patch/DQXI_SaveRepair.py')      # the patcher's "Repair old save" button / --repair-save
    zf.write(H/'README_EXE.txt','DQXI_English_Patch/README.txt')
    zf.write(H/'README_LINUX.txt','DQXI_English_Patch/README_LINUX.txt')
    zf.write(H/'README_ANDROID.txt','DQXI_English_Patch/README_ANDROID.txt')
    zf.write(H/'LUMA_FOLDER_LIMITS.txt','DQXI_English_Patch/LUMA_FOLDER_LIMITS.txt')
    za=zipfile.ZipInfo('DQXI_English_Patch/patch_android.sh');za.external_attr=(0o755<<16)|(0o100000<<16)
    za.compress_type=zipfile.ZIP_DEFLATED
    zf.writestr(za,(H/'patch_android.sh').read_bytes().replace(b'\r\n',b'\n'))
    zi=zipfile.ZipInfo('DQXI_English_Patch/patch.sh');zi.external_attr=(0o755<<16)|(0o100000<<16)
    zi.compress_type=zipfile.ZIP_DEFLATED
    zf.writestr(zi,(H/'patch.sh').read_bytes().replace(b'\r\n',b'\n'))
print('wrote',lz,round(lz.stat().st_size/1e6,1),'MB')
# the list of what to upload for this version
_ups = [('DQXI_3DS_English_Patch_v%s.zip' % v, 'Windows (DQXIEnglishPatcher.exe)'),
        ('DQXI_3DS_English_Patch_Linux_v%s.zip' % v, 'Linux / Steam Deck / macOS (and the Termux route for Android)'),
        ('DQXI_English_Patcher_Android_v%s.apk' % v, 'Android app (arm64 phones / handhelds; build it with android_patcher\\build_apk.bat release)')]
_lines = ['Release v%s - attach these files to the GitHub release (nothing else in this folder):' % v, '']
_lines += ['  [%s] %s   - %s' % ('x' if (H / 'dist' / n).exists() else 'MISSING', n, d) for n, d in _ups]
_lines += ['', 'Texts: release/GITHUB_RELEASE_v%s.md (release notes), release/DISCORD_POST_v%s.md (Discord).' % (v, v),
           'archive/ = older versions and test files (do not upload).  _build/ = build intermediates.',
           'NEVER upload the test .cia/.3ds (they contain the game) or android_patcher/*.keystore / keystore.properties.']
(H / 'dist' / 'UPLOAD_THESE.txt').write_text('\n'.join(_lines) + '\n', encoding='utf-8')

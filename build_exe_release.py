"""Build DQXIEnglishPatcher.exe, the Windows zip (exe + README + changelog + license) and the Linux/Steam Deck zip."""
import subprocess,sys,shutil,zipfile
from pathlib import Path
H=Path(__file__).parent
subprocess.check_call([sys.executable,str(H/'make_patch.py')],cwd=str(H))
for f in ('dqxi_en.dqp','code.ips'):shutil.copy2(H/'dist'/f,H/f)
r=str(H)
subprocess.check_call([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--windowed','--name','DQXIEnglishPatcher',
    '--add-data',r+r'\dqxi_en.dqp;.','--add-data',r+r'\code.ips;.','--add-data',r+r'\code_layered.ips;.','--add-data',r+r'\VERSION;.',
    '--add-data',r+r'\CHANGELOG.txt;.','--add-data',r+r'\logo.png;.','--add-data',r+r'\cia_templates.bin;.',
    '--distpath',str(H/'exe_dist'),'--workpath',str(H/'exe_build'),'--specpath',str(H/'exe_build'),str(H/'DQXIEnglishPatcher.py')],cwd=r)
v=(H/'VERSION').read_text().strip()
z=H/'dist'/f'DQXI_3DS_English_Patch_v{v}.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as zf:
    zf.write(H/'exe_dist'/'DQXIEnglishPatcher.exe','DQXIEnglishPatcher.exe')
    zf.write(H/'README_EXE.txt','README.txt')
    zf.write(H/'CHANGELOG.txt','CHANGELOG.txt')
    zf.write(H/'LICENSE-dqxi-format-tools.txt','LICENSE-dqxi-format-tools.txt')
print('wrote',z,round(z.stat().st_size/1e6,1),'MB')
# Linux / Steam Deck / macOS package: python sources + data + launcher (the launcher keeps its executable bit)
lz=H/'dist'/f'DQXI_3DS_English_Patch_Linux_v{v}.zip'
SRC=['cia_patcher.py','DQXIEnglishPatcher.py','dqxi_blz.py','dqxi_en_patcher.py']
DATA=['dqxi_en.dqp','code.ips','code_layered.ips','cia_templates.bin','VERSION','CHANGELOG.txt','logo.png','LICENSE-dqxi-format-tools.txt']
with zipfile.ZipFile(lz,'w',zipfile.ZIP_DEFLATED) as zf:
    for f in SRC+DATA:zf.write(H/f,'DQXI_English_Patch/'+f)
    zf.write(H/'README_EXE.txt','DQXI_English_Patch/README.txt')
    zf.write(H/'README_LINUX.txt','DQXI_English_Patch/README_LINUX.txt')
    zi=zipfile.ZipInfo('DQXI_English_Patch/patch.sh');zi.external_attr=(0o755<<16)|(0o100000<<16)
    zi.compress_type=zipfile.ZIP_DEFLATED
    zf.writestr(zi,(H/'patch.sh').read_bytes().replace(b'\r\n',b'\n'))
print('wrote',lz,round(lz.stat().st_size/1e6,1),'MB')


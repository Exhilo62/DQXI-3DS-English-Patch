#!/usr/bin/env python3
"""Dragon Quest XI (3DS) English Patcher - simple GUI around cia_patcher."""
import os,sys,threading,queue,shutil,time,traceback,subprocess,json
from pathlib import Path
try:
    import tkinter as tk
    from tkinter import ttk,filedialog,messagebox
    HAVE_TK=True
except Exception:      # no window library (e.g. python3-tk missing on Linux): command-line use still works
    HAVE_TK=False
    class _NoTk: Tk=object
    tk=_NoTk();ttk=filedialog=messagebox=None

def res(name):
    base=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
    return base/name
sys.path.insert(0,str(Path(__file__).parent))
import cia_patcher

VERSION='?'
UPDATE_FOLDERS=False   # Luma update folders are paused: patches change too often, so full .cia/.3ds only
try:VERSION=res('VERSION').read_text().strip()
except Exception:pass
def load_notes():
    """CHANGELOG.txt (bundled in the exe / next to the script), newest version first."""
    for p in (res('CHANGELOG.txt'),Path(__file__).parent/'CHANGELOG.txt'):
        try:
            t=p.read_text(encoding='utf-8-sig').strip()
            if t:return t
        except Exception:pass
    return 'Patch notes are not available in this copy.'
REPO='https://github.com/Exhilo62/DQXI-3DS-English-Patch'
DISCORD='https://discord.gg/w2DSajEUx'
def fs_name(path):
    """file system of the drive holding `path` (Windows only; '' when unknown)"""
    try:
        import ctypes
        if os.name!='nt':return ''
        root=Path(path).resolve().anchor
        buf=ctypes.create_unicode_buffer(64)
        if ctypes.windll.kernel32.GetVolumeInformationW(ctypes.c_wchar_p(root),None,0,None,None,None,buf,64):return buf.value
    except Exception:pass
    return ''
def settings_path():
    base=Path(os.environ.get('APPDATA') or (Path.home()/'.config'))
    return base/'DQXIEnglishPatch'/'settings.json'
def load_settings():
    try:return json.loads(settings_path().read_text(encoding='utf-8'))
    except Exception:return {}
def save_settings(d):
    try:
        p=settings_path();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=1),encoding='utf-8')
    except Exception:pass
def fmt_secs(s):
    s=int(max(0,s))
    return '%d s'%s if s<90 else '%d min %02d s'%(s//60,s%60)
def redact(text):
    """no user name / home folder in text people paste into bug reports"""
    try:
        home=str(Path.home())
        text=text.replace(home,'~').replace(home.replace('\\','/'),'~')
        user=Path.home().name
        if len(user)>2:text=text.replace(user,'<user>')
    except Exception:pass
    return text
AUTONAME='Dragon Quest XI - Echoes of an Elusive Age'
def autoname(ext):
    # the .cia keeps the shorter name (easier to read in FBI / HOME menu lists)
    return AUTONAME+('' if ext=='.cia' else ' (English)')+ext

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Dragon Quest XI English Patcher  v'+VERSION)
        self.geometry('700x760');self.minsize(620,600)
        self.q=queue.Queue();self.busy=False;self.exporting=None
        self.logbuf=[];self.runinfo={};self.settings=load_settings();self.t_start=0;self.phase=(0,1)
        pad=dict(padx=14,pady=4)
        # header: title + short help on the left, the Mage's Arcane Gazette logo on the right
        hdr=ttk.Frame(self);hdr.pack(fill='x',padx=14,pady=(10,0))
        self.logo=None
        for p in (res('logo.png'),Path(__file__).parent/'logo.png'):
            try:
                self.logo=tk.PhotoImage(file=str(p));break
            except Exception:pass
        if self.logo:ttk.Label(hdr,image=self.logo).pack(side='right',padx=(8,0))
        tf=ttk.Frame(hdr);tf.pack(side='left',fill='x',expand=True)
        ttk.Label(tf,text='Dragon Quest XI (3DS) - English Patch',font=('Segoe UI',14,'bold')).pack(anchor='w',pady=(6,0))
        ttk.Label(tf,text='Select your Japanese game file, choose where to save the English version, then press Patch.',
                  wraplength=520).pack(anchor='w',pady=(0,8))
        f1=ttk.LabelFrame(self,text='1. Game file (.cia or .3ds, decrypted)');f1.pack(fill='x',**pad)
        self.src=tk.StringVar()
        ttk.Entry(f1,textvariable=self.src).pack(side='left',fill='x',expand=True,padx=(8,4),pady=8)
        ttk.Button(f1,text='Browse...',command=self.pick_src).pack(side='right',padx=(4,8),pady=8)
        f2=ttk.LabelFrame(self,text='2. Save the patched file as');f2.pack(fill='x',**pad)
        # output format (only offered for a .3ds source: it can become a .3ds or an installable .cia)
        self.fmt=tk.StringVar(value='3ds')
        self.fmtframe=ttk.Frame(self)
        ttk.Label(self.fmtframe,text='Output format:').pack(side='left',padx=(2,8))
        ttk.Radiobutton(self.fmtframe,text='.3ds (emulator / cartridge dump)',variable=self.fmt,value='3ds',command=self.fmt_changed).pack(side='left',padx=4)
        ttk.Radiobutton(self.fmtframe,text='.cia (install on a 3DS with FBI)',variable=self.fmt,value='cia',command=self.fmt_changed).pack(side='left',padx=4)
        self.f2=f2;self.pad=pad
        self.dst=tk.StringVar()
        ttk.Entry(f2,textvariable=self.dst).pack(side='left',fill='x',expand=True,padx=(8,4),pady=8)
        ttk.Button(f2,text='Browse...',command=self.pick_dst).pack(side='right',padx=(4,8),pady=8)
        # buttons that matter are all in this top row so they are always visible (Report a problem / diagnostics included)
        bf=ttk.Frame(self);bf.pack(pady=(6,4))
        self.btn=ttk.Button(bf,text='Patch',command=self.start);self.btn.pack(side='left',padx=5,ipadx=22,ipady=4)
        self.btn_open=ttk.Button(bf,text='Open output folder',command=self.open_out,state='disabled');self.btn_open.pack(side='left',padx=5,ipady=4)
        ttk.Button(bf,text='Report a problem...',command=self.report).pack(side='left',padx=5,ipady=4)
        ttk.Button(bf,text='Copy diagnostics',command=self.copy_diag).pack(side='left',padx=5,ipady=4)
        # update folders are paused: the button object stays (the code paths use it) but is not shown
        self.btn2=ttk.Button(bf,text='Create update folder',command=self.start_export)
        if not UPDATE_FOLDERS:self.btn2.config(state='disabled')
        else:self.btn2.pack(side='left',padx=5,ipady=4)
        self.verify=tk.BooleanVar(value=True)
        ttk.Checkbutton(self,text='Check the new file when it is done (recommended, takes about a minute)',variable=self.verify).pack(anchor='w',padx=18)
        self.bar=ttk.Progressbar(self,mode='determinate',maximum=100);self.bar.pack(fill='x',padx=14)
        self.prog_lbl=ttk.Label(self,text='');self.prog_lbl.pack(anchor='w',padx=16)
        # the bottom area (project link and log) is packed from the bottom BEFORE the patch notes, so a small screen
        # shrinks the notes instead of pushing the log and the link out of the window
        url=REPO
        link=tk.Label(self,text='Project page / downloads / bug reports:  '+url.replace('https://',''),fg='#1a4f9c',cursor='hand2',
                      font=('Segoe UI',9,'underline'))
        link.pack(side='bottom',pady=(0,8))
        def open_link(_e=None):
            try:
                import webbrowser;webbrowser.open(url)
            except Exception:pass
        link.bind('<Button-1>',open_link)
        self.log=tk.Text(self,height=5,state='disabled',wrap='word',font='TkFixedFont');self.log.pack(side='bottom',fill='x',padx=14,pady=(6,6))
        ttk.Label(self,text='Installing a new full game (.cia / .3ds) on a 3DS? Delete any old update folder from the SD card first: '
                  'SD:/luma/titles/0004000000199200. Old files left there override the new install.',
                  wraplength=630,foreground='#a33a00').pack(anchor='w',padx=14,pady=(6,0))
        ttk.Label(self,text='This is version %s. Because the patch changes often, the best results come from making a NEW full patched .cia/.3ds and installing it each time. '
                  'Update (Luma) folders are turned off for now and will come back in a future patch once the game is more stable.'%VERSION,
                  wraplength=630,foreground='#1a4f9c').pack(anchor='w',padx=14,pady=(6,0))
        ttk.Label(self,text='Playing a save from 0.1.17 - 0.1.20? Veronica and Sylvando were saved with names that the new game draws wrongly (stray symbol or wrong letters; crashes reported mostly on Old 3DS). '
                  'Use the separate "DQXI_3DS_Save_Repair" download (same GitHub page) on a copy of your save to fix it, then play with a game patched with 0.1.21 or newer. New games started with 0.1.21 do not need it.',
                  wraplength=630,foreground='#a33a00').pack(anchor='w',padx=14,pady=(6,0))
        nf=ttk.LabelFrame(self,text="What's new (patch notes)");nf.pack(fill='both',expand=True,padx=14,pady=(6,0))
        sb=ttk.Scrollbar(nf,orient='vertical')
        self.notes=tk.Text(nf,height=6,wrap='word',font=('Segoe UI',10),yscrollcommand=sb.set,padx=8,pady=6,spacing1=2,spacing3=2)
        sb.config(command=self.notes.yview);sb.pack(side='right',fill='y');self.notes.pack(side='left',fill='both',expand=True,padx=(6,0),pady=6)
        self.render_notes(load_notes());self.notes.config(state='disabled')
        ls=self.settings.get('last_src')
        if ls and Path(ls).is_file():self.set_src(ls)          # remember the last game file and output folder
        self.after(150,self.poll)
    def render_notes(self,text):
        """Reflow the plain-text changelog: version headings stand out, bullets get a hanging indent and the
        hard line breaks inside a bullet are joined so the text wraps to whatever width the window has."""
        t=self.notes
        t.tag_configure('title',font=('Segoe UI',11,'bold'))
        t.tag_configure('ver',font=('Segoe UI',11,'bold'),foreground='#1a4f9c',spacing1=12,spacing3=3)
        t.tag_configure('bul',lmargin1=10,lmargin2=26,spacing1=3)
        import re
        items=[]   # (kind,text)
        for ln in text.splitlines():
            s=ln.rstrip()
            if not s.strip() or set(s.strip())=={'='}:continue
            if re.match(r'^\d+\.\d+\.\d+',s.strip()) and not s.startswith(' '):items.append(('ver',s.strip()))
            elif s.lstrip().startswith('* '):items.append(('bul','\u2022 '+s.lstrip()[2:]))
            elif items and items[-1][0]=='bul' and s.startswith(' '):items[-1]=('bul',items[-1][1]+' '+s.strip())
            else:items.append(('title' if not items else 'bul',s.strip()))
        for i,(k,s) in enumerate(items):
            t.insert('end',s+'\n',k)
    # ---- helpers
    def say(self,msg):
        self.logbuf.append(str(msg));self.q.put(('log',str(msg)))
    def diag_text(self):
        """a short, shareable description of this run (no user name or folder paths)"""
        import platform
        info=cia_patcher.read_patch_header(res('dqxi_en.dqp'))
        ri=self.runinfo
        lines=['DQXI English Patcher diagnostics',
               'Patcher version: %s   patch data: v%s (built %s, %s files)'%(VERSION,info.get('version','?'),info.get('built','?'),info.get('files','?')),
               'System: %s, Python %s%s, window library: %s'%(platform.platform(),platform.python_version(),' (exe)' if getattr(sys,'frozen',False) else '','yes' if HAVE_TK else 'no')]
        if ri:
            lines.append('Input: %s (%s, %.2f GB)   output: %s   check after patching: %s'%(ri.get('src','?'),ri.get('srcext','?'),ri.get('srcsize',0)/1e9,ri.get('dstext','?'),'on' if ri.get('verify') else 'off'))
            lines.append('Output drive: %s free, file system %s'%('%.1f GB'%(ri['free']/1e9) if 'free' in ri else '?',ri.get('fs') or 'unknown'))
            if 'rc' in ri:lines.append('Result code: %s   time: %s s'%(ri['rc'],ri.get('secs','?')))
        else:lines.append('(no patch has been run yet)')
        lines+=['','Log:']+self.logbuf[-60:]
        return redact('\n'.join(lines))
    def copy_diag(self):
        try:
            self.clipboard_clear();self.clipboard_append(self.diag_text());self.update()
            messagebox.showinfo('Copied','The diagnostics were copied. Paste them into your bug report.\n(They contain no user name or folder paths.)')
        except Exception as e:messagebox.showerror('Could not copy',str(e))
    def report(self):
        try:
            self.clipboard_clear();self.clipboard_append(self.diag_text());self.update()
        except Exception:pass
        messagebox.showinfo('Report a problem','The diagnostics were copied to your clipboard.\n\n'
            'Your browser will open the issue page - paste them there (Ctrl+V) and add a screenshot, the 2D/3D mode and where in the game it happened.\n\n'
            'You can also ask on Discord: '+DISCORD.replace('https://',''))
        try:
            import webbrowser;webbrowser.open(REPO+'/issues/new')
        except Exception:pass
    def done_text(self):
        """what to do with the finished file (short steps; differs for .cia and .3ds)"""
        d=self.dst.get()
        stamp='On the title screen look for  "English patch v%s"  under the logo - that confirms you are on this version.'%VERSION
        if d.lower().endswith('.cia'):
            steps=('1. FIRST delete the old update folder on your SD card, if you ever had one:\n'
                   '    SD:/luma/titles/0004000000199200\n'
                   '    (files left there override the new game and some text stays Japanese).\n'
                   '2. Copy the .cia to your SD card and install it with FBI (Files > SD > the .cia > Install).\n'
                   '3. Start the game from the HOME menu. Your saves carry over - back them up first to be safe.\n')
        else:
            steps=('1. Emulators (Azahar / Citra): open the .3ds. If you used a mods or load folder for this game before,\n'
                   '    delete it (load/mods/0004000000199200) so old files do not override the new game.\n'
                   '2. Real 3DS: use the .cia format instead (or a flashcart that runs decrypted .3ds files).\n')
        return 'The English game was created:\n\n'+d+'\n\n'+steps+'\n'+stamp+'\n\nProblems? Use "Report a problem..." in this window.'
    def save_log(self,dst):
        """patch log next to the output (kept on failure too, so it can be attached to a bug report)"""
        try:
            Path(str(dst)).with_name(Path(str(dst)).stem+' - patch log.txt').write_text(self.diag_text(),encoding='utf-8')
        except Exception:pass
    def poll(self):
        try:
            while True:
                k,v=self.q.get_nowait()
                if k=='log':
                    self.log.config(state='normal');self.log.insert('end',v+'\n');self.log.see('end');self.log.config(state='disabled')
                elif k=='prog':
                    frac,label=v
                    el=time.time()-self.t_start
                    eta='' if (frac<0.04 or el<4) else '  -  about %s left'%fmt_secs(el*(1-frac)/frac)
                    self.bar.config(value=100*frac);self.prog_lbl.config(text='%s  -  %d%%%s'%(label,int(100*frac),eta))
                elif k=='done':
                    self.busy=False;self.bar.stop();self.bar.config(value=100 if v==0 else 0);self.btn.config(state='normal');self.btn2.config(state='normal' if UPDATE_FOLDERS else 'disabled')
                    self.prog_lbl.config(text='Done - finished in %s.'%fmt_secs(time.time()-self.t_start) if v==0 else 'Stopped - see the log.')
                    if v==0 and not self.exporting:self.btn_open.config(state='normal')
                    if v==0 and self.exporting:messagebox.showinfo('Done','The update folder was created:\n\n'+self.exporting+'\n\nCopy its "luma" folder to the root of your 3DS SD card (see the README).')
                    elif v==0:messagebox.showinfo('Done',self.done_text())
                    elif v==-1:messagebox.showerror('Error','Something went wrong - see the log for details.')
                    elif v==3:messagebox.showwarning('Not the original game','This file does not match the original Japanese game that the patch was made for (a different game revision or a modified dump).\n\nUse an unmodified, decrypted dump of the Japanese game. Details are in the log.')
                    elif v==4:messagebox.showwarning('Not the Japanese game','This is not the Japanese Dragon Quest XI.\n\nThe patch only works on the Japanese 3DS game (title ID 0004000000199200). A different region, a demo or another game cannot be patched.')
                    elif v==5:messagebox.showwarning('Already patched','This file looks like it is ALREADY PATCHED (by this or an older version).\n\nPatch your original, unpatched Japanese dump instead - a patched game cannot be patched again.')
                    elif v==6:messagebox.showerror('Check failed','The new file did not pass the check, so it was deleted. Please try again, and if it happens again use "Report a problem..." and attach the diagnostics.')
                    else:messagebox.showwarning('Could not patch','The file could not be patched - see the log for details.')
        except queue.Empty:pass
        self.after(150,self.poll)
    def pick_src(self):
        init=self.settings.get('last_src_dir')
        p=filedialog.askopenfilename(title='Select your Dragon Quest XI .cia or .3ds',filetypes=[('3DS game','*.cia *.3ds *.cci'),('All files','*.*')],
                                     initialdir=init if init and Path(init).is_dir() else None)
        if p:self.set_src(p)
    def set_src(self,p):
        self.src.set(p)
        is3ds=Path(p).suffix.lower() in ('.3ds','.cci')
        if is3ds:
            self.fmtframe.pack(fill='x',before=self.f2,**self.pad)
            self.fmt.set(self.settings.get('fmt','3ds') if self.settings.get('fmt') in ('3ds','cia') else '3ds')
        else:
            self.fmtframe.pack_forget();self.fmt.set('cia')
        dd=self.settings.get('last_dst_dir')
        # the output goes where the last one went (or next to the game file the first time)
        self.dst.set(str((Path(dd) if dd and Path(dd).is_dir() else Path(p).parent)/autoname(self.out_ext())))
        self.settings['last_src_dir']=str(Path(p).parent);self.settings['last_src']=p;save_settings(self.settings)
    def open_out(self):
        p=Path(self.dst.get().strip().strip('"'))
        try:
            if os.name=='nt':
                if p.exists():subprocess.Popen(['explorer','/select,'+str(p)])
                else:os.startfile(str(p.parent))
            elif sys.platform=='darwin':subprocess.Popen(['open','-R',str(p)] if p.exists() else ['open',str(p.parent)])
            else:subprocess.Popen(['xdg-open',str(p.parent)])
        except Exception as e:messagebox.showerror('Could not open the folder',str(e))
    def out_ext(self):
        return '.cia' if self.fmt.get()=='cia' else '.3ds'
    def fmt_changed(self):
        d=self.dst.get().strip()
        if d:self.dst.set(str(Path(d).with_suffix(self.out_ext())))
    def pick_dst(self):
        ext=self.out_ext()
        init=Path(self.dst.get()) if self.dst.get() else None
        p=filedialog.asksaveasfilename(title='Save the English game as',defaultextension=ext,
              initialfile=autoname(ext),initialdir=str(init.parent) if init else self.settings.get('last_dst_dir'),
              filetypes=[('3DS game','*'+ext)])
        if p:
            self.dst.set(p);self.settings['last_dst_dir']=str(Path(p).parent);save_settings(self.settings)
    def start(self):
        if self.busy:return
        s=Path(self.src.get().strip().strip('"'));d=Path(self.dst.get().strip().strip('"'))
        if not s.is_file():messagebox.showerror('Missing file','Please select your Dragon Quest XI .cia or .3ds file.');return
        if not self.dst.get().strip():messagebox.showerror('Missing location','Please choose where to save the patched file.');return
        if s.suffix.lower()=='.cia':self.fmt.set('cia')
        if d.suffix.lower()!=self.out_ext():d=d.with_suffix(self.out_ext())
        if d.resolve()==s.resolve():messagebox.showerror('Same file','Choose a different location or name than the original file.');return
        try:
            d.parent.mkdir(parents=True,exist_ok=True)
            need=s.stat().st_size+(300<<20)
            free=shutil.disk_usage(d.parent).free
            if free<need and not messagebox.askyesno('Low disk space','There may not be enough free space (about %.1f GB needed). Continue anyway?'%(need/1e9)):return
            fs=fs_name(d.parent)
            if self.out_ext()=='.3ds' and fs.upper()=='FAT32':
                messagebox.showerror('This drive cannot hold the file','The patched .3ds is 4 GB, but this drive is formatted as FAT32 (largest file 4 GB minus 1 byte).\n\nSave it on another drive, or choose the .cia format (about 2.8 GB).');return
            self.runinfo=dict(src=s.name,srcext=s.suffix.lower(),srcsize=s.stat().st_size,dstext=self.out_ext(),verify=self.verify.get(),free=free,fs=fs)
        except Exception as e:
            messagebox.showerror('Location error',str(e));return
        if d.exists() and not messagebox.askyesno('Replace file','"%s" already exists. Replace it?'%d.name):return
        self.dst.set(str(d))
        self.settings['last_dst_dir']=str(d.parent);self.settings['fmt']=self.out_ext().lstrip('.');save_settings(self.settings)
        self.btn_open.config(state='disabled');self.t_start=time.time();self.phase=(0.0,0.88 if self.verify.get() else 1.0)
        self.bar.config(value=0);self.prog_lbl.config(text='Starting ...')
        self.exporting=None
        self.busy=True;self.btn.config(state='disabled');self.btn2.config(state='disabled')
        self.log.config(state='normal');self.log.delete('1.0','end');self.log.config(state='disabled');self.logbuf=[]
        threading.Thread(target=self.work,args=(str(s),str(d)),daemon=True).start()
    def start_export(self):
        if self.busy or not UPDATE_FOLDERS:return
        s=Path(self.src.get().strip().strip('"'))
        if not s.is_file():messagebox.showerror('Missing file','Please select your original (decrypted) Japanese .cia or .3ds file in step 1 first.');return
        o=filedialog.askdirectory(title='Where should the update folder be created?',initialdir=str(s.parent))
        if not o:return
        self.exporting=str(Path(o)/'DQXI_English_Update')
        self.busy=True;self.btn.config(state='disabled');self.btn2.config(state='disabled');self.t_start=time.time()
        self.log.config(state='normal');self.log.delete('1.0','end');self.log.config(state='disabled')
        threading.Thread(target=self.work_export,args=(str(s),self.exporting),daemon=True).start()
    def work_export(self,s,out):
        t0=time.time()
        try:
            self.say('Reading %s ...'%Path(s).name)
            rc=cia_patcher.patch(s,None,str(res('dqxi_en.dqp')),str(res('code_layered.ips')),log=self.say,export_dir=out)
            if rc==0:self.say('Finished in %d seconds.'%(time.time()-t0))
            self.q.put(('done',rc))
        except Exception as e:
            self.say('ERROR: %s'%e);self.say(traceback.format_exc());self.q.put(('done',-1))
    def work(self,s,d):
        t0=time.time()
        try:
            self.say('Reading %s ...'%Path(s).name)
            hi=0.88 if self.runinfo.get('verify') else 1.0
            def mk(lo,hi_):
                return lambda x,label='':self.q.put(('prog',(lo+(hi_-lo)*max(0.0,min(1.0,x)),label)))
            rc=cia_patcher.patch(s,d,str(res('dqxi_en.dqp')),str(res('code.ips')),log=self.say,progress=mk(0.0,hi))
            if rc==0 and self.runinfo.get('verify'):
                self.say('Checking the new file (about a minute) ...')
                if not cia_patcher.verify_output(d,str(res('dqxi_en.dqp')),log=self.say,progress=mk(hi,1.0)):
                    self.say('The new file did not pass the check and was deleted. Please try again.');rc=6
            if rc==0:self.say('Finished in %d seconds.'%(time.time()-t0))
            elif rc==2:
                self.say('')
                self.say('This file has to be DECRYPTED first (one-time step).')
                self.say('See the README: GodMode9 > select the file > "CIA/NCSD image options" > "Decrypt file (SD output)".')
            if rc!=0:
                try:
                    if Path(d).exists():Path(d).unlink()
                except Exception:pass
            self.runinfo.update(rc=rc,secs=int(time.time()-t0));self.save_log(d)
            self.q.put(('done',rc))
        except Exception as e:
            self.say('ERROR: %s'%e);self.say(traceback.format_exc())
            try:
                if Path(d).exists():Path(d).unlink()
            except Exception:pass
            self.runinfo.update(rc=-1,secs=int(time.time()-t0));self.save_log(d)
            self.q.put(('done',-1))

def cli(argv):
    """Command line (no window needed): <input> [<output>] [--cia] [--export <folder>]
    The output follows the input (.3ds -> .3ds, .cia -> .cia); --cia turns a .3ds into an installable .cia."""
    flags=[a for a in argv if a.startswith('--')]
    args=[a for a in argv if not a.startswith('--')]
    if sys.stdout is None:     # windowed .exe has no console: write the log next to the output instead
        lf=open(str(Path(args[1] if len(args)>1 else args[0]).with_suffix('.log')),'w',encoding='utf-8')
        print=lambda m:(lf.write(str(m)+'\n'),lf.flush())
    else:
        import builtins;print=builtins.print
    if not args or not os.path.exists(args[0]):
        print('Game file not found: %s'%(args[0] if args else '(none given)'))
        return 2
    if '--export' in argv and not UPDATE_FOLDERS:
        print('Update folders are turned off in this version. Make a full patched .cia/.3ds instead.')
        return 2
    if '--export' in argv:
        i=argv.index('--export');out=argv[i+1] if i+1<len(argv) else 'dqxi_update'
        args=[a for a in args if a!=out][:1]
        return cia_patcher.patch(args[0],None,str(res('dqxi_en.dqp')),str(res('code_layered.ips')),export_dir=out,log=print)
    src=args[0]
    if len(args)>1:
        dst=args[1]
    else:
        want_cia='--cia' in flags or Path(src).suffix.lower()=='.cia'
        dst=str(Path(src).with_name('Dragon Quest XI - Echoes of an Elusive Age'+('.cia' if want_cia else ' (English).3ds')))
    rc=cia_patcher.patch(src,dst,str(res('dqxi_en.dqp')),str(res('code.ips')),log=print)
    if rc==0 and '--no-verify' not in flags:
        print('Checking the new file (about a minute) ...')
        if not cia_patcher.verify_output(dst,str(res('dqxi_en.dqp')),log=print):
            print('The new file did not pass the check - do not install it. Please try again or report the problem.');rc=6
    return rc

if __name__=='__main__':
    if len(sys.argv)>=2:
        sys.exit(cli(sys.argv[1:]))
    if not HAVE_TK:
        print('The window needs Python\'s tkinter (Debian/Ubuntu: sudo apt install python3-tk; Arch: sudo pacman -S tk).')
        print('You can also run without it:  python3 DQXIEnglishPatcher.py "game.3ds"     (writes "... (English).3ds")')
        print('                              python3 DQXIEnglishPatcher.py "game.cia" "out.cia"')
        sys.exit(1)
    App().mainloop()


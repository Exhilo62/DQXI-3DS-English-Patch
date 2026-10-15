#!/usr/bin/env python3
"""Dragon Quest XI (3DS) English Patcher - simple GUI around cia_patcher."""
import os,sys,threading,queue,shutil,time,traceback
from pathlib import Path
import tkinter as tk
from tkinter import ttk,filedialog,messagebox

def res(name):
    base=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
    return base/name
sys.path.insert(0,str(Path(__file__).parent))
import cia_patcher

VERSION='?'
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
AUTONAME='Dragon Quest XI - Echoes of an Elusive Age'
def autoname(ext):
    # the .cia keeps the shorter name (easier to read in FBI / HOME menu lists)
    return AUTONAME+('' if ext=='.cia' else ' (English)')+ext

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Dragon Quest XI English Patcher  v'+VERSION)
        self.geometry('680x720');self.minsize(600,620)
        self.q=queue.Queue();self.busy=False;self.exporting=None
        pad=dict(padx=14,pady=4)
        ttk.Label(self,text='Dragon Quest XI (3DS) - English Patch',font=('Segoe UI',14,'bold')).pack(anchor='w',padx=14,pady=(12,0))
        ttk.Label(self,text='Select your Japanese game file, choose where to save the English version, then press Patch.',
                  wraplength=600).pack(anchor='w',padx=14,pady=(0,8))
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
        bf=ttk.Frame(self);bf.pack(pady=8)
        self.btn=ttk.Button(bf,text='Patch',command=self.start);self.btn.pack(side='left',padx=6,ipadx=24,ipady=4)
        self.btn2=ttk.Button(bf,text='Create update folder (already patched game)',command=self.start_export);self.btn2.pack(side='left',padx=6,ipady=4)
        self.bar=ttk.Progressbar(self,mode='indeterminate');self.bar.pack(fill='x',padx=14)
        # patch notes (CHANGELOG.txt shipped next to the tool) and the progress log
        nf=ttk.LabelFrame(self,text="What's new (patch notes)");nf.pack(fill='both',expand=True,padx=14,pady=(8,0))
        sb=ttk.Scrollbar(nf,orient='vertical')
        self.notes=tk.Text(nf,height=11,wrap='word',font=('Segoe UI',10),yscrollcommand=sb.set,padx=8,pady=6,spacing1=2,spacing3=2)
        sb.config(command=self.notes.yview);sb.pack(side='right',fill='y');self.notes.pack(side='left',fill='both',expand=True,padx=(6,0),pady=6)
        self.render_notes(load_notes());self.notes.config(state='disabled')
        self.log=tk.Text(self,height=6,state='disabled',wrap='word',font='TkFixedFont');self.log.pack(fill='x',padx=14,pady=(8,12))
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
            elif s.lstrip().startswith('* '):items.append(('bul','• '+s.lstrip()[2:]))
            elif items and items[-1][0]=='bul' and s.startswith(' '):items[-1]=('bul',items[-1][1]+' '+s.strip())
            else:items.append(('title' if not items else 'bul',s.strip()))
        for i,(k,s) in enumerate(items):
            t.insert('end',s+'\n',k)
    # ---- helpers
    def say(self,msg):self.q.put(('log',str(msg)))
    def poll(self):
        try:
            while True:
                k,v=self.q.get_nowait()
                if k=='log':
                    self.log.config(state='normal');self.log.insert('end',v+'\n');self.log.see('end');self.log.config(state='disabled')
                elif k=='done':
                    self.busy=False;self.bar.stop();self.btn.config(state='normal');self.btn2.config(state='normal')
                    if v==0 and self.exporting:messagebox.showinfo('Done','The update folder was created:\n\n'+self.exporting+'\n\nCopy its "luma" folder to the root of your 3DS SD card (see the README).')
                    elif v==0:messagebox.showinfo('Done','The English game was created:\n\n'+self.dst.get())
                    elif v==-1:messagebox.showerror('Error','Something went wrong - see the log for details.')
                    else:messagebox.showwarning('Could not patch','The file could not be patched - see the log for details.')
        except queue.Empty:pass
        self.after(150,self.poll)
    def pick_src(self):
        p=filedialog.askopenfilename(title='Select your Dragon Quest XI .cia or .3ds',filetypes=[('3DS game','*.cia *.3ds *.cci'),('All files','*.*')])
        if p:
            self.src.set(p)
            is3ds=Path(p).suffix.lower() in ('.3ds','.cci')
            if is3ds:
                self.fmtframe.pack(fill='x',before=self.f2,**self.pad)
                self.fmt.set('3ds')
            else:
                self.fmtframe.pack_forget();self.fmt.set('cia')
            self.dst.set(str(Path(p).with_name(autoname(self.out_ext()))))
    def out_ext(self):
        return '.cia' if self.fmt.get()=='cia' else '.3ds'
    def fmt_changed(self):
        d=self.dst.get().strip()
        if d:self.dst.set(str(Path(d).with_suffix(self.out_ext())))
    def pick_dst(self):
        ext=self.out_ext()
        init=Path(self.dst.get()) if self.dst.get() else None
        p=filedialog.asksaveasfilename(title='Save the English game as',defaultextension=ext,
              initialfile=autoname(ext),initialdir=str(init.parent) if init else None,
              filetypes=[('3DS game','*'+ext)])
        if p:self.dst.set(p)
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
        except Exception as e:
            messagebox.showerror('Location error',str(e));return
        if d.exists() and not messagebox.askyesno('Replace file','"%s" already exists. Replace it?'%d.name):return
        self.dst.set(str(d))
        self.exporting=None
        self.busy=True;self.btn.config(state='disabled');self.btn2.config(state='disabled');self.bar.start(12)
        self.log.config(state='normal');self.log.delete('1.0','end');self.log.config(state='disabled')
        threading.Thread(target=self.work,args=(str(s),str(d)),daemon=True).start()
    def start_export(self):
        if self.busy:return
        s=Path(self.src.get().strip().strip('"'))
        if not s.is_file():messagebox.showerror('Missing file','Please select your original (decrypted) Japanese .cia or .3ds file in step 1 first.');return
        o=filedialog.askdirectory(title='Where should the update folder be created?',initialdir=str(s.parent))
        if not o:return
        self.exporting=str(Path(o)/'DQXI_English_Update')
        self.busy=True;self.btn.config(state='disabled');self.btn2.config(state='disabled');self.bar.start(12)
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
            rc=cia_patcher.patch(s,d,str(res('dqxi_en.dqp')),str(res('code.ips')),log=self.say)
            if rc==0:self.say('Finished in %d seconds.'%(time.time()-t0))
            elif rc==2:
                self.say('')
                self.say('This file has to be DECRYPTED first (one-time step).')
                self.say('See the README: GodMode9 > select the file > "CIA/NCSD image options" > "Decrypt file (SD output)".')
            if rc!=0:
                try:
                    if Path(d).exists():Path(d).unlink()
                except Exception:pass
            self.q.put(('done',rc))
        except Exception as e:
            self.say('ERROR: %s'%e);self.say(traceback.format_exc())
            try:
                if Path(d).exists():Path(d).unlink()
            except Exception:pass
            self.q.put(('done',-1))

if __name__=='__main__':
    if len(sys.argv)>=3:        # headless: DQXIEnglishPatcher.exe <input> <output>
        logf=open(str(Path(sys.argv[2]).with_suffix('.log')),'w',encoding='utf-8')
        rc=cia_patcher.patch(sys.argv[1],sys.argv[2],str(res('dqxi_en.dqp')),str(res('code.ips')),log=lambda m:(logf.write(str(m)+'\n'),logf.flush()))
        sys.exit(rc)
    App().mainloop()

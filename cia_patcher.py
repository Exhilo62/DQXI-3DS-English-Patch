#!/usr/bin/env python3
"""Dragon Quest XI (3DS, JP) English patch - CIA patcher.

Usage:  python cia_patcher.py <decrypted game.cia> [output.cia]

Takes a *decrypted* CIA of the Japanese game, applies the English patch and writes a new,
installable CIA (decrypted, install with FBI on a CFW console with signature patches).
Standard library only. The input file is never modified.
"""
import sys,os,struct,hashlib,json,zlib,time
from pathlib import Path
HERE=Path(__file__).parent
sys.path.insert(0,str(HERE))
from dqxi_blz import decompress
from dqxi_en_patcher import bspatch,base_of

MU=0x200
def al(x,a):return (x+a-1)//a*a
def u32(b,o):return struct.unpack_from('<I',b,o)[0]
def u64(b,o):return struct.unpack_from('<Q',b,o)[0]

class CIA:
    def __init__(self,f):
        self.f=f
        h=self.rd(0,0x2020)
        self.hs,_,_,self.cc,self.tk,self.tmd,self.meta,self.cs=struct.unpack_from('<IHHIIIIQ',h,0)
        a=lambda x:al(x,0x40)
        self.o_cert=a(self.hs);self.o_tik=self.o_cert+a(self.cc);self.o_tmd=self.o_tik+a(self.tk)
        self.o_cont=self.o_tmd+a(self.tmd);self.o_meta=self.o_cont+a(self.cs)
        self.tmd_b=self.rd(self.o_tmd,self.tmd)
        sig=struct.unpack_from('>I',self.tmd_b,0)[0]
        sl={0x10000:0x200,0x10001:0x100,0x10002:0x3c,0x10003:0x200,0x10004:0x100,0x10005:0x3c}[sig]
        self.tb=al(4+sl,0x40)           # TMD header offset
        self.nc=struct.unpack_from('>H',self.tmd_b,self.tb+0x9e)[0]
        self.chunks=[]
        pos=self.o_cont
        for i in range(self.nc):
            r=self.tb+0x9c4+0x30*i
            cid,idx,typ,size=struct.unpack_from('>IHHQ',self.tmd_b,r)
            self.chunks.append(dict(rec=r,id=cid,idx=idx,type=typ,size=size,off=pos,hash=self.tmd_b[r+16:r+48]))
            pos+=size
    def rd(self,o,n):
        self.f.seek(o);return self.f.read(n)

class Ncch:
    """read access to a decrypted NCCH living at file offset `base` of file `f`"""
    def __init__(self,f,base,size):
        self.f=f;self.base=base;self.size=size
        self.hdr=self.rd(0,0x200)
        assert self.hdr[0x100:0x104]==b'NCCH','not an NCCH'
        self.flags=self.hdr[0x188:0x190]
        self.exh_size=u32(self.hdr,0x180)
        self.exefs_off=u32(self.hdr,0x1a0)*MU;self.exefs_size=u32(self.hdr,0x1a4)*MU
        self.romfs_off=u32(self.hdr,0x1b0)*MU;self.romfs_size=u32(self.hdr,0x1b4)*MU
    def rd(self,o,n):
        self.f.seek(self.base+o);return self.f.read(n)
    @property
    def decrypted(self):return bool(self.flags[7]&4)

class RomFS:
    def __init__(self,nc):
        self.nc=nc;self.off=nc.romfs_off
        h=nc.rd(self.off,0x60)
        assert h[:4]==b'IVFC'
        self.master=u32(h,8)
        self.l3_size=u64(h,0x3c+8)
        self.l3_phys=al(0x60+self.master,0x1000)
        l3=self.off+self.l3_phys
        hd=nc.rd(l3,0x28)
        (self.hlen,self.dh_o,self.dh_s,self.dm_o,self.dm_s,self.fh_o,self.fh_s,self.fm_o,self.fm_s,self.data_o)=struct.unpack_from('<10I',hd,0)
        assert self.hlen==0x28
        self.tables=nc.rd(l3,self.data_o)
        self.files=[]       # dicts: path,meta_off,off,size
        dm=self.tables[self.dm_o:self.dm_o+self.dm_s];fm=self.tables[self.fm_o:self.fm_o+self.fm_s]
        def dname(o):
            par,sib,cd,cf,nh,nl=struct.unpack_from('<6I',dm,o);nm=dm[o+24:o+24+nl].decode('utf-16le')
            return par,nm
        def dpath(o):
            parts=[]
            while True:
                par,nm=dname(o)
                if o==0:break
                parts.append(nm);o=par
            return '/'.join(reversed(parts))
        cache={}
        p=0
        while p<len(fm):
            par,sib,doff,dsz,nh,nl=struct.unpack_from('<IIQQII',fm,p)
            nm=fm[p+0x20:p+0x20+nl].decode('utf-16le')
            if par not in cache:cache[par]=dpath(par)
            path=(cache[par]+'/'+nm) if cache[par] else nm
            self.files.append(dict(path=path,meta=p,off=doff,size=dsz))
            p+=0x20+al(nl,4)
        self.by_path={e['path']:e for e in self.files}
    def read(self,e):
        return self.nc.rd(self.off+self.l3_phys+self.data_o+e['off'],e['size'])

def apply_ips(code,ips):
    assert ips[:5]==b'PATCH'
    out=bytearray(code);p=5
    while ips[p:p+3]!=b'EOF':
        o=int.from_bytes(ips[p:p+3],'big');s=int.from_bytes(ips[p+3:p+5],'big');p+=5
        if s==0:
            rl=int.from_bytes(ips[p:p+2],'big');v=ips[p+2:p+3];p+=3
            if o+rl>len(out):out.extend(bytes(o+rl-len(out)))
            out[o:o+rl]=v*rl
        else:
            if o+s>len(out):out.extend(bytes(o+s-len(out)))
            out[o:o+s]=ips[p:p+s];p+=s
    return bytes(out)

def exefs_files(old):
    out={}
    for i in range(10):
        nm=old[i*16:i*16+8].rstrip(b'\0')
        if not nm:continue
        o,s=struct.unpack_from('<II',old,i*16+8)
        out[nm.decode()]=old[0x200+o:0x200+o+s]
    return out
def build_exefs(old,repl):
    """old: exefs bytes; repl: {name: new bytes} (e.g. '.code', 'banner', 'icon').
    Returns a new exefs (files re-aligned to 0x200, hashes redone)."""
    ents=[]
    for i in range(10):
        nm=old[i*16:i*16+8].rstrip(b'\0')
        if not nm:continue
        o,s=struct.unpack_from('<II',old,i*16+8)
        ents.append((nm,old[0x200+o:0x200+o+s]))
    ents=[(n,repl.get(n.decode(),d)) for n,d in ents]
    hdr=bytearray(0x200);body=bytearray()
    for i,(n,d) in enumerate(ents):
        struct.pack_into('<8sII',hdr,i*16,n,len(body),len(d))
        hdr[0xc0+0x20*(9-i):0xc0+0x20*(10-i)]=hashlib.sha256(d).digest()
        body+=d+bytes(al(len(d),0x200)-len(d))
    return bytes(hdr)+bytes(body)

class VCIA:
    """A CIA container built from templates (certificate chain, fake ticket, TMD, meta header) so a decrypted
    .3ds/.cci can be converted to an installable CIA.  Same attribute names as CIA."""
    def __init__(self,tpl,parts,icon):
        self.cia_header=bytes.fromhex(tpl['cia_header'])
        self.certs=bytes.fromhex(tpl['certs']);self.ticket=bytes.fromhex(tpl['ticket'])
        self.tmd_b=bytes.fromhex(tpl['tmd'])
        a=lambda x:al(x,0x40)
        self.hs,_,_,self.cc,self.tk,self.tmd,self.meta,self.cs=struct.unpack_from('<IHHIIIIQ',self.cia_header,0)
        assert (self.cc,self.tk,self.tmd)==(len(self.certs),len(self.ticket),len(self.tmd_b))
        self.o_cert=a(self.hs);self.o_tik=self.o_cert+a(self.cc);self.o_tmd=self.o_tik+a(self.tk)
        self.o_cont=self.o_tmd+a(self.tmd);self.o_meta=0   # meta is written after the contents (offset unknown here)
        sig=struct.unpack_from('>I',self.tmd_b,0)[0]
        sl={0x10000:0x200,0x10001:0x100,0x10002:0x3c,0x10003:0x200,0x10004:0x100,0x10005:0x3c}[sig]
        self.tb=al(4+sl,0x40)
        self.nc=struct.unpack_from('>H',self.tmd_b,self.tb+0x9e)[0]
        self.chunks=[]
        for i in range(self.nc):
            r=self.tb+0x9c4+0x30*i
            cid,idx,typ,size=struct.unpack_from('>IHHQ',self.tmd_b,r)
            off=parts[idx][0] if idx<len(parts) else 0    # contents index == .3ds partition index (0 exe, 1 manual)
            self.chunks.append(dict(rec=r,id=cid,idx=idx,type=typ,size=size,off=off,hash=self.tmd_b[r+16:r+48]))
        # meta: header (dependency list, core version) + the (new) SMDH icon
        mh=bytes.fromhex(tpl['meta_head']);ml=tpl['meta_len']
        self.meta_b=(mh+icon).ljust(ml,b'\0')[:ml]
        head=bytearray(self.cia_header)
        self.prefix=bytes(head[:self.hs]).ljust(a(self.hs),b'\0')+self.certs.ljust(a(self.cc),b'\0')+\
            self.ticket.ljust(a(self.tk),b'\0')+self.tmd_b.ljust(a(self.tmd),b'\0')
    def rd(self,o,n):
        if o==0 and n==self.o_cont:return self.prefix
        if n==self.meta:return self.meta_b
        return self.prefix[o:o+n]
def load_templates():
    base=Path(getattr(sys,'_MEIPASS',HERE))
    return json.loads(zlib.decompress((base/'cia_templates.bin').read_bytes()))

def patch(src,dst,patchfile,ips_file,keep_code=False,log=print,export_dir=None,progress=None):
    t0=time.time()
    def prog(x,label):
        if progress:progress(x,label)
    f=open(src,'rb')
    f.seek(0x100);ncsd=f.read(4)==b'NCSD'
    to_cia=Path(dst).suffix.lower()=='.cia' if dst else False
    if not ncsd and not to_cia and not export_dir:
        log('A .cia can only be patched to a .cia (choose a .cia output name).');return 2
    if ncsd:
        # ---- .3ds / .cci (NCSD) container
        sh=f.read(0)
        f.seek(0);nh0=f.read(0x4000)
        parts=[]
        for i in range(8):
            o,s=struct.unpack_from('<II',nh0,0x120+8*i)
            parts.append((o*MU,s*MU))
        c0=dict(off=parts[0][0],size=parts[0][1])
        cia=None
        f.seek(c0['off']);ncch_ok=f.read(0x200)[0x100:0x104]==b'NCCH'
        if not ncch_ok:
            log('This .3ds is not a readable game image (no NCCH header). It is probably encrypted, compressed (.z3ds)');log('or not a full cartridge dump. Use a decrypted .3ds/.cci, or decrypt it first with GodMode9.');return 2
        nc=Ncch(f,c0['off'],c0['size'])
        if not nc.decrypted:
            log('This .3ds is still encrypted. Decrypt it first (GodMode9: select the file ->');log('  "NCSD image options" -> "Decrypt file (SD output)"), or use a decrypted dump.');return 2
        for i,(o,s) in enumerate(parts[1:],1):
            if s:
                f.seek(o);hd=f.read(0x200)
                if hd[0x100:0x104]==b'NCCH' and not hd[0x188+7]&4:
                    log('Partition %d of this .3ds is still encrypted - decrypt the whole file first.'%i);return 2
    else:
        cia=CIA(f)
        c0=cia.chunks[0]
        f.seek(c0['off']);ncch_ok=f.read(0x200)[0x100:0x104]==b'NCCH'
        if not ncch_ok:
            log('This CIA is encrypted (its content is still locked with the title key), so it cannot be patched yet.')
            log('Decrypt it first with GodMode9: select the .cia -> "CIA image options" -> "Decrypt file (SD output)",')
            log('then patch the decrypted file it produces.');return 2
        nc=Ncch(f,c0['off'],c0['size'])
        if not nc.decrypted:
            log('This CIA is still encrypted (NCCH). Decrypt it first, e.g. with GodMode9:');log('  select the .cia -> "CIA image options" -> "Decrypt file (SD output)"');return 2
        for c in cia.chunks[1:]:
            f.seek(c['off']);hd=f.read(0x200)
            if hd[0x100:0x104]==b'NCCH' and not hd[0x188+7]&4:
                log('Content %d of this CIA (the manual) is still encrypted - the CIA was only partly decrypted.'%c['idx'])
                log('Decrypt the whole file with GodMode9 ("CIA image options" -> "Decrypt file (SD output)").');return 2
    pid=struct.unpack_from('<Q',nc.hdr,0x118)[0]
    if pid!=0x0004000000199200:
        log('This is not the Japanese Dragon Quest XI (its title ID is %016X).'%pid)
        log('The patch is made for the Japanese 3DS game "Dragon Quest XI: Sugi Sarishi Toki o Motomete" (title ID 0004000000199200).')
        log('Use your own dump of that game (a different region, a demo or another game cannot be patched).');return 4
    rfs=RomFS(nc)
    log('romfs files: %d'%len(rfs.files))
    # ---- payload
    if patchfile:
        data=zlib.decompress(Path(patchfile).read_bytes())
        assert data[:8]==b'DQXIENP1'
        hl=struct.unpack_from('<I',data,8)[0];hdr=json.loads(data[12:12+hl]);pos=12+hl
        log('English patch v%s (%s)'%(hdr.get('patch_version','?'),hdr.get('built','?')))
    else:
        hdr=dict(entries=[]);data=b'';pos=0
    repl={};exe_repl={}
    old_exefs=nc.rd(nc.exefs_off,nc.exefs_size)
    old_files=exefs_files(old_exefs)
    bad=0;already=0
    for _i,e in enumerate(hdr['entries']):
        if _i%25==0:prog(0.75*_i/max(1,len(hdr['entries'])),'Applying the patch to the game files')
        blob=data[pos:pos+e['len']];pos+=e['len']
        if e['path'].startswith('exefs:'):      # HOME-menu banner / icon (ExeFS files)
            name=e['path'][6:];raw=old_files.get(name)
            if raw is None or hashlib.sha256(raw).hexdigest()!=e['sha_orig']:
                log('MISMATCH (different game version?): '+e['path']);bad+=1;continue
            new=bspatch(raw,blob)
            if hashlib.sha256(new).hexdigest()!=e['sha_new']:log('VERIFY FAILED: '+e['path']);bad+=1;continue
            exe_repl[name]=new;continue
        if e['kind']=='new':new=zlib.decompress(blob)
        else:
            ent=rfs.by_path.get(e['path'])
            if ent is None:log('missing in your game: '+e['path']);bad+=1;continue
            raw=rfs.read(ent)
            rs=hashlib.sha256(raw).hexdigest()
            if rs!=e['sha_orig']:
                if rs==e['sha_new']:already+=1
                if bad<4:log('does not match the original game: '+e['path'])
                bad+=1;continue
            base=base_of(raw)
            new=base if e['kind']=='expand' else bspatch(base,blob)
        if hashlib.sha256(new).hexdigest()!=e['sha_new']:log('VERIFY FAILED: '+e['path']);bad+=1;continue
        repl[e['path']]=new
    if bad:
        log('%d file(s) do not match the original Japanese game; nothing was written.'%bad)
        if already or bad>=20:
            log('Most likely this file is ALREADY PATCHED (by this or an older version of the patch).')
            log('Patch your original, unpatched Japanese dump instead - a patched game cannot be patched again.');return 5
        log('This is not the original Japanese version the patch was made for (a different game revision or a modified dump).')
        log('Use an unmodified, decrypted dump of the Japanese game.');return 3
    log('patched files ready: %d (%.0fs)'%(len(repl),time.time()-t0))
    if export_dir:
        # update folder for an already patched game: only the changed romfs files + code.ips, loaded by LayeredFS
        tid=hdr.get('title_id','0004000000199200')
        root=Path(export_dir)/'luma'/'titles'/tid
        restore=[x for x in os.environ.get('DQXI_RESTORE_PREFIXES','').split(',') if x]     # diagnostics: write the ORIGINAL file for these prefixes
        for pth,new in sorted(repl.items()):
            if restore and any(pth.startswith(x) for x in restore):
                ent=rfs.by_path.get(pth)
                if ent is not None:new=rfs.read(ent)
            t=root/'romfs'/pth;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(new)
        if ips_file:
            (root/'code.ips').write_bytes(Path(ips_file).read_bytes())
        log('wrote %d files to %s (%.0fs)'%(len(repl),root,time.time()-t0))
        return 0
    # ---- exefs / code
    exh=bytearray(nc.rd(0x200,0x800))
    new_exefs=old_exefs;new_exh_hash=nc.hdr[0x160:0x180]
    if ips_file and not keep_code:
        code=old_files['.code']
        compressed=exh[0x0d]&1
        if compressed:code=decompress(code)
        code=apply_ips(code,Path(ips_file).read_bytes())
        exh[0x0d]&=0xfe                 # code is now stored uncompressed
        exe_repl['.code']=code
        new_exh_hash=hashlib.sha256(bytes(exh[:0x400])).digest()
        log('code patched (%d bytes)'%len(code))
    if exe_repl:
        new_exefs=build_exefs(old_exefs,exe_repl)
        if 'banner' in exe_repl:log('HOME menu banner/icon updated')
    # ---- new romfs layout
    order=sorted(rfs.files,key=lambda e:e['off'])
    cur=0;newoff={}
    for e in order:
        cur=al(cur,0x10);newoff[e['path']]=cur
        cur+=len(repl[e['path']]) if e['path'] in repl else e['size']
    l3_size=rfs.data_o+cur
    nb3=(l3_size+0xfff)//0x1000
    l2_size=nb3*32;nb2=(l2_size+0xfff)//0x1000
    l1_size=nb2*32;nb1=(l1_size+0xfff)//0x1000
    master=nb1*32
    l3_phys=al(0x60+master,0x1000)
    l1_phys=al(l3_phys+l3_size,0x1000)
    l2_phys=l1_phys+al(l1_size,0x1000)
    romfs_total=l2_phys+al(l2_size,0x1000)
    # ---- ncch layout
    exefs_off=nc.exefs_off
    exefs_size=len(new_exefs)
    romfs_off=al(exefs_off+exefs_size,0x1000)
    ncch_size=romfs_off+romfs_total
    # table updates
    tables=bytearray(rfs.tables)
    for e in rfs.files:
        struct.pack_into('<QQ',tables,rfs.fm_o+e['meta']+8,newoff[e['path']],len(repl[e['path']]) if e['path'] in repl else e['size'])
    # ---- write
    if ncsd and to_cia:
        cia=VCIA(load_templates(),parts,exe_repl.get('icon',old_files['icon']))
        for c in cia.chunks[1:]:
            if c['idx']<len(parts) and parts[c['idx']][1]:c['size']=parts[c['idx']][1]
    out=open(dst,'w+b')
    out.write(nh0[:c0['off']] if (ncsd and not to_cia) else cia.rd(0,cia.o_cont))
    # content 0
    c0_start=out.tell()
    hh=hashlib.sha256()
    def w(b):
        out.write(b);hh.update(b)
    nh=bytearray(nc.hdr)
    struct.pack_into('<I',nh,0x104,ncch_size//MU)
    struct.pack_into('<II',nh,0x1a0,exefs_off//MU,exefs_size//MU)
    struct.pack_into('<II',nh,0x1b0,romfs_off//MU,romfs_total//MU)
    nh[0x160:0x180]=new_exh_hash
    nh[0x1c0:0x1e0]=hashlib.sha256(new_exefs[:0x200]).digest()
    # romfs superblock hash filled after we know the first 0x1000 bytes
    romfs_head_pos=None
    w(bytes(nh))
    w(bytes(exh))
    w(nc.rd(0xa00,exefs_off-0xa00))            # plain region / logo padding
    w(new_exefs)
    w(bytes(romfs_off-(exefs_off+exefs_size)))
    romfs_start=out.tell()
    # romfs: header placeholder, level 3 stream
    out.write(bytes(0x1000));hh.update(bytes(0x1000))   # patched later (hash recomputed at end)
    l2=bytearray();blk=hashlib.sha256;buf=bytearray()
    def feed(b):
        nonlocal buf
        out.write(b);hh.update(b)
        buf+=b
        while len(buf)>=0x1000:
            l2.extend(blk(bytes(buf[:0x1000])).digest());del buf[:0x1000]
    feed(bytes(tables))
    pos=0
    src_base=nc.base+rfs.off+rfs.l3_phys+rfs.data_o
    for _k,e in enumerate(order):
        if _k%150==0:prog(0.75+0.2*_k/max(1,len(order)),'Writing the new game file')
        p=newoff[e['path']]
        if p>pos:feed(bytes(p-pos));pos=p
        if e['path'] in repl:
            b=repl[e['path']];feed(b);pos+=len(b)
        else:
            f.seek(src_base+e['off']);left=e['size']
            while left:
                ch=f.read(min(left,8<<20));feed(ch);left-=len(ch)
            pos+=e['size']
    prog(0.95,'Finishing the new game file')
    if buf:
        feed(bytes(0x1000-len(buf)))   # zero pad hashed block (also physical padding)
        # padding beyond l3_size is physical padding up to the 0x1000 boundary: already written
    assert len(l2)==nb3*32,(len(l2),nb3*32)
    # level 1 / level 2 (physical order: L1 then L2)
    l2b=bytes(l2)+bytes(al(l2_size,0x1000)-l2_size)
    l1=bytearray()
    for i in range(0,len(l2b),0x1000):l1.extend(blk(l2b[i:i+0x1000]).digest())
    assert len(l1)==nb2*32
    l1b=bytes(l1)+bytes(al(l1_size,0x1000)-l1_size)
    masterh=bytearray()
    for i in range(0,len(l1b),0x1000):masterh.extend(blk(l1b[i:i+0x1000]).digest())
    assert len(masterh)==master
    # padding between end of L3 data and L1_phys is already inside feed() zero pad; write L1, L2
    cur_pos=out.tell()-romfs_start
    assert cur_pos==al(l3_phys+l3_size,0x1000)==l1_phys,(hex(cur_pos),hex(l1_phys))
    w(l1b);w(l2b)
    assert out.tell()-romfs_start==romfs_total
    # ivfc header + master hash
    ivfc=bytearray(0x1000)
    ivfc[0:4]=b'IVFC';struct.pack_into('<II',ivfc,4,0x10000,master)
    l2_off=al(l1_size,0x1000);l3_off=l2_off+al(l2_size,0x1000)
    struct.pack_into('<QQII',ivfc,0x0c,0,l1_size,12,0)
    struct.pack_into('<QQII',ivfc,0x24,l2_off,l2_size,12,0)
    struct.pack_into('<QQII',ivfc,0x3c,l3_off,l3_size,12,0)
    struct.pack_into('<I',ivfc,0x54,0x5c)
    ivfc[0x60:0x60+master]=masterh
    out.seek(romfs_start);out.write(bytes(ivfc))
    # level-3 header sits at start of L3 (tables): offsets unchanged. Rewrite NCCH header with romfs hash
    region=al(0x60+master,MU)
    romfs_hash=hashlib.sha256(bytes(ivfc[:region])).digest()
    struct.pack_into('<I',nh,0x1b8,region//MU)
    nh[0x1e0:0x200]=romfs_hash
    out.seek(c0_start);out.write(bytes(nh))
    # content hash: recompute over the written range (file-backed streaming)
    out.flush()
    h2=hashlib.sha256();out.seek(c0_start);left=ncch_size
    while left:
        ch=out.read(min(left,16<<20));assert ch;h2.update(ch);left-=len(ch)
    c0_hash=h2.digest()
    assert out.tell()-c0_start==ncch_size
    out.seek(0,2)
    if ncsd and not to_cia:
        delta=ncch_size-c0['size']
        pos_end=c0['off']+ncch_size
        # remaining partitions keep their layout, shifted by delta
        for i,(o,s) in enumerate(parts[1:],1):
            if not s:continue
            gap=o-(parts[i-1][0]+parts[i-1][1]) if parts[i-1][1] else 0
            assert o+delta>=pos_end
            out.write(bytes(o+delta-pos_end));pos_end=o+delta
            f.seek(o);left=s
            while left:
                ch=f.read(min(left,16<<20));out.write(ch);left-=len(ch)
            pos_end+=s
        # keep the original image length (cartridge padding)
        f.seek(0,2);orig_len=f.tell()
        old_used=max(o+s for o,s in parts)
        padb=b'\xff'
        if old_used<orig_len:
            f.seek(old_used);padb=f.read(1)
        if pos_end<orig_len:
            left=orig_len-pos_end;chunk=padb*(1<<20)
            while left:
                n=min(left,1<<20);out.write(chunk[:n]);left-=n
        # NCSD header: sizes/offsets, image size, extended-header hash
        hd=bytearray(nh0[:0x4000])
        out.seek(0);cur_hdr=bytearray(out.read(0x4000))
        struct.pack_into('<I',cur_hdr,0x104,max(u32(cur_hdr,0x104),pos_end//MU))   # media size = cartridge capacity
        struct.pack_into('<II',cur_hdr,0x120,c0['off']//MU,ncch_size//MU)
        for i,(o,s) in enumerate(parts[1:],1):
            if s:struct.pack_into('<II',cur_hdr,0x120+8*i,(o+delta)//MU,s//MU)
        out.seek(0);out.write(bytes(cur_hdr));out.close()
        log('wrote %s (%.0f MB) in %.0fs'%(dst,os.path.getsize(dst)/1e6,time.time()-t0))
        return 0
    # remaining contents (manual etc.)
    total=ncch_size
    other_hash={}
    for c in cia.chunks[1:]:
        f.seek(c['off']);left=c['size'];hc=hashlib.sha256()
        while left:
            ch=f.read(min(left,16<<20));out.write(ch);hc.update(ch);left-=len(ch)
        other_hash[c['rec']]=(c['size'],hc.digest())
        total+=c['size']
    pad=al(total,0x40)-total
    out.write(bytes(pad))
    # meta
    if cia.meta:
        mb=bytearray(cia.rd(cia.o_meta,cia.meta))
        ic=exe_repl.get('icon')
        if ic and mb[0x400:0x404]==b'SMDH':        # keep the meta icon (shown by FBI) in step with the ExeFS icon
            mb[0x400:0x400+len(ic)]=ic
        out.write(bytes(mb))
    # TMD fix
    t=bytearray(cia.tmd_b)
    r=cia.chunks[0]['rec']
    struct.pack_into('>Q',t,r+8,ncch_size);t[r+16:r+48]=c0_hash
    for rr,(sz,hv) in other_hash.items():           # manual etc. (hash is unchanged for a CIA, new for a converted .3ds)
        struct.pack_into('>Q',t,rr+8,sz);t[rr+16:rr+48]=hv
    # content info record 0 hash over chunk records
    ci=cia.tb+0xc4
    cnt=struct.unpack_from('>H',t,ci+2)[0]
    t[ci+4:ci+36]=hashlib.sha256(bytes(t[cia.tb+0x9c4:cia.tb+0x9c4+0x30*cnt])).digest()
    t[cia.tb+0xa4:cia.tb+0xc4]=hashlib.sha256(bytes(t[ci:ci+0x24*64])).digest()
    out.seek(cia.o_tmd);out.write(bytes(t))
    # CIA header: content size
    out.seek(0x18);out.write(struct.pack('<Q',total))
    out.close()
    log('wrote %s (%.0f MB) in %.0fs'%(dst,os.path.getsize(dst)/1e6,time.time()-t0))
    return 0

def read_patch_header(patchfile):
    """patch version / date / file count of dqxi_en.dqp without decompressing the whole payload"""
    try:
        d=zlib.decompressobj();buf=d.decompress(Path(patchfile).read_bytes(),1<<21)
        if buf[:8]!=b'DQXIENP1':return {}
        hl=struct.unpack_from('<I',buf,8)[0];hdr=json.loads(buf[12:12+hl])
        return dict(version=hdr.get('patch_version','?'),built=hdr.get('built','?'),files=len(hdr.get('entries',[])))
    except Exception:
        return {}

def verify_output(dst,patchfile,log=print,progress=None):
    """Re-open the finished .cia/.3ds and check it: container hashes (TMD / NCCH / ExeFS / ExHeader / romfs hash tree) and that every
    patched file reads back with exactly the expected content. Returns True when everything is fine."""
    t0=time.time();ok=True
    def prog(x,label='Checking the new file'):
        if progress:progress(x,label)
    f=open(dst,'rb')
    try:
        f.seek(0x100)
        if f.read(4)==b'NCSD':
            f.seek(0x120);po,ps=struct.unpack('<II',f.read(8));c=dict(off=po*MU,size=ps*MU)
        else:
            cia=CIA(f);c=cia.chunks[0]
            h=hashlib.sha256();f.seek(c['off']);left=c['size']
            tot=max(1,c['size'])
            while left:
                ch=f.read(min(left,16<<20));h.update(ch);left-=len(ch);prog(0.45*(tot-left)/tot)
            if h.digest()!=c['hash']:log('  FAILED: the game content does not match its CIA checksum');ok=False
        nc=Ncch(f,c['off'],c['size'])
        if u32(nc.hdr,0x104)*MU!=c['size']:log('  FAILED: game size field');ok=False
        ex=nc.rd(nc.exefs_off,nc.exefs_size)
        if hashlib.sha256(ex[:0x200]).digest()!=nc.hdr[0x1c0:0x1e0]:log('  FAILED: ExeFS header checksum');ok=False
        if hashlib.sha256(nc.rd(0x200,0x400)).digest()!=nc.hdr[0x160:0x180]:log('  FAILED: ExHeader checksum');ok=False
        efs=exefs_files(ex)
        for i in range(10):
            nm=ex[i*16:i*16+8].rstrip(b'\0')
            if nm:
                o,s=struct.unpack_from('<II',ex,i*16+8)
                if hashlib.sha256(ex[0x200+o:0x200+o+s]).digest()!=ex[0xc0+0x20*(9-i):0xc0+0x20*(10-i)]:log('  FAILED: ExeFS file '+nm.decode());ok=False
        base=nc.romfs_off
        hd=nc.rd(base,0x60);master=u32(hd,8)
        l3s=struct.unpack_from('<Q',hd,0x3c+8)[0];l1s=struct.unpack_from('<Q',hd,0x0c+8)[0];l2s=struct.unpack_from('<Q',hd,0x24+8)[0]
        l3p=al(0x60+master,0x1000);l1p=al(l3p+l3s,0x1000);l2p=l1p+al(l1s,0x1000)
        def hash_blocks(off,size):
            out=bytearray();pos=0
            while pos<size:
                n=min(0x1000,size-pos);b=nc.rd(base+off+pos,n)+bytes(0x1000-n);out+=hashlib.sha256(b).digest();pos+=0x1000
                if (pos>>12)%16384==0:prog(0.45+0.4*min(1.0,pos/max(1,size)))
            return bytes(out)
        if nc.rd(base+l2p,l2s)!=hash_blocks(l3p,l3s):log('  FAILED: romfs hash tree (level 2)');ok=False
        if nc.rd(base+l1p,l1s)!=hash_blocks(l2p,l2s):log('  FAILED: romfs hash tree (level 1)');ok=False
        if nc.rd(base+0x60,master)!=hash_blocks(l1p,l1s):log('  FAILED: romfs hash tree (master)');ok=False
        if hashlib.sha256(nc.rd(base,al(0x60+master,0x200))).digest()!=nc.hdr[0x1e0:0x200]:log('  FAILED: romfs superblock checksum');ok=False
        # every patched file reads back as expected
        data=zlib.decompress(Path(patchfile).read_bytes());hl=struct.unpack_from('<I',data,8)[0];hdr=json.loads(data[12:12+hl])
        rfs=RomFS(nc);bad=0;n=0
        prog(0.88)
        for _i,e in enumerate(hdr['entries']):
            if _i%100==0:prog(0.88+0.12*_i/max(1,len(hdr['entries'])))
            if e['path'].startswith('exefs:'):
                raw=efs.get(e['path'][6:]);got=hashlib.sha256(raw).hexdigest() if raw is not None else None
            else:
                ent=rfs.by_path.get(e['path']);got=hashlib.sha256(rfs.read(ent)).hexdigest() if ent is not None else None
            n+=1
            if got!=e['sha_new']:bad+=1
        if bad:log('  FAILED: %d of %d patched files do not read back correctly'%(bad,n));ok=False
        log('Verified %d patched files and the file structure in %d seconds: %s'%(n,time.time()-t0,'OK' if ok else 'PROBLEMS FOUND'))
    except Exception as ex:
        log('  verification could not finish: %s'%ex);ok=False
    finally:
        f.close()
    return ok

if __name__=='__main__':
    args=[a for a in sys.argv[1:] if not a.startswith('--')]
    if '--export' in sys.argv:args=args[:1]
    if not args:print(__doc__);sys.exit(1)
    src=args[0]
    ext=Path(src).suffix.lower()
    if len(args)>1:dst=args[1]
    else:
        want_cia='--cia' in sys.argv or ext=='.cia'      # --cia converts a .3ds into an installable .cia
        dst=str(Path(src).with_name('Dragon Quest XI - Echoes of an Elusive Age'+('.cia' if want_cia else ' (English).3ds')))
    if '--export' in sys.argv:         # --export <folder>: LayeredFS update folder instead of a new game file
        i=sys.argv.index('--export');out=sys.argv[i+1] if i+1<len(sys.argv) else 'dqxi_update'
        sys.exit(patch(src,None,HERE/'dqxi_en.dqp',HERE/'code_layered.ips',export_dir=out))
    keep='--identity' in sys.argv      # rebuild without any change (self-test)
    pf=None if keep else HERE/'dqxi_en.dqp'
    rc=patch(src,dst,pf,None if keep else HERE/'code.ips',keep_code=keep)
    if rc==0 and not keep and '--no-verify' not in sys.argv:
        print('Verifying the new file (about a minute) ...')
        rc=0 if verify_output(dst,pf) else 6
    sys.exit(rc)

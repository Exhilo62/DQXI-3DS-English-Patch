#!/usr/bin/env python3
"""Dragon Quest XI (3DS, JP) English patch - applier.

Usage:  python dqxi_en_patcher.py <path to your dumped original romfs folder> [output folder]

Creates   <output>/luma/titles/0004000000199200/romfs/...   and   code.ips
Copy the `luma` folder to the root of your 3DS SD card (Luma3DS with "Enable game patching" on).
Your original files are only read; the patch contains nothing but the differences.
"""
import sys,os,json,struct,zlib,bz2,hashlib,time
from pathlib import Path
HERE=Path(__file__).parent
sys.path.insert(0,str(HERE))
from dqxi_blz import decompress
TITLE='0004000000199200'

def offtin(b):
    v=int.from_bytes(b,'little')
    if v&(1<<63):return -(v&~(1<<63))
    return v
def bspatch(old,patch):
    assert patch[:8]==b'BSDIFF40','bad delta'
    cl,dl,nsz=offtin(patch[8:16]),offtin(patch[16:24]),offtin(patch[24:32])
    ctrl=bz2.decompress(patch[32:32+cl]);diff=bz2.decompress(patch[32+cl:32+cl+dl]);extra=bz2.decompress(patch[32+cl+dl:])
    new=bytearray(nsz);np_=op=dp=ep=0;cp=0
    while np_<nsz:
        x=offtin(ctrl[cp:cp+8]);y=offtin(ctrl[cp+8:cp+16]);z=offtin(ctrl[cp+16:cp+24]);cp+=24
        if x:
            d=diff[dp:dp+x];o=old[op:op+x]
            if len(o)<x:o=o+bytes(x-len(o))
            if d.count(0)==len(d):new[np_:np_+x]=o
            else:
                step=4096;buf=bytearray(x)
                for i in range(0,x,step):
                    dd=d[i:i+step];oo=o[i:i+step]
                    if dd.count(0)==len(dd):buf[i:i+len(dd)]=oo
                    else:buf[i:i+len(dd)]=bytes((a+b)&255 for a,b in zip(oo,dd))
                new[np_:np_+x]=buf
            np_+=x;op+=x;dp+=x
        if y:
            new[np_:np_+y]=extra[ep:ep+y];np_+=y;ep+=y
        op+=z
    return bytes(new)
def base_of(raw):
    if raw[:4]==b'PACA':return b'PACK'+decompress(raw)[4:]
    return raw
def main():
    if len(sys.argv)<2:print(__doc__);return 1
    src=Path(sys.argv[1]);out=Path(sys.argv[2]) if len(sys.argv)>2 else Path('.')/'dqxi_en_out'
    pf=HERE/'dqxi_en.dqp'
    data=zlib.decompress(pf.read_bytes())
    assert data[:8]==b'DQXIENP1'
    hl=struct.unpack_from('<I',data,8)[0];hdr=json.loads(data[12:12+hl]);pos=12+hl
    ents=hdr['entries'];print('DQXI English patch v%s (%s) - files to build: %d'%(hdr.get('patch_version','?'),hdr.get('built','?'),len(ents)))
    dest=out/'luma'/'titles'/hdr['title_id']
    # pre-check
    missing=[e['path'] for e in ents if e['kind']!='new' and not (src/e['path']).exists()]
    if missing:
        print('Your romfs folder is missing %d expected files, e.g.:'%len(missing));print('  '+'\n  '.join(missing[:5]))
        print('Point the tool at the folder that contains e.g. "ui", "param", "syscmn.pack" (the extracted RomFS of the JP game).');return 2
    bad=0;t0=time.time()
    for n,e in enumerate(ents,1):
        blob=data[pos:pos+e['len']];pos+=e['len']
        if e['kind']=='new':new=zlib.decompress(blob)
        else:
            raw=(src/e['path']).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=e['sha_orig']:
                print('MISMATCH (different game version/dump?):',e['path']);bad+=1;continue
            base=base_of(raw)
            new=base if e['kind']=='expand' else bspatch(base,blob)
        if hashlib.sha256(new).hexdigest()!=e['sha_new']:
            print('VERIFY FAILED:',e['path']);bad+=1;continue
        t=dest/'romfs'/e['path'];t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(new)
        if n%50==0 or n==len(ents):print('  %d/%d  (%.0fs)'%(n,len(ents),time.time()-t0))
    ips=HERE/'code.ips'
    if ips.exists():
        (dest/'code.ips').write_bytes(ips.read_bytes())
    print('done' if not bad else 'finished with %d problem file(s)'%bad)
    print('Copy the "%s" folder to the root of your SD card.'%(out/'luma'))
    return 1 if bad else 0
if __name__=='__main__':sys.exit(main())

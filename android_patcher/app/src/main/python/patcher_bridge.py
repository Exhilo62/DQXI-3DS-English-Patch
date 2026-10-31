"""Bridge between the Android app (Java) and the patcher (cia_patcher.py, the same code as the PC / Linux tool).

run(data_dir, src, dst, cb) -> return code (0 = fine).  cb is a Java object with  log(String)  and  progress(double, String).
src / dst are real files in the app's private folder; the file extension (.3ds / .cia) decides the output format."""
import os
import sys
import traceback


def run(data_dir, src, dst, cb):
    sys._MEIPASS = data_dir          # cia_patcher.load_templates() looks for cia_templates.bin here (same trick as the PyInstaller exe)
    import cia_patcher

    patchfile = os.path.join(data_dir, 'dqxi_en.dqp')
    ips = os.path.join(data_dir, 'code.ips')

    def log(m):
        cb.log(str(m))

    def span(lo, hi):
        return lambda x, label='': cb.progress(lo + (hi - lo) * max(0.0, min(1.0, float(x))), str(label))

    try:
        rc = cia_patcher.patch(src, dst, patchfile, ips, log=log, progress=span(0.0, 0.88))
        if rc == 0:
            log('Checking the new file (about a minute) ...')
            if not cia_patcher.verify_output(dst, patchfile, log=log, progress=span(0.88, 1.0)):
                log('The new file did not pass the check.')
                rc = 6
        return rc
    except Exception:
        log(traceback.format_exc())
        return -1


def repair_saves(work_dir):
    """Old-save repair (DQXI_SaveRepair, the same code as the PC tool).  work_dir/in/<n>/Data0..Data9 are repaired in place; the
    untouched originals are first copied to work_dir/orig/<n>/.  Returns JSON {"code", "report", "changed": ["<n>/DataX", ...]}."""
    import json
    import shutil
    try:
        import DQXI_SaveRepair
        src = os.path.join(work_dir, 'in')
        orig = os.path.join(work_dir, 'orig')
        shutil.rmtree(orig, ignore_errors=True)
        shutil.copytree(src, orig)
        code, report = DQXI_SaveRepair.run([src], backup_base=os.path.join(work_dir, 'backups'), log=lambda m: None)
        changed = []
        for dp, dn, fn in os.walk(src):
            for f in fn:
                rel = os.path.relpath(os.path.join(dp, f), src).replace(os.sep, '/')
                if open(os.path.join(src, rel), 'rb').read() != open(os.path.join(orig, rel), 'rb').read():
                    changed.append(rel)
        return json.dumps({'code': code, 'report': report, 'changed': changed})
    except Exception:
        return json.dumps({'code': -1, 'report': traceback.format_exc(), 'changed': []})

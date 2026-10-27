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

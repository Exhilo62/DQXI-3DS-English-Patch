package com.exhilo.dqxipatcher;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.net.Uri;
import android.os.Build;
import android.os.IBinder;
import android.os.ParcelFileDescriptor;
import android.os.PowerManager;
import android.provider.DocumentsContract;
import android.system.Os;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.RandomAccessFile;
import java.util.Locale;

/**
 * Foreground service that does the patching, so it keeps running when the app is not in front or the screen turns off.
 * The activity only starts it and shows the shared state below.
 * The game is read and the result is written straight through file descriptors (/proc/self/fd symlinks with the right
 * .3ds / .cia name, which the Python patcher needs); if the system does not allow that, it falls back to temporary copies.
 */
public class PatchService extends Service {
    public static final String EXTRA_DST = "dst", EXTRA_EXT = "ext", EXTRA_OUT_EXT = "outExt", EXTRA_SIZE = "size";
    static final String[] ASSETS = {"dqxi_en.dqp", "code.ips", "cia_templates.bin", "VERSION"};
    static final String CHANNEL = "patching";
    static final int NOTIF_ID = 1, DONE_ID = 2;

    // ------------------------------------------------------------------ shared state
    public interface Listener {
        void onLog(String line);

        void onProgress(double fraction, String label);

        void onFinished(boolean ok);
    }

    static final StringBuilder LOG = new StringBuilder();
    static volatile Listener listener;
    public static volatile boolean running;
    public static volatile boolean starting;         // set by the activity between pressing Save and the service starting
    public static volatile double fraction;
    public static volatile String label = "";
    public static volatile int outcome;          // 0 = nothing yet / running, 1 = done, 2 = failed

    public static String logText() {
        synchronized (LOG) {
            return LOG.toString();
        }
    }

    static void addLog(String m) {
        synchronized (LOG) {
            LOG.append(m).append('\n');
        }
        Listener l = listener;
        if (l != null) l.onLog(m);
    }

    /** called from Python */
    public static class Cb {
        final PatchService s;
        final double lo, hi;

        Cb(PatchService s, double lo, double hi) {
            this.s = s;
            this.lo = lo;
            this.hi = hi;
        }

        public void log(String m) {
            addLog(m);
        }

        public void progress(double f, String lab) {
            s.setProgress(lo + (hi - lo) * f, lab);
        }
    }

    // ------------------------------------------------------------------ service
    PowerManager.WakeLock wakeLock;
    NotificationManager nm;
    long lastNotify;

    @Override
    public IBinder onBind(Intent i) {
        return null;
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent == null || running) return START_NOT_STICKY;
        final Uri src = intent.getData();
        final Uri dst = Uri.parse(intent.getStringExtra(EXTRA_DST));
        final String ext = intent.getStringExtra(EXTRA_EXT), outExt = intent.getStringExtra(EXTRA_OUT_EXT);
        final long size = intent.getLongExtra(EXTRA_SIZE, 0);
        running = true;
        starting = false;
        outcome = 0;
        fraction = 0;
        label = "Starting";
        synchronized (LOG) {
            LOG.setLength(0);
        }
        nm = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel ch = new NotificationChannel(CHANNEL, "Patching", NotificationManager.IMPORTANCE_LOW);
            nm.createNotificationChannel(ch);
        }
        Notification n = notification("Patching the game", "Starting ...", 0, true);
        if (Build.VERSION.SDK_INT >= 29)
            startForeground(NOTIF_ID, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC);
        else startForeground(NOTIF_ID, n);
        new Thread(() -> work(src, dst, ext, outExt, size), "patcher").start();
        return START_NOT_STICKY;
    }

    Notification notification(String title, String text, int progress1000, boolean ongoing) {
        Notification.Builder b = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(this, CHANNEL) : new Notification.Builder(this);
        b.setSmallIcon(android.R.drawable.stat_sys_download).setContentTitle(title).setContentText(text).setOngoing(ongoing);
        if (ongoing) b.setProgress(1000, progress1000, false);
        Intent open = new Intent(this, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_NEW_TASK);
        b.setContentIntent(PendingIntent.getActivity(this, 0, open, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT));
        return b.build();
    }

    void setProgress(double f, String lab) {
        fraction = f;
        label = lab == null ? "" : lab;
        Listener l = listener;
        if (l != null) l.onProgress(f, label);
        long now = System.currentTimeMillis();
        if (now - lastNotify > 1500) {
            lastNotify = now;
            nm.notify(NOTIF_ID, notification("Patching the game", String.format(Locale.US, "%.0f%%  %s", f * 100, label), (int) Math.round(f * 1000), true));
        }
    }

    // ------------------------------------------------------------------ the work
    void copyAssets(File dir) throws Exception {
        dir.mkdirs();
        for (String name : ASSETS) {
            try (InputStream in = getAssets().open(name); OutputStream out = new FileOutputStream(new File(dir, name))) {
                byte[] buf = new byte[1 << 16];
                int n;
                while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
            }
        }
    }

    interface Fraction {
        void at(double f, String label);
    }

    static void copy(InputStream in, OutputStream out, long total, Fraction p, String label) throws Exception {
        byte[] buf = new byte[1 << 20];
        long done = 0, last = 0;
        int n;
        while ((n = in.read(buf)) > 0) {
            out.write(buf, 0, n);
            done += n;
            if (done - last > (32 << 20)) {
                last = done;
                p.at(total > 0 ? Math.min(1.0, done / (double) total) : 0, label);
            }
        }
        out.flush();
    }

    /** make `link` (named like the game file) point at the open descriptor; true when the Python side will be able to open it */
    static boolean link(File link, ParcelFileDescriptor p, boolean write) {
        link.delete();
        try {
            Os.symlink("/proc/self/fd/" + p.getFd(), link.getAbsolutePath());
            if (write) {
                try (RandomAccessFile r = new RandomAccessFile(link, "rw")) {
                    r.length();
                }
            } else {
                try (FileInputStream t = new FileInputStream(link)) {
                    t.read(new byte[16]);
                }
            }
            return true;
        } catch (Throwable t) {
            link.delete();
            addLog("(direct file access is not available here: " + t.getMessage() + " - using a temporary copy)");
            return false;
        }
    }

    void work(Uri src, Uri dst, String ext, String outExt, long size) {
        File dir = getFilesDir(), data = new File(dir, "data");
        File in = new File(dir, "input" + ext), out = new File(dir, "output" + outExt);
        ParcelFileDescriptor inP = null, outP = null;
        boolean ok = false;
        try {
            PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
            wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "dqxipatcher:work");
            wakeLock.acquire(3 * 60 * 60 * 1000L);
            in.delete();
            out.delete();
            copyAssets(data);
            addLog("Patch data ready.");

            inP = getContentResolver().openFileDescriptor(src, "r");
            outP = getContentResolver().openFileDescriptor(dst, "rwt");
            boolean inDirect = link(in, inP, false);
            boolean outDirect = link(out, outP, true);
            long need = (inDirect ? 0 : size) + (outDirect ? 0 : size) + (300L << 20);
            if (need > (300L << 20) && dir.getUsableSpace() < need) {
                addLog(String.format(Locale.US, "Not enough free space: about %.1f GB needed in the app's storage, %.1f GB free.",
                        need / 1073741824.0, dir.getUsableSpace() / 1073741824.0));
                return;
            }
            if (!inDirect) {
                addLog("Copying your game into the app ...");
                try (InputStream is = new FileInputStream(inP.getFileDescriptor()); OutputStream os = new FileOutputStream(in)) {
                    copy(is, os, size, (f, l) -> setProgress(0.10 * f, l), "Copying your game into the app");
                }
            } else {
                addLog("Reading your game directly (no copy needed).");
            }
            addLog("Starting Python ...");
            if (!Python.isStarted()) Python.start(new AndroidPlatform(this));
            PyObject mod = Python.getInstance().getModule("patcher_bridge");
            double lo = inDirect ? 0.0 : 0.10, hi = outDirect ? 1.0 : 0.85;
            int rc = mod.callAttr("run", data.getAbsolutePath(), in.getAbsolutePath(), out.getAbsolutePath(), new Cb(this, lo, hi)).toInt();
            if (rc == 0 && !outDirect) {
                addLog("Saving the English game to the place you chose ...");
                try (InputStream is = new FileInputStream(out); OutputStream os = new FileOutputStream(outP.getFileDescriptor())) {
                    copy(is, os, out.length(), (f, l) -> setProgress(0.85 + 0.15 * f, l), "Saving");
                }
            }
            if (rc == 0) {
                ok = true;
                setProgress(1.0, "Done");
                addLog("Done. Your English game was saved. Keep the Japanese original as a backup.");
            } else {
                addLog("The patch did not finish (code " + rc + "). Nothing was saved. See the messages above.");
            }
        } catch (Throwable t) {
            addLog("ERROR: " + t);
            java.io.StringWriter sw = new java.io.StringWriter();
            t.printStackTrace(new java.io.PrintWriter(sw));
            addLog(sw.toString());
        } finally {
            in.delete();
            out.delete();
            try {
                if (inP != null) inP.close();
                if (outP != null) outP.close();
            } catch (Exception ignored) {
            }
            if (!ok) {
                try {
                    DocumentsContract.deleteDocument(getContentResolver(), dst);     // do not leave an empty / broken file behind
                } catch (Throwable ignored) {
                }
            }
            if (wakeLock != null && wakeLock.isHeld()) wakeLock.release();
            outcome = ok ? 1 : 2;
            running = false;
            stopForeground(false);
            nm.cancel(NOTIF_ID);
            nm.notify(DONE_ID, notification(ok ? "English game ready" : "Patching did not finish",
                    ok ? "Your English game was saved." : "Open the app to see what went wrong.", 0, false));
            Listener l = listener;
            if (l != null) l.onFinished(ok);
            stopSelf();
        }
    }
}

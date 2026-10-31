package com.exhilo.dqxipatcher;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.DocumentsContract;
import android.provider.OpenableColumns;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.ScrollView;
import android.widget.TextView;

import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * DQXI English patcher for Android: pick the decrypted Japanese .3ds / .cia, choose the output format and where to save, patch.
 * The patching runs in PatchService (a foreground service) with the same Python code as the PC tool (python/cia_patcher.py, via Chaquopy).
 */
public class MainActivity extends Activity implements PatchService.Listener {
    static final int REQ_PICK = 1, REQ_SAVE = 2, REQ_TREE = 3;

    Uri srcUri;
    String srcName = "", ext = "";
    long srcSize;
    TextView tvFile, tvStatus, tvLog;
    Button btnPick, btnPatch, btnRepair;
    volatile boolean repairing;
    ProgressBar bar;
    ScrollView scroll;
    RadioGroup rgFormat;
    RadioButton rb3ds, rbCia;

    int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        String version = "?";
        try {
            version = getPackageManager().getPackageInfo(getPackageName(), 0).versionName;
        } catch (Exception ignored) {
        }
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(20), dp(20), dp(20), dp(20));

        TextView title = new TextView(this);
        title.setText("Dragon Quest XI (3DS) English patch v" + version);
        title.setTextSize(20);
        root.addView(title);

        TextView info = new TextView(this);
        info.setText("1. Choose your DECRYPTED Japanese game (.3ds or .cia).\n"
                + "2. Choose the output format.\n"
                + "3. Press Patch and choose where to save the English game.\n"
                + "It takes about 5 - 10 minutes and keeps running if you leave the app (a notification shows the progress). "
                + "Your original file is never changed. Make sure there is room for the new file (a .3ds is about 4 GB, a .cia about 2.7 GB).");
        info.setPadding(0, dp(10), 0, dp(10));
        root.addView(info);

        btnPick = new Button(this);
        btnPick.setText("1. Choose the Japanese game file");
        btnPick.setOnClickListener(v -> pick());
        root.addView(btnPick);

        tvFile = new TextView(this);
        tvFile.setText("No file chosen yet.");
        tvFile.setPadding(0, dp(6), 0, dp(6));
        root.addView(tvFile);

        TextView fmt = new TextView(this);
        fmt.setText("2. Output format:");
        fmt.setPadding(0, dp(6), 0, 0);
        root.addView(fmt);
        rgFormat = new RadioGroup(this);
        rgFormat.setOrientation(RadioGroup.VERTICAL);
        rb3ds = new RadioButton(this);
        rb3ds.setText(".3ds  (emulator, e.g. Azahar)");
        rb3ds.setId(View.generateViewId());
        rbCia = new RadioButton(this);
        rbCia.setText(".cia  (install on a 3DS with FBI)");
        rbCia.setId(View.generateViewId());
        rgFormat.addView(rb3ds);
        rgFormat.addView(rbCia);
        rb3ds.setChecked(true);
        root.addView(rgFormat);

        btnPatch = new Button(this);
        btnPatch.setText("3. Patch");
        btnPatch.setOnClickListener(v -> startSave());
        root.addView(btnPatch);

        btnRepair = new Button(this);
        btnRepair.setText("Repair an old save (patch 0.1.17 - 0.1.20)");
        btnRepair.setOnClickListener(v -> pickSaveFolder());
        root.addView(btnRepair);

        bar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        bar.setMax(1000);
        root.addView(bar, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(24)));

        tvStatus = new TextView(this);
        tvStatus.setGravity(Gravity.START);
        root.addView(tvStatus);

        tvLog = new TextView(this);
        tvLog.setTypeface(android.graphics.Typeface.MONOSPACE);
        tvLog.setTextSize(11);
        tvLog.setTextIsSelectable(true);
        root.addView(tvLog);

        scroll = new ScrollView(this);          // the whole screen scrolls (small screens / landscape)
        scroll.addView(root);
        setContentView(scroll);

        updateButtons();
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 7);     // only for the progress notification
    }

    @Override
    protected void onResume() {
        super.onResume();
        PatchService.listener = this;
        tvLog.setText(PatchService.logText());
        bar.setProgress((int) Math.round(PatchService.fraction * 1000));
        if (PatchService.running || PatchService.outcome != 0)
            tvStatus.setText(String.format(Locale.US, "%.0f%%  %s", PatchService.fraction * 100, PatchService.label)
                    + (PatchService.outcome == 2 ? "  (not finished)" : ""));
        updateButtons();
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (PatchService.listener == this) PatchService.listener = null;
    }

    void updateButtons() {
        boolean busy = PatchService.running || PatchService.starting || repairing;
        btnRepair.setEnabled(!busy);
        boolean haveFile = srcUri != null && !ext.isEmpty();
        btnPick.setEnabled(!busy);
        btnPatch.setEnabled(!busy && haveFile);
        rb3ds.setEnabled(!busy && haveFile && ext.equals(".3ds"));
        rbCia.setEnabled(!busy && haveFile);
    }

    // ------------------------------------------------------------------ choosing files
    void pick() {
        if (PatchService.running || PatchService.starting) return;
        Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.setType("*/*");
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        startActivityForResult(i, REQ_PICK);
    }

    /** the format the user chose; a .cia source can only become a .cia */
    String outExt() {
        return ext.equals(".cia") || rbCia.isChecked() ? ".cia" : ".3ds";
    }

    void startSave() {
        if (PatchService.running || srcUri == null) return;
        Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.setType("application/octet-stream");
        i.putExtra(Intent.EXTRA_TITLE, outExt().equals(".cia") ? "Dragon Quest XI - Echoes of an Elusive Age.cia"
                : "Dragon Quest XI - Echoes of an Elusive Age (English).3ds");
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        startActivityForResult(i, REQ_SAVE);
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (res != RESULT_OK || data == null || data.getData() == null) return;
        if (req == REQ_TREE) {
            repairTree(data.getData());
        } else if (req == REQ_PICK) {
            srcUri = data.getData();
            try {
                getContentResolver().takePersistableUriPermission(srcUri, Intent.FLAG_GRANT_READ_URI_PERMISSION);
            } catch (Exception ignored) {
            }
            srcName = "";
            srcSize = 0;
            try (Cursor c = getContentResolver().query(srcUri, null, null, null, null)) {
                if (c != null && c.moveToFirst()) {
                    int n = c.getColumnIndex(OpenableColumns.DISPLAY_NAME), s = c.getColumnIndex(OpenableColumns.SIZE);
                    if (n >= 0) srcName = c.getString(n);
                    if (s >= 0) srcSize = c.getLong(s);
                }
            } catch (Exception ignored) {
            }
            String low = srcName.toLowerCase(Locale.ROOT);
            ext = low.endsWith(".cia") ? ".cia" : low.endsWith(".3ds") || low.endsWith(".cci") ? ".3ds" : "";
            if (ext.isEmpty()) {
                tvFile.setText(srcName + "\nThis is not a .3ds or .cia file. Choose your decrypted Japanese Dragon Quest XI.");
            } else {
                tvFile.setText(srcName + "  (" + String.format(Locale.US, "%.2f", srcSize / 1073741824.0) + " GB)");
                if (ext.equals(".cia")) rbCia.setChecked(true);
                else rb3ds.setChecked(true);
            }
            updateButtons();
        } else if (req == REQ_SAVE) {
            Uri dst = data.getData();
            try {
                getContentResolver().takePersistableUriPermission(dst, Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            } catch (Exception ignored) {
            }
            tvLog.setText("");
            tvStatus.setText("Starting ...");
            bar.setProgress(0);
            Intent s = new Intent(this, PatchService.class);
            s.setData(srcUri);
            s.putExtra(PatchService.EXTRA_DST, dst.toString());
            s.putExtra(PatchService.EXTRA_EXT, ext);
            s.putExtra(PatchService.EXTRA_OUT_EXT, outExt());
            s.putExtra(PatchService.EXTRA_SIZE, srcSize);
            s.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            PatchService.starting = true;       // lock the buttons at once; the service takes over the state
            updateButtons();
            if (Build.VERSION.SDK_INT >= 26) startForegroundService(s);
            else startService(s);
        }
    }

    // ------------------------------------------------------------------ old save repair
    static final String BACKUPS = "DQXI_SaveRepair_backups";

    void pickSaveFolder() {
        if (PatchService.running || PatchService.starting || repairing) return;
        Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);
        tvLog.setText("Choose the folder that holds your save files (Data0, Data1, Data2, Data3, mini_0 ...). It must be a folder the system lets "
                + "apps open (Android does not allow another app's private data folder: copy the save folder to Documents first). "
                + "The original files are copied to a " + BACKUPS + " folder inside it before anything is changed.\n");
        startActivityForResult(i, REQ_TREE);
    }

    static class SaveFile {
        String docId, name, rel;
    }

    void scanSaves(Uri tree, String parentId, String rel, int depth, List<SaveFile> out) {
        Uri kids = DocumentsContract.buildChildDocumentsUriUsingTree(tree, parentId);
        try (Cursor c = getContentResolver().query(kids, new String[]{DocumentsContract.Document.COLUMN_DOCUMENT_ID,
                DocumentsContract.Document.COLUMN_DISPLAY_NAME, DocumentsContract.Document.COLUMN_MIME_TYPE}, null, null, null)) {
            if (c == null) return;
            List<String[]> dirs = new ArrayList<>();
            while (c.moveToNext()) {
                String id = c.getString(0), name = c.getString(1), mime = c.getString(2);
                if (DocumentsContract.Document.MIME_TYPE_DIR.equals(mime)) {
                    if (depth < 3 && !BACKUPS.equals(name)) dirs.add(new String[]{id, name});
                } else if (name != null && name.matches("Data[0-9]")) {
                    SaveFile f = new SaveFile();
                    f.docId = id;
                    f.name = name;
                    f.rel = rel;
                    out.add(f);
                }
            }
            for (String[] d : dirs) scanSaves(tree, d[0], rel + d[1] + "/", depth + 1, out);
        }
    }

    static byte[] readAll(InputStream in) throws Exception {
        ByteArrayOutputStream bo = new ByteArrayOutputStream();
        byte[] buf = new byte[65536];
        int n;
        while ((n = in.read(buf)) > 0) bo.write(buf, 0, n);
        in.close();
        return bo.toByteArray();
    }

    static void deleteTree(File f) {
        File[] k = f.listFiles();
        if (k != null) for (File x : k) deleteTree(x);
        f.delete();
    }

    void say(final String m) {
        runOnUiThread(() -> {
            tvLog.append(m + "\n");
            scroll.post(() -> scroll.fullScroll(View.FOCUS_DOWN));
        });
    }

    void repairTree(final Uri tree) {
        repairing = true;
        tvLog.setText("");
        tvStatus.setText("Repairing the save ...");
        updateButtons();
        new Thread(() -> {
            try {
                String rootId = DocumentsContract.getTreeDocumentId(tree);
                List<SaveFile> files = new ArrayList<>();
                scanSaves(tree, rootId, "", 0, files);
                if (files.isEmpty()) {
                    say("No save files named Data0 ... Data9 found in that folder (or its sub folders).");
                    say("Choose the folder that directly holds Data0, Data1, Data2, Data3 (on an emulator it is called 00000001).");
                    return;
                }
                File work = new File(getFilesDir(), "saverepair");
                deleteTree(work);
                for (int i = 0; i < files.size(); i++) {
                    File d = new File(work, "in/" + i);
                    d.mkdirs();
                    byte[] b = readAll(getContentResolver().openInputStream(DocumentsContract.buildDocumentUriUsingTree(tree, files.get(i).docId)));
                    try (FileOutputStream fo = new FileOutputStream(new File(d, files.get(i).name))) {
                        fo.write(b);
                    }
                }
                if (!Python.isStarted()) Python.start(new AndroidPlatform(this));
                JSONObject res = new JSONObject(Python.getInstance().getModule("patcher_bridge")
                        .callAttr("repair_saves", work.getAbsolutePath()).toString());
                JSONArray changed = res.getJSONArray("changed");
                String report = res.getString("report").replace(work.getAbsolutePath() + "/in/", "");
                for (int i = 0; i < files.size(); i++)          // the temporary copies are numbered folders: show the real file names
                    report = report.replace("  " + i + "/" + files.get(i).name + ":", "  " + files.get(i).rel + files.get(i).name + ":");
                say(report.replaceAll("(?m)^\\s*original kept in .*\\n?", "")
                        .replaceAll("(?m)^(The repaired files are in|emulator \\(close|The originals are kept in).*\\n?", ""));
                if (changed.length() == 0) return;
                // back up the originals inside the chosen folder, check them, only then overwrite
                Uri root = DocumentsContract.buildDocumentUriUsingTree(tree, rootId);
                Uri bk = DocumentsContract.createDocument(getContentResolver(), root, DocumentsContract.Document.MIME_TYPE_DIR, BACKUPS);
                if (bk == null) throw new Exception("could not create the " + BACKUPS + " folder here");
                bk = DocumentsContract.createDocument(getContentResolver(), bk, DocumentsContract.Document.MIME_TYPE_DIR,
                        new java.text.SimpleDateFormat("yyyy-MM-dd_HH-mm-ss", Locale.US).format(new java.util.Date()));
                if (bk == null) throw new Exception("could not create the backup folder");
                for (int k = 0; k < changed.length(); k++) {
                    String rel = changed.getString(k);
                    SaveFile f = files.get(Integer.parseInt(rel.split("/")[0]));
                    byte[] orig = readAll(new FileInputStream(new File(work, "orig/" + rel)));
                    byte[] fixed = readAll(new FileInputStream(new File(work, "in/" + rel)));
                    Uri b = DocumentsContract.createDocument(getContentResolver(), bk, "application/octet-stream",
                            f.rel.replace("/", "_") + f.name);
                    if (b == null) throw new Exception("could not write the backup of " + f.name);
                    try (OutputStream o = getContentResolver().openOutputStream(b, "wt")) {
                        o.write(orig);
                    }
                    if (readAll(getContentResolver().openInputStream(b)).length != orig.length)
                        throw new Exception("the backup of " + f.name + " is incomplete - it was not changed");
                    try (OutputStream o = getContentResolver().openOutputStream(DocumentsContract.buildDocumentUriUsingTree(tree, f.docId), "wt")) {
                        o.write(fixed);
                    }
                }
                say("The repaired files were written into the folder you chose. The originals are in its " + BACKUPS + " folder.");
                say("Close the emulator before you start the game again, then play with the game patched with 0.1.21 or newer.");
            } catch (Throwable t) {
                say("The save could not be repaired: " + t);
            } finally {
                repairing = false;
                runOnUiThread(() -> {
                    tvStatus.setText("");
                    updateButtons();
                });
            }
        }).start();
    }

    // ------------------------------------------------------------------ PatchService.Listener (called from the worker thread)
    @Override
    public void onLog(final String line) {
        runOnUiThread(() -> {
            tvLog.append(line + "\n");
            scroll.post(() -> scroll.fullScroll(View.FOCUS_DOWN));
        });
    }

    @Override
    public void onProgress(final double f, final String label) {
        runOnUiThread(() -> {
            bar.setProgress((int) Math.round(f * 1000));
            tvStatus.setText(String.format(Locale.US, "%.0f%%  %s", f * 100, label == null ? "" : label));
        });
    }

    @Override
    public void onFinished(final boolean ok) {
        runOnUiThread(() -> {
            if (!ok) tvStatus.append("  (not finished)");
            updateButtons();
        });
    }
}

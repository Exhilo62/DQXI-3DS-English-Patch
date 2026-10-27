package com.exhilo.dqxipatcher;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
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

import java.util.Locale;

/**
 * DQXI English patcher for Android: pick the decrypted Japanese .3ds / .cia, choose the output format and where to save, patch.
 * The patching runs in PatchService (a foreground service) with the same Python code as the PC tool (python/cia_patcher.py, via Chaquopy).
 */
public class MainActivity extends Activity implements PatchService.Listener {
    static final int REQ_PICK = 1, REQ_SAVE = 2;

    Uri srcUri;
    String srcName = "", ext = "";
    long srcSize;
    TextView tvFile, tvStatus, tvLog;
    Button btnPick, btnPatch;
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
        boolean busy = PatchService.running || PatchService.starting;
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
        if (req == REQ_PICK) {
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

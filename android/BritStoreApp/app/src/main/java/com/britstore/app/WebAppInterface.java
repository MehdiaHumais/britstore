package com.britstore.app;

import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import android.widget.Toast;

import androidx.core.content.FileProvider;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

public class WebAppInterface {

    private Context context;
    private WebView webView;
    private Handler mainHandler;
    private ExecutorService executor = Executors.newSingleThreadExecutor();
    private volatile DownloadTask currentDownload;
    private int lastProgress = -1;

    public WebAppInterface(Context context, WebView webView) {
        this.context = context;
        this.webView = webView;
        this.mainHandler = new Handler(Looper.getMainLooper());
    }

    @JavascriptInterface
    public String getPlatform() {
        return "android";
    }

    @JavascriptInterface
    public boolean isAppInstalled(String packageName) {
        if (packageName == null || packageName.isEmpty()) return false;
        try {
            context.getPackageManager().getPackageInfo(packageName, 0);
            return true;
        } catch (PackageManager.NameNotFoundException e) {
            return false;
        }
    }

    @JavascriptInterface
    public void downloadAndInstall(String url, String packageName) {
        if (currentDownload != null) {
            currentDownload.cancel();
        }
        currentDownload = new DownloadTask(url, packageName);
        executor.submit(currentDownload);
    }

    @JavascriptInterface
    public int getDownloadProgress() {
        if (currentDownload == null) return -1;
        return currentDownload.getProgress();
    }

    @JavascriptInterface
    public void cancelDownload() {
        if (currentDownload != null) {
            currentDownload.cancel();
            currentDownload = null;
        }
        lastProgress = -1;
        notifyProgress(-1);
    }

    @JavascriptInterface
    public void openApp(String packageName) {
        try {
            Intent intent = context.getPackageManager().getLaunchIntentForPackage(packageName);
            if (intent != null) {
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                context.startActivity(intent);
            }
        } catch (Exception e) {
            Toast.makeText(context, "Could not open app", Toast.LENGTH_SHORT).show();
        }
    }

    @JavascriptInterface
    public void uninstallApp(String packageName) {
        try {
            Uri uri = Uri.parse("package:" + packageName);
            Intent intent = new Intent(Intent.ACTION_DELETE, uri);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(intent);
        } catch (Exception e) {
            Toast.makeText(context, "Could not uninstall", Toast.LENGTH_SHORT).show();
        }
    }

    private void notifyProgress(int pct) {
        if (pct == lastProgress) return;
        lastProgress = pct;
        final int p = pct;
        mainHandler.post(() -> {
            if (p >= 0) {
                webView.evaluateJavascript(
                    "if(window.onDownloadProgress) onDownloadProgress(" + p + ");", null);
            } else {
                webView.evaluateJavascript(
                    "if(window.onDownloadProgress) onDownloadProgress(-1);", null);
            }
        });
    }

    private class DownloadTask implements Runnable {
        private String url;
        private String packageName;
        private volatile int progress = -1;
        private AtomicBoolean cancelled = new AtomicBoolean(false);

        DownloadTask(String url, String packageName) {
            this.url = url;
            this.packageName = packageName;
        }

        int getProgress() { return progress; }

        void cancel() { cancelled.set(true); }

        @Override
        public void run() {
            HttpURLConnection conn = null;
            try {
                notifyProgress(0);

                URL downloadUrl = new URL(url);
                conn = (HttpURLConnection) downloadUrl.openConnection();
                conn.setInstanceFollowRedirects(true);
                conn.setConnectTimeout(30000);
                conn.setReadTimeout(30000);
                conn.connect();

                int responseCode = conn.getResponseCode();
                if (responseCode != HttpURLConnection.HTTP_OK) {
                    notifyProgress(-1);
                    return;
                }

                int length = conn.getContentLength();
                File dir = new File(context.getCacheDir(), "downloads");
                dir.mkdirs();
                File apkFile = new File(dir, packageName + "_" + System.currentTimeMillis() + ".apk");

                try (InputStream in = conn.getInputStream();
                     FileOutputStream out = new FileOutputStream(apkFile)) {
                    byte[] buf = new byte[8192];
                    int total = 0, read;
                    while ((read = in.read(buf)) != -1) {
                        if (cancelled.get()) {
                            apkFile.delete();
                            return;
                        }
                        out.write(buf, 0, read);
                        total += read;
                        if (length > 0) {
                            progress = (int) (total * 100L / length);
                            notifyProgress(progress);
                        }
                    }
                }

                if (cancelled.get()) {
                    apkFile.delete();
                    return;
                }

                progress = 100;
                notifyProgress(100);
                installApk(apkFile);
                currentDownload = null;

            } catch (Exception e) {
                notifyProgress(-1);
            } finally {
                if (conn != null) conn.disconnect();
            }
        }

        private void installApk(File apkFile) {
            try {
                Uri apkUri;
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                    apkUri = FileProvider.getUriForFile(context,
                            "com.britstore.app.fileprovider", apkFile);
                } else {
                    apkUri = Uri.fromFile(apkFile);
                }
                Intent install = new Intent(Intent.ACTION_VIEW);
                install.setDataAndType(apkUri, "application/vnd.android.package-archive");
                install.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                install.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                context.startActivity(install);
            } catch (Exception e) {
                Toast.makeText(context, "Install failed: " + e.getMessage(),
                        Toast.LENGTH_LONG).show();
            }
        }
    }
}

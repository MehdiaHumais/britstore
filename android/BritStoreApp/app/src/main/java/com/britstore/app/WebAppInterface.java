package com.britstore.app;

import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.AsyncTask;
import android.os.Build;
import android.os.Environment;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import android.widget.Toast;

import androidx.core.content.FileProvider;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class WebAppInterface {

    private Context context;
    private WebView webView;
    private DownloadTask currentDownload;
    private int lastProgress = -1;

    public WebAppInterface(Context context, WebView webView) {
        this.context = context;
        this.webView = webView;
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
            currentDownload.cancel(true);
        }
        currentDownload = new DownloadTask(url, packageName);
        currentDownload.execute();
    }

    @JavascriptInterface
    public int getDownloadProgress() {
        if (currentDownload == null) return -1;
        return currentDownload.getProgress();
    }

    @JavascriptInterface
    public void cancelDownload() {
        if (currentDownload != null) {
            currentDownload.cancel(true);
            currentDownload = null;
            lastProgress = -1;
            notifyProgress(-1);
        }
    }

    @JavascriptInterface
    public void openApp(String packageName) {
        try {
            Intent intent = context.getPackageManager().getLaunchIntentForPackage(packageName);
            if (intent != null) {
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
        webView.post(() -> {
            if (p >= 0) {
                webView.evaluateJavascript(
                    "if(window.onDownloadProgress) onDownloadProgress(" + p + ");", null);
            } else {
                webView.evaluateJavascript(
                    "if(window.onDownloadProgress) onDownloadProgress(-1);", null);
            }
        });
    }

    private class DownloadTask extends AsyncTask<Void, Integer, File> {
        private String url;
        private String packageName;
        private int progress = -1;
        private boolean cancelled = false;

        DownloadTask(String url, String packageName) {
            this.url = url;
            this.packageName = packageName;
        }

        int getProgress() { return progress; }

        @Override
        protected void onPreExecute() {
            notifyProgress(0);
        }

        @Override
        protected File doInBackground(Void... params) {
            HttpURLConnection conn = null;
            try {
                conn = (HttpURLConnection) new URL(url).openConnection();
                conn.connect();
                int length = conn.getContentLength();
                File dir = new File(context.getCacheDir(), "downloads");
                dir.mkdirs();
                File apkFile = new File(dir, packageName + "_" + System.currentTimeMillis() + ".apk");

                try (InputStream in = conn.getInputStream();
                     FileOutputStream out = new FileOutputStream(apkFile)) {
                    byte[] buf = new byte[8192];
                    int total = 0, read;
                    while ((read = in.read(buf)) != -1) {
                        if (isCancelled() || cancelled) {
                            apkFile.delete();
                            return null;
                        }
                        out.write(buf, 0, read);
                        total += read;
                        if (length > 0) {
                            progress = (int) (total * 100L / length);
                            publishProgress(progress);
                        }
                    }
                }
                return apkFile;
            } catch (Exception e) {
                return null;
            } finally {
                if (conn != null) conn.disconnect();
            }
        }

        @Override
        protected void onProgressUpdate(Integer... values) {
            notifyProgress(values[0]);
        }

        @Override
        protected void onPostExecute(File apkFile) {
            if (apkFile == null || !apkFile.exists()) {
                notifyProgress(-1);
                return;
            }
            progress = 100;
            notifyProgress(100);
            installApk(apkFile);
            currentDownload = null;
        }

        @Override
        protected void onCancelled(File result) {
            if (result != null) result.delete();
            progress = -1;
            notifyProgress(-1);
            currentDownload = null;
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

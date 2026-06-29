package com.britstore.app;

import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.net.http.SslError;
import android.os.Build;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.webkit.JsResult;
import android.webkit.SslErrorHandler;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.browser.customtabs.CustomTabsIntent;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;

public class MainActivity extends AppCompatActivity {

    private WebView webView;
    private SwipeRefreshLayout swipeRefresh;
    private View loadingOverlay;
    private ValueCallback<Uri[]> uploadMessage;
    private static final int FILE_CHOOSER_CODE = 1;
    private static final String STORE_URL = "https://store.britsyncai.com";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        swipeRefresh = findViewById(R.id.swipeRefresh);
        webView = findViewById(R.id.webView);
        loadingOverlay = findViewById(R.id.loadingOverlay);

        setupWebView();
        swipeRefresh.setOnRefreshListener(() -> webView.reload());
        swipeRefresh.setColorSchemeResources(android.R.color.black, android.R.color.darker_gray);

        webView.addJavascriptInterface(
                new WebAppInterface(this, this, webView), "Android");

        webView.loadUrl(STORE_URL);
    }

    private void setupWebView() {
        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        s.setDatabaseEnabled(true);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            s.setSafeBrowsingEnabled(true);
        }

        webView.setWebViewClient(new StoreWebClient());
        webView.setWebChromeClient(new StoreChromeClient());
    }

    private void openInCustomTab(String url) {
        CustomTabsIntent.Builder builder = new CustomTabsIntent.Builder();
        builder.setShowTitle(true);
        builder.build().launchUrl(this, Uri.parse(url));
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && webView.canGoBack()) {
            webView.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        if (requestCode == FILE_CHOOSER_CODE) {
            if (uploadMessage != null) {
                uploadMessage.onReceiveValue(
                    WebChromeClient.FileChooserParams.parseResult(resultCode, data));
                uploadMessage = null;
            }
            return;
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    private class StoreWebClient extends WebViewClient {
        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
            String url = req.getUrl().toString();
            if (url.contains("webauthn") || url.contains("fingerprint")
                    || url.contains(".well-known") || url.contains("make-credential")
                    || url.contains("get-assertion")) {
                openInCustomTab(url);
                return true;
            }
            if (!url.startsWith(STORE_URL)) {
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
                } catch (Exception ignored) {}
                return true;
            }
            return false;
        }

        @Override
        public void onPageFinished(WebView view, String url) {
            super.onPageFinished(view, url);
            swipeRefresh.setRefreshing(false);
            loadingOverlay.setVisibility(View.GONE);

            view.evaluateJavascript(
                "(function(){" +
                "try{" +
                "if(!window.Android||!Android.getPlatform||Android.getPlatform()!=='android')return;" +
                "var path=window.location.pathname;" +
                "var g=function(id){var e=document.getElementById(id);if(!e){e=document.createElement('button');e.id=id;e.className='btn btn-outline btn-block fingerprint-btn';var d=document.querySelector('.auth-divider');if(d)d.parentNode.insertBefore(e,d.nextSibling);}return e;};" +
                "if(path.indexOf('/login/')>=0){" +
                "var b=g('androidFpLoginBtn');b.style.display='block';b.innerHTML='<span class=\"fp-icon\">👆</span> Sign In with Fingerprint';" +
                "b.onclick=function(){b.disabled=true;b.textContent='Scanning fingerprint...';window.onFingerprintResult=function(s,t){if(!s){b.disabled=false;b.innerHTML='<span class=\"fp-icon\">👆</span> Sign In with Fingerprint';return;}var token=t||localStorage.getItem('android_fp_token');if(!token){alert('No fingerprint registered.');b.disabled=false;b.innerHTML='<span class=\"fp-icon\">👆</span> Sign In with Fingerprint';return;}fetch('/api/fingerprint/android/login/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':document.querySelector('[name=csrfmiddlewaretoken]')?document.querySelector('[name=csrfmiddlewaretoken]').value:''},body:JSON.stringify({device_token:token})}).then(function(r){return r.json();}).then(function(d){if(d.status==='ok'){window.location.href='/';}else{alert(d.message||'Login failed');b.disabled=false;b.innerHTML='<span class=\"fp-icon\">👆</span> Sign In with Fingerprint';}}).catch(function(){alert('Network error');b.disabled=false;b.innerHTML='<span class=\"fp-icon\">👆</span> Sign In with Fingerprint';});};Android.authenticateFingerprint('login');};" +
                "}" +
                "if(path.indexOf('/signup/')>=0){" +
                "var b=g('androidFpSignupBtn');b.style.display='block';b.innerHTML='<span class=\"fp-icon\">👆</span> Sign Up with Fingerprint';" +
                "b.onclick=function(){b.disabled=true;b.textContent='Scanning fingerprint...';window.onFingerprintResult=function(s,t){if(!s){b.disabled=false;b.innerHTML='<span class=\"fp-icon\">👆</span> Sign Up with Fingerprint';return;}if(!t){alert('Scan failed');b.disabled=false;b.innerHTML='<span class=\"fp-icon\">👆</span> Sign Up with Fingerprint';return;}localStorage.setItem('android_fp_token',t);fetch('/api/fingerprint/android/signup/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':document.querySelector('[name=csrfmiddlewaretoken]')?document.querySelector('[name=csrfmiddlewaretoken]').value:''},body:JSON.stringify({device_token:t})}).then(function(r){return r.json();}).then(function(d){if(d.status==='ok'){window.location.href='/profile/';}else{alert(d.message||'Signup failed');b.disabled=false;b.innerHTML='<span class=\"fp-icon\">👆</span> Sign Up with Fingerprint';}}).catch(function(){alert('Network error');b.disabled=false;b.innerHTML='<span class=\"fp-icon\">👆</span> Sign Up with Fingerprint';});};Android.authenticateFingerprint('signup');};" +
                "}" +
                "if(path.indexOf('/profile/')>=0){" +
                "var b=document.getElementById('verifyFpBtn');if(b&&!b._fp){b._fp=true;var ob=b.onclick;b.onclick=function(){if(typeof Android!=='undefined'&&Android.getPlatform&&Android.getPlatform()==='android'){var btn=document.getElementById('verifyFpBtn');var prog=document.getElementById('verifyProgress');if(btn)btn.style.display='none';if(prog)prog.style.display='block';window.onFingerprintResult=function(s){if(s){var g=document.getElementById('fpGate');var f=document.getElementById('profileForm');if(g)g.style.display='none';if(f)f.style.display='block';}else{if(btn)btn.style.display='block';if(prog)prog.style.display='none';alert('Verification failed');}};Android.authenticateFingerprint('verify');}else{var g=document.getElementById('fpGate');var f=document.getElementById('profileForm');if(g)g.style.display='none';if(f)f.style.display='block';}};}" +
                "}" +
                "}catch(e){console.error('BritStore FP:',e);}" +
                "})()",
                null);
        }
    }

    private class StoreChromeClient extends WebChromeClient {
        @Override
        public boolean onJsConfirm(WebView view, String url, String message, final JsResult result) {
            new AlertDialog.Builder(new android.view.ContextThemeWrapper(
                    MainActivity.this, android.R.style.Theme_DeviceDefault_Dialog_Alert))
                    .setTitle("Confirm")
                    .setMessage(message)
                    .setPositiveButton("Yes",
                            (dialog, which) -> result.confirm())
                    .setNegativeButton("No",
                            (dialog, which) -> result.cancel())
                    .setOnCancelListener(dialog -> result.cancel())
                    .show();
            return true;
        }

        @Override
        public boolean onJsAlert(WebView view, String url, String message, final JsResult result) {
            new AlertDialog.Builder(new android.view.ContextThemeWrapper(
                    MainActivity.this, android.R.style.Theme_DeviceDefault_Dialog_Alert))
                    .setTitle("Alert")
                    .setMessage(message)
                    .setPositiveButton("OK",
                            (dialog, which) -> result.confirm())
                    .setOnCancelListener(dialog -> result.cancel())
                    .show();
            return true;
        }

        @Override
        public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> filePath,
                                          FileChooserParams params) {
            if (uploadMessage != null) {
                uploadMessage.onReceiveValue(null);
                uploadMessage = null;
            }
            uploadMessage = filePath;
            try {
                startActivityForResult(params.createIntent(), FILE_CHOOSER_CODE);
            } catch (Exception e) {
                uploadMessage = null;
                return false;
            }
            return true;
        }

        @Override
        public void onProgressChanged(WebView view, int p) {
            if (p == 100) swipeRefresh.setRefreshing(false);
        }
    }
}

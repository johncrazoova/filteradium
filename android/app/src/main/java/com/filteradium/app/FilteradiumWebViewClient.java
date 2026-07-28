package com.filteradium.app;

import android.app.Activity;
import android.view.View;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.ProgressBar;
import android.widget.Toast;

public class FilteradiumWebViewClient extends WebViewClient {
    
    private Activity activity;
    
    public FilteradiumWebViewClient(Activity activity) {
        this.activity = activity;
    }
    
    @Override
    public void onPageFinished(WebView view, String url) {
        super.onPageFinished(view, url);
        ProgressBar progressBar = (ProgressBar) activity.findViewById(R.id.progressBar);
        if (progressBar != null) {
            progressBar.setVisibility(View.GONE);
        }
    }
    
    @Override
    public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
        super.onReceivedError(view, errorCode, description, failingUrl);
        ProgressBar progressBar = (ProgressBar) activity.findViewById(R.id.progressBar);
        if (progressBar != null) {
            progressBar.setVisibility(View.GONE);
        }
        Toast.makeText(activity, "Error: " + description, Toast.LENGTH_LONG).show();
    }
}

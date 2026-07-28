package com.filteradium.app;

import android.app.Activity;
import android.view.View;
import android.webkit.WebChromeClient;
import android.webkit.WebView;
import android.widget.ProgressBar;

public class FilteradiumChromeClient extends WebChromeClient {
    
    private Activity activity;
    
    public FilteradiumChromeClient(Activity activity) {
        this.activity = activity;
    }
    
    @Override
    public void onProgressChanged(WebView view, int newProgress) {
        ProgressBar progressBar = (ProgressBar) activity.findViewById(R.id.progressBar);
        if (progressBar != null) {
            if (newProgress < 100) {
                progressBar.setVisibility(View.VISIBLE);
                progressBar.setProgress(newProgress);
            } else {
                progressBar.setVisibility(View.GONE);
            }
        }
    }
}

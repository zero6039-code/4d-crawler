package com.my4d.viewer

import android.app.Activity
import android.app.AlertDialog
import android.app.DownloadManager
import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : Activity() {

    companion object {
        private const val START_URL = "https://my4d.vercel.app"
        private const val ALLOWED_HOST = "my4d.vercel.app"
        private const val VERSION_URL = "https://my4d.vercel.app/version.json"
    }

    private lateinit var webView: WebView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        webView = WebView(this)
        setContentView(webView)

        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
        }

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(
                view: WebView?,
                request: WebResourceRequest?
            ): Boolean {
                val uri = request?.url ?: return true
                val allowed = uri.scheme == "https" && uri.host == ALLOWED_HOST
                if (allowed) return false
                try {
                    startActivity(Intent(Intent.ACTION_VIEW, uri))
                } catch (_: ActivityNotFoundException) {
                }
                return true
            }
        }

        webView.loadUrl(START_URL)
        checkUpdate()
    }

    private fun checkUpdate() {
        Thread {
            try {
                val conn = URL(VERSION_URL).openConnection() as HttpURLConnection
                conn.connectTimeout = 5000
                conn.readTimeout = 5000
                val text = conn.inputStream.bufferedReader().use { it.readText() }
                val json = JSONObject(text)
                if (json.getInt("versionCode") > packageManager.getPackageInfo(packageName, 0).versionCode) {
                    val url = json.getString("apkUrl")
                    runOnUiThread { showUpdateDialog(url) }
                }
            } catch (_: Exception) {
            }
        }.start()
    }

    private fun showUpdateDialog(url: String) {
        AlertDialog.Builder(this)
            .setTitle("新版本可用")
            .setMessage("检测到新版本，是否下载更新？")
            .setPositiveButton("更新") { _, _ ->
                val req = DownloadManager.Request(Uri.parse(url)).apply {
                    setTitle("my4d 更新")
                    setDescription("正在下载新版本")
                    setNotificationVisibility(
                        DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED
                    )
                }
                (getSystemService(DOWNLOAD_SERVICE) as DownloadManager).enqueue(req)
            }
            .setNegativeButton("取消", null)
            .show()
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }
}

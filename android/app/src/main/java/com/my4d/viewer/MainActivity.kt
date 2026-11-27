package com.my4d.viewer

import android.app.Activity
import android.app.AlertDialog
import android.app.DownloadManager
import android.content.ActivityNotFoundException
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.view.ViewGroup
import android.webkit.RenderProcessGoneDetail
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest

class MainActivity : Activity() {

    companion object {
        private const val START_URL = "https://my4d.vercel.app"
        private const val ALLOWED_HOST = "my4d.vercel.app"
        private const val VERSION_URL = "https://my4d.vercel.app/version.json"
        private const val MAX_VERSION_JSON = 4096
        private val EXTERNAL_SCHEMES = setOf("https", "http", "mailto", "tel")
    }

    private lateinit var webView: WebView
    private var downloadId = -1L
    private var expectedSha256: String? = null
    private var receiverRegistered = false

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
                if (uri.scheme in EXTERNAL_SCHEMES) {
                    try {
                        startActivity(Intent(Intent.ACTION_VIEW, uri))
                    } catch (_: ActivityNotFoundException) {
                    }
                }
                return true
            }

            override fun onRenderProcessGone(view: WebView, detail: RenderProcessGoneDetail): Boolean {
                (view.parent as? ViewGroup)?.removeView(view)
                view.destroy()
                this@MainActivity.recreate()
                return true
            }
        }

        webView.loadUrl(START_URL)
        checkUpdate()
    }

    private fun checkUpdate() {
        Thread {
            var conn: HttpURLConnection? = null
            try {
                conn = (URL(VERSION_URL).openConnection() as HttpURLConnection).apply {
                    connectTimeout = 5000
                    readTimeout = 5000
                    instanceFollowRedirects = false
                }
                if (conn.responseCode != HttpURLConnection.HTTP_OK) return@Thread
                val text = conn.inputStream.bufferedReader().use { it.readText() }
                if (text.length > MAX_VERSION_JSON) return@Thread
                val json = JSONObject(text)
                val sha = json.getString("sha256").lowercase()
                val url = Uri.parse(json.getString("apkUrl"))
                val valid = url.scheme == "https" && url.host == ALLOWED_HOST &&
                    url.path?.endsWith(".apk") == true && Regex("^[0-9a-f]{64}$").matches(sha)
                if (valid && json.getLong("versionCode") > installedVersionCode()) {
                    runOnUiThread {
                        if (!isFinishing && !isDestroyed) showUpdateDialog(url, sha)
                    }
                }
            } catch (_: Exception) {
            } finally {
                conn?.disconnect()
            }
        }.start()
    }

    @Suppress("DEPRECATION")
    private fun installedVersionCode(): Long {
        val info = packageManager.getPackageInfo(packageName, 0)
        return if (Build.VERSION.SDK_INT >= 28) info.longVersionCode else info.versionCode.toLong()
    }

    @Suppress("DEPRECATION")
    private fun signedByUs(apk: java.io.File): Boolean {
        val same = if (Build.VERSION.SDK_INT >= 28) {
            val flags = PackageManager.GET_SIGNING_CERTIFICATES
            val theirs = packageManager.getPackageArchiveInfo(apk.path, flags)?.signingInfo?.apkContentsSigners ?: return false
            val mine = packageManager.getPackageInfo(packageName, flags).signingInfo?.apkContentsSigners ?: return false
            theirs.toSet() == mine.toSet()
        } else {
            val flags = PackageManager.GET_SIGNATURES
            val theirs = packageManager.getPackageArchiveInfo(apk.path, flags)?.signatures ?: return false
            val mine = packageManager.getPackageInfo(packageName, flags).signatures ?: return false
            theirs.toSet() == mine.toSet()
        }
        return same
    }

    private fun showUpdateDialog(url: Uri, sha256: String) {
        AlertDialog.Builder(this)
            .setTitle("新版本可用")
            .setMessage("检测到新版本，是否下载更新？")
            .setPositiveButton("更新") { _, _ ->
                expectedSha256 = sha256
                val req = DownloadManager.Request(url).apply {
                    setTitle("my4d 更新")
                    setDescription("正在下载新版本")
                    setMimeType("application/vnd.android.package-archive")
                    setDestinationInExternalFilesDir(
                        this@MainActivity,
                        Environment.DIRECTORY_DOWNLOADS,
                        "my4d-update.apk"
                    )
                    setNotificationVisibility(
                        DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED
                    )
                }
                downloadId = (getSystemService(DOWNLOAD_SERVICE) as DownloadManager).enqueue(req)
                registerDownloadReceiver()
            }
            .setNegativeButton("取消", null)
            .show()
    }

    private fun registerDownloadReceiver() {
        if (receiverRegistered) return
        val filter = IntentFilter(DownloadManager.ACTION_DOWNLOAD_COMPLETE)
        if (Build.VERSION.SDK_INT >= 33) {
            registerReceiver(downloadDone, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            @Suppress("DEPRECATION")
            registerReceiver(downloadDone, filter)
        }
        receiverRegistered = true
    }

    private val downloadDone = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            if (intent.getLongExtra(DownloadManager.EXTRA_DOWNLOAD_ID, -1L) != downloadId) return
            val dm = getSystemService(DOWNLOAD_SERVICE) as DownloadManager
            val uri = dm.getUriForDownloadedFile(downloadId) ?: return
            val ok = try {
                sha256Of(uri) == expectedSha256
            } catch (_: Exception) {
                false
            }
            if (!ok) {
                dm.remove(downloadId)
                expectedSha256 = null
                if (!isFinishing && !isDestroyed) {
                    AlertDialog.Builder(this@MainActivity)
                        .setMessage("更新包校验失败，已丢弃。")
                        .setPositiveButton("确定", null)
                        .show()
                }
                return
            }
            val apk = java.io.File(getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS)?.path ?: "", "my4d-update.apk")
            if (!signedByUs(apk)) {
                dm.remove(downloadId)
                expectedSha256 = null
                if (!isFinishing && !isDestroyed) {
                    AlertDialog.Builder(this@MainActivity)
                        .setMessage("更新包签名与当前应用不一致，已丢弃。")
                        .setPositiveButton("确定", null)
                        .show()
                }
                return
            }
            try {
                startActivity(Intent(Intent.ACTION_VIEW).apply {
                    setDataAndType(uri, "application/vnd.android.package-archive")
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                })
            } catch (_: ActivityNotFoundException) {
            }
        }
    }

    private fun sha256Of(uri: Uri): String {
        val md = MessageDigest.getInstance("SHA-256")
        contentResolver.openInputStream(uri)!!.use { s ->
            val buf = ByteArray(8192)
            while (true) {
                val n = s.read(buf)
                if (n < 0) break
                md.update(buf, 0, n)
            }
        }
        return md.digest().joinToString("") { "%02x".format(it) }
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }

    override fun onDestroy() {
        if (receiverRegistered) {
            try {
                unregisterReceiver(downloadDone)
            } catch (_: IllegalArgumentException) {
            }
            receiverRegistered = false
        }
        if (::webView.isInitialized) {
            (webView.parent as? ViewGroup)?.removeView(webView)
            webView.destroy()
        }
        super.onDestroy()
    }
}

# my4d Android viewer

- Package: com.my4d.viewer
- URL: https://my4d.vercel.app (exact host/scheme)
- External links: system browser via Intent.ACTION_VIEW
- JS: enabled for site rendering; file/content and cleartext blocked

Build:
    sdkmanager "platforms;android-36"
    export KEYSTORE_PATH=/path/to/release.jks
    export KS_PASS=...
    export KEY_ALIAS=...
    export KEY_PASS=...
    ./gradlew assembleRelease

Output: app/build/outputs/apk/release/app-release.apk

Verify:
    $ANDROID_SDK_ROOT/build-tools/34.0.0/apksigner verify --verbose --print-certs app/build/outputs/apk/release/app-release.apk
    sha256sum app/build/outputs/apk/release/app-release.apk

Expected: debuggable=false, allowBackup=false, v1/v2/v3 true, signer not Android Debug.

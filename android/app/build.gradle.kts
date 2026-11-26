import java.io.File

val keystorePath: String? = System.getenv("KEYSTORE_PATH")
val ksPass: String? = System.getenv("KS_PASS")
val envKeyAlias: String? = System.getenv("KEY_ALIAS")
val keyPass: String? = System.getenv("KEY_PASS")

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.my4d.viewer"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.my4d.viewer"
        minSdk = 24
        targetSdk = 36
        versionCode = 4
        versionName = "1.2.1"
    }

    signingConfigs {
        create("release") {
            if (keystorePath != null) {
                storeFile = File(keystorePath)
                storePassword = ksPass
                keyAlias = envKeyAlias
                keyPassword = keyPass
            }
        }
    }

    buildTypes {
        getByName("release") {
            isMinifyEnabled = true
            isShrinkResources = true
            isDebuggable = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            if (keystorePath != null) {
                signingConfig = signingConfigs.getByName("release")
            }
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
}

afterEvaluate {
    tasks.matching { it.name == "assembleRelease" || it.name == "bundleRelease" }.configureEach {
        doFirst {
            check(keystorePath != null && ksPass != null && envKeyAlias != null && keyPass != null) {
                "Release 构建需要 KEYSTORE_PATH / KS_PASS / KEY_ALIAS / KEY_PASS"
            }
        }
    }
}

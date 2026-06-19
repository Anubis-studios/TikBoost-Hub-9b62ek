import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FLUTTER_DIR = os.path.join(ROOT, "flutter_sdk")
FLUTTER_MODULE = os.path.join(ROOT, "flutter_module")
ANDROID_DIR = os.path.join(ROOT, "android")
APP_DIR = os.path.join(ANDROID_DIR, "app")
LIBS_DIR = os.path.join(APP_DIR, "libs")

def run(cmd, cwd=None):
    print(f"\n>>> Running: {cmd}")
    subprocess.check_call(cmd, shell=True, cwd=cwd)

def ensure_flutter():
    if not os.path.isdir(FLUTTER_DIR):
        print("Cloning Flutter SDK...")
        run(f"git clone https://github.com/flutter/flutter.git -b stable {FLUTTER_DIR}")
    os.environ["PATH"] = FLUTTER_DIR + "/bin:" + os.environ["PATH"]
    run("flutter doctor")

def build_flutter_module():
    print("Building Flutter module (AAR)...")
    run("flutter build aar", cwd=FLUTTER_MODULE)

def inject_flutter_into_android():
    print("Injecting Flutter AARs into Android project...")

    os.makedirs(LIBS_DIR, exist_ok=True)

    repo_path = os.path.join(
        FLUTTER_MODULE, "build", "host", "outputs", "repo"
    )

    if not os.path.isdir(repo_path):
        raise Exception("Flutter AAR repo not found. Build failed.")

    # Copy AAR repo into Android libs
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            src = os.path.join(root, file)
            dst = os.path.join(LIBS_DIR, file)
            shutil.copy(src, dst)

    # Modify settings.gradle
    settings_gradle = os.path.join(ANDROID_DIR, "settings.gradle")
    flutter_settings = """

// Flutter module repo
include ':flutter'
project(':flutter').projectDir = new File('../flutter_module')
"""

    with open(settings_gradle, "a") as f:
        f.write(flutter_settings)

    # Modify app/build.gradle
    app_gradle = os.path.join(APP_DIR, "build.gradle")
    with open(app_gradle, "r") as f:
        content = f.read()

    if "implementation project(':flutter')" not in content:
        content = content.replace(
            "dependencies {",
            "dependencies {\n    implementation project(':flutter')"
        )

    with open(app_gradle, "w") as f:
        f.write(content)

    # Inject FlutterActivity into AndroidManifest
    manifest = os.path.join(APP_DIR, "src/main/AndroidManifest.xml")
    with open(manifest, "r") as f:
        manifest_content = f.read()

    if "io.flutter.embedding.android.FlutterActivity" not in manifest_content:
        insert = """
        <activity
            android:name="io.flutter.embedding.android.FlutterActivity"
            android:theme="@style/LaunchTheme"
            android:configChanges="orientation|keyboardHidden|keyboard|screenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode"
            android:hardwareAccelerated="true"
            android:windowSoftInputMode="adjustResize" />
        """

        manifest_content = manifest_content.replace("</application>", insert + "\n</application>")

        with open(manifest, "w") as f:
            f.write(manifest_content)

def build_android():
    print("Building Android APK...")
    run("./gradlew assembleRelease", cwd=ANDROID_DIR)

def main():
    print("=== FULL BUILD STARTED ===")

    ensure_flutter()
    build_flutter_module()
    inject_flutter_into_android()
    build_android()

    print("\n=== BUILD COMPLETE ===")
    print("APK output located in: android/app/build/outputs/apk/release/")

if __name__ == "__main__":
    main() 

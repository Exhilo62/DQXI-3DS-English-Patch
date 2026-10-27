# DQXI English Patcher for Android

A small Android app that patches the user's own decrypted Japanese Dragon Quest XI (`.3ds` or `.cia`) on the device. It bundles the same
Python patcher as the PC / Linux tool (`cia_patcher.py`, run with [Chaquopy](https://chaquo.com/chaquopy/)), so the result is identical.

1. **Choose the Japanese game file** (Android file picker).
2. **Output format**: `.3ds` (emulators such as Azahar) or `.cia` (install on a 3DS with FBI). A `.cia` source can only become a `.cia`.
3. **Patch**, then choose where to save. Progress bar, log, final check; the original file is never changed.

How it works: `PatchService` (a foreground service, so it keeps running in the background / with the screen off, with a progress
notification) runs `app/src/main/python/patcher_bridge.py`, which calls `cia_patcher.patch()` + `verify_output()`. The game is read and the
result is written **directly through file descriptors** (`/proc/self/fd/N` symlinks named `input.3ds` / `output.cia`, which the Python code
needs for the file extension); no copy of the game is made. If the system does not allow that, the service falls back to temporary copies
in the app's storage (needs about twice the game's size free) and says so in the log.

## Build

`build_apk.bat` copies `cia_patcher.py`, `dqxi_blz.py`, `dqxi_en_patcher.py`, `dqxi_en.dqp`, `code.ips`, `cia_templates.bin` and `VERSION`
from `..\release` into the app, then runs Gradle. Needs a JDK 17+, the Android SDK (platform 34, build-tools 34.0.0) and **Python 3.14**
on the build PC (Chaquopy uses the same version at build time).

* `build_apk.bat` -> debug APK `app\build\outputs\apk\debug\app-debug.apk`
* `build_apk.bat release` -> signed release APK, also copied to `..\release\dist\DQXI_English_Patcher_Android_v<version>.apk`

### Signing (important)

The release APK is signed with `dqxi-release.keystore` (settings in `keystore.properties`; both are git-ignored and must never be
published). **Back up both files somewhere safe.** Android only installs an update over an installed app if it is signed with the same key;
without the keystore every user would have to uninstall the app before updating. A debug build is signed with a different key, so
uninstall it before installing the release APK.

## Tested

Retroid Pocket Duo Lite (Android 15): `.cia` -> `.cia` and `.3ds` -> `.cia`, about 6.5 minutes each; the patch keeps running with the app in
the background and the screen off; direct file reading works on that device; results are byte-identical to the PC builds (SHA-1).

## Not done yet

* Only arm64 devices (`abiFilters 'arm64-v8a'`); add `armeabi-v7a` / `x86_64` if needed.
* Luma-folder export (`--export`) is not in the app.
* Not tested on other phones / Android versions; the notification permission (Android 13+) is only used for the progress notification.

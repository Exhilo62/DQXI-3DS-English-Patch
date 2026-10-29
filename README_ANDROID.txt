Dragon Quest XI (3DS, Japanese) - English Patch - ANDROID (Termux)
==================================================================

EASIEST: THE ANDROID APP
------------------------
Download DQXI_English_Patcher_Android_v0.1.29.apk from the GitHub release page and open it on the device (Android asks you to allow "install unknown apps" for the
app you opened it from; it is not from the Play Store, so Play Protect may warn). Then: choose your decrypted Japanese .3ds / .cia,
choose the output (.3ds for emulators such as Azahar, .cia for a 3DS), press Patch and choose where to save. It keeps running in the
background (a notification shows the progress) and takes about 6 minutes on a Retroid Pocket Duo Lite. arm64 devices only.
Everything below is the alternative for people who prefer a terminal (Termux).

For phones / tablets without a PC. You need your own DECRYPTED Japanese game (.3ds or .cia) on the device
(see README.txt, "GodMode9: Decrypt file (SD output)"). This package contains no game data.

You need about twice the size of the game in free storage (a .cia is about 2.7 GB, a .3ds about 4 GB, so 6 - 9 GB free),
and a few minutes to an hour of patching depending on the device (about 1 minute on a PC; it uses little memory, about 300 MB). Tested on a Retroid Pocket Duo Lite (Android 15): about 4 minutes for a .cia or a .3ds, identical result to the PC, and the .3ds boots in Azahar to the English title screen. Other phones are untested: if something goes wrong, tell us in the Discord with your phone model and Android version.

1. Install Termux from F-Droid (f-droid.org) or the Termux GitHub releases. Do NOT use the Play Store version (outdated).
2. Copy the downloaded zip (DQXI_3DS_English_Patch_Linux_vX.Y.Z.zip) and your decrypted game into the Download folder.
3. Open Termux and type these lines (one at a time):

       termux-setup-storage            (press Allow when Android asks)
       echo "deb https://packages.termux.dev/apt/termux-main stable main" > $PREFIX/etc/apt/sources.list
       pkg update -y
       pkg install -y python unzip
       cd ~/storage/downloads
       unzip DQXI_3DS_English_Patch_Linux_v*.zip
       cd DQXI_English_Patch
       bash patch_android.sh

   The script finds your .3ds / .cia in Downloads (or pass the path: bash patch_android.sh "/storage/emulated/0/Download/game.3ds").
4. Wait until it says Done. Keep the screen on and Termux in the foreground (the script asks Android not to sleep).
5. Your patched game is next to the original, named "... (English).3ds" (or .cia).
   Azahar / Citra only list .3ds files (they do not list a .cia): patch a .3ds, copy the "... (English).3ds" into your
   games folder and start it from the game list. A .cia is for installing on a real 3DS (FBI).

Notes
 * The 'echo ... sources.list' line picks Termux's main download server. Without it Termux may pick a random mirror that is
   out of date and fail with "Some index files failed to download" (this happened in our test).
 * A .3ds gives a patched .3ds (for emulators). Installing on a real 3DS needs a .cia: patch a .cia (or use the PC tool).
 * If the phone stops the app mid-way, turn off battery optimisation for Termux and try again.
 * Your original file is never modified.
 * Made with AI assistance (Anthropic's Claude) and the author's direction and testing.
   File-format tooling is based on dqxi-format-tools by Kenzie-1377 (MIT).

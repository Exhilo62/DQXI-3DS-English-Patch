@echo off
rem Builds the DQXI English Patcher Android app: debug APK (app\build\outputs\apk\debug\app-debug.apk); with the argument "release" the
rem signed release APK (needs keystore.properties + dqxi-release.keystore), also copied to ..\release\dist\DQXI_English_Patcher_Android_v<version>.apk.
rem Needs: a JDK 17+, the Android SDK (platform 34, build-tools 34.0.0) and Python 3.14 on this PC (Chaquopy uses it at build time).
rem Copies the patcher code and patch data from ..\release into the app first, so the app always matches the release build.
if "%JAVA_HOME%"=="" set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot
if "%ANDROID_HOME%"=="" set ANDROID_HOME=D:\android-sdk\sdk
set PATH=%JAVA_HOME%\bin;%PATH%
cd /d %~dp0
set REL=%~dp0..\release
if not exist "%REL%\cia_patcher.py" set REL=%~dp0..
set PY=%~dp0app\src\main\python
set AS=%~dp0app\src\main\assets
if not exist "%AS%" mkdir "%AS%"
copy /y "%REL%\cia_patcher.py" "%PY%\" >nul || exit /b 1
copy /y "%REL%\dqxi_blz.py" "%PY%\" >nul || exit /b 1
copy /y "%REL%\dqxi_en_patcher.py" "%PY%\" >nul || exit /b 1
copy /y "%REL%\dqxi_en.dqp" "%AS%\" >nul || exit /b 1
copy /y "%REL%\code.ips" "%AS%\" >nul || exit /b 1
copy /y "%REL%\cia_templates.bin" "%AS%\" >nul || exit /b 1
copy /y "%REL%\VERSION" "%AS%\" >nul || exit /b 1
if not exist gradlew.bat (
  if exist D:\android-sdk\gradle-8.7\bin\gradle.bat call D:\android-sdk\gradle-8.7\bin\gradle.bat wrapper --gradle-version 8.7 || exit /b 1
)
set /p VER=<"%REL%\VERSION"
if /i "%~1"=="release" (
  call "%~dp0gradlew.bat" --no-daemon assembleRelease || exit /b 1
  if not exist "%REL%\dist" mkdir "%REL%\dist"
  copy /y "%~dp0app\build\outputs\apk\release\app-release.apk" "%REL%\dist\DQXI_English_Patcher_Android_v%VER%.apk" >nul || exit /b 1
) else (
  call "%~dp0gradlew.bat" --no-daemon %* assembleDebug
)

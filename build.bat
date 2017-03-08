@echo off
call gradlew build vocBuild
call gradlew installDebug run
call adb shell am start -n org.grapesoda.chessclock/android.PythonActivity

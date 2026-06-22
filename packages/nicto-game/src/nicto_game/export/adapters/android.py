"""Android export adapter — generates Pygame Substrate APK project."""

from __future__ import annotations
import os
from pathlib import Path

from nicto_game.export.adapters.base import PlatformAdapter


class AndroidAdapter(PlatformAdapter):
    """Exports game project structure for Android via pygame-substrate or pgs4a."""

    def export(self, code: str, output_dir: str, game_name: str, world_data: dict) -> dict:
        android_dir = Path(output_dir) / "android"
        android_dir.mkdir(parents=True, exist_ok=True)

        main_path = android_dir / "main.py"
        with open(main_path, "w", encoding="utf-8") as f:
            f.write(code)

        manifest = (
            f'<?xml version="1.0" encoding="utf-8"?>\n'
            f'<manifest xmlns:android="http://schemas.android.com/apk/res/android"\n'
            f'    package="com.nicto.{game_name.lower().replace(" ", "").replace("_", "")}">\n'
            f'    <uses-sdk android:minSdkVersion="21" android:targetSdkVersion="33" />\n'
            f'    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />\n'
            f'    <application android:label="{game_name}" android:allowBackup="true">\n'
            f'        <activity android:name="org.renpy.android.PythonActivity"\n'
            f'            android:label="{game_name}" android:configChanges="orientation|keyboardHidden">\n'
            f'            <intent-filter>\n'
            f'                <action android:name="android.intent.action.MAIN" />\n'
            f'                <category android:name="android.intent.category.LAUNCHER" />\n'
            f'            </intent-filter>\n'
            f'        </activity>\n'
            f'    </application>\n'
            f'</manifest>\n'
        )
        manifest_path = android_dir / "AndroidManifest.xml"
        with open(manifest_path, "w") as f:
            f.write(manifest)

        build_script = (
            f'@echo off\n'
            f'REM Build {game_name} for Android\n'
            f'REM Requires: python-for-android (p4a) or pygame-substrate\n'
            f'p4a apk --requirements=pygame,numpy --private=. --package=com.nicto.{game_name.lower().replace(" ", "").replace("_", "")} '
            f'--release --name="{game_name}"\n'
        )
        build_path = android_dir / "build_android.bat"
        with open(build_path, "w") as f:
            f.write(build_script)

        return {
            "project_dir": str(android_dir),
            "main_py": str(main_path),
            "manifest": str(manifest_path),
            "platform": "android",
            "notes": "Build with python-for-android or pygame-substrate",
        }

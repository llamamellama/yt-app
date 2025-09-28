# PyInstaller spec for YouTube Downloader GUI

import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Discover optional ffmpeg/ffprobe binaries via env vars
ffmpeg_path = os.environ.get("FFMPEG_PATH")
ffprobe_path = os.environ.get("FFPROBE_PATH")

bin_adds = []
if ffmpeg_path and os.path.exists(ffmpeg_path):
    bin_adds.append((ffmpeg_path, "bin"))
if ffprobe_path and os.path.exists(ffprobe_path):
    bin_adds.append((ffprobe_path, "bin"))

hiddenimports = collect_submodules("yt_dlp")

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=bin_adds,
    datas=[
        ("gui/templates", "gui/templates"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="YouTubeDownloader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="YouTubeDownloader",
)


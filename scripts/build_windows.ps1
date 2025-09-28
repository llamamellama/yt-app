Param(
  [string]$FfmpegPath = "",
  [string]$FfprobePath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Push-Location (Split-Path -Parent $MyInvocation.MyCommand.Path) | Out-Null
Push-Location .. | Out-Null

try {
  python -c "import PyInstaller" | Out-Null
} catch {
  python -m pip install pyinstaller
}

if ($FfmpegPath) { $env:FFMPEG_PATH = $FfmpegPath }
if ($FfprobePath) { $env:FFPROBE_PATH = $FfprobePath }

python -m PyInstaller yt_downloader.spec --noconfirm

Pop-Location | Out-Null
Pop-Location | Out-Null

Write-Host "Build complete. See dist/YouTubeDownloader"


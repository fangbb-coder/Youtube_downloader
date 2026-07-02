import os
import subprocess
import sys

DENO_PATH = r"D:\程序\deno\deno.exe"
FFMPEG_PATH = r"C:\Users\win11\AppData\Local\hermes\hermes-agent\venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
SCRIPT_PATH = r"D:\程序\youtube_downloader_gui.py"
DIST_DIR = r"D:\程序\dist"

os.makedirs(DIST_DIR, exist_ok=True)

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--windowed",
    "--onefile",
    "--name", "YouTube_Downloader",
    f"--add-data={DENO_PATH};deno",
    f"--add-data={FFMPEG_PATH};ffmpeg",
    "--distpath", DIST_DIR,
    SCRIPT_PATH,
]

print(f"打包命令: {' '.join(cmd)}")
result = subprocess.run(cmd, capture_output=True, text=True)
print(f"退出码: {result.returncode}")
if result.stdout:
    print("STDOUT:\n", result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
if result.stderr:
    print("STDERR:\n", result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
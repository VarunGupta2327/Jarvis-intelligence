"""
Build script - Creates JARVIS .exe files for desktop and mobile server.
Run: python build_exe.py
"""
import subprocess
import sys
import os

BASE = os.path.dirname(os.path.abspath(__file__))
PYINSTALLER = sys.executable.replace("python.exe", "Scripts\\pyinstaller.exe")
# Fallback
if not os.path.exists(PYINSTALLER):
    PYINSTALLER = "pyinstaller"

def build():
    print("=" * 50)
    print("  Building J.A.R.V.I.S Executables")
    print("=" * 50)

    # Desktop .exe
    print("\n[1/2] Building Desktop Jarvis...")
    subprocess.run([
        PYINSTALLER,
        "--onefile",
        "--name=JARVIS_Desktop",
        "--console",
        "--add-data=jarvis_brain.py;.",
        os.path.join(BASE, "jarvis.py")
    ], cwd=BASE)

    # Mobile server .exe
    print("\n[2/2] Building Mobile Server...")
    subprocess.run([
        PYINSTALLER,
        "--onefile",
        "--name=JARVIS_Mobile",
        "--console",
        "--add-data=templates;templates",
        "--add-data=jarvis_brain.py;.",
        os.path.join(BASE, "jarvis_mobile.py")
    ], cwd=BASE)

    print("\n" + "=" * 50)
    print("  BUILD COMPLETE!")
    print(f"  Desktop: {BASE}\\dist\\JARVIS_Desktop.exe")
    print(f"  Mobile:  {BASE}\\dist\\JARVIS_Mobile.exe")
    print("=" * 50)

if __name__ == "__main__":
    build()

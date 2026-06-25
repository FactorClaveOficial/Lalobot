import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
REPORTS_DIR = Path(__file__).parent.parent / "reports"
SHERLOCK_DIR = BASE_DIR / "sherlock"


def setup():
    """Instala holehe y sherlock si no están presentes."""
    try:
        import holehe  # noqa: F401
    except ImportError:
        print("[*] Instalando holehe...")
        subprocess.run([sys.executable, "-m", "pip", "install", "holehe"], check=True)

    if not SHERLOCK_DIR.exists():
        print("[*] Clonando sherlock...")
        subprocess.run(["git", "clone", "https://github.com/sherlock-project/sherlock.git", str(SHERLOCK_DIR)])
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(SHERLOCK_DIR / "requirements.txt")])


def run_sherlock(username: str) -> Path:
    """Ejecuta Sherlock para un nombre de usuario y guarda el reporte."""
    REPORTS_DIR.mkdir(exist_ok=True)
    output_file = REPORTS_DIR / f"sherlock_{username}.txt"
    os.system(f"python3 {SHERLOCK_DIR}/sherlock {username} --timeout 2 | tee {output_file}")
    return output_file


def run_holehe(email: str) -> Path:
    """Ejecuta Holehe para un correo y guarda el reporte."""
    REPORTS_DIR.mkdir(exist_ok=True)
    output_file = REPORTS_DIR / f"holehe_{email}.txt"
    os.system(f"holehe {email} --only-used | tee {output_file}")
    return output_file


def scan(username: str = None, email: str = None):
    """Ejecuta el escaneo completo de usuario y/o email."""
    if username:
        print(f"\n{'='*40}")
        print(f" Sherlock → {username}")
        print(f"{'='*40}")
        report = run_sherlock(username)
        print(f"\n[✓] Reporte guardado: {report}")

    if email:
        print(f"\n{'='*40}")
        print(f" Holehe → {email}")
        print(f"{'='*40}")
        report = run_holehe(email)
        print(f"\n[✓] Reporte guardado: {report}")

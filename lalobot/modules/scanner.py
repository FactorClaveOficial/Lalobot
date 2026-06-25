import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

BASE_DIR = Path(__file__).parent.parent.parent
REPORTS_DIR = Path(__file__).parent.parent / "reports"
SHERLOCK_DIR = BASE_DIR / "sherlock"

_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
_PHONE_RE = re.compile(r'^\+?[\d\s\-\(\)\.]{7,20}$')
_ANSI_RE  = re.compile(r'\033\[[0-9;]+m')


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


def detect_type(value: str) -> str:
    """Detecta si el valor es 'email', 'phone' o 'username'."""
    value = value.strip()
    if _EMAIL_RE.match(value):
        return "email"
    digits = re.sub(r'\D', '', value)
    if _PHONE_RE.match(value) and 7 <= len(digits) <= 15:
        return "phone"
    return "username"


# ── Sherlock ──────────────────────────────────────────────────────────────────

def capture_sherlock(username: str) -> dict:
    """Ejecuta Sherlock y devuelve perfiles encontrados."""
    if not SHERLOCK_DIR.exists():
        return {"error": "Sherlock no instalado. Ejecuta: python3 main.py scan --user <usuario>", "found": []}
    try:
        result = subprocess.run(
            [sys.executable, "-m", "sherlock_project", username,
             "--print-found", "--no-color", "--timeout", "10"],
            capture_output=True, text=True, timeout=120,
            cwd=str(SHERLOCK_DIR)
        )
        raw = result.stdout
        found = []
        for line in raw.splitlines():
            m = re.match(r'\[\+\]\s+(.+?):\s+(https?://\S+)', line)
            if m:
                found.append({"platform": m.group(1).strip(), "url": m.group(2).strip()})
        return {"found": found, "total": len(found)}
    except subprocess.TimeoutExpired:
        return {"error": "Timeout (>120s)", "found": []}
    except Exception as e:
        return {"error": str(e), "found": []}


# ── Holehe ────────────────────────────────────────────────────────────────────

def capture_holehe(email: str) -> dict:
    """Ejecuta Holehe y devuelve servicios encontrados."""
    try:
        result = subprocess.run(
            ["holehe", email, "--only-used"],
            capture_output=True, text=True, timeout=90
        )
        raw = _ANSI_RE.sub('', result.stdout + result.stderr)
        found, not_found = [], []
        for line in raw.splitlines():
            if re.match(r'\[\+\]', line):
                name = re.sub(r'\[\+\]\s*', '', line).split('(')[0].strip()
                if name:
                    found.append({"service": name})
            elif re.match(r'\[-\]', line):
                name = re.sub(r'\[-\]\s*', '', line).split('(')[0].strip()
                if name:
                    not_found.append({"service": name})
        return {"found": found, "not_found": not_found, "total": len(found)}
    except subprocess.TimeoutExpired:
        return {"error": "Timeout (>90s)", "found": [], "not_found": []}
    except FileNotFoundError:
        return {"error": "Holehe no instalado. Ejecuta: pip install holehe", "found": [], "not_found": []}
    except Exception as e:
        return {"error": str(e), "found": [], "not_found": []}


# ── Teléfono ──────────────────────────────────────────────────────────────────

def phone_dorks(phone: str) -> list:
    """Genera links de búsqueda OSINT para un número de teléfono."""
    q = quote(phone)
    raw = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    return [
        {"name": "Google", "url": f"https://www.google.com/search?q=%22{q}%22"},
        {"name": "Google (redes sociales)", "url": f"https://www.google.com/search?q=%22{q}%22+site%3Afacebook.com+OR+site%3Atwitter.com+OR+site%3Alinkedin.com"},
        {"name": "Truecaller", "url": f"https://www.truecaller.com/search/mx/{raw}"},
        {"name": "NumLookup", "url": f"https://www.numlookup.com/phone-lookup/{raw}"},
        {"name": "WhoCalledMe", "url": f"https://whocalledme.com/PhoneNumber/{raw}"},
        {"name": "SpyDialer", "url": f"https://www.spydialer.com/default.aspx?phone={raw}"},
    ]


# ── CLI ───────────────────────────────────────────────────────────────────────

def run_sherlock(username: str) -> Path:
    """Ejecuta Sherlock (modo CLI) y guarda el reporte."""
    import os
    REPORTS_DIR.mkdir(exist_ok=True)
    output_file = REPORTS_DIR / f"sherlock_{username}.txt"
    os.system(f"cd {SHERLOCK_DIR} && python3 -m sherlock_project {username} --timeout 10 | tee {output_file}")
    return output_file


def run_holehe(email: str) -> Path:
    """Ejecuta Holehe (modo CLI) y guarda el reporte."""
    import os
    REPORTS_DIR.mkdir(exist_ok=True)
    output_file = REPORTS_DIR / f"holehe_{email}.txt"
    os.system(f"holehe {email} --only-used | tee {output_file}")
    return output_file


def scan(username: str = None, email: str = None):
    """Ejecuta el escaneo completo (modo CLI)."""
    if username:
        print(f"\n{'='*40}\n Sherlock → {username}\n{'='*40}")
        report = run_sherlock(username)
        print(f"\n[✓] Reporte guardado: {report}")
    if email:
        print(f"\n{'='*40}\n Holehe → {email}\n{'='*40}")
        report = run_holehe(email)
        print(f"\n[✓] Reporte guardado: {report}")

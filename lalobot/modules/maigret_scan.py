import re
import subprocess
import sys


def setup():
    try:
        subprocess.run(
            [sys.executable, "-m", "maigret", "--version"],
            capture_output=True, timeout=5, check=True
        )
    except Exception:
        print("[*] Instalando maigret...")
        subprocess.run([sys.executable, "-m", "pip", "install", "maigret"], check=True)


def capture_maigret(username: str) -> dict:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "maigret", username,
             "--no-color", "--timeout", "10"],
            capture_output=True, text=True, timeout=150
        )
        found = []
        for line in result.stdout.splitlines():
            m = re.match(r'\[\+\]\s+(.+?):\s+(https?://\S+)', line)
            if m:
                found.append({"platform": m.group(1).strip(), "url": m.group(2).strip()})
        return {"found": found, "total": len(found)}
    except subprocess.TimeoutExpired:
        return {"error": "Timeout (>150s)", "found": []}
    except Exception as e:
        return {"error": str(e), "found": []}

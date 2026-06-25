import re
import subprocess


def is_configured() -> bool:
    try:
        r = subprocess.run(["ghunt", "--version"], capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def capture_ghunt(email: str) -> dict:
    try:
        result = subprocess.run(
            ["ghunt", "email", email],
            capture_output=True, text=True, timeout=60
        )
        output = result.stdout + result.stderr

        if "not logged" in output.lower() or "login" in output.lower():
            return {"error": "GHunt no autenticado. Ejecuta: ghunt login", "data": {}}

        data = {}

        m = re.search(r'Name\s*[:\-]\s*(.+)', output, re.IGNORECASE)
        if m:
            data['name'] = m.group(1).strip()

        m = re.search(r'Gaia ID\s*[:\-]\s*(\d+)', output, re.IGNORECASE)
        if m:
            data['gaia_id'] = m.group(1).strip()

        m = re.search(r'Profile photo\s*[:\-]\s*(https?://\S+)', output, re.IGNORECASE)
        if m:
            data['photo'] = m.group(1).strip()

        m = re.search(r'Last profile edit\s*[:\-]\s*(.+)', output, re.IGNORECASE)
        if m:
            data['last_edit'] = m.group(1).strip()

        services = re.findall(r'\[✓\]\s+(.+)', output)
        if services:
            data['services'] = services

        activated = re.findall(r'\[\+\]\s+(.+)', output)
        if activated:
            data['activated'] = activated

        if not data:
            return {"error": "Sin resultados o cuenta no encontrada", "data": {}}

        return {"data": data}
    except FileNotFoundError:
        return {"error": "GHunt no instalado. Ejecuta: pip install ghunt && ghunt login", "data": {}}
    except subprocess.TimeoutExpired:
        return {"error": "Timeout (>60s)", "data": {}}
    except Exception as e:
        return {"error": str(e), "data": {}}
